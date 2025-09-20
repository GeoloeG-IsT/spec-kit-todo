"""
AuthProvider domain model for the TODO list application.

Links users to external OAuth providers for multi-provider authentication.
Follows the data model specification from data-model.md.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship


class AuthProviderType(str, Enum):
    """Enumeration for supported authentication providers."""
    GOOGLE = "google"
    GITHUB = "github"
    LINKEDIN = "linkedin"
    EMAIL = "email"


class AuthProvider(SQLModel, table=True):
    """
    AuthProvider entity linking users to external OAuth providers.

    Fields:
    - id: UUID (primary key)
    - user_id: UUID (foreign key)
    - provider: String (google, github, linkedin, email)
    - provider_user_id: String (external user ID from provider)
    - email: String (nullable, email from provider)
    - created_at: DateTime
    - last_used_at: DateTime

    Relationships:
    - Many-to-one with User

    Validation Rules:
    - combination of user_id + provider must be unique
    - provider must be one of: google, github, linkedin, email
    - provider_user_id must be unique per provider
    """

    __tablename__ = "authproviders"

    # Primary key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # User association
    user_id: UUID = Field(foreign_key="users.id", index=True)

    # Provider information
    provider: AuthProviderType = Field(index=True)
    provider_user_id: str = Field(min_length=1, max_length=255, index=True)
    email: Optional[str] = Field(default=None, max_length=255)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="auth_providers")

    def __str__(self) -> str:
        """String representation of the auth provider."""
        return f"AuthProvider({self.provider.value}: {self.provider_user_id})"

    def __repr__(self) -> str:
        """Detailed representation of the auth provider."""
        return (
            f"AuthProvider("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"provider={self.provider.value}, "
            f"provider_user_id='{self.provider_user_id}', "
            f"email='{self.email}'"
            f")"
        )

    def update_last_used(self) -> None:
        """Update the last used timestamp."""
        self.last_used_at = datetime.utcnow()

    def update_email(self, email: Optional[str]) -> None:
        """Update the email from the provider."""
        self.email = email
        self.last_used_at = datetime.utcnow()

    @property
    def is_oauth_provider(self) -> bool:
        """Check if this is an OAuth provider (not email/password)."""
        return self.provider != AuthProviderType.EMAIL

    @property
    def is_email_provider(self) -> bool:
        """Check if this is email/password authentication."""
        return self.provider == AuthProviderType.EMAIL

    @classmethod
    def create_oauth_provider(cls, user_id: UUID, provider: AuthProviderType,
                             provider_user_id: str, email: Optional[str] = None) -> "AuthProvider":
        """
        Create a new OAuth provider link.

        Args:
            user_id: User ID to link to
            provider: OAuth provider type
            provider_user_id: External user ID from the provider
            email: Email from the provider (optional)

        Returns:
            New AuthProvider instance
        """
        if provider == AuthProviderType.EMAIL:
            raise ValueError("Use create_email_provider for email authentication")

        return cls(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            email=email
        )

    @classmethod
    def create_email_provider(cls, user_id: UUID, email: str) -> "AuthProvider":
        """
        Create a new email/password provider link.

        Args:
            user_id: User ID to link to
            email: User's email address

        Returns:
            New AuthProvider instance for email authentication
        """
        return cls(
            user_id=user_id,
            provider=AuthProviderType.EMAIL,
            provider_user_id=email,  # For email auth, email is the provider user ID
            email=email
        )

    def to_response_dict(self) -> dict:
        """
        Convert auth provider to dictionary for API responses.

        Returns:
            Dictionary with auth provider data for client
        """
        return {
            "provider": self.provider.value,
            "email": self.email,
            "created_at": self.created_at.isoformat() + "Z",
            "last_used_at": self.last_used_at.isoformat() + "Z"
        }