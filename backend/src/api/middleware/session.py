"""
Session middleware for handling guest user sessions.

Manages session creation, validation, and automatic session management
for guest users who haven't registered yet.
"""

from typing import Optional, Callable
import os

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from ...application.services.session_service import SessionService
from ...infrastructure.database import get_session
from ...domain.schemas import SessionCreate

logger = structlog.get_logger(__name__)


class SessionMiddleware(BaseHTTPMiddleware):
    """Middleware for managing guest user sessions."""

    def __init__(self, app, auto_create_sessions: bool = True):
        """
        Initialize session middleware.

        Args:
            app: FastAPI application
            auto_create_sessions: Whether to automatically create sessions for guests
        """
        super().__init__(app)
        self.auto_create_sessions = auto_create_sessions
        self.session_cookie_name = "todo_session_id"
        self.session_header_name = "X-Session-ID"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and handle session management.

        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler

        Returns:
            Response object with session handling
        """
        # Extract session ID from cookie or header
        session_id = self._extract_session_id(request)

        # Validate existing session if provided
        session_obj = None
        if session_id:
            session_obj = await self._validate_session(session_id)
            if not session_obj:
                logger.warning("Invalid session ID provided", session_id=session_id)
                session_id = None

        # Create new session for guests if needed
        if not session_id and self.auto_create_sessions and self._should_create_session(request):
            session_obj = await self._create_new_session(request)
            if session_obj:
                session_id = session_obj.id
                logger.info("New guest session created", session_id=session_id)

        # Add session info to request state
        request.state.session_id = session_id
        request.state.session_obj = session_obj
        request.state.is_guest_session = session_id is not None

        # Process request
        response = await call_next(request)

        # Set session cookie if we have a session
        if session_id and self._should_set_cookie(request, response):
            self._set_session_cookie(response, session_id)

        return response

    def _extract_session_id(self, request: Request) -> Optional[str]:
        """
        Extract session ID from request cookies or headers.

        Args:
            request: FastAPI request object

        Returns:
            Session ID or None if not found
        """
        # First try header (for API clients)
        session_id = request.headers.get(self.session_header_name)
        if session_id:
            return session_id

        # Then try cookie (for web browsers)
        session_id = request.cookies.get(self.session_cookie_name)
        if session_id:
            return session_id

        return None

    async def _validate_session(self, session_id: str) -> Optional[object]:
        """
        Validate a session ID and return session object if valid.

        Args:
            session_id: Session ID to validate

        Returns:
            Session object if valid, None otherwise
        """
        try:
            async with get_session() as db_session:
                session_service = SessionService(db_session)
                return await session_service.validate_session(session_id)
        except Exception as e:
            logger.error("Error validating session", session_id=session_id, error=str(e))
            return None

    async def _create_new_session(self, request: Request) -> Optional[object]:
        """
        Create a new guest session.

        Args:
            request: FastAPI request object

        Returns:
            Created session object or None if creation failed
        """
        try:
            # Extract client information
            user_agent = request.headers.get("user-agent")
            ip_address = self._get_client_ip(request)

            async with get_session() as db_session:
                session_service = SessionService(db_session)
                session_data = SessionCreate(
                    user_agent=user_agent,
                    ip_address=ip_address
                )
                return await session_service.create_session(session_data)
        except Exception as e:
            logger.error("Error creating new session", error=str(e))
            return None

    def _should_create_session(self, request: Request) -> bool:
        """
        Determine if we should create a new session for this request.

        Args:
            request: FastAPI request object

        Returns:
            True if session should be created, False otherwise
        """
        # Don't create sessions for certain paths
        excluded_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        ]

        path = request.url.path
        if any(path.startswith(excluded) for excluded in excluded_paths):
            return False

        # Don't create sessions for OPTIONS requests
        if request.method == "OPTIONS":
            return False

        # Create sessions for API routes that might need guest functionality
        if path.startswith("/api/"):
            return True

        return False

    def _should_set_cookie(self, request: Request, response: Response) -> bool:
        """
        Determine if we should set a session cookie in the response.

        Args:
            request: FastAPI request object
            response: FastAPI response object

        Returns:
            True if cookie should be set, False otherwise
        """
        # Only set cookies for successful responses
        if response.status_code >= 400:
            return False

        # Don't set cookies for API-only requests (they should use headers)
        accept_header = request.headers.get("accept", "")
        if "application/json" in accept_header and "text/html" not in accept_header:
            return False

        return True

    def _set_session_cookie(self, response: Response, session_id: str) -> None:
        """
        Set session cookie in response.

        Args:
            response: FastAPI response object
            session_id: Session ID to set in cookie
        """
        # Cookie settings
        max_age = 60 * 60 * 24 * 30  # 30 days
        secure = os.getenv("ENVIRONMENT", "development").lower() == "production"
        samesite = "lax"

        response.set_cookie(
            key=self.session_cookie_name,
            value=session_id,
            max_age=max_age,
            secure=secure,
            httponly=True,
            samesite=samesite
        )

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """
        Extract client IP address from request.

        Args:
            request: FastAPI request object

        Returns:
            Client IP address or None
        """
        # Check for forwarded headers (common in production deployments)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return forwarded_for.split(",")[0].strip()

        # Check for real IP header (used by some proxies)
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return None