# Data Model: TODO List App

**Feature**: TODO List App
**Date**: 2025-01-19

## Domain Entities

### User
Represents registered users with authentication credentials and persistent data.

**Fields**:
- `id`: UUID (primary key)
- `clerk_user_id`: String (unique, external ID from Clerk)
- `email`: String (unique, nullable for OAuth-only users)
- `display_name`: String (user's preferred name)
- `avatar_url`: String (nullable, profile image URL)
- `created_at`: DateTime
- `updated_at`: DateTime
- `last_login_at`: DateTime (nullable)

**Relationships**:
- One-to-many with TodoItem
- One-to-many with AuthProvider

**Validation Rules**:
- clerk_user_id must be unique across all users
- email must be valid email format when provided
- display_name cannot be empty string

**State Transitions**:
- Created → Active (on first login)
- Active → Inactive (after 1 year of no login - soft delete)

### TodoItem
Represents individual TODO tasks with completion status and metadata.

**Fields**:
- `id`: UUID (primary key)
- `user_id`: UUID (foreign key, nullable for guest todos)
- `session_id`: String (nullable, for guest user sessions)
- `title`: Text (required, max 2000 characters)
- `description`: Text (nullable, max 10000 characters)
- `completed`: Boolean (default: false)
- `completed_at`: DateTime (nullable)
- `priority`: Integer (1=low, 2=medium, 3=high, default: 2)
- `order_index`: Integer (for user-defined ordering)
- `created_at`: DateTime
- `updated_at`: DateTime

**Relationships**:
- Many-to-one with User (nullable for guest todos)

**Validation Rules**:
- title cannot be empty string
- either user_id or session_id must be provided (not both)
- priority must be 1, 2, or 3
- order_index must be positive integer

**State Transitions**:
- Created → Pending (default state)
- Pending → Completed (when marked complete)
- Completed → Pending (when unmarked)
- Any → Deleted (soft delete with deleted_at timestamp)

### Session
Represents guest user sessions with temporary TODO storage.

**Fields**:
- `id`: String (primary key, session token)
- `created_at`: DateTime
- `last_accessed_at`: DateTime
- `expires_at`: DateTime (nullable, no timeout for guest sessions)
- `user_agent`: String (for security tracking)
- `ip_address`: String (for security tracking)

**Relationships**:
- One-to-many with TodoItem (via session_id)

**Validation Rules**:
- id must be unique session identifier
- last_accessed_at updated on every request
- session persists until browser closure (no server-side expiration)

**State Transitions**:
- Created → Active (when first TODO created)
- Active → Converted (when guest upgrades to registered user)
- Active → Expired (when browser session ends)

### AuthProvider
Links users to external OAuth providers for multi-provider authentication.

**Fields**:
- `id`: UUID (primary key)
- `user_id`: UUID (foreign key)
- `provider`: String (google, github, linkedin, email)
- `provider_user_id`: String (external user ID from provider)
- `email`: String (nullable, email from provider)
- `created_at`: DateTime
- `last_used_at`: DateTime

**Relationships**:
- Many-to-one with User

**Validation Rules**:
- combination of user_id + provider must be unique
- provider must be one of: google, github, linkedin, email
- provider_user_id must be unique per provider

## Database Schema (SQLModel)

```python
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

class TodoPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class AuthProviderType(str, Enum):
    GOOGLE = "google"
    GITHUB = "github"
    LINKEDIN = "linkedin"
    EMAIL = "email"

class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    clerk_user_id: str = Field(unique=True, index=True)
    email: Optional[str] = Field(default=None, unique=True, index=True)
    display_name: str
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None

    # Relationships
    todos: List["TodoItem"] = Relationship(back_populates="user")
    auth_providers: List["AuthProvider"] = Relationship(back_populates="user")

class TodoItem(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="user.id")
    session_id: Optional[str] = Field(default=None, index=True)
    title: str = Field(max_length=2000)
    description: Optional[str] = Field(default=None, max_length=10000)
    completed: bool = Field(default=False)
    completed_at: Optional[datetime] = None
    priority: TodoPriority = Field(default=TodoPriority.MEDIUM)
    order_index: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    # Relationships
    user: Optional[User] = Relationship(back_populates="todos")

class Session(SQLModel, table=True):
    id: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

class AuthProvider(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    provider: AuthProviderType
    provider_user_id: str
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="auth_providers")

    class Config:
        # Unique constraint on user_id + provider
        table_args = (
            UniqueConstraint('user_id', 'provider'),
            UniqueConstraint('provider', 'provider_user_id'),
        )
```

## Pydantic Schemas (API Contract Types)

```python
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# User Schemas
class UserBase(BaseModel):
    display_name: str
    email: Optional[EmailStr] = None

class UserCreate(UserBase):
    clerk_user_id: str

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    clerk_user_id: str
    avatar_url: Optional[str]
    created_at: datetime
    last_login_at: Optional[datetime]

# TodoItem Schemas
class TodoItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TodoPriority = TodoPriority.MEDIUM

class TodoItemCreate(TodoItemBase):
    pass

class TodoItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[TodoPriority] = None
    order_index: Optional[int] = None

class TodoItemResponse(TodoItemBase):
    id: UUID
    completed: bool
    completed_at: Optional[datetime]
    order_index: int
    created_at: datetime
    updated_at: datetime

# Session Schemas
class SessionCreate(BaseModel):
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

class SessionResponse(BaseModel):
    id: str
    created_at: datetime
    last_accessed_at: datetime

# Auth Provider Schemas
class AuthProviderResponse(BaseModel):
    provider: AuthProviderType
    email: Optional[str]
    created_at: datetime
    last_used_at: datetime

# Bulk Operations
class TodoItemBulkUpdate(BaseModel):
    todo_ids: List[UUID]
    completed: Optional[bool] = None
    priority: Optional[TodoPriority] = None

class TodoItemReorder(BaseModel):
    todo_orders: List[tuple[UUID, int]]  # (todo_id, new_order_index)
```

## Business Rules

### Guest Session Management
1. Guest sessions are created automatically when first TODO is added
2. Session IDs are cryptographically secure random strings
3. Guest TODOs are associated with session_id only (user_id = null)
4. No server-side session expiration (persists until browser closure)

### User Registration and Migration
1. When guest converts to registered user:
   - Create User record with Clerk user ID
   - Update all session TODOs to reference new user_id
   - Clear session_id from migrated TODOs
   - Session record remains for audit trail

### Authentication and Authorization
1. All API endpoints require either:
   - Valid Clerk JWT token (registered users)
   - Valid session ID (guest users)
2. Users can only access their own TODOs
3. Guest users can only access TODOs from their session

### Real-time Sync Rules
1. "Last Write Wins" conflict resolution
2. Updates broadcast to all user sessions via SSE
3. Guest sessions receive updates only for their session
4. Optimistic updates on frontend with rollback on conflict

### Data Retention
1. User data retained permanently (per specification)
2. Guest session data cleaned up after 30 days of inactivity
3. Soft delete for TODOs (deleted_at timestamp)
4. Hard delete for sessions after cleanup period

## Migration Strategy

### Database Migrations
```sql
-- Initial schema creation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clerk_user_id VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE,
    display_name VARCHAR NOT NULL,
    avatar_url VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP
);

-- Sessions table
CREATE TABLE sessions (
    id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    last_accessed_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    user_agent VARCHAR,
    ip_address VARCHAR
);

-- Todo items table
CREATE TABLE todoitems (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    session_id VARCHAR REFERENCES sessions(id),
    title TEXT NOT NULL CHECK (length(title) <= 2000),
    description TEXT CHECK (length(description) <= 10000),
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    priority VARCHAR DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    CHECK (
        (user_id IS NOT NULL AND session_id IS NULL) OR
        (user_id IS NULL AND session_id IS NOT NULL)
    )
);

-- Auth providers table
CREATE TABLE authproviders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) NOT NULL,
    provider VARCHAR NOT NULL CHECK (provider IN ('google', 'github', 'linkedin', 'email')),
    provider_user_id VARCHAR NOT NULL,
    email VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, provider),
    UNIQUE(provider, provider_user_id)
);

-- Indexes for performance
CREATE INDEX idx_todos_user_id ON todoitems(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_todos_session_id ON todoitems(session_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_todos_created_at ON todoitems(created_at);
CREATE INDEX idx_sessions_last_accessed ON sessions(last_accessed_at);
```

This data model supports the complete feature set including guest users, registered users, OAuth authentication, real-time sync, and session management while maintaining clean separation of concerns and scalability.