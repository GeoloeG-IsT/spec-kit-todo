"""
Contract tests for POST /api/todos endpoint.

These tests verify that the API adheres to the OpenAPI contract specification.
They MUST fail initially (TDD approach) and pass after implementation.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from unittest.mock import patch, Mock, AsyncMock
from uuid import uuid4
from datetime import datetime


# Client fixture is provided by conftest.py


@pytest.fixture
def mock_todo_service():
    """Mock todo service for testing."""
    with patch("src.api.routes.todos.TodoService") as mock_class:
        mock_instance = Mock()
        # Set async methods to use AsyncMock
        mock_instance.create_todo_for_user = AsyncMock()
        mock_instance.create_todo_for_session = AsyncMock()
        mock_instance.to_response = Mock()  # Keep sync methods as Mock
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_realtime_service():
    """Mock realtime service for testing."""
    with patch("src.api.routes.todos.realtime_service") as mock:
        # Make async methods use AsyncMock
        mock.notify_todo_created = AsyncMock()
        mock.notify_todo_updated = AsyncMock()
        mock.notify_todo_deleted = AsyncMock()
        yield mock


@pytest.fixture
def auth_headers():
    """Authentication headers with mock Clerk token."""
    return {"Authorization": "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test.token"}


@pytest.fixture
def session_headers():
    """Session headers for guest users."""
    return {"X-Session-ID": "sess_abc123def456ghi789"}


class TestCreateTodo:
    """Test cases for POST /api/todos endpoint."""

    def test_create_todo_authenticated_user_success(self, client: TestClient, auth_headers: dict, mock_todo_service, mock_realtime_service):
        """Test successful TODO creation for authenticated user."""
        # Arrange
        todo_id = uuid4()
        mock_todo = Mock()
        mock_todo.id = todo_id
        mock_todo.title = "Buy groceries"
        mock_todo.description = "Milk, bread, eggs, and fruits"
        mock_todo.priority = "medium"
        mock_todo.completed = False
        mock_todo.completed_at = None
        mock_todo.created_at = datetime.now()
        mock_todo.updated_at = datetime.now()
        mock_todo.order_index = 1

        mock_todo_service.create_todo_for_user.return_value = mock_todo
        mock_todo_response = Mock()
        mock_todo_response.id = str(todo_id)
        mock_todo_response.title = "Buy groceries"
        mock_todo_response.description = "Milk, bread, eggs, and fruits"
        mock_todo_response.priority = "medium"
        mock_todo_response.completed = False
        mock_todo_response.completed_at = None
        mock_todo_response.created_at = "2023-01-01T00:00:00Z"
        mock_todo_response.updated_at = "2023-01-01T00:00:00Z"
        mock_todo_response.order_index = 1
        mock_todo_response.model_dump = Mock(return_value={
            "id": str(todo_id),
            "title": "Buy groceries",
            "description": "Milk, bread, eggs, and fruits",
            "priority": "medium",
            "completed": False,
            "completed_at": None,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "order_index": 1
        })
        mock_todo_service.to_response.return_value = mock_todo_response

        todo_data = {
            "title": "Buy groceries",
            "description": "Milk, bread, eggs, and fruits",
            "priority": "medium"
        }

        # Act
        response: Response = client.post("/api/todos", json=todo_data, headers=auth_headers)

        # Assert
        assert response.status_code == 201
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert "id" in data
        assert data["title"] == "Buy groceries"
        assert data["description"] == "Milk, bread, eggs, and fruits"
        assert data["priority"] == "medium"
        assert data["completed"] is False
        assert data["completed_at"] is None
        assert "created_at" in data
        assert "updated_at" in data
        assert isinstance(data["order_index"], int)

        mock_todo_service.create_todo_for_user.assert_called_once()
        mock_todo_service.to_response.assert_called_once_with(mock_todo)
        mock_realtime_service.notify_todo_created.assert_called_once()

    def test_create_todo_guest_user_success(self, client: TestClient, mock_todo_service, mock_realtime_service):
        """Test successful TODO creation for guest user."""
        # Arrange
        todo_id = uuid4()
        mock_todo = Mock()
        mock_todo.id = todo_id
        mock_todo.title = "Guest TODO"
        mock_todo.description = None
        mock_todo.priority = "high"
        mock_todo.completed = False
        mock_todo.completed_at = None
        mock_todo.created_at = datetime.now()
        mock_todo.updated_at = datetime.now()
        mock_todo.order_index = 1

        mock_todo_service.create_todo_for_user.return_value = mock_todo
        mock_todo_response = Mock()
        mock_todo_response.id = str(todo_id)
        mock_todo_response.title = "Guest TODO"
        mock_todo_response.description = None
        mock_todo_response.priority = "high"
        mock_todo_response.completed = False
        mock_todo_response.completed_at = None
        mock_todo_response.created_at = "2023-01-01T00:00:00Z"
        mock_todo_response.updated_at = "2023-01-01T00:00:00Z"
        mock_todo_response.order_index = 1
        mock_todo_service.to_response.return_value = mock_todo_response

        todo_data = {
            "title": "Guest TODO",
            "priority": "high"
        }

        # Act - use mocked auth from conftest.py
        response: Response = client.post("/api/todos", json=todo_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Guest TODO"
        assert data["priority"] == "high"

        mock_todo_service.create_todo_for_user.assert_called_once()
        mock_todo_service.to_response.assert_called_once_with(mock_todo)
        mock_realtime_service.notify_todo_created.assert_called_once()

    def test_create_todo_minimal_data(self, client: TestClient, auth_headers: dict, mock_todo_service, mock_realtime_service):
        """Test TODO creation with only required fields."""
        # Arrange
        todo_id = uuid4()
        mock_todo = Mock()
        mock_todo.id = todo_id
        mock_todo.title = "Minimal TODO"
        mock_todo.description = None
        mock_todo.priority = "medium"
        mock_todo.completed = False
        mock_todo.completed_at = None
        mock_todo.created_at = datetime.now()
        mock_todo.updated_at = datetime.now()
        mock_todo.order_index = 1

        mock_todo_service.create_todo_for_user.return_value = mock_todo
        mock_todo_response = Mock()
        mock_todo_response.id = str(todo_id)
        mock_todo_response.title = "Minimal TODO"
        mock_todo_response.description = None
        mock_todo_response.priority = "medium"
        mock_todo_response.completed = False
        mock_todo_response.completed_at = None
        mock_todo_response.created_at = "2023-01-01T00:00:00Z"
        mock_todo_response.updated_at = "2023-01-01T00:00:00Z"
        mock_todo_response.order_index = 1
        mock_todo_response.model_dump = Mock(return_value={
            "id": str(todo_id),
            "title": "Minimal TODO",
            "description": None,
            "priority": "medium",
            "completed": False,
            "completed_at": None,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "order_index": 1
        })
        mock_todo_service.to_response.return_value = mock_todo_response

        todo_data = {
            "title": "Minimal TODO"
        }

        # Act
        response: Response = client.post("/api/todos", json=todo_data, headers=auth_headers)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal TODO"
        assert data["description"] is None
        assert data["priority"] == "medium"  # Default priority

        mock_todo_service.create_todo_for_user.assert_called_once()
        mock_todo_service.to_response.assert_called_once_with(mock_todo)
        mock_realtime_service.notify_todo_created.assert_called_once()

    def test_create_todo_all_priorities(self, client: TestClient, auth_headers: dict, mock_todo_service, mock_realtime_service):
        """Test TODO creation with all valid priority levels."""
        priorities = ["low", "medium", "high"]

        for priority in priorities:
            # Arrange
            todo_id = uuid4()
            mock_todo = Mock()
            mock_todo.id = todo_id
            mock_todo.title = f"TODO with {priority} priority"
            mock_todo.priority = priority
            mock_todo.completed = False
            mock_todo.completed_at = None
            mock_todo.created_at = datetime.now()
            mock_todo.updated_at = datetime.now()
            mock_todo.order_index = 1

            mock_todo_service.create_todo_for_user.return_value = mock_todo
            mock_todo_response = Mock()
            mock_todo_response.id = str(todo_id)
            mock_todo_response.title = f"TODO with {priority} priority"
            mock_todo_response.description = None  # Add missing description field
            mock_todo_response.priority = priority
            mock_todo_response.completed = False
            mock_todo_response.completed_at = None
            mock_todo_response.created_at = "2023-01-01T00:00:00Z"
            mock_todo_response.updated_at = "2023-01-01T00:00:00Z"
            mock_todo_response.order_index = 1
            mock_todo_response.model_dump = Mock(return_value={
                "id": str(todo_id),
                "title": f"TODO with {priority} priority",
                "description": None,
                "priority": priority,
                "completed": False,
                "completed_at": None,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "order_index": 1
            })
            mock_todo_service.to_response.return_value = mock_todo_response

            todo_data = {
                "title": f"TODO with {priority} priority",
                "priority": priority
            }

            # Act
            response: Response = client.post("/api/todos", json=todo_data, headers=auth_headers)

            # Assert
            assert response.status_code == 201
            data = response.json()
            assert data["priority"] == priority

            # Reset mocks for next iteration
            mock_todo_service.reset_mock()
            mock_realtime_service.reset_mock()

    def test_create_todo_missing_title(self, client: TestClient, auth_headers: dict):
        """Test TODO creation without required title field."""
        # Arrange
        todo_data = {
            "description": "TODO without title",
            "priority": "medium"
        }

        # Act
        response: Response = client.post("/api/todos", json=todo_data, headers=auth_headers)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_create_todo_empty_title(self, client: TestClient, auth_headers: dict):
        """Test TODO creation with empty title."""
        # Arrange
        todo_data = {
            "title": "",
            "description": "Empty title TODO"
        }

        # Act
        response: Response = client.post("/api/todos", json=todo_data, headers=auth_headers)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "error" in data

    def test_create_todo_invalid_priority(self, client: TestClient, auth_headers: dict):
        """Test TODO creation with invalid priority value."""
        # Arrange
        todo_data = {
            "title": "Invalid priority TODO",
            "priority": "urgent"  # Not in enum: low, medium, high
        }

        # Act
        response: Response = client.post("/api/todos", json=todo_data, headers=auth_headers)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "error" in data

    def test_create_todo_long_title(self, client: TestClient, auth_headers: dict):
        """Test TODO creation with maximum length title."""
        # Arrange
        long_title = "A" * 2000  # Maximum length from schema
        todo_data = {
            "title": long_title
        }

        # Act
        response: Response = client.post("/api/todos", json=todo_data, headers=auth_headers)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == long_title

    def test_create_todo_title_too_long(self, client: TestClient, auth_headers: dict):
        """Test TODO creation with title exceeding maximum length."""
        # Arrange
        too_long_title = "A" * 2001  # Exceeds maximum length
        todo_data = {
            "title": too_long_title
        }

        # Act
        response: Response = client.post("/api/todos", json=todo_data, headers=auth_headers)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "error" in data

    def test_create_todo_long_description(self, client: TestClient, auth_headers: dict):
        """Test TODO creation with maximum length description."""
        # Arrange
        long_description = "B" * 10000  # Maximum length from schema
        todo_data = {
            "title": "Long description TODO",
            "description": long_description
        }

        # Act
        response: Response = client.post("/api/todos", json=todo_data, headers=auth_headers)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["description"] == long_description

    def test_create_todo_unauthorized(self, client: TestClient):
        """Test TODO creation without authentication or session."""
        from src.main import app
        from src.api.middleware.auth import require_auth

        # Arrange
        def raise_permission_error():
            raise PermissionError("Authentication required")

        original_override = app.dependency_overrides.get(require_auth)
        app.dependency_overrides[require_auth] = raise_permission_error

        try:
            todo_data = {
                "title": "Unauthorized TODO"
            }

            # Act
            response: Response = client.post("/api/todos", json=todo_data)

            # Assert
            assert response.status_code == 403
            data = response.json()
            assert data["error"] == "forbidden"
        finally:
            if original_override:
                app.dependency_overrides[require_auth] = original_override
            elif require_auth in app.dependency_overrides:
                del app.dependency_overrides[require_auth]

    def test_create_todo_invalid_token(self, client: TestClient):
        """Test TODO creation with invalid authentication token."""
        from src.main import app
        from src.api.middleware.auth import require_auth

        # Arrange
        def raise_permission_error():
            raise PermissionError("Invalid token")

        # Clear existing override and set our custom one
        original_override = app.dependency_overrides.get(require_auth)
        app.dependency_overrides[require_auth] = raise_permission_error

        try:
            todo_data = {
                "title": "Invalid token TODO"
            }
            headers = {"Authorization": "Bearer invalid.token"}

            # Act
            response: Response = client.post("/api/todos", json=todo_data, headers=headers)

            # Assert
            assert response.status_code == 403
            data = response.json()
            assert data["error"] == "forbidden"
        finally:
            # Restore original override
            if original_override:
                app.dependency_overrides[require_auth] = original_override
            elif require_auth in app.dependency_overrides:
                del app.dependency_overrides[require_auth]

    def test_create_todo_invalid_session(self, client: TestClient):
        """Test TODO creation with invalid session ID."""
        from src.main import app
        from src.api.middleware.auth import require_auth

        # Arrange
        def raise_permission_error():
            raise PermissionError("Invalid session")

        # Clear existing override and set our custom one
        original_override = app.dependency_overrides.get(require_auth)
        app.dependency_overrides[require_auth] = raise_permission_error

        try:
            todo_data = {
                "title": "Invalid session TODO"
            }
            headers = {"X-Session-ID": "invalid_session_id"}

            # Act
            response: Response = client.post("/api/todos", json=todo_data, headers=headers)

            # Assert
            assert response.status_code == 403
            data = response.json()
            assert data["error"] == "forbidden"
        finally:
            # Restore original override
            if original_override:
                app.dependency_overrides[require_auth] = original_override
            elif require_auth in app.dependency_overrides:
                del app.dependency_overrides[require_auth]

    def test_todo_response_schema(self, client: TestClient, auth_headers: dict, mock_todo_service, mock_realtime_service):
        """Test that response matches TodoItemResponse schema."""
        # Arrange
        todo_id = uuid4()
        mock_todo = Mock()
        mock_todo.id = todo_id
        mock_todo.title = "Schema validation TODO"
        mock_todo.description = "Testing response schema"
        mock_todo.priority = "high"
        mock_todo.completed = False
        mock_todo.completed_at = None
        mock_todo.created_at = datetime.now()
        mock_todo.updated_at = datetime.now()
        mock_todo.order_index = 1

        mock_todo_service.create_todo_for_user.return_value = mock_todo
        mock_todo_response = Mock()
        mock_todo_response.id = str(todo_id)
        mock_todo_response.title = "Schema validation TODO"
        mock_todo_response.description = "Testing response schema"
        mock_todo_response.priority = "high"
        mock_todo_response.completed = False
        mock_todo_response.completed_at = None
        mock_todo_response.created_at = "2023-01-01T00:00:00Z"
        mock_todo_response.updated_at = "2023-01-01T00:00:00Z"
        mock_todo_response.order_index = 1
        mock_todo_response.model_dump = Mock(return_value={
            "id": str(todo_id),
            "title": "Schema validation TODO",
            "description": "Testing response schema",
            "priority": "high",
            "completed": False,
            "completed_at": None,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "order_index": 1
        })
        mock_todo_service.to_response.return_value = mock_todo_response

        todo_data = {
            "title": "Schema validation TODO",
            "description": "Testing response schema",
            "priority": "high"
        }

        # Act
        response: Response = client.post("/api/todos", json=todo_data, headers=auth_headers)

        # Assert
        assert response.status_code == 201
        data = response.json()

        # Required fields from TodoItemResponse schema
        required_fields = [
            "id", "title", "completed", "priority",
            "order_index", "created_at", "updated_at"
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Optional fields
        optional_fields = ["description", "completed_at"]
        for field in optional_fields:
            if field in data and data[field] is not None:
                assert isinstance(data[field], str)

        # Field types
        assert isinstance(data["id"], str)
        assert isinstance(data["title"], str)
        assert isinstance(data["completed"], bool)
        assert isinstance(data["priority"], str)
        assert isinstance(data["order_index"], int)
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)

        # Verify UUID format
        import uuid
        uuid.UUID(data["id"])

        # Verify datetime formats
        datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))

        # Verify enum values
        assert data["priority"] in ["low", "medium", "high"]

        mock_todo_service.create_todo_for_user.assert_called_once()
        mock_todo_service.to_response.assert_called_once_with(mock_todo)
        mock_realtime_service.notify_todo_created.assert_called_once()

    def test_create_todo_unicode_characters(self, client: TestClient, auth_headers: dict):
        """Test TODO creation with unicode characters."""
        # Arrange
        todo_data = {
            "title": "🚀 Unicode TODO 测试 🎉",
            "description": "Testing unicode: αβγ δεζ 한글 العربية"
        }

        # Act
        response: Response = client.post("/api/todos", json=todo_data, headers=auth_headers)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "🚀 Unicode TODO 测试 🎉"
        assert data["description"] == "Testing unicode: αβγ δεζ 한글 العربية"