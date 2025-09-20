"""
Development authentication routes for local testing.

These routes are only available in development mode and provide
a simple way to authenticate without setting up Clerk.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import os

from ...application.services.dev_auth_service import DevelopmentAuthService
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()
dev_auth_service = DevelopmentAuthService()


class DevTokenRequest(BaseModel):
    username: str


class DevTokenResponse(BaseModel):
    token: str
    user: Dict[str, Any]
    expires_in: int = 86400  # 24 hours


@router.get("/help", tags=["Development Auth"])
async def get_dev_auth_help():
    """
    Get help information for development authentication.

    Only available in development mode.
    """
    if os.getenv("ENVIRONMENT", "development").lower() != "development":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Development auth not available in production"
        )

    return dev_auth_service.get_auth_help()


@router.post("/token", response_model=DevTokenResponse, tags=["Development Auth"])
async def create_dev_token(request: DevTokenRequest):
    """
    Create a development authentication token.

    Only available in development mode. Use this to get a JWT token
    for testing authenticated endpoints without setting up Clerk.

    Available usernames:
    - dev_user_1: Regular development user
    - admin: Admin development user
    """
    if os.getenv("ENVIRONMENT", "development").lower() != "development":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Development auth not available in production"
        )

    token = dev_auth_service.create_dev_token(request.username)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid username: {request.username}"
        )

    # Get user info
    users = dev_auth_service.get_dev_users()
    user_info = users.get(request.username)

    logger.info("Development token created", username=request.username)

    return DevTokenResponse(
        token=token,
        user=user_info,
        expires_in=86400
    )


@router.get("/users", tags=["Development Auth"])
async def list_dev_users():
    """
    List available development users.

    Only available in development mode.
    """
    if os.getenv("ENVIRONMENT", "development").lower() != "development":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Development auth not available in production"
        )

    users = dev_auth_service.get_dev_users()
    return {
        "users": {
            username: {
                "email": user["email"],
                "name": user["name"],
                "clerk_user_id": user["clerk_user_id"]
            }
            for username, user in users.items()
        }
    }


@router.post("/guest-session", tags=["Development Auth"])
async def create_dev_guest_session():
    """
    Create a development guest session.

    Only available in development mode. Use the returned session_id
    with the X-Session-ID header for guest requests.
    """
    if os.getenv("ENVIRONMENT", "development").lower() != "development":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Development auth not available in production"
        )

    session_id = dev_auth_service.create_guest_session()

    logger.info("Development guest session created", session_id=session_id)

    return {
        "session_id": session_id,
        "usage": "Include 'X-Session-ID: {session_id}' header in requests"
    }