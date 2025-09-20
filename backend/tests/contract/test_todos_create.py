"""
Contract tests for POST /api/todos endpoint.

These tests verify that the API adheres to the OpenAPI contract specification.
They MUST fail initially (TDD approach) and pass after implementation.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import Response


@pytest.fixture
def client():
    """Test client for the FastAPI application."""
    # This will fail initially since the app doesn't exist yet
    from src.main import app
    return TestClient(app)


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

    def test_create_todo_authenticated_user_success(self, client: TestClient, auth_headers: dict):
        """Test successful TODO creation for authenticated user."""
        # Arrange
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

        # Verify UUID format for id
        import uuid
        uuid.UUID(data["id"])

    def test_create_todo_guest_user_success(self, client: TestClient, session_headers: dict):
        """Test successful TODO creation for guest user."""
        # Arrange
        todo_data = {
            "title": "Guest TODO",
            "priority": "high"
        }

        # Act
        response: Response = client.post("/api/todos", json=todo_data, headers=session_headers)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Guest TODO"
        assert data["priority"] == "high"

    def test_create_todo_minimal_data(self, client: TestClient, auth_headers: dict):
        """Test TODO creation with only required fields."""
        # Arrange
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

    def test_create_todo_all_priorities(self, client: TestClient, auth_headers: dict):
        """Test TODO creation with all valid priority levels."""
        priorities = ["low", "medium", "high"]

        for priority in priorities:
            # Arrange
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
        assert response.status_code == 400
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
        assert response.status_code == 400
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
        assert response.status_code == 400
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
        assert response.status_code == 400
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
        # Arrange
        todo_data = {
            "title": "Unauthorized TODO"
        }

        # Act
        response: Response = client.post("/api/todos", json=todo_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["error"] == "unauthorized"

    def test_create_todo_invalid_token(self, client: TestClient):
        """Test TODO creation with invalid authentication token."""
        # Arrange
        todo_data = {
            "title": "Invalid token TODO"
        }
        headers = {"Authorization": "Bearer invalid.token"}

        # Act
        response: Response = client.post("/api/todos", json=todo_data, headers=headers)

        # Assert
        assert response.status_code == 401

    def test_create_todo_invalid_session(self, client: TestClient):
        """Test TODO creation with invalid session ID."""
        # Arrange
        todo_data = {
            "title": "Invalid session TODO"
        }
        headers = {"X-Session-ID": "invalid_session_id"}

        # Act
        response: Response = client.post("/api/todos", json=todo_data, headers=headers)

        # Assert
        assert response.status_code == 401

    def test_todo_response_schema(self, client: TestClient, auth_headers: dict):
        """Test that response matches TodoItemResponse schema."""
        # Arrange
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
        from datetime import datetime
        datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))

        # Verify enum values
        assert data["priority"] in ["low", "medium", "high"]

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