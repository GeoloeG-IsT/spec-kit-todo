"""
FastAPI route handlers for the TODO list application.

Contains all API endpoints organized by feature area:
authentication, TODO management, and real-time streaming.
"""

from . import auth, todos, stream

__all__ = [
    "auth",
    "todos",
    "stream"
]