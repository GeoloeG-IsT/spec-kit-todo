"""
pytest configuration for the TODO list backend tests.

Sets up test client with mocked dependencies for rapid TDD feedback.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from contextlib import asynccontextmanager

# Import the application
from src.main import app
from src.infrastructure.database import get_db_session, get_session
from src.api.middleware.auth import require_auth, require_user


# Global storage for test data persistence across requests
_test_storage = {
    'todos': {},  # todo_id -> todo_item
    'users': {},  # user_id -> user
    'sessions': {},  # session_id -> session
    'next_order_index': 0
}


@pytest.fixture
def mock_db_session():
    """Mock database session for testing with in-memory storage."""
    from unittest.mock import MagicMock

    # Clear storage at start of each test
    _test_storage['todos'].clear()
    _test_storage['users'].clear()
    _test_storage['sessions'].clear()
    _test_storage['next_order_index'] = 0

    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.refresh = AsyncMock()

    # Store added items
    added_items = []

    def mock_add(item):
        added_items.append(item)
        if hasattr(item, 'id') and item.id is None:
            # Generate a mock ID for new items
            from uuid import uuid4
            item.id = uuid4()

        # Ensure all required attributes are present for TodoItem
        if hasattr(item, 'title'):  # This looks like a TodoItem
            from datetime import datetime, timezone
            if not hasattr(item, 'created_at') or item.created_at is None:
                item.created_at = datetime.now(timezone.utc)
            if not hasattr(item, 'updated_at') or item.updated_at is None:
                item.updated_at = datetime.now(timezone.utc)
            if not hasattr(item, 'completed'):
                item.completed = False
            if not hasattr(item, 'completed_at'):
                item.completed_at = None
            if not hasattr(item, 'priority') or item.priority is None:
                item.priority = 'medium'
            if not hasattr(item, 'order_index') or item.order_index is None:
                item.order_index = _test_storage['next_order_index']
                _test_storage['next_order_index'] += 1

        # Store in appropriate collection
        if hasattr(item, 'session_id') and item.session_id:
            _test_storage['todos'][str(item.id)] = item
        elif hasattr(item, 'user_id') and item.user_id:
            _test_storage['todos'][str(item.id)] = item

    session.add = mock_add
    session.delete = MagicMock()

    # Mock execute for queries
    async def mock_execute(query):
        mock_result = MagicMock()
        query_str = str(query)

        # DEBUG: Print queries to understand what's happening (removed for cleaner output)

        # Check if this is a count query
        if 'count(' in query_str.lower():
            # Start with all stored TODOs for counting and filter out soft-deleted ones
            todos = [todo for todo in _test_storage['todos'].values()
                    if getattr(todo, 'deleted_at', None) is None]

            # Note: Session filtering would require complex SQL parameter parsing
            # For integration tests, basic functionality verification is sufficient

            # Apply same filtering logic as select queries
            if 'priority' in query_str.lower():
                import re
                # Try different pattern variations for priority matching
                priority_match = re.search(r"priority.*?=.*?:([^)]+)", query_str, re.IGNORECASE)
                if not priority_match:
                    priority_match = re.search(r"priority.*?=.*?'([^']+)'", query_str, re.IGNORECASE)
                if priority_match:
                    priority_filter = priority_match.group(1).strip()
                    todos = [todo for todo in todos if getattr(todo, 'priority', None) == priority_filter]

            if 'completed' in query_str.lower():
                # Handle both parameter and literal forms
                if 'completed = true' in query_str.lower() or 'completed = 1' in query_str.lower() or 'completed = :' in query_str.lower():
                    todos = [todo for todo in todos if getattr(todo, 'completed', False) == True]
                elif 'completed = false' in query_str.lower() or 'completed = 0' in query_str.lower():
                    todos = [todo for todo in todos if getattr(todo, 'completed', False) == False]

            todo_count = len(todos)
            mock_result.scalar.return_value = todo_count
            return mock_result

        # Check if this is an order_index query (for next order calculation)
        elif 'order_index' in query_str.lower() and 'max' in query_str.lower():
            # Return current max order index
            mock_result.scalar.return_value = _test_storage['next_order_index'] - 1 if _test_storage['next_order_index'] > 0 else None
            return mock_result

        # Check if this is a TODO listing query
        elif 'todoitems' in query_str.lower() and 'select' in query_str.lower():
            # Start with all stored TODOs and filter out soft-deleted ones
            todos = [todo for todo in _test_storage['todos'].values()
                    if getattr(todo, 'deleted_at', None) is None]

            # Note: Session filtering would require complex SQL parameter parsing
            # For integration tests, basic functionality verification is sufficient

            # Apply filtering based on query conditions
            if 'priority' in query_str.lower():
                # Extract priority value from query (basic pattern matching)
                import re
                # Try different pattern variations for priority matching
                priority_match = re.search(r"priority.*?=.*?:([^)]+)", query_str, re.IGNORECASE)
                if not priority_match:
                    priority_match = re.search(r"priority.*?=.*?'([^']+)'", query_str, re.IGNORECASE)
                if priority_match:
                    priority_filter = priority_match.group(1).strip()
                    todos = [todo for todo in todos if getattr(todo, 'priority', None) == priority_filter]

            if 'completed' in query_str.lower():
                # Extract completed status from query
                if 'completed = true' in query_str.lower() or 'completed = 1' in query_str.lower() or 'completed = :' in query_str.lower():
                    todos = [todo for todo in todos if getattr(todo, 'completed', False) == True]
                elif 'completed = false' in query_str.lower() or 'completed = 0' in query_str.lower():
                    todos = [todo for todo in todos if getattr(todo, 'completed', False) == False]

            # Mock the scalars().all() chain
            mock_scalars = MagicMock()
            mock_scalars.all.return_value = todos
            mock_result.scalars.return_value = mock_scalars

            # Also support scalar_one_or_none for single item queries
            mock_result.scalar_one_or_none.return_value = todos[0] if todos else None
            return mock_result

        else:
            # Default fallback for other queries
            mock_result.scalar_one_or_none.return_value = None

            # Return empty list for scalars
            empty_scalars = MagicMock()
            empty_scalars.all.return_value = []
            mock_result.scalars.return_value = empty_scalars

            mock_result.scalar.return_value = 0
            return mock_result

    session.execute = mock_execute
    session._test_storage = _test_storage  # Store reference for debugging

    return session


@asynccontextmanager
async def test_lifespan(app):
    """Test lifespan context manager that skips database initialization."""
    # Skip database setup for tests
    yield


@pytest.fixture
def mock_session_service():
    """Mock session service for middleware testing."""
    from unittest.mock import Mock, AsyncMock
    service = Mock()
    service.validate_session = AsyncMock()
    service.create_session = AsyncMock()

    # Mock a valid session object
    mock_session = Mock()
    mock_session.id = "test_session_123"
    mock_session.created_at = "2023-01-01T00:00:00Z"
    mock_session.last_accessed_at = "2023-01-01T00:00:00Z"

    service.validate_session.return_value = mock_session
    service.create_session.return_value = mock_session
    return service


@asynccontextmanager
async def override_get_session():
    """Mock get_session for middleware."""
    from unittest.mock import AsyncMock
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    yield mock_session


@pytest.fixture
def client(mock_db_session, mock_session_service):
    """Create a test client with mocked database session."""
    from unittest.mock import patch, Mock

    # Use a lambda to return the same session instance for each request
    def override_get_db_session():
        yield mock_db_session

    def mock_require_auth():
        """Mock auth dependency that returns a fake user context."""
        return {
            "type": "user",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "clerk_user_id": "user_2ABC123DEF456",
            "authenticated": True,
            "session_id": None
        }

    def mock_require_user():
        """Mock user dependency that returns a fake user context."""
        return {
            "type": "user",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "clerk_user_id": "user_2ABC123DEF456",
            "authenticated": True,
            "session_id": None
        }

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[require_auth] = mock_require_auth
    app.dependency_overrides[require_user] = mock_require_user

    # Override the lifespan to skip database initialization
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = test_lifespan

    # Mock the session service for middleware
    with patch('src.infrastructure.database.get_session', side_effect=override_get_session), \
         patch('src.application.services.session_service.SessionService', return_value=mock_session_service), \
         patch('src.api.middleware.session.SessionMiddleware._validate_session', new=AsyncMock(return_value=mock_session_service.validate_session.return_value)), \
         patch('src.api.middleware.session.SessionMiddleware._create_new_session', new=AsyncMock(return_value=mock_session_service.create_session.return_value)):

        with TestClient(app) as client:
            yield client

    # Clean up
    app.dependency_overrides.clear()
    app.router.lifespan_context = original_lifespan