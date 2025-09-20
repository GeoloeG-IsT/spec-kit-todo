"""
Contract tests for GET /api/todos endpoint.
Tests the API contract for listing TODO items.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from uuid import uuid4
from datetime import datetime


@pytest.fixture
def mock_todo_service():
    """Mock todo service for testing."""
    with patch("src.api.routes.todos.todo_service") as mock:
        yield mock


@pytest.fixture
def sample_todos():
    """Sample TODO items for testing."""
    return [
        {
            "id": str(uuid4()),
            "title": "Buy groceries",
            "description": "Milk, bread, eggs",
            "completed": False,
            "completed_at": None,
            "priority": "medium",
            "order_index": 0,
            "created_at": "2025-01-19T10:30:00Z",
            "updated_at": "2025-01-19T10:30:00Z"
        },
        {
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
    ]


class TestTodosGet:
    """Test suite for GET /api/todos endpoint."""

    def test_get_todos_success_authenticated(self, client: TestClient, mock_todo_service, sample_todos):
        """Test successful TODO retrieval for authenticated user."""
        # Arrange
        mock_todo_service.get_user_todos.return_value = {
            "items": sample_todos,
            "total": 2,
            "limit": 50,
            "offset": 0
        }

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get("/api/todos", headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        assert "items" in response_data
        assert "total" in response_data
        assert "limit" in response_data
        assert "offset" in response_data

        assert len(response_data["items"]) == 2
        assert response_data["total"] == 2
        assert response_data["limit"] == 50
        assert response_data["offset"] == 0

        # Check first TODO item structure
        todo = response_data["items"][0]
        assert "id" in todo
        assert "title" in todo
        assert "description" in todo
        assert "completed" in todo
        assert "completed_at" in todo
        assert "priority" in todo
        assert "order_index" in todo
        assert "created_at" in todo
        assert "updated_at" in todo

    def test_get_todos_success_guest_session(self, client: TestClient, mock_todo_service, sample_todos):
        """Test successful TODO retrieval for guest session."""
        # Arrange
        mock_todo_service.get_session_todos.return_value = {
            "items": sample_todos[:1],  # Guest has only one TODO
            "total": 1,
            "limit": 50,
            "offset": 0
        }

        headers = {"X-Session-ID": "sess_abc123def456ghi789"}

        # Act
        response = client.get("/api/todos", headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data["items"]) == 1
        assert response_data["total"] == 1

    def test_get_todos_no_auth(self, client: TestClient):
        """Test TODO retrieval without authentication."""
        # Act
        response = client.get("/api/todos")

        # Assert
        assert response.status_code == 401
        response_data = response.json()
        assert response_data["error"] == "unauthorized"
        assert "authentication required" in response_data["message"].lower()

    def test_get_todos_invalid_token(self, client: TestClient):
        """Test TODO retrieval with invalid JWT token."""
        # Arrange
        headers = {"Authorization": "Bearer invalid_jwt_token"}

        # Act
        response = client.get("/api/todos", headers=headers)

        # Assert
        assert response.status_code == 401
        response_data = response.json()
        assert response_data["error"] == "unauthorized"

    def test_get_todos_invalid_session(self, client: TestClient):
        """Test TODO retrieval with invalid session ID."""
        # Arrange
        headers = {"X-Session-ID": "invalid_session"}

        # Act
        response = client.get("/api/todos", headers=headers)

        # Assert
        assert response.status_code == 401
        response_data = response.json()
        assert response_data["error"] == "unauthorized"

    def test_get_todos_filter_completed_true(self, client: TestClient, mock_todo_service):
        """Test TODO retrieval filtered by completed=true."""
        # Arrange
        completed_todos = [
            {
                "id": str(uuid4()),
                "title": "Completed task",
                "description": None,
                "completed": True,
                "completed_at": "2025-01-19T11:00:00Z",
                "priority": "low",
                "order_index": 0,
                "created_at": "2025-01-19T09:00:00Z",
                "updated_at": "2025-01-19T11:00:00Z"
            }
        ]

        mock_todo_service.get_user_todos.return_value = {
            "items": completed_todos,
            "total": 1,
            "limit": 50,
            "offset": 0
        }

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get("/api/todos?completed=true", headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data["items"]) == 1
        assert response_data["items"][0]["completed"] == True

    def test_get_todos_filter_completed_false(self, client: TestClient, mock_todo_service):
        """Test TODO retrieval filtered by completed=false."""
        # Arrange
        pending_todos = [
            {
                "id": str(uuid4()),
                "title": "Pending task",
                "description": None,
                "completed": False,
                "completed_at": None,
                "priority": "high",
                "order_index": 0,
                "created_at": "2025-01-19T09:00:00Z",
                "updated_at": "2025-01-19T09:00:00Z"
            }
        ]

        mock_todo_service.get_user_todos.return_value = {
            "items": pending_todos,
            "total": 1,
            "limit": 50,
            "offset": 0
        }

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get("/api/todos?completed=false", headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data["items"]) == 1
        assert response_data["items"][0]["completed"] == False

    def test_get_todos_filter_priority(self, client: TestClient, mock_todo_service):
        """Test TODO retrieval filtered by priority."""
        # Arrange
        high_priority_todos = [
            {
                "id": str(uuid4()),
                "title": "High priority task",
                "description": None,
                "completed": False,
                "completed_at": None,
                "priority": "high",
                "order_index": 0,
                "created_at": "2025-01-19T09:00:00Z",
                "updated_at": "2025-01-19T09:00:00Z"
            }
        ]

        mock_todo_service.get_user_todos.return_value = {
            "items": high_priority_todos,
            "total": 1,
            "limit": 50,
            "offset": 0
        }

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get("/api/todos?priority=high", headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data["items"]) == 1
        assert response_data["items"][0]["priority"] == "high"

    def test_get_todos_invalid_priority(self, client: TestClient):
        """Test TODO retrieval with invalid priority filter."""
        # Arrange
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get("/api/todos?priority=invalid", headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "priority" in response_data["message"].lower()

    def test_get_todos_order_by_created_at(self, client: TestClient, mock_todo_service, sample_todos):
        """Test TODO retrieval ordered by created_at."""
        # Arrange
        mock_todo_service.get_user_todos.return_value = {
            "items": sample_todos,
            "total": 2,
            "limit": 50,
            "offset": 0
        }

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get("/api/todos?order_by=created_at&order_direction=desc", headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data["items"]) == 2

    def test_get_todos_invalid_order_by(self, client: TestClient):
        """Test TODO retrieval with invalid order_by parameter."""
        # Arrange
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get("/api/todos?order_by=invalid_field", headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "order_by" in response_data["message"].lower()

    def test_get_todos_pagination_limit(self, client: TestClient, mock_todo_service, sample_todos):
        """Test TODO retrieval with limit parameter."""
        # Arrange
        mock_todo_service.get_user_todos.return_value = {
            "items": sample_todos[:1],
            "total": 2,
            "limit": 1,
            "offset": 0
        }

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get("/api/todos?limit=1", headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data["items"]) == 1
        assert response_data["limit"] == 1
        assert response_data["total"] == 2

    def test_get_todos_pagination_offset(self, client: TestClient, mock_todo_service, sample_todos):
        """Test TODO retrieval with offset parameter."""
        # Arrange
        mock_todo_service.get_user_todos.return_value = {
            "items": sample_todos[1:],
            "total": 2,
            "limit": 50,
            "offset": 1
        }

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get("/api/todos?offset=1", headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data["items"]) == 1
        assert response_data["offset"] == 1
        assert response_data["total"] == 2

    def test_get_todos_invalid_limit_too_high(self, client: TestClient):
        """Test TODO retrieval with limit exceeding maximum."""
        # Arrange
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get("/api/todos?limit=101", headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "limit" in response_data["message"].lower()

    def test_get_todos_invalid_limit_zero(self, client: TestClient):
        """Test TODO retrieval with limit of zero."""
        # Arrange
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get("/api/todos?limit=0", headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "limit" in response_data["message"].lower()

    def test_get_todos_invalid_offset_negative(self, client: TestClient):
        """Test TODO retrieval with negative offset."""
        # Arrange
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get("/api/todos?offset=-1", headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "offset" in response_data["message"].lower()

    def test_get_todos_empty_list(self, client: TestClient, mock_todo_service):
        """Test TODO retrieval when user has no TODOs."""
        # Arrange
        mock_todo_service.get_user_todos.return_value = {
            "items": [],
            "total": 0,
            "limit": 50,
            "offset": 0
        }

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get("/api/todos", headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["items"] == []
        assert response_data["total"] == 0

    def test_get_todos_response_schema_validation(self, client: TestClient, mock_todo_service, sample_todos):
        """Test that response matches expected schema exactly."""
        # Arrange
        mock_todo_service.get_user_todos.return_value = {
            "items": sample_todos,
            "total": 2,
            "limit": 50,
            "offset": 0
        }

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.get("/api/todos", headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Check root object structure
        required_fields = {"items", "total", "limit", "offset"}
        assert set(response_data.keys()) == required_fields

        # Check items array
        assert isinstance(response_data["items"], list)

        # Check each TODO item
        for todo in response_data["items"]:
            required_todo_fields = {
                "id", "title", "description", "completed", "completed_at",
                "priority", "order_index", "created_at", "updated_at"
            }
            assert set(todo.keys()) == required_todo_fields

            # Check field types
            assert isinstance(todo["id"], str)
            assert isinstance(todo["title"], str)
            assert todo["description"] is None or isinstance(todo["description"], str)
            assert isinstance(todo["completed"], bool)
            assert todo["completed_at"] is None or isinstance(todo["completed_at"], str)
            assert todo["priority"] in ["low", "medium", "high"]
            assert isinstance(todo["order_index"], int)
            assert isinstance(todo["created_at"], str)
            assert isinstance(todo["updated_at"], str)

        # Check metadata fields
        assert isinstance(response_data["total"], int)
        assert isinstance(response_data["limit"], int)
        assert isinstance(response_data["offset"], int)
        assert response_data["total"] >= 0
        assert response_data["limit"] > 0
        assert response_data["offset"] >= 0