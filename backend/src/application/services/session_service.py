"""
Session service for managing guest user sessions.

Handles session creation, validation, cleanup, and security tracking
for guest users who haven't registered yet.
"""

from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import structlog

from ...domain.models.session import Session
from ...domain.schemas import SessionCreate, SessionResponse

logger = structlog.get_logger(__name__)


class SessionService:
    """Service for guest session management operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, session_data: SessionCreate) -> Session:
        """
        Create a new guest session.

        Args:
            session_data: Session creation data with optional user agent and IP

        Returns:
            Created session instance
        """
        session_obj = Session.create_new_session(
            user_agent=session_data.user_agent,
            ip_address=session_data.ip_address
        )

        self.session.add(session_obj)
        # Don't commit here - let the route handler manage transactions

        logger.info("Guest session created", session_id=session_obj.id)
        return session_obj

    async def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        result = await self.session.execute(
            select(Session).where(Session.id == session_id)
        )
        return result.scalar_one_or_none()

    async def validate_session(self, session_id: str) -> Optional[Session]:
        """
        Validate a session and update last accessed timestamp.

        Args:
            session_id: Session ID to validate

        Returns:
            Session if valid, None if not found or expired
        """
        logger.info("SessionService validating session", session_id=session_id)
        session_obj = await self.get_session_by_id(session_id)
        logger.info("SessionService session lookup result", session_id=session_id, found=bool(session_obj))

        if not session_obj:
            logger.warning("Session not found", session_id=session_id)
            return None

        # Check if session is expired (though guest sessions don't expire server-side)
        if session_obj.is_expired:
            logger.warning("Expired session accessed", session_id=session_id)
            return None

        # Update last accessed timestamp
        session_obj.update_last_accessed()
        # Note: Commit should be handled by route handler

        logger.info("Session validation successful", session_id=session_id)
        return session_obj

    async def update_session_access(self, session_id: str) -> bool:
        """
        Update session's last accessed timestamp.

        Args:
            session_id: Session ID to update

        Returns:
            True if session was found and updated, False otherwise
        """
        session_obj = await self.get_session_by_id(session_id)
        if not session_obj:
            return False

        session_obj.update_last_accessed()
        # Note: Commit should be handled by route handler

        return True

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its associated data.

        Args:
            session_id: Session ID to delete

        Returns:
            True if session was deleted, False if not found
        """
        session_obj = await self.get_session_by_id(session_id)
        if not session_obj:
            return False

        # Delete session (cascades to TODOs via application logic)
        await self.session.delete(session_obj)
        # Note: Commit should be handled by route handler

        logger.info("Guest session deleted", session_id=session_id)
        return True

    async def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """
        Clean up old, inactive sessions.

        Args:
            days_old: Delete sessions older than this many days

        Returns:
            Number of sessions deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        result = await self.session.execute(
            delete(Session).where(Session.last_accessed_at < cutoff_date)
        )

        # Note: Commit should be handled by caller
        deleted_count = result.rowcount or 0

        logger.info("Old sessions cleaned up", deleted_count=deleted_count, days_old=days_old)
        return deleted_count

    async def get_session_stats(self, session_id: str) -> Optional[dict]:
        """
        Get session statistics and metadata.

        Args:
            session_id: Session ID to get stats for

        Returns:
            Dictionary with session stats or None if session not found
        """
        session_obj = await self.get_session_by_id(session_id)
        if not session_obj:
            return None

        return {
            "id": session_obj.id,
            "created_at": session_obj.created_at,
            "last_accessed_at": session_obj.last_accessed_at,
            "age_seconds": session_obj.age_in_seconds,
            "time_since_last_access_seconds": session_obj.time_since_last_access_seconds,
            "user_agent": session_obj.user_agent,
            "ip_address": session_obj.ip_address,
            "is_expired": session_obj.is_expired
        }

    async def is_session_valid(self, session_id: str) -> bool:
        """
        Check if a session ID is valid without updating timestamps.

        Args:
            session_id: Session ID to check

        Returns:
            True if session exists and is not expired, False otherwise
        """
        session_obj = await self.get_session_by_id(session_id)
        return session_obj is not None and not session_obj.is_expired

    def to_response(self, session_obj: Session) -> SessionResponse:
        """Convert Session model to response schema."""
        return SessionResponse(
            id=session_obj.id,
            created_at=session_obj.created_at,
            last_accessed_at=session_obj.last_accessed_at
        )