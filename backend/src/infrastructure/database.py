"""
Database connection and management for the TODO list application.

Provides SQLModel engine setup, connection pooling, and table management
for the PostgreSQL database using Neon in production and local development.
"""

import os
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel
import structlog

from ..domain.models.user import User
from ..domain.models.todo_item import TodoItem
from ..domain.models.session import Session
from ..domain.models.auth_provider import AuthProvider

logger = structlog.get_logger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/todolist_dev"
)

# Create async engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=bool(os.getenv("SQL_DEBUG", False)),  # Log SQL queries in debug mode
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=3600,   # Recycle connections every hour
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def create_tables() -> None:
    """
    Create all database tables.

    Used during application startup to ensure all tables exist.
    In production, this should be handled by Alembic migrations.
    """
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered with SQLModel
            # This is already done above, but being explicit
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise


async def close_database() -> None:
    """
    Close database connections.

    Used during application shutdown to cleanly close all connections.
    """
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error("Error closing database connections", error=str(e))
        raise


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session with automatic cleanup.

    Usage:
        async with get_session() as session:
            # Use session for database operations
            result = await session.execute(select(User))

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Dependency for FastAPI routes
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.

    Usage in routes:
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_db_session)):
            # Use session
    """
    async with get_session() as session:
        yield session


# Health check function
async def check_database_health() -> bool:
    """
    Check if database is healthy and accessible.

    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        async with get_session() as session:
            # Simple query to test connection
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False