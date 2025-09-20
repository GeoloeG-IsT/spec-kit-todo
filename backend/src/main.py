"""
FastAPI application entry point for the TODO list API.

This module initializes the FastAPI application with all necessary configurations,
middleware, routes, and error handlers.
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment from: {env_path}")
    else:
        print(f"No .env file found at: {env_path}")
except ImportError:
    print("python-dotenv not available, skipping .env file loading")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog

from .api.middleware.error_handler import ErrorHandlerMiddleware
from .api.middleware.auth import AuthMiddleware
from .api.middleware.session import SessionMiddleware
from .api.routes import auth, todos, stream, dev_auth
from .infrastructure.database import create_tables, close_database
from .domain.schemas import HealthResponse, ErrorResponse

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting TODO List API")
    try:
        await create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down TODO List API")
    try:
        await close_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error("Error closing database connections", error=str(e))


# Create FastAPI application
app = FastAPI(
    title="TODO List API",
    description="A cyberpunk-themed TODO list application with guest and authenticated user support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js development server
        "http://127.0.0.1:3000",  # Alternative localhost
        "https://*.vercel.app",   # Vercel deployments
        "https://*.cloud.run",    # Google Cloud Run
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(SessionMiddleware)
app.add_middleware(AuthMiddleware)

# Include API routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(todos.router, prefix="/api/todos", tags=["TODOs"])
app.include_router(stream.router, prefix="/api/todos", tags=["Real-time"])

# Include development auth routes (only in development)
import os
if os.getenv("ENVIRONMENT", "development").lower() == "development":
    app.include_router(dev_auth.router, prefix="/api/auth/dev", tags=["Development Auth"])


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns the current status of the API service.
    """
    return HealthResponse()


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint providing basic API information.
    """
    return {
        "message": "TODO List API",
        "version": "1.0.0",
        "description": "A cyberpunk-themed TODO list application",
        "docs": "/docs",
        "health": "/health"
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle FastAPI request validation errors."""
    from .api.middleware.error_handler import ValidationErrorHandler

    return JSONResponse(
        status_code=422,
        content=ValidationErrorHandler.format_validation_error(exc).model_dump()
    )


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 Not Found errors."""
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error="not_found",
            message="The requested resource was not found"
        ).model_dump()
    )


@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    """Handle 500 Internal Server Error."""
    logger.error("Internal server error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_error",
            message="An unexpected error occurred"
        ).model_dump()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )