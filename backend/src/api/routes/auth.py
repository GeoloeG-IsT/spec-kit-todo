"""
Authentication API routes for user management and session conversion.

Handles user profile endpoints and guest session to user conversion.
Authentication itself is handled by Clerk, these routes manage the
application-specific user data and session migration.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ...infrastructure.database import get_db_session
from ...application.services.user_service import UserService
from ...application.services.todo_service import TodoService
from ...application.services.session_service import SessionService
from ...api.middleware.auth import require_user, require_auth
from ...domain.schemas import (
    UserCreate, UserResponse, UserUpdate, AuthProviderResponse,
    SessionCreate, SessionResponse, SessionConvertRequest, SessionConvertResponse, ErrorResponse
)

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/session", response_model=SessionResponse, status_code=201, tags=["Session Management"])
async def create_guest_session(
    session_data: SessionCreate,
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Create a new guest session for anonymous users.

    Args:
        session_data: Session creation data including user agent and IP address

    Returns:
        Created session information with session ID
    """
    session_service = SessionService(db_session)

    try:
        session = await session_service.create_session(session_data)
        await db_session.commit()

        logger.info("Guest session created", session_id=session.id)
        return SessionResponse(
            id=session.id,
            created_at=session.created_at,
            last_accessed_at=session.last_accessed_at
        )
    except Exception as e:
        await db_session.rollback()
        logger.error("Failed to create guest session", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.post("/user", response_model=UserResponse, status_code=201, tags=["User Management"])
async def create_or_update_user(
    user_data: UserCreate,
    user_context: dict = Depends(require_auth),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Create or update a user from Clerk authentication token.

    Args:
        user_data: User creation data

    Returns:
        Created or updated user information
    """
    user_service = UserService(db_session)

    try:
        # Create or update user
        user, created = await user_service.create_or_update_user(user_data)
        await db_session.commit()

        status_code = 201 if created else 200
        action = "created" if created else "updated"
        logger.info(f"User {action}", user_id=str(user.id), clerk_user_id=user_data.clerk_user_id)

        response = user_service.to_response(user)
        # Update status code in response
        return Response(
            content=response.model_dump_json(),
            media_type="application/json",
            status_code=status_code
        )

    except Exception as e:
        await db_session.rollback()
        logger.error("Failed to create/update user", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create or update user")


@router.get("/user", response_model=UserResponse, tags=["User Management"])
async def get_current_user_alt(
    user_context: dict = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Get current authenticated user's profile (alternative endpoint).

    Returns:
        Current user's profile information
    """
    user_service = UserService(db_session)
    user_id = UUID(user_context["user_id"])

    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user_service.to_response(user)


@router.get("/me", response_model=UserResponse, tags=["User Profile"])
async def get_current_user(
    user_context: dict = Depends(require_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get current authenticated user's profile.

    Returns:
        Current user's profile information
    """
    user_service = UserService(session)
    user_id = UUID(user_context["user_id"])

    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user_service.to_response(user)


@router.put("/me", response_model=UserResponse, tags=["User Profile"])
async def update_current_user(
    user_update: UserUpdate,
    user_context: dict = Depends(require_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Update current authenticated user's profile.

    Args:
        user_update: User update data

    Returns:
        Updated user profile
    """
    user_service = UserService(session)
    user_id = UUID(user_context["user_id"])

    user = await user_service.update_user(user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    logger.info("User profile updated", user_id=str(user_id))
    return user_service.to_response(user)


@router.get("/me/auth-providers", response_model=List[AuthProviderResponse], tags=["User Profile"])
async def get_user_auth_providers(
    user_context: dict = Depends(require_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get all authentication providers linked to current user.

    Returns:
        List of linked authentication providers
    """
    user_service = UserService(session)
    user_id = UUID(user_context["user_id"])

    auth_providers = await user_service.get_user_auth_providers(user_id)

    return [
        AuthProviderResponse(
            provider=provider.provider,
            email=provider.email,
            created_at=provider.created_at,
            last_used_at=provider.last_used_at
        )
        for provider in auth_providers
    ]


@router.post("/convert-session", response_model=SessionConvertResponse, tags=["Session Management"])
async def convert_guest_session(
    convert_request: SessionConvertRequest,
    user_context: dict = Depends(require_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Convert a guest session's TODOs to the current authenticated user.

    This endpoint allows users who created TODOs as guests to migrate
    them to their user account after signing up/logging in.

    Args:
        convert_request: Session conversion request with session ID

    Returns:
        Number of TODOs migrated
    """
    user_service = UserService(session)
    todo_service = TodoService(session)
    user_id = UUID(user_context["user_id"])

    # Verify user exists
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Migrate session TODOs to user
    migrated_count = await todo_service.migrate_session_todos_to_user(
        convert_request.session_id,
        user_id
    )

    logger.info("Guest session converted to user",
               user_id=str(user_id), session_id=convert_request.session_id, migrated_count=migrated_count)

    return SessionConvertResponse(migrated_todos_count=migrated_count)


@router.delete("/me", status_code=204, tags=["User Profile"])
async def delete_current_user(
    user_context: dict = Depends(require_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Delete current authenticated user and all associated data.

    This is a destructive operation that removes:
    - User profile
    - All TODOs
    - All authentication providers
    - All associated data

    Returns:
        No content (204) on successful deletion
    """
    user_service = UserService(session)
    user_id = UUID(user_context["user_id"])

    deleted = await user_service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    logger.info("User account deleted", user_id=str(user_id))


@router.get("/session-info", tags=["Session Management"])
async def get_session_info(
    user_context: dict = Depends(require_auth)
):
    """
    Get information about the current session/user context.

    This endpoint helps clients understand their authentication state
    and available features.

    Returns:
        Session/user context information
    """
    return {
        "authenticated": user_context.get("authenticated", False),
        "type": user_context.get("type"),
        "user_id": user_context.get("user_id"),
        "session_id": user_context.get("session_id"),
        "features": {
            "persistent_todos": user_context.get("authenticated", False),
            "real_time_sync": True,
            "export_data": user_context.get("authenticated", False),
            "multiple_devices": user_context.get("authenticated", False)
        }
    }