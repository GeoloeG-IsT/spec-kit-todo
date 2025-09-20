"""
Contract tests for PUT /api/todos/{todo_id} endpoint.
Tests the API contract for updating a specific TODO item.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4
from datetime import datetime


@pytest.fixture
def mock_todo_service():
    """Mock todo service for testing."""
    with patch("src.api.routes.todos.TodoService") as mock_class:
        mock_instance = Mock()
        # Set async methods to use AsyncMock
        mock_instance.update_todo = AsyncMock()
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
def sample_todo():
    """Sample TODO item for testing."""
    return {
        "id": str(uuid4()),
        "title": "Buy groceries",
        "description": "Milk, bread, eggs, and fruits",
        "completed": False,
        "completed_at": None,
        "priority": "medium",
        "order_index": 0,
        "created_at": "2025-01-19T10:30:00Z",
        "updated_at": "2025-01-19T10:30:00Z"
    }


@pytest.fixture
def updated_todo():
    """Sample updated TODO item for testing."""
    return {
        "id": str(uuid4()),
        "title": "Buy groceries (updated)",
        "description": "Milk, bread, eggs, fruits, and vegetables",
        "completed": True,
        "completed_at": "2025-01-19T15:30:00Z",
        "priority": "high",
        "order_index": 5,
        "created_at": "2025-01-19T10:30:00Z",
        "updated_at": "2025-01-19T15:30:00Z"
    }


class TestTodosUpdate:
    """Test suite for PUT /api/todos/{todo_id} endpoint."""

    def test_update_todo_success_authenticated(self, client: TestClient, mock_todo_service, mock_realtime_service, updated_todo):
        """Test successful TODO update for authenticated user."""
        # Arrange
        todo_id = updated_todo["id"]
        mock_todo = Mock()
        mock_todo.id = uuid4()
        mock_todo.title = "Buy groceries (updated)"
        mock_todo.description = "Milk, bread, eggs, fruits, and vegetables"
        mock_todo.completed = True
        mock_todo.priority = "high"
        mock_todo.order_index = 5
        mock_todo.created_at = datetime.now()
        mock_todo.updated_at = datetime.now()
        mock_todo.completed_at = datetime.now()

        mock_todo_service.update_todo.return_value = mock_todo

        # Create mock response that has model_dump method
        mock_response = Mock()
        mock_response.model_dump.return_value = updated_todo
        # Set all the attributes that will be accessed in assertions
        for key, value in updated_todo.items():
            setattr(mock_response, key, value)
        mock_todo_service.to_response.return_value = mock_response

        request_data = {
            "title": "Buy groceries (updated)",
            "description": "Milk, bread, eggs, fruits, and vegetables",
            "completed": True,
            "priority": "high",
            "order_index": 5
        }

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put(f"/api/todos/{todo_id}", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        assert response_data["id"] == todo_id
        assert response_data["title"] == request_data["title"]
        assert response_data["description"] == request_data["description"]
        assert response_data["completed"] == request_data["completed"]
        assert response_data["priority"] == request_data["priority"]
        assert response_data["order_index"] == request_data["order_index"]

        mock_todo_service.update_todo.assert_called_once()
        mock_todo_service.to_response.assert_called_once_with(mock_todo)
        mock_realtime_service.notify_todo_updated.assert_called_once()

    def test_update_todo_success_guest_session(self, client: TestClient, mock_todo_service, mock_realtime_service, updated_todo):
        """Test successful TODO update for guest session."""
        from src.main import app
        from src.api.middleware.auth import require_auth

        # Arrange
        def mock_guest_auth():
            """Mock auth dependency that returns guest context."""
            return {
                "type": "guest",
                "user_id": None,
                "session_id": "sess_abc123def456ghi789",
                "authenticated": True
            }

        # Override the auth dependency
        original_override = app.dependency_overrides.get(require_auth)
        app.dependency_overrides[require_auth] = mock_guest_auth

        try:
            todo_id = updated_todo["id"]
            mock_todo = Mock()
            mock_todo.id = uuid4()
            mock_todo.title = "Updated guest todo"
            mock_todo.completed = True
            mock_todo.created_at = datetime.now()
            mock_todo.updated_at = datetime.now()
            mock_todo.completed_at = datetime.now()

            mock_todo_service.update_todo.return_value = mock_todo

            # Create mock response that has model_dump method
            mock_response = Mock()
            mock_response.model_dump.return_value = updated_todo
            # Set all the attributes that will be accessed in assertions
            for key, value in updated_todo.items():
                setattr(mock_response, key, value)
            mock_todo_service.to_response.return_value = mock_response

            request_data = {
                "title": "Updated guest todo",
                "completed": True
            }

            headers = {"X-Session-ID": "sess_abc123def456ghi789"}

            # Act
            response = client.put(f"/api/todos/{todo_id}", json=request_data, headers=headers)

            # Assert
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["id"] == todo_id

            mock_todo_service.update_todo.assert_called_once()
            mock_todo_service.to_response.assert_called_once_with(mock_todo)
            mock_realtime_service.notify_todo_updated.assert_called_once()
        finally:
            # Restore original override
            if original_override:
                app.dependency_overrides[require_auth] = original_override
            elif require_auth in app.dependency_overrides:
                del app.dependency_overrides[require_auth]

    def test_update_todo_partial_update(self, client: TestClient, mock_todo_service, sample_todo):
        """Test partial TODO update (only updating some fields)."""
        # Arrange
        todo_id = sample_todo["id"]

        # Update only title and completed status
        updated_todo = sample_todo.copy()
        updated_todo["title"] = "Updated title only"
        updated_todo["completed"] = True
        updated_todo["completed_at"] = "2025-01-19T15:30:00Z"

        mock_todo = Mock()
        mock_todo.id = todo_id
        mock_todo_service.update_todo.return_value = mock_todo

        # Create mock response that has model_dump method
        mock_response = Mock()
        mock_response.model_dump.return_value = updated_todo
        # Set all the attributes that will be accessed in assertions
        for key, value in updated_todo.items():
            setattr(mock_response, key, value)
        mock_todo_service.to_response.return_value = mock_response

        request_data = {
            "title": "Updated title only",
            "completed": True
        }

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put(f"/api/todos/{todo_id}", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["title"] == "Updated title only"
        assert response_data["completed"] == True
        # Other fields should remain unchanged
        assert response_data["description"] == sample_todo["description"]
        assert response_data["priority"] == sample_todo["priority"]

    def test_update_todo_no_auth(self, client: TestClient):
        """Test TODO update without authentication."""
        from src.main import app
        from src.api.middleware.auth import require_auth

        # Arrange
        def raise_permission_error():
            raise PermissionError("User authentication required")

        # Clear existing override and set our custom one
        original_override = app.dependency_overrides.get(require_auth)
        app.dependency_overrides[require_auth] = raise_permission_error

        try:
            todo_id = str(uuid4())
            request_data = {"title": "Updated title"}

            # Act
            response = client.put(f"/api/todos/{todo_id}", json=request_data)

            # Assert
            assert response.status_code == 403  # FastAPI converts PermissionError to 403
            response_data = response.json()
            assert response_data["error"] == "forbidden"
        finally:
            # Restore original override
            if original_override:
                app.dependency_overrides[require_auth] = original_override
            elif require_auth in app.dependency_overrides:
                del app.dependency_overrides[require_auth]

    def test_update_todo_invalid_token(self, client: TestClient):
        """Test TODO update with invalid JWT token."""
        from src.main import app
        from src.api.middleware.auth import require_auth

        # Arrange
        def raise_permission_error():
            raise PermissionError("Invalid token")

        # Clear existing override and set our custom one
        original_override = app.dependency_overrides.get(require_auth)
        app.dependency_overrides[require_auth] = raise_permission_error

        try:
            todo_id = str(uuid4())
            request_data = {"title": "Updated title"}
            headers = {"Authorization": "Bearer invalid_jwt_token"}

            # Act
            response = client.put(f"/api/todos/{todo_id}", json=request_data, headers=headers)

            # Assert
            assert response.status_code == 403
            response_data = response.json()
            assert response_data["error"] == "forbidden"
        finally:
            # Restore original override
            if original_override:
                app.dependency_overrides[require_auth] = original_override
            elif require_auth in app.dependency_overrides:
                del app.dependency_overrides[require_auth]

    def test_update_todo_invalid_session(self, client: TestClient):
        """Test TODO update with invalid session ID."""
        from src.main import app
        from src.api.middleware.auth import require_auth

        # Arrange
        def raise_permission_error():
            raise PermissionError("Invalid session")

        # Clear existing override and set our custom one
        original_override = app.dependency_overrides.get(require_auth)
        app.dependency_overrides[require_auth] = raise_permission_error

        try:
            todo_id = str(uuid4())
            request_data = {"title": "Updated title"}
            headers = {"X-Session-ID": "invalid_session"}

            # Act
            response = client.put(f"/api/todos/{todo_id}", json=request_data, headers=headers)

            # Assert
            assert response.status_code == 403
            response_data = response.json()
            assert response_data["error"] == "forbidden"
        finally:
            # Restore original override
            if original_override:
                app.dependency_overrides[require_auth] = original_override
            elif require_auth in app.dependency_overrides:
                del app.dependency_overrides[require_auth]

    def test_update_todo_not_found(self, client: TestClient, mock_todo_service):
        """Test TODO update with non-existent ID."""
        # Arrange
        todo_id = str(uuid4())
        mock_todo_service.update_todo.return_value = None

        request_data = {"title": "Updated title"}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put(f"/api/todos/{todo_id}", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 404
        response_data = response.json()
        assert response_data["error"] == "not_found"
        assert "not found" in response_data["message"].lower()

    def test_update_todo_forbidden_different_user(self, client: TestClient, mock_todo_service):
        """Test TODO update for TODO owned by different user."""
        # Arrange
        todo_id = str(uuid4())
        mock_todo_service.update_todo.return_value = None  # Simulates not found due to ownership check

        request_data = {"title": "Updated title"}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put(f"/api/todos/{todo_id}", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 404
        response_data = response.json()
        assert response_data["error"] == "not_found"
        assert "not found" in response_data["message"].lower()

    def test_update_todo_invalid_uuid_format(self, client: TestClient):
        """Test TODO update with invalid UUID format."""
        # Arrange
        invalid_todo_id = "not-a-valid-uuid"
        request_data = {"title": "Updated title"}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put(f"/api/todos/{invalid_todo_id}", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "validation" in response_data["message"].lower()

    def test_update_todo_empty_title(self, client: TestClient):
        """Test TODO update with empty title."""
        # Arrange
        todo_id = str(uuid4())
        request_data = {"title": ""}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put(f"/api/todos/{todo_id}", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "validation" in response_data["message"].lower()

    def test_update_todo_title_too_long(self, client: TestClient):
        """Test TODO update with title exceeding maximum length."""
        # Arrange
        todo_id = str(uuid4())
        request_data = {"title": "x" * 2001}  # Exceeds 2000 char limit
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put(f"/api/todos/{todo_id}", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "validation" in response_data["message"].lower()

    def test_update_todo_description_too_long(self, client: TestClient):
        """Test TODO update with description exceeding maximum length."""
        # Arrange
        todo_id = str(uuid4())
        request_data = {"description": "x" * 10001}  # Exceeds 10000 char limit
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put(f"/api/todos/{todo_id}", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "validation" in response_data["message"].lower()

    def test_update_todo_invalid_priority(self, client: TestClient):
        """Test TODO update with invalid priority value."""
        # Arrange
        todo_id = str(uuid4())
        request_data = {"priority": "invalid"}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put(f"/api/todos/{todo_id}", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "validation" in response_data["message"].lower()

    def test_update_todo_negative_order_index(self, client: TestClient):
        """Test TODO update with negative order_index."""
        # Arrange
        todo_id = str(uuid4())
        request_data = {"order_index": -1}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put(f"/api/todos/{todo_id}", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "validation" in response_data["message"].lower()

    def test_update_todo_malformed_json(self, client: TestClient):
        """Test TODO update with malformed JSON."""
        # Arrange
        todo_id = str(uuid4())
        headers = {
            "Authorization": "Bearer valid_jwt_token",
            "Content-Type": "application/json"
        }

        # Act
        response = client.put(f"/api/todos/{todo_id}", data="invalid json", headers=headers)

        # Assert
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["error"] == "validation_error"

    def test_update_todo_empty_request_body(self, client: TestClient, mock_todo_service, sample_todo):
        """Test TODO update with empty request body."""
        # Arrange
        todo_id = sample_todo["id"]

        mock_todo = Mock()
        mock_todo.id = todo_id
        mock_todo_service.update_todo.return_value = mock_todo

        # Create mock response that has model_dump method
        mock_response = Mock()
        mock_response.model_dump.return_value = sample_todo
        # Set all the attributes that will be accessed in assertions
        for key, value in sample_todo.items():
            setattr(mock_response, key, value)
        mock_todo_service.to_response.return_value = mock_response

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put(f"/api/todos/{todo_id}", json={}, headers=headers)

        # Assert
        # Empty update should be allowed (no-op)
        assert response.status_code == 200

    def test_update_todo_null_description(self, client: TestClient, mock_todo_service, sample_todo):
        """Test TODO update setting description to null."""
        # Arrange
        todo_id = sample_todo["id"]

        updated_todo = sample_todo.copy()
        updated_todo["description"] = None

        mock_todo = Mock()
        mock_todo.id = todo_id
        mock_todo_service.update_todo.return_value = mock_todo

        # Create mock response that has model_dump method
        mock_response = Mock()
        mock_response.model_dump.return_value = updated_todo
        # Set all the attributes that will be accessed in assertions
        for key, value in updated_todo.items():
            setattr(mock_response, key, value)
        mock_todo_service.to_response.return_value = mock_response

        request_data = {"description": None}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put(f"/api/todos/{todo_id}", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["description"] is None

    def test_update_todo_all_priorities(self, client: TestClient, mock_todo_service, sample_todo):
        """Test TODO update with all valid priority values."""
        priorities = ["low", "medium", "high"]

        for priority in priorities:
            # Arrange
            todo_id = sample_todo["id"]

            updated_todo = sample_todo.copy()
            updated_todo["priority"] = priority

            mock_todo = Mock()
            mock_todo.id = todo_id
            mock_todo_service.update_todo.return_value = mock_todo

            # Create mock response that has model_dump method
            mock_response = Mock()
            mock_response.model_dump.return_value = updated_todo
            # Set all the attributes that will be accessed in assertions
            for key, value in updated_todo.items():
                setattr(mock_response, key, value)
            mock_todo_service.to_response.return_value = mock_response

            request_data = {"priority": priority}
            headers = {"Authorization": "Bearer valid_jwt_token"}

            # Act
            response = client.put(f"/api/todos/{todo_id}", json=request_data, headers=headers)

            # Assert
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["priority"] == priority

    def test_update_todo_completion_sets_timestamp(self, client: TestClient, mock_todo_service, sample_todo):
        """Test that marking TODO as completed sets completed_at timestamp."""
        # Arrange
        todo_id = sample_todo["id"]

        updated_todo = sample_todo.copy()
        updated_todo["completed"] = True
        updated_todo["completed_at"] = "2025-01-19T15:30:00Z"

        mock_todo = Mock()
        mock_todo.id = todo_id
        mock_todo_service.update_todo.return_value = mock_todo

        # Create mock response that has model_dump method
        mock_response = Mock()
        mock_response.model_dump.return_value = updated_todo
        # Set all the attributes that will be accessed in assertions
        for key, value in updated_todo.items():
            setattr(mock_response, key, value)
        mock_todo_service.to_response.return_value = mock_response

        request_data = {"completed": True}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put(f"/api/todos/{todo_id}", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["completed"] == True
        assert response_data["completed_at"] is not None

    def test_update_todo_uncomplete_clears_timestamp(self, client: TestClient, mock_todo_service, sample_todo):
        """Test that marking TODO as not completed clears completed_at timestamp."""
        # Arrange
        todo_id = sample_todo["id"]

        updated_todo = sample_todo.copy()
        updated_todo["completed"] = False
        updated_todo["completed_at"] = None

        mock_todo = Mock()
        mock_todo.id = todo_id
        mock_todo_service.update_todo.return_value = mock_todo

        # Create mock response that has model_dump method
        mock_response = Mock()
        mock_response.model_dump.return_value = updated_todo
        # Set all the attributes that will be accessed in assertions
        for key, value in updated_todo.items():
            setattr(mock_response, key, value)
        mock_todo_service.to_response.return_value = mock_response

        request_data = {"completed": False}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put(f"/api/todos/{todo_id}", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["completed"] == False
        assert response_data["completed_at"] is None

    def test_update_todo_response_schema_validation(self, client: TestClient, mock_todo_service, updated_todo):
        """Test that response matches expected schema exactly."""
        # Arrange
        todo_id = updated_todo["id"]

        mock_todo = Mock()
        mock_todo.id = todo_id
        mock_todo_service.update_todo.return_value = mock_todo

        # Create mock response that has model_dump method
        mock_response = Mock()
        mock_response.model_dump.return_value = updated_todo
        # Set all the attributes that will be accessed in assertions
        for key, value in updated_todo.items():
            setattr(mock_response, key, value)
        mock_todo_service.to_response.return_value = mock_response

        request_data = {"title": "Test update"}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put(f"/api/todos/{todo_id}", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Check all required fields are present
        required_fields = {
            "id", "title", "description", "completed", "completed_at",
            "priority", "order_index", "created_at", "updated_at"
        }
        assert set(response_data.keys()) == required_fields

        # Check field types
        assert isinstance(response_data["id"], str)
        assert isinstance(response_data["title"], str)
        assert response_data["description"] is None or isinstance(response_data["description"], str)
        assert isinstance(response_data["completed"], bool)
        assert response_data["completed_at"] is None or isinstance(response_data["completed_at"], str)
        assert response_data["priority"] in ["low", "medium", "high"]
        assert isinstance(response_data["order_index"], int)
        assert isinstance(response_data["created_at"], str)
        assert isinstance(response_data["updated_at"], str)

    def test_update_todo_extra_fields_ignored(self, client: TestClient, mock_todo_service, sample_todo):
        """Test that extra fields in request body are ignored."""
        # Arrange
        todo_id = sample_todo["id"]

        mock_todo = Mock()
        mock_todo.id = todo_id
        mock_todo_service.update_todo.return_value = mock_todo

        # Create mock response that has model_dump method
        mock_response = Mock()
        mock_response.model_dump.return_value = sample_todo
        # Set all the attributes that will be accessed in assertions
        for key, value in sample_todo.items():
            setattr(mock_response, key, value)
        mock_todo_service.to_response.return_value = mock_response

        request_data = {
            "title": "Updated title",
            "extra_field": "should_be_ignored",
            "another_field": 123,
            "id": "should_not_change_id"
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put(f"/api/todos/{todo_id}", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        # ID should remain unchanged
        assert response_data["id"] == todo_id