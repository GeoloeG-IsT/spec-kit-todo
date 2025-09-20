"""
User service for managing user operations.

Handles user creation, updates, authentication, and profile management.
Coordinates with Clerk authentication and manages user sessions.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import structlog

from ...domain.models.user import User
from ...domain.models.auth_provider import AuthProvider, AuthProviderType
from ...domain.schemas import UserCreate, UserUpdate, UserResponse, SessionConvertRequest

logger = structlog.get_logger(__name__)


class UserService:
    """Service for user management operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_or_update_user(self, user_data: UserCreate) -> tuple[User, bool]:
        """
        Create a new user or update existing user.

        Args:
            user_data: User creation data with Clerk user ID

        Returns:
            Tuple of (user, created) where created is True if user was created, False if updated
        """
        # Check if user with this Clerk ID already exists
        existing_user = await self._get_user_by_clerk_id(user_data.clerk_user_id)

        if existing_user:
            # Update existing user
            if user_data.display_name:
                existing_user.display_name = user_data.display_name
            if user_data.email:
                existing_user.email = user_data.email
            existing_user.update_last_login()

            logger.info("User updated", user_id=str(existing_user.id), clerk_id=user_data.clerk_user_id)
            return existing_user, False
        else:
            # Create new user
            user = User.create_from_clerk(
                clerk_user_id=user_data.clerk_user_id,
                display_name=user_data.display_name,
                email=user_data.email
            )

            self.session.add(user)

            logger.info("User created", user_id=str(user.id), clerk_id=user_data.clerk_user_id)
            return user, True

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user account.

        Args:
            user_data: User creation data with Clerk user ID

        Returns:
            Created user instance

        Raises:
            ValueError: If user with Clerk ID already exists
        """
        try:
            # Check if user with this Clerk ID already exists
            existing_user = await self._get_user_by_clerk_id(user_data.clerk_user_id)
            if existing_user:
                raise ValueError(f"User with Clerk ID {user_data.clerk_user_id} already exists")

            # Create new user
            user = User.create_from_clerk(
                clerk_user_id=user_data.clerk_user_id,
                display_name=user_data.display_name,
                email=user_data.email
            )

            self.session.add(user)
            # Don't commit here - let route handler manage transactions

            logger.info("User created successfully", user_id=str(user.id), clerk_id=user_data.clerk_user_id)
            return user

        except IntegrityError as e:
            await self.session.rollback()
            logger.error("Failed to create user due to integrity error", error=str(e))
            raise ValueError("User creation failed due to data integrity constraints")

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by their UUID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_clerk_id(self, clerk_user_id: str) -> Optional[User]:
        """Get user by their Clerk user ID."""
        return await self._get_user_by_clerk_id(clerk_user_id)

    async def _get_user_by_clerk_id(self, clerk_user_id: str) -> Optional[User]:
        """Internal method to get user by Clerk ID."""
        result = await self.session.execute(
            select(User).where(User.clerk_user_id == clerk_user_id)
        )
        return result.scalar_one_or_none()

    async def update_user(self, user_id: UUID, user_update: UserUpdate) -> Optional[User]:
        """
        Update user information.

        Args:
            user_id: User's UUID
            user_update: Update data

        Returns:
            Updated user or None if user not found
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # Update fields if provided
        if user_update.display_name is not None:
            user.display_name = user_update.display_name
        if user_update.avatar_url is not None:
            user.avatar_url = user_update.avatar_url

        user.updated_at = datetime.utcnow()
        # Don't commit here - let route handler manage transactions

        logger.info("User updated successfully", user_id=str(user.id))
        return user

    async def update_last_login(self, user_id: UUID) -> Optional[User]:
        """Update user's last login timestamp."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        user.update_last_login()
        # Don't commit here - let route handler manage transactions

        return user

    async def get_user_auth_providers(self, user_id: UUID) -> List[AuthProvider]:
        """Get all authentication providers for a user."""
        result = await self.session.execute(
            select(AuthProvider).where(AuthProvider.user_id == user_id)
        )
        return list(result.scalars().all())

    async def add_auth_provider(self, user_id: UUID, provider_type: AuthProviderType,
                               provider_user_id: str, email: Optional[str] = None) -> AuthProvider:
        """
        Add an authentication provider to a user.

        Args:
            user_id: User's UUID
            provider_type: Type of auth provider
            provider_user_id: External user ID from provider
            email: Email from provider (optional)

        Returns:
            Created AuthProvider instance

        Raises:
            ValueError: If provider already exists for user
        """
        # Check if this provider already exists for the user
        existing = await self.session.execute(
            select(AuthProvider).where(
                AuthProvider.user_id == user_id,
                AuthProvider.provider == provider_type
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"User already has {provider_type.value} provider linked")

        # Create the auth provider
        if provider_type == AuthProviderType.EMAIL:
            auth_provider = AuthProvider.create_email_provider(user_id, email or provider_user_id)
        else:
            auth_provider = AuthProvider.create_oauth_provider(user_id, provider_type, provider_user_id, email)

        self.session.add(auth_provider)
        # Don't commit here - let route handler manage transactions

        logger.info("Auth provider added", user_id=str(user_id), provider=provider_type.value)
        return auth_provider

    async def get_user_by_provider(self, provider_type: AuthProviderType,
                                  provider_user_id: str) -> Optional[User]:
        """
        Get user by their authentication provider information.

        Args:
            provider_type: Type of auth provider
            provider_user_id: External user ID from provider

        Returns:
            User if found, None otherwise
        """
        result = await self.session.execute(
            select(User)
            .join(AuthProvider)
            .where(
                AuthProvider.provider == provider_type,
                AuthProvider.provider_user_id == provider_user_id
            )
        )
        return result.scalar_one_or_none()

    async def convert_guest_session(self, user_id: UUID, session_id: str) -> int:
        """
        Convert guest session TODOs to a registered user.

        Args:
            user_id: Target user ID
            session_id: Guest session ID to convert

        Returns:
            Number of TODOs migrated

        Note: This method updates TODOs but doesn't import TodoItem here
        to avoid circular imports. The actual migration is handled by TodoService.
        """
        # This is a placeholder - the actual implementation should delegate
        # to TodoService to avoid circular imports
        logger.info("Guest session conversion requested", user_id=str(user_id), session_id=session_id)
        return 0  # Will be implemented when TodoService is available

    async def delete_user(self, user_id: UUID) -> bool:
        """
        Delete a user and all associated data.

        Args:
            user_id: User's UUID

        Returns:
            True if user was deleted, False if user not found
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        # Delete user (cascades to auth providers and TODOs via DB constraints)
        await self.session.delete(user)
        # Don't commit here - let route handler manage transactions

        logger.info("User deleted successfully", user_id=str(user_id))
        return True

    def to_response(self, user: User) -> UserResponse:
        """Convert User model to response schema."""
        return UserResponse(
            id=user.id,
            clerk_user_id=user.clerk_user_id,
            display_name=user.display_name,
            email=user.email,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )