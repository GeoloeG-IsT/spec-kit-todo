"""
User domain model for the TODO list application.

Represents registered users with authentication credentials and persistent data.
Follows the data model specification from data-model.md.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    """
    User entity representing registered users with authentication credentials.

    Fields:
    - id: UUID (primary key)
    - clerk_user_id: String (unique, external ID from Clerk)
    - email: String (unique, nullable for OAuth-only users)
    - display_name: String (user's preferred name)
    - avatar_url: String (nullable, profile image URL)
    - created_at: DateTime
    - updated_at: DateTime
    - last_login_at: DateTime (nullable)

    Relationships:
    - One-to-many with TodoItem
    - One-to-many with AuthProvider

    Validation Rules:
    - clerk_user_id must be unique across all users
    - email must be valid email format when provided
    - display_name cannot be empty string

    State Transitions:
    - Created → Active (on first login)
    - Active → Inactive (after 1 year of no login - soft delete)
    """

    __tablename__ = "users"

    # Primary key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Clerk integration
    clerk_user_id: str = Field(unique=True, index=True, min_length=1)

    # User profile information
    email: Optional[str] = Field(default=None, unique=True, index=True, max_length=255)
    display_name: str = Field(min_length=1, max_length=100)
    avatar_url: Optional[str] = Field(default=None, max_length=500)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = Field(default=None)

    # Relationships (will be defined when we import the related models)
    todos: List["TodoItem"] = Relationship(back_populates="user")
    auth_providers: List["AuthProvider"] = Relationship(back_populates="user")

    def __str__(self) -> str:
        """String representation of the user."""
        return f"User(id={self.id}, display_name='{self.display_name}', email='{self.email}')"

    def __repr__(self) -> str:
        """Detailed representation of the user."""
        return (
            f"User("
            f"id={self.id}, "
            f"clerk_user_id='{self.clerk_user_id}', "
            f"display_name='{self.display_name}', "
            f"email='{self.email}', "
            f"created_at={self.created_at}"
            f")"
        )

    def update_last_login(self) -> None:
        """Update the last login timestamp and updated_at."""
        self.last_login_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_profile(self, display_name: Optional[str] = None,
                      avatar_url: Optional[str] = None) -> None:
        """Update user profile information."""
        if display_name is not None:
            self.display_name = display_name
        if avatar_url is not None:
            self.avatar_url = avatar_url
        self.updated_at = datetime.utcnow()

    @property
    def is_active(self) -> bool:
        """Check if user is considered active (logged in within last year)."""
        if not self.last_login_at:
            return True  # New users are considered active

        one_year_ago = datetime.utcnow().replace(year=datetime.utcnow().year - 1)
        return self.last_login_at > one_year_ago

    @classmethod
    def create_from_clerk(cls, clerk_user_id: str, display_name: str,
                         email: Optional[str] = None) -> "User":
        """
        Create a new user from Clerk authentication data.

        Args:
            clerk_user_id: Unique identifier from Clerk
            display_name: User's display name
            email: User's email address (optional)

        Returns:
            New User instance
        """
        return cls(
            clerk_user_id=clerk_user_id,
            display_name=display_name,
            email=email,
            last_login_at=datetime.utcnow()  # Set login time for new users
        )