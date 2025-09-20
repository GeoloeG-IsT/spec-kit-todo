"""
Session domain model for the TODO list application.

Represents guest user sessions with temporary TODO storage.
Follows the data model specification from data-model.md.
"""

from datetime import datetime
from typing import Optional
import secrets
import string

from sqlmodel import SQLModel, Field


class Session(SQLModel, table=True):
    """
    Session entity representing guest user sessions.

    Fields:
    - id: String (primary key, session token)
    - created_at: DateTime
    - last_accessed_at: DateTime
    - expires_at: DateTime (nullable, no timeout for guest sessions)
    - user_agent: String (for security tracking)
    - ip_address: String (for security tracking)

    Relationships:
    - One-to-many with TodoItem (via session_id)

    Validation Rules:
    - id must be unique session identifier
    - last_accessed_at updated on every request
    - session persists until browser closure (no server-side expiration)

    State Transitions:
    - Created → Active (when first TODO created)
    - Active → Converted (when guest upgrades to registered user)
    - Active → Expired (when browser session ends)
    """

    __tablename__ = "sessions"

    # Primary key (cryptographically secure session ID)
    id: str = Field(primary_key=True, min_length=20, max_length=255)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None)  # No timeout for guest sessions

    # Security tracking
    user_agent: Optional[str] = Field(default=None, max_length=1000)
    ip_address: Optional[str] = Field(default=None, max_length=45)  # IPv6 max length

    def __str__(self) -> str:
        """String representation of the session."""
        return f"Session(id={self.id[:8]}..., created_at={self.created_at})"

    def __repr__(self) -> str:
        """Detailed representation of the session."""
        return (
            f"Session("
            f"id='{self.id}', "
            f"created_at={self.created_at}, "
            f"last_accessed_at={self.last_accessed_at}, "
            f"user_agent='{self.user_agent[:50] if self.user_agent else None}...'"
            f")"
        )

    def update_last_accessed(self) -> None:
        """Update the last accessed timestamp."""
        self.last_accessed_at = datetime.utcnow()

    @property
    def is_expired(self) -> bool:
        """
        Check if session is expired.
        For guest sessions, we don't expire server-side (returns False).
        """
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def age_in_seconds(self) -> int:
        """Get the age of the session in seconds."""
        return int((datetime.utcnow() - self.created_at).total_seconds())

    @property
    def time_since_last_access_seconds(self) -> int:
        """Get seconds since last access."""
        return int((datetime.utcnow() - self.last_accessed_at).total_seconds())

    @classmethod
    def generate_session_id(cls, length: int = 32) -> str:
        """
        Generate a cryptographically secure session ID.

        Args:
            length: Length of the session ID (default: 32 characters)

        Returns:
            Secure random session ID string
        """
        # Use URL-safe characters for session ID
        alphabet = string.ascii_letters + string.digits + "-_"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    @classmethod
    def create_new_session(cls, user_agent: Optional[str] = None,
                          ip_address: Optional[str] = None) -> "Session":
        """
        Create a new guest session.

        Args:
            user_agent: User-Agent header from the request
            ip_address: IP address of the client

        Returns:
            New Session instance with generated ID
        """
        session_id = cls.generate_session_id()
        return cls(
            id=session_id,
            user_agent=user_agent,
            ip_address=ip_address
        )

    def to_response_dict(self) -> dict:
        """
        Convert session to dictionary for API responses.

        Returns:
            Dictionary with session data for client
        """
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() + "Z",
            "last_accessed_at": self.last_accessed_at.isoformat() + "Z"
        }