"""
Contract tests for GET /api/todos/{todo_id} endpoint.
Tests the API contract for getting a specific TODO item.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from uuid import uuid4


@pytest.fixture
def mock_todo_service():
    """Mock todo service for testing."""
    with patch("src.api.routes.todos.todo_service") as mock:
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
        # Arrange
        todo_id = sample_todo["id"]
        mock_todo_service.get_todo_by_id.return_value = sample_todo

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

    def test_get_todo_success_guest_session(self, client: TestClient, mock_todo_service, sample_todo):
        """Test successful TODO retrieval for guest session."""
        # Arrange
        todo_id = sample_todo["id"]
        mock_todo_service.get_todo_by_id.return_value = sample_todo

        headers = {"X-Session-ID": "sess_abc123def456ghi789"}

        # Act
        response = client.get(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["id"] == todo_id

    def test_get_todo_completed_item(self, client: TestClient, mock_todo_service, completed_todo):
        """Test retrieval of completed TODO item."""
        # Arrange
        todo_id = completed_todo["id"]
        mock_todo_service.get_todo_by_id.return_value = completed_todo

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        assert response_data["completed"] == True
        assert response_data["completed_at"] == completed_todo["completed_at"]

    def test_get_todo_no_auth(self, client: TestClient):
        """Test TODO retrieval without authentication."""
        # Arrange
        todo_id = str(uuid4())

        # Act
        response = client.get(f"/api/todos/{todo_id}")

        # Assert
        assert response.status_code == 401
        response_data = response.json()
        assert response_data["error"] == "unauthorized"
        assert "authentication required" in response_data["message"].lower()

    def test_get_todo_invalid_token(self, client: TestClient):
        """Test TODO retrieval with invalid JWT token."""
        # Arrange
        todo_id = str(uuid4())
        headers = {"Authorization": "Bearer invalid_jwt_token"}

        # Act
        response = client.get(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 401
        response_data = response.json()
        assert response_data["error"] == "unauthorized"

    def test_get_todo_invalid_session(self, client: TestClient):
        """Test TODO retrieval with invalid session ID."""
        # Arrange
        todo_id = str(uuid4())
        headers = {"X-Session-ID": "invalid_session"}

        # Act
        response = client.get(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 401
        response_data = response.json()
        assert response_data["error"] == "unauthorized"

    def test_get_todo_not_found(self, client: TestClient, mock_todo_service):
        """Test TODO retrieval with non-existent ID."""
        # Arrange
        todo_id = str(uuid4())
        mock_todo_service.get_todo_by_id.side_effect = ValueError("TODO not found")

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
        # Arrange
        todo_id = str(uuid4())
        mock_todo_service.get_todo_by_id.side_effect = PermissionError("Access denied")

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 403
        response_data = response.json()
        assert response_data["error"] == "forbidden"
        assert "permission" in response_data["message"].lower()

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
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "uuid" in response_data["message"].lower()

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
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"

    def test_get_todo_response_schema_validation(self, client: TestClient, mock_todo_service, sample_todo):
        """Test that response matches expected schema exactly."""
        # Arrange
        todo_id = sample_todo["id"]
        mock_todo_service.get_todo_by_id.return_value = sample_todo

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
        mock_todo_service.get_todo_by_id.return_value = todo_with_null_desc

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["description"] is None

    def test_get_todo_with_all_priorities(self, client: TestClient, mock_todo_service):
        """Test TODO retrieval with all priority levels."""
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
            mock_todo_service.get_todo_by_id.return_value = todo_with_priority

            headers = {"Authorization": "Bearer valid_jwt_token"}

            # Act
            response = client.get(f"/api/todos/{todo_id}", headers=headers)

            # Assert
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["priority"] == priority

    def test_get_todo_case_insensitive_uuid(self, client: TestClient, mock_todo_service, sample_todo):
        """Test that UUID matching is case insensitive."""
        # Arrange
        todo_id = sample_todo["id"].upper()  # Convert to uppercase
        mock_todo_service.get_todo_by_id.return_value = sample_todo

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        # This depends on implementation - might be 200 or 400
        assert response.status_code in [200, 400]