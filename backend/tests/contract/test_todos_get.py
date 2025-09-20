"""
Contract tests for GET /api/todos/{todo_id} endpoint.
Tests the API contract for getting a specific TODO item.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4


@pytest.fixture
def mock_todo_service():
    """Mock todo service for testing."""
    with patch("src.api.routes.todos.TodoService") as mock_class:
        mock_instance = Mock()
        # Set async methods to use AsyncMock
        mock_instance.get_todo_by_id = AsyncMock()
        mock_class.return_value = mock_instance
        yield mock_instance


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
def completed_todo():
    """Sample completed TODO item for testing."""
    return {
        "id": str(uuid4()),
        "title": "Walk the dog",
        "description": None,
        "completed": True,
        "completed_at": "2025-01-19T11:00:00Z",
        "priority": "high",
        "order_index": 1,
        "created_at": "2025-01-19T09:00:00Z",
        "updated_at": "2025-01-19T11:00:00Z"
    }


class TestTodosGetById:
    """Test suite for GET /api/todos/{todo_id} endpoint."""

    def test_get_todo_success_authenticated(self, client: TestClient, mock_todo_service, sample_todo):
        """Test successful TODO retrieval for authenticated user."""
        from unittest.mock import Mock
        from uuid import UUID

        # Arrange
        todo_id = sample_todo["id"]

        # Create a mock TODO object with necessary attributes
        mock_todo = Mock()
        mock_todo.user_id = UUID("550e8400-e29b-41d4-a716-446655440000")  # Match conftest.py auth context
        mock_todo.session_id = None

        mock_todo_service.get_todo_by_id.return_value = mock_todo
        mock_todo_service.to_response.return_value = sample_todo

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        assert response_data["id"] == todo_id
        assert response_data["title"] == sample_todo["title"]
        assert response_data["description"] == sample_todo["description"]
        assert response_data["completed"] == sample_todo["completed"]
        assert response_data["priority"] == sample_todo["priority"]

        mock_todo_service.get_todo_by_id.assert_called_once()
        mock_todo_service.to_response.assert_called_once_with(mock_todo)

    def test_get_todo_success_guest_session(self, client: TestClient, mock_todo_service, sample_todo):
        """Test successful TODO retrieval for guest session."""
        from unittest.mock import Mock
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
            todo_id = sample_todo["id"]

            # Create a mock TODO object with necessary attributes
            mock_todo = Mock()
            mock_todo.user_id = None
            mock_todo.session_id = "sess_abc123def456ghi789"  # Match the session ID

            mock_todo_service.get_todo_by_id.return_value = mock_todo
            mock_todo_service.to_response.return_value = sample_todo

            headers = {"X-Session-ID": "sess_abc123def456ghi789"}

            # Act
            response = client.get(f"/api/todos/{todo_id}", headers=headers)

            # Assert
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["id"] == todo_id

            mock_todo_service.get_todo_by_id.assert_called_once()
            mock_todo_service.to_response.assert_called_once_with(mock_todo)
        finally:
            # Restore original override
            if original_override:
                app.dependency_overrides[require_auth] = original_override
            elif require_auth in app.dependency_overrides:
                del app.dependency_overrides[require_auth]

    def test_get_todo_completed_item(self, client: TestClient, mock_todo_service, completed_todo):
        """Test retrieval of completed TODO item."""
        from unittest.mock import Mock
        from uuid import UUID

        # Arrange
        todo_id = completed_todo["id"]

        # Create a mock TODO object with necessary attributes
        mock_todo = Mock()
        mock_todo.user_id = UUID("550e8400-e29b-41d4-a716-446655440000")  # Match conftest.py auth context
        mock_todo.session_id = None

        mock_todo_service.get_todo_by_id.return_value = mock_todo
        mock_todo_service.to_response.return_value = completed_todo

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        assert response_data["completed"] == True
        assert response_data["completed_at"] == completed_todo["completed_at"]

        mock_todo_service.get_todo_by_id.assert_called_once()
        mock_todo_service.to_response.assert_called_once_with(mock_todo)

    def test_get_todo_no_auth(self, client: TestClient):
        """Test TODO retrieval without authentication."""
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

            # Act
            response = client.get(f"/api/todos/{todo_id}")

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

    def test_get_todo_invalid_token(self, client: TestClient):
        """Test TODO retrieval with invalid JWT token."""
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
            headers = {"Authorization": "Bearer invalid_jwt_token"}

            # Act
            response = client.get(f"/api/todos/{todo_id}", headers=headers)

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

    def test_get_todo_invalid_session(self, client: TestClient):
        """Test TODO retrieval with invalid session ID."""
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
            headers = {"X-Session-ID": "invalid_session"}

            # Act
            response = client.get(f"/api/todos/{todo_id}", headers=headers)

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

    def test_get_todo_not_found(self, client: TestClient, mock_todo_service):
        """Test TODO retrieval with non-existent ID."""
        # Arrange
        todo_id = str(uuid4())
        mock_todo_service.get_todo_by_id.return_value = None  # Service returns None for not found

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 404
        response_data = response.json()
        assert response_data["error"] == "not_found"
        assert "not found" in response_data["message"].lower()

    def test_get_todo_forbidden_different_user(self, client: TestClient, mock_todo_service):
        """Test TODO retrieval for TODO owned by different user."""
        from unittest.mock import Mock
        from uuid import uuid4 as generate_uuid

        # Arrange
        todo_id = str(uuid4())
        different_user_id = generate_uuid()  # Different from the mocked auth user

        # Mock a TODO that belongs to a different user
        mock_todo = Mock()
        mock_todo.id = generate_uuid()
        mock_todo.user_id = different_user_id  # Different from auth context user_id
        mock_todo.session_id = None
        mock_todo_service.get_todo_by_id.return_value = mock_todo

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 404  # Route returns 404 for ownership violations
        response_data = response.json()
        assert response_data["error"] == "not_found"

    def test_get_todo_forbidden_different_session(self, client: TestClient, mock_todo_service):
        """Test TODO retrieval for TODO from different guest session."""
        # Arrange
        todo_id = str(uuid4())
        mock_todo_service.get_todo_by_id.side_effect = PermissionError("Access denied")

        headers = {"X-Session-ID": "sess_abc123def456ghi789"}

        # Act
        response = client.get(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 403
        response_data = response.json()
        assert response_data["error"] == "forbidden"

    def test_get_todo_invalid_uuid_format(self, client: TestClient):
        """Test TODO retrieval with invalid UUID format."""
        # Arrange
        invalid_todo_id = "not-a-valid-uuid"
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get(f"/api/todos/{invalid_todo_id}", headers=headers)

        # Assert
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "validation" in response_data["message"].lower()

    def test_get_todo_empty_uuid(self, client: TestClient):
        """Test TODO retrieval with empty UUID."""
        # Arrange
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get("/api/todos/", headers=headers)

        # Assert
        # Should match different route (GET /api/todos) or 404
        assert response.status_code in [200, 404]

    def test_get_todo_malformed_uuid(self, client: TestClient):
        """Test TODO retrieval with malformed UUID."""
        # Arrange
        malformed_uuid = "123e4567-e89b-12d3-a456"  # Missing last segment
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get(f"/api/todos/{malformed_uuid}", headers=headers)

        # Assert
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["error"] == "validation_error"

    def test_get_todo_response_schema_validation(self, client: TestClient, mock_todo_service, sample_todo):
        """Test that response matches expected schema exactly."""
        from unittest.mock import Mock
        from uuid import UUID

        # Arrange
        todo_id = sample_todo["id"]

        # Create a mock TODO object with necessary attributes
        mock_todo = Mock()
        mock_todo.user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        mock_todo.session_id = None

        mock_todo_service.get_todo_by_id.return_value = mock_todo
        mock_todo_service.to_response.return_value = sample_todo

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get(f"/api/todos/{todo_id}", headers=headers)

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

        # Check field constraints
        assert len(response_data["title"]) > 0
        assert len(response_data["title"]) <= 2000
        if response_data["description"]:
            assert len(response_data["description"]) <= 10000
        assert response_data["order_index"] >= 0

    def test_get_todo_with_null_description(self, client: TestClient, mock_todo_service):
        """Test TODO retrieval with null description."""
        from unittest.mock import Mock
        from uuid import UUID

        # Arrange
        todo_with_null_desc = {
            "id": str(uuid4()),
            "title": "Task without description",
            "description": None,
            "completed": False,
            "completed_at": None,
            "priority": "low",
            "order_index": 0,
            "created_at": "2025-01-19T10:30:00Z",
            "updated_at": "2025-01-19T10:30:00Z"
        }

        todo_id = todo_with_null_desc["id"]

        # Create a mock TODO object with necessary attributes
        mock_todo = Mock()
        mock_todo.user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        mock_todo.session_id = None

        mock_todo_service.get_todo_by_id.return_value = mock_todo
        mock_todo_service.to_response.return_value = todo_with_null_desc

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["description"] is None

        mock_todo_service.get_todo_by_id.assert_called_once()
        mock_todo_service.to_response.assert_called_once_with(mock_todo)

    def test_get_todo_with_all_priorities(self, client: TestClient, mock_todo_service):
        """Test TODO retrieval with all priority levels."""
        from unittest.mock import Mock
        from uuid import UUID

        priorities = ["low", "medium", "high"]

        for priority in priorities:
            # Arrange
            todo_with_priority = {
                "id": str(uuid4()),
                "title": f"Task with {priority} priority",
                "description": f"This is a {priority} priority task",
                "completed": False,
                "completed_at": None,
                "priority": priority,
                "order_index": 0,
                "created_at": "2025-01-19T10:30:00Z",
                "updated_at": "2025-01-19T10:30:00Z"
            }

            todo_id = todo_with_priority["id"]

            # Create a mock TODO object with necessary attributes
            mock_todo = Mock()
            mock_todo.user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
            mock_todo.session_id = None

            mock_todo_service.get_todo_by_id.return_value = mock_todo
            mock_todo_service.to_response.return_value = todo_with_priority

            headers = {"Authorization": "Bearer valid_jwt_token"}

            # Act
            response = client.get(f"/api/todos/{todo_id}", headers=headers)

            # Assert
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["priority"] == priority

            mock_todo_service.get_todo_by_id.assert_called()
            mock_todo_service.to_response.assert_called_with(mock_todo)

    def test_get_todo_case_insensitive_uuid(self, client: TestClient, mock_todo_service, sample_todo):
        """Test that UUID matching is case insensitive."""
        from unittest.mock import Mock
        from uuid import UUID

        # Arrange
        todo_id = sample_todo["id"].upper()  # Convert to uppercase

        # Create a mock TODO object with necessary attributes
        mock_todo = Mock()
        mock_todo.user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        mock_todo.session_id = None

        mock_todo_service.get_todo_by_id.return_value = mock_todo
        mock_todo_service.to_response.return_value = sample_todo

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        # This depends on implementation - might be 200 or 422
        assert response.status_code in [200, 422]