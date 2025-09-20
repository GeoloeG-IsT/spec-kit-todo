"""
Authentication middleware for handling JWT tokens and user context.

Validates Clerk JWT tokens, extracts user information, and sets up
authentication context for both authenticated users and guest sessions.
"""

from typing import Optional, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from ...application.services.auth_service import AuthService
from ...application.services.user_service import UserService
from ...infrastructure.database import get_session

logger = structlog.get_logger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication and user context management."""

    def __init__(self, app):
        """
        Initialize authentication middleware.

        Args:
            app: FastAPI application
        """
        super().__init__(app)
        self.auth_service = AuthService()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and handle authentication.

        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler

        Returns:
            Response object
        """
        # Initialize auth context
        request.state.user_context = None
        request.state.is_authenticated = False
        request.state.user_id = None
        request.state.clerk_user_id = None

        # Skip authentication for certain paths
        if self._should_skip_auth(request):
            return await call_next(request)

        # Try to authenticate with JWT token
        await self._authenticate_with_jwt(request)

        # If not authenticated with JWT, set up guest context
        if not request.state.is_authenticated:
            await self._setup_guest_context(request)

        return await call_next(request)

    async def _authenticate_with_jwt(self, request: Request) -> None:
        """
        Attempt to authenticate user with JWT token.

        Args:
            request: FastAPI request object
        """
        try:
            # Extract bearer token from Authorization header
            auth_header = request.headers.get("authorization")
            token = self.auth_service.extract_bearer_token(auth_header)

            if not token:
                return

            # Verify JWT token and extract user info
            user_info = await self.auth_service.get_user_from_token(token)
            if not user_info:
                logger.warning("Invalid JWT token provided")
                return

            # Get or create user in our database
            user = await self._get_or_create_user(user_info)
            if not user:
                logger.error("Failed to get/create user from JWT", clerk_id=user_info.get("clerk_user_id"))
                return

            # Set up authenticated user context
            request.state.user_context = await self.auth_service.create_user_context(
                user_info, str(user.id)
            )
            request.state.is_authenticated = True
            request.state.user_id = str(user.id)
            request.state.clerk_user_id = user_info.get("clerk_user_id")

            # Update user's last login time
            async with get_session() as db_session:
                user_service = UserService(db_session)
                await user_service.update_last_login(user.id)

            logger.info("User authenticated successfully",
                       user_id=str(user.id), clerk_id=user_info.get("clerk_user_id"))

        except Exception as e:
            logger.error("Error during JWT authentication", error=str(e))

    async def _setup_guest_context(self, request: Request) -> None:
        """
        Set up guest user context from session.

        Args:
            request: FastAPI request object
        """
        try:
            # Get session ID from request state (set by SessionMiddleware)
            session_id = getattr(request.state, "session_id", None)
            if not session_id:
                return

            # Create guest context
            request.state.user_context = await self.auth_service.create_guest_context(session_id)
            request.state.is_authenticated = False
            request.state.user_id = None
            request.state.clerk_user_id = None

            logger.debug("Guest context established", session_id=session_id)

        except Exception as e:
            logger.error("Error setting up guest context", error=str(e))

    async def _get_or_create_user(self, user_info: dict) -> Optional[object]:
        """
        Get existing user or create new user from JWT information.

        Args:
            user_info: User information from JWT token

        Returns:
            User object or None if operation failed
        """
        try:
            clerk_user_id = user_info.get("clerk_user_id")
            if not clerk_user_id:
                return None

            async with get_session() as db_session:
                user_service = UserService(db_session)

                # Try to get existing user
                user = await user_service.get_user_by_clerk_id(clerk_user_id)
                if user:
                    return user

                # Create new user if doesn't exist
                from ...domain.schemas import UserCreate
                user_create = UserCreate(
                    clerk_user_id=clerk_user_id,
                    display_name=user_info.get("name", "User"),
                    email=user_info.get("email")
                )

                user = await user_service.create_user(user_create)
                logger.info("New user created from JWT", user_id=str(user.id), clerk_id=clerk_user_id)
                return user

        except Exception as e:
            logger.error("Error getting/creating user", error=str(e))
            return None

    def _should_skip_auth(self, request: Request) -> bool:
        """
        Determine if authentication should be skipped for this request.

        Args:
            request: FastAPI request object

        Returns:
            True if auth should be skipped, False otherwise
        """
        # Skip auth for certain paths
        excluded_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        ]

        path = request.url.path
        if any(path.startswith(excluded) for excluded in excluded_paths):
            return True

        # Skip auth for OPTIONS requests
        if request.method == "OPTIONS":
            return True

        return False


class RequireAuth:
    """Decorator/dependency for routes that require authentication."""

    def __init__(self, allow_guest: bool = False):
        """
        Initialize auth requirement.

        Args:
            allow_guest: Whether to allow guest users (with sessions)
        """
        self.allow_guest = allow_guest

    def __call__(self, request: Request) -> dict:
        """
        Check authentication and return user context.

        Args:
            request: FastAPI request object

        Returns:
            User context dictionary

        Raises:
            PermissionError: If authentication is required but not provided
        """
        is_authenticated = getattr(request.state, "is_authenticated", False)
        user_context = getattr(request.state, "user_context", None)

        # Check if user is authenticated
        if is_authenticated and user_context:
            return user_context

        # Check if guest access is allowed
        if self.allow_guest and user_context and user_context.get("type") == "guest":
            return user_context

        # Authentication required but not provided
        raise PermissionError("Authentication required")


class RequireUser:
    """Dependency for routes that require authenticated users only."""

    def __call__(self, request: Request) -> dict:
        """
        Require authenticated user and return context.

        Args:
            request: FastAPI request object

        Returns:
            User context dictionary

        Raises:
            PermissionError: If user is not authenticated
        """
        is_authenticated = getattr(request.state, "is_authenticated", False)
        user_context = getattr(request.state, "user_context", None)

        if not is_authenticated or not user_context or user_context.get("type") != "user":
            raise PermissionError("User authentication required")

        return user_context


# Create dependency instances
require_auth = RequireAuth(allow_guest=True)
require_auth_no_guest = RequireAuth(allow_guest=False)
require_user = RequireUser()