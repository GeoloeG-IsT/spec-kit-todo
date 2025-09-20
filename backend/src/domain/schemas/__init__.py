"""
Pydantic schemas for API contracts.

These schemas define the request and response data structures for the TODO list API.
They ensure data validation and provide clear API documentation.
Based on the OpenAPI contract specification.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict

from ..models.todo_item import TodoPriority
from ..models.auth_provider import AuthProviderType


# User Schemas
class UserBase(BaseModel):
    """Base user schema with common fields."""
    display_name: str = Field(..., min_length=1, max_length=100, description="User's display name")
    email: Optional[EmailStr] = Field(None, description="User's email address")


class UserCreate(UserBase):
    """Schema for creating a new user."""
    clerk_user_id: str = Field(..., min_length=1, description="Clerk user ID")


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500)


class UserResponse(UserBase):
    """Schema for user response data."""
    id: UUID = Field(..., description="User's unique identifier")
    clerk_user_id: str = Field(..., description="Clerk user ID")
    avatar_url: Optional[str] = Field(None, description="User's avatar URL")
    created_at: datetime = Field(..., description="User creation timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")

    model_config = ConfigDict(from_attributes=True)


# TodoItem Schemas
class TodoItemBase(BaseModel):
    """Base TODO item schema with common fields."""
    title: str = Field(..., min_length=1, max_length=2000, description="TODO item title")
    description: Optional[str] = Field(None, max_length=10000, description="TODO item description")
    priority: TodoPriority = Field(TodoPriority.MEDIUM, description="TODO item priority")


class TodoItemCreate(TodoItemBase):
    """Schema for creating a new TODO item."""
    pass


class TodoItemUpdate(BaseModel):
    """Schema for updating a TODO item."""
    title: Optional[str] = Field(None, min_length=1, max_length=2000)
    description: Optional[str] = Field(None, max_length=10000)
    completed: Optional[bool] = None
    priority: Optional[TodoPriority] = None
    order_index: Optional[int] = Field(None, ge=0)


class TodoItemResponse(TodoItemBase):
    """Schema for TODO item response data."""
    id: UUID = Field(..., description="TODO item unique identifier")
    completed: bool = Field(..., description="Whether the TODO is completed")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    order_index: int = Field(..., description="Order index for custom sorting")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# Session Schemas
class SessionCreate(BaseModel):
    """Schema for creating a new guest session."""
    user_agent: Optional[str] = Field(None, max_length=1000, description="User agent string")
    ip_address: Optional[str] = Field(None, max_length=45, description="Client IP address")


class SessionResponse(BaseModel):
    """Schema for session response data."""
    id: str = Field(..., description="Session unique identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")
    last_accessed_at: datetime = Field(..., description="Last access timestamp")

    model_config = ConfigDict(from_attributes=True)


# Auth Provider Schemas
class AuthProviderResponse(BaseModel):
    """Schema for auth provider response data."""
    provider: AuthProviderType = Field(..., description="Authentication provider type")
    email: Optional[str] = Field(None, description="Email from provider")
    created_at: datetime = Field(..., description="Provider link creation timestamp")
    last_used_at: datetime = Field(..., description="Last usage timestamp")

    model_config = ConfigDict(from_attributes=True)


# Bulk Operation Schemas
class TodoItemBulkUpdate(BaseModel):
    """Schema for bulk updating TODO items."""
    todo_ids: List[UUID] = Field(..., min_length=1, description="List of TODO item IDs to update")
    completed: Optional[bool] = Field(None, description="Set completion status")
    priority: Optional[TodoPriority] = Field(None, description="Set priority level")

    @field_validator('todo_ids')
    @classmethod
    def validate_todo_ids(cls, v):
        if not v:
            raise ValueError('At least one TODO ID is required')
        # Allow duplicates - service layer will handle deduplication
        return v

    @model_validator(mode='after')
    def validate_at_least_one_update_field(self):
        if self.completed is None and self.priority is None:
            raise ValueError('At least one update field (completed or priority) must be provided')
        return self


class TodoItemOrderUpdate(BaseModel):
    """Schema for a single TODO item order update."""
    todo_id: UUID = Field(..., description="TODO item ID")
    order_index: int = Field(..., ge=0, description="New order index")


class TodoItemReorder(BaseModel):
    """Schema for reordering TODO items."""
    todo_orders: List[TodoItemOrderUpdate] = Field(
        ..., min_length=1, description="List of TODO items with new order indices"
    )

    @field_validator('todo_orders')
    @classmethod
    def validate_todo_orders(cls, v):
        if not v:
            raise ValueError('At least one TODO order update is required')
        todo_ids = [item.todo_id for item in v]
        if len(todo_ids) != len(set(todo_ids)):
            raise ValueError('Duplicate TODO IDs in reorder request')
        return v


# Session Conversion Schema
class SessionConvertRequest(BaseModel):
    """Schema for converting guest session to registered user."""
    session_id: str = Field(..., min_length=1, description="Guest session ID to convert")


class SessionConvertResponse(BaseModel):
    """Schema for session conversion response."""
    migrated_todos_count: int = Field(..., ge=0, description="Number of TODOs migrated")


# List Response Schemas
class TodoItemListResponse(BaseModel):
    """Schema for paginated TODO item list response."""
    items: List[TodoItemResponse] = Field(..., description="List of TODO items")
    total: int = Field(..., ge=0, description="Total number of items")
    limit: int = Field(..., ge=0, description="Items per page limit")
    offset: int = Field(..., ge=0, description="Pagination offset")


# Bulk Operation Response Schemas
class BulkUpdateResponse(BaseModel):
    """Schema for bulk update operation response."""
    updated_count: int = Field(..., ge=0, description="Number of items updated")


# Error Schemas
class ErrorResponse(BaseModel):
    """Schema for API error responses."""
    error: str = Field(..., description="Error type identifier")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error details")


# Health Check Schema
class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str = Field("healthy", description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    version: str = Field("1.0.0", description="API version")


# Export all schemas
__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",

    # TODO item schemas
    "TodoItemBase",
    "TodoItemCreate",
    "TodoItemUpdate",
    "TodoItemResponse",
    "TodoItemListResponse",

    # Session schemas
    "SessionCreate",
    "SessionResponse",
    "SessionConvertRequest",
    "SessionConvertResponse",

    # Auth provider schemas
    "AuthProviderResponse",

    # Bulk operation schemas
    "TodoItemBulkUpdate",
    "TodoItemOrderUpdate",
    "TodoItemReorder",
    "BulkUpdateResponse",

    # Common schemas
    "ErrorResponse",
    "HealthResponse",
]