"""
Error handling middleware for consistent API error responses.

Catches and formats exceptions into standardized error responses,
logs errors appropriately, and ensures proper HTTP status codes.
"""

import traceback
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from ...domain.schemas import ErrorResponse

logger = structlog.get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling exceptions and formatting error responses."""

    def _add_cors_headers(self, response: JSONResponse, request: Request) -> JSONResponse:
        """
        Add CORS headers to error responses to prevent browser blocking.

        Args:
            response: JSONResponse to add headers to
            request: Original request for determining origin

        Returns:
            Response with CORS headers added
        """
        # Get origin from request
        origin = request.headers.get("origin")

        # Define allowed origins (same as in main.py)
        allowed_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]

        # Check if origin is allowed
        if origin and (origin in allowed_origins or origin.endswith(".vercel.app") or origin.endswith(".cloud.run")):
            response.headers["Access-Control-Allow-Origin"] = origin
        elif not origin:
            # For same-origin requests or when no origin header
            response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"

        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"

        return response

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and handle any exceptions that occur.

        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler

        Returns:
            Response object
        """
        try:
            response = await call_next(request)
            return response

        except ValueError as e:
            # Client errors (400 Bad Request)
            logger.warning("Client error occurred",
                         error=str(e), path=request.url.path, method=request.method)
            response = JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error="bad_request",
                    message=str(e)
                ).model_dump()
            )
            return self._add_cors_headers(response, request)

        except PermissionError as e:
            # Authorization errors (403 Forbidden)
            logger.warning("Permission denied",
                         error=str(e), path=request.url.path, method=request.method)
            response = JSONResponse(
                status_code=403,
                content=ErrorResponse(
                    error="forbidden",
                    message="Access denied"
                ).model_dump()
            )
            return self._add_cors_headers(response, request)

        except FileNotFoundError as e:
            # Not found errors (404 Not Found)
            logger.warning("Resource not found",
                         error=str(e), path=request.url.path, method=request.method)
            response = JSONResponse(
                status_code=404,
                content=ErrorResponse(
                    error="not_found",
                    message="Resource not found"
                ).model_dump()
            )
            return self._add_cors_headers(response, request)

        except NotImplementedError as e:
            # Method not allowed (501 Not Implemented)
            logger.warning("Method not implemented",
                         error=str(e), path=request.url.path, method=request.method)
            response = JSONResponse(
                status_code=501,
                content=ErrorResponse(
                    error="not_implemented",
                    message="This feature is not yet implemented"
                ).model_dump()
            )
            return self._add_cors_headers(response, request)

        except Exception as e:
            # Unexpected server errors (500 Internal Server Error)
            error_id = self._log_server_error(e, request)

            response = JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    error="internal_error",
                    message="An unexpected error occurred",
                    details={"error_id": error_id} if error_id else None
                ).model_dump()
            )
            return self._add_cors_headers(response, request)

    def _log_server_error(self, error: Exception, request: Request) -> str:
        """
        Log server error with full context and return error ID.

        Args:
            error: Exception that occurred
            request: FastAPI request object

        Returns:
            Error ID for tracking
        """
        import uuid
        error_id = str(uuid.uuid4())

        # Get request details
        request_details = {
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "headers": dict(request.headers),
            "client_ip": request.client.host if request.client else None
        }

        # Log the error with full context
        logger.error(
            "Unhandled server error",
            error_id=error_id,
            error=str(error),
            error_type=type(error).__name__,
            traceback=traceback.format_exc(),
            request=request_details
        )

        return error_id


class ValidationErrorHandler:
    """Helper class for handling Pydantic validation errors."""

    @staticmethod
    def format_validation_error(error) -> ErrorResponse:
        """
        Format Pydantic validation error into standardized response.

        Args:
            error: Pydantic ValidationError

        Returns:
            Formatted error response
        """
        # Extract field errors
        field_errors = {}
        for err in error.errors():
            field_path = ".".join(str(x) for x in err["loc"])
            field_errors[field_path] = err["msg"]

        return ErrorResponse(
            error="validation_error",
            message="Request validation failed",
            details={
                "field_errors": field_errors,
                "error_count": len(error.errors())
            }
        )


class DatabaseErrorHandler:
    """Helper class for handling database-related errors."""

    @staticmethod
    def format_database_error(error) -> ErrorResponse:
        """
        Format database error into user-friendly response.

        Args:
            error: Database exception

        Returns:
            Formatted error response
        """
        error_str = str(error).lower()

        # Handle common database constraint violations
        if "unique constraint" in error_str or "duplicate key" in error_str:
            return ErrorResponse(
                error="duplicate_resource",
                message="A resource with these details already exists"
            )
        elif "foreign key constraint" in error_str:
            return ErrorResponse(
                error="invalid_reference",
                message="Referenced resource does not exist"
            )
        elif "not null constraint" in error_str:
            return ErrorResponse(
                error="missing_required_field",
                message="Required field cannot be empty"
            )
        else:
            # Generic database error
            return ErrorResponse(
                error="database_error",
                message="A database error occurred"
            )