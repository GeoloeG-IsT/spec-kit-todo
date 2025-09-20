"""
TodoItem domain model for the TODO list application.

Represents individual TODO tasks with completion status and metadata.
Follows the data model specification from data-model.md.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship


class TodoPriority(str, Enum):
    """Enumeration for TODO priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TodoItem(SQLModel, table=True):
    """
    TodoItem entity representing individual TODO tasks.

    Fields:
    - id: UUID (primary key)
    - user_id: UUID (foreign key, nullable for guest todos)
    - session_id: String (nullable, for guest user sessions)
    - title: Text (required, max 2000 characters)
    - description: Text (nullable, max 10000 characters)
    - completed: Boolean (default: false)
    - completed_at: DateTime (nullable)
    - priority: Integer (1=low, 2=medium, 3=high, default: 2)
    - order_index: Integer (for user-defined ordering)
    - created_at: DateTime
    - updated_at: DateTime

    Relationships:
    - Many-to-one with User (nullable for guest todos)

    Validation Rules:
    - title cannot be empty string
    - either user_id or session_id must be provided (not both)
    - priority must be 1, 2, or 3
    - order_index must be positive integer

    State Transitions:
    - Created → Pending (default state)
    - Pending → Completed (when marked complete)
    - Completed → Pending (when unmarked)
    - Any → Deleted (soft delete with deleted_at timestamp)
    """

    __tablename__ = "todoitems"

    # Primary key
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # User/session association (exactly one must be set)
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.id", index=True)
    session_id: Optional[str] = Field(default=None, index=True, max_length=255)

    # TODO content
    title: str = Field(min_length=1, max_length=2000)
    description: Optional[str] = Field(default=None, max_length=10000)

    # Status and completion
    completed: bool = Field(default=False)
    completed_at: Optional[datetime] = Field(default=None)

    # Priority and ordering
    priority: TodoPriority = Field(default=TodoPriority.MEDIUM)
    order_index: int = Field(default=0, ge=0)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)

    # Relationships
    user: Optional["User"] = Relationship(back_populates="todos")

    def __str__(self) -> str:
        """String representation of the TODO item."""
        status = "✓" if self.completed else "○"
        return f"{status} {self.title} [{self.priority.value}]"

    def __repr__(self) -> str:
        """Detailed representation of the TODO item."""
        return (
            f"TodoItem("
            f"id={self.id}, "
            f"title='{self.title}', "
            f"completed={self.completed}, "
            f"priority={self.priority.value}, "
            f"user_id={self.user_id}, "
            f"session_id='{self.session_id}'"
            f")"
        )

    def mark_completed(self) -> None:
        """Mark the TODO as completed."""
        if not self.completed:
            self.completed = True
            self.completed_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

    def mark_pending(self) -> None:
        """Mark the TODO as pending (not completed)."""
        if self.completed:
            self.completed = False
            self.completed_at = None
            self.updated_at = datetime.utcnow()

    def update_content(self, title: Optional[str] = None,
                      description: Optional[str] = None,
                      priority: Optional[TodoPriority] = None) -> None:
        """Update TODO content."""
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if priority is not None:
            self.priority = priority
        self.updated_at = datetime.utcnow()

    def set_order_index(self, order_index: int) -> None:
        """Update the order index for custom ordering."""
        if order_index >= 0:
            self.order_index = order_index
            self.updated_at = datetime.utcnow()

    def soft_delete(self) -> None:
        """Soft delete the TODO by setting deleted_at timestamp."""
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @property
    def is_deleted(self) -> bool:
        """Check if the TODO is soft deleted."""
        return self.deleted_at is not None

    @property
    def belongs_to_user(self) -> bool:
        """Check if TODO belongs to a registered user."""
        return self.user_id is not None

    @property
    def belongs_to_session(self) -> bool:
        """Check if TODO belongs to a guest session."""
        return self.session_id is not None

    @classmethod
    def create_for_user(cls, user_id: UUID, title: str,
                       description: Optional[str] = None,
                       priority: TodoPriority = TodoPriority.MEDIUM) -> "TodoItem":
        """Create a new TODO for a registered user."""
        return cls(
            user_id=user_id,
            session_id=None,
            title=title,
            description=description,
            priority=priority
        )

    @classmethod
    def create_for_session(cls, session_id: str, title: str,
                          description: Optional[str] = None,
                          priority: TodoPriority = TodoPriority.MEDIUM) -> "TodoItem":
        """Create a new TODO for a guest session."""
        return cls(
            user_id=None,
            session_id=session_id,
            title=title,
            description=description,
            priority=priority
        )