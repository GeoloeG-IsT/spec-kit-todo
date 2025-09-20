"""
Alembic environment configuration for async SQLModel migrations.

This file configures Alembic to work with async SQLAlchemy and SQLModel,
providing both online and offline migration capabilities.
"""

import asyncio
import os
from logging.config import fileConfig
from typing import Any

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from sqlmodel import SQLModel

# Import all models to ensure they're registered with SQLModel metadata
from src.domain.models.user import User
from src.domain.models.todo_item import TodoItem
from src.domain.models.session import Session
from src.domain.models.auth_provider import AuthProvider

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the SQLModel metadata for 'autogenerate' support
target_metadata = SQLModel.metadata

# Get database URL from environment variable or config
database_url = os.getenv(
    "DATABASE_URL",
    config.get_main_option("sqlalchemy.url", "postgresql+asyncpg://user:password@localhost:5432/todolist_dev")
)

# Ensure we're using the async driver
if database_url and not database_url.startswith("postgresql+asyncpg"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode using async engine.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = create_async_engine(
        database_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()