"""
Development authentication service for local testing.

This service provides a simple authentication mechanism for local development
when Clerk API is not available or you want to test without external dependencies.
Only use this in development mode.
"""

from typing import Optional, Dict, Any
import os
import json
import jwt
from datetime import datetime, timedelta
import secrets

import structlog

logger = structlog.get_logger(__name__)


class DevelopmentAuthService:
    """Development-only authentication service."""

    def __init__(self):
        self.dev_secret = os.getenv("DEV_AUTH_SECRET", "dev-secret-key-change-in-production")
        self.is_dev_mode = os.getenv("ENVIRONMENT", "development").lower() == "development"

        # Development users (in-memory store)
        self.dev_users = {
            "dev_user_1": {
                "clerk_user_id": "user_dev123",
                "email": "dev@example.com",
                "name": "Development User",
                "given_name": "Development",
                "family_name": "User",
                "email_verified": True,
                "picture": None
            },
            "admin": {
                "clerk_user_id": "user_admin123",
                "email": "admin@example.com",
                "name": "Admin User",
                "given_name": "Admin",
                "family_name": "User",
                "email_verified": True,
                "picture": None
            }
        }

    def create_dev_token(self, username: str) -> Optional[str]:
        """
        Create a development JWT token for a given username.

        Args:
            username: Username for the development user

        Returns:
            JWT token string or None if user not found
        """
        if not self.is_dev_mode:
            logger.error("Development tokens can only be created in development mode")
            return None

        user = self.dev_users.get(username)
        if not user:
            logger.error("Development user not found", username=username)
            return None

        # Create JWT payload
        now = datetime.utcnow()
        payload = {
            "sub": user["clerk_user_id"],
            "email": user["email"],
            "email_verified": user["email_verified"],
            "name": user["name"],
            "given_name": user["given_name"],
            "family_name": user["family_name"],
            "picture": user["picture"],
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=24)).timestamp()),
            "iss": "development",
            "aud": "todo-app"
        }

        # Sign with development secret
        token = jwt.encode(payload, self.dev_secret, algorithm="HS256")
        logger.info("Development token created", username=username, user_id=user["clerk_user_id"])
        return token

    async def verify_dev_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a development JWT token.

        Args:
            token: JWT token to verify

        Returns:
            User information dict if valid, None if invalid
        """
        if not self.is_dev_mode:
            return None

        try:
            # Decode and verify with development secret
            decoded = jwt.decode(token, self.dev_secret, algorithms=["HS256"])

            # Check if it's a development token
            if decoded.get("iss") != "development":
                return None

            logger.info("Development token verified", user_id=decoded.get("sub"))
            return decoded

        except jwt.ExpiredSignatureError:
            logger.warning("Development JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid development JWT token", error=str(e))
            return None
        except Exception as e:
            logger.error("Error verifying development JWT token", error=str(e))
            return None

    def get_dev_users(self) -> Dict[str, Dict[str, Any]]:
        """Get list of development users."""
        if not self.is_dev_mode:
            return {}
        return self.dev_users.copy()

    def create_guest_session(self) -> str:
        """Create a development guest session ID."""
        return f"dev_session_{secrets.token_hex(16)}"

    def get_auth_help(self) -> Dict[str, Any]:
        """
        Get authentication help for development mode.

        Returns:
            Help information for using development auth
        """
        if not self.is_dev_mode:
            return {"error": "Development auth only available in development mode"}

        return {
            "development_mode": True,
            "available_users": list(self.dev_users.keys()),
            "usage": {
                "get_token": "POST /api/auth/dev/token with {\"username\": \"dev_user_1\"}",
                "use_token": "Include 'Authorization: Bearer <token>' header in requests",
                "guest_mode": "Use 'X-Session-ID' header with any session ID"
            },
            "example_users": {
                username: {
                    "email": user["email"],
                    "name": user["name"]
                }
                for username, user in self.dev_users.items()
            }
        }