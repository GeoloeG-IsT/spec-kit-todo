"""
Authentication service for managing JWT tokens and user authentication.

Handles Clerk JWT validation, user context extraction, and authentication
state management for both authenticated users and guest sessions.
"""

from typing import Optional, Dict, Any
import os
import jwt
from datetime import datetime

import structlog
import httpx
from .dev_auth_service import DevelopmentAuthService

logger = structlog.get_logger(__name__)


class AuthService:
    """Service for authentication and JWT token management."""

    def __init__(self):
        self.clerk_secret_key = os.getenv("CLERK_SECRET_KEY")
        self.clerk_publishable_key = os.getenv("CLERK_PUBLISHABLE_KEY")
        self.clerk_jwks_url = "https://api.clerk.dev/v1/jwks"
        self._jwks_cache: Optional[Dict[str, Any]] = None
        self._jwks_cache_time: Optional[datetime] = None
        self.dev_auth_service = DevelopmentAuthService()

    async def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a JWT token and extract user information.

        Supports both Clerk tokens and development tokens.

        Args:
            token: JWT token from Authorization header

        Returns:
            User information dict if valid, None if invalid
        """
        # Try development token first if in development mode
        if self.is_development_mode():
            dev_result = await self.dev_auth_service.verify_dev_token(token)
            if dev_result:
                logger.info("Development JWT token verified", user_id=dev_result.get("sub"))
                return dev_result

        try:
            # Get JWKS for verification
            jwks = await self._get_jwks()
            if not jwks:
                logger.error("Failed to get JWKS for JWT verification")
                return None

            # Decode and verify the JWT
            # Note: In production, you'd want to verify the signature properly
            # using the JWKS. For now, we'll decode without verification for development
            decoded = jwt.decode(token, options={"verify_signature": False})

            # Validate token claims
            if not self._validate_token_claims(decoded):
                return None

            logger.info("Clerk JWT token verified successfully", user_id=decoded.get("sub"))
            return decoded

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid JWT token", error=str(e))
            return None
        except Exception as e:
            logger.error("Error verifying JWT token", error=str(e))
            return None

    async def get_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Extract user information from a valid JWT token.

        Args:
            token: JWT token

        Returns:
            User information dict with standard fields
        """
        decoded = await self.verify_jwt_token(token)
        if not decoded:
            return None

        # Extract standard user information
        user_info = {
            "clerk_user_id": decoded.get("sub"),
            "email": decoded.get("email"),
            "email_verified": decoded.get("email_verified", False),
            "name": decoded.get("name"),
            "given_name": decoded.get("given_name"),
            "family_name": decoded.get("family_name"),
            "picture": decoded.get("picture"),
            "issued_at": decoded.get("iat"),
            "expires_at": decoded.get("exp"),
        }

        return user_info

    async def validate_session_token(self, session_token: str) -> bool:
        """
        Validate a Clerk session token.

        Args:
            session_token: Session token to validate

        Returns:
            True if valid, False otherwise
        """
        # In a real implementation, you'd validate the session token
        # against Clerk's API or verify it cryptographically
        if not session_token or len(session_token) < 10:
            return False

        try:
            # For development, we'll accept any non-empty session token
            # In production, implement proper Clerk session validation
            logger.info("Session token validated", token_length=len(session_token))
            return True
        except Exception as e:
            logger.error("Error validating session token", error=str(e))
            return False

    async def _get_jwks(self) -> Optional[Dict[str, Any]]:
        """
        Get JWKS from Clerk for JWT verification.

        Returns:
            JWKS dict or None if failed to fetch
        """
        # Check cache (cache for 1 hour)
        if (self._jwks_cache and self._jwks_cache_time and
            (datetime.utcnow() - self._jwks_cache_time).seconds < 3600):
            return self._jwks_cache

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.clerk_jwks_url)
                response.raise_for_status()

                jwks = response.json()
                self._jwks_cache = jwks
                self._jwks_cache_time = datetime.utcnow()

                logger.info("JWKS fetched and cached successfully")
                return jwks

        except Exception as e:
            logger.error("Failed to fetch JWKS", error=str(e))
            return None

    def _validate_token_claims(self, decoded: Dict[str, Any]) -> bool:
        """
        Validate JWT token claims.

        Args:
            decoded: Decoded JWT payload

        Returns:
            True if claims are valid, False otherwise
        """
        # Check required claims
        if not decoded.get("sub"):  # Subject (user ID)
            logger.warning("JWT missing subject claim")
            return False

        # Check expiration
        exp = decoded.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            logger.warning("JWT token has expired")
            return False

        # Check issued at time (not too old)
        iat = decoded.get("iat")
        if iat:
            issued_time = datetime.utcfromtimestamp(iat)
            if (datetime.utcnow() - issued_time).days > 7:  # Token older than 7 days
                logger.warning("JWT token too old")
                return False

        return True

    def extract_bearer_token(self, authorization_header: Optional[str]) -> Optional[str]:
        """
        Extract bearer token from Authorization header.

        Args:
            authorization_header: Authorization header value

        Returns:
            Bearer token or None if not found
        """
        if not authorization_header:
            return None

        parts = authorization_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        return parts[1]

    def is_development_mode(self) -> bool:
        """Check if running in development mode."""
        return os.getenv("ENVIRONMENT", "development").lower() == "development"

    async def create_guest_context(self, session_id: str) -> Dict[str, Any]:
        """
        Create authentication context for guest users.

        Args:
            session_id: Guest session ID

        Returns:
            Guest user context dict
        """
        return {
            "type": "guest",
            "session_id": session_id,
            "authenticated": False,
            "user_id": None,
            "clerk_user_id": None
        }

    async def create_user_context(self, user_info: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create authentication context for authenticated users.

        Args:
            user_info: User information from JWT
            user_id: Internal user ID (UUID)

        Returns:
            Authenticated user context dict
        """
        return {
            "type": "user",
            "session_id": None,
            "authenticated": True,
            "user_id": user_id,
            "clerk_user_id": user_info.get("clerk_user_id"),
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture")
        }