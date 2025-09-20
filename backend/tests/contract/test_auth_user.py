"""
Contract tests for /api/auth/user endpoints.

These tests verify that the API adheres to the OpenAPI contract specification.
They MUST fail initially (TDD approach) and pass after implementation.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from unittest.mock import patch


@pytest.fixture
def client():
    """Test client for the FastAPI application."""
    # This will fail initially since the app doesn't exist yet
    from src.main import app
    return TestClient(app)


@pytest.fixture
def mock_clerk_token():
    """Mock Clerk JWT token for testing."""
    return "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test.token"


@pytest.fixture
def auth_headers(mock_clerk_token):
    """Authentication headers with mock token."""
    return {"Authorization": f"Bearer {mock_clerk_token}"}


class TestCreateOrUpdateUser:
    """Test cases for POST /api/auth/user endpoint."""

    def test_create_user_success(self, client: TestClient, auth_headers: dict):
        """Test successful user creation."""
        # Arrange
        user_data = {
            "display_name": "John Doe",
            "clerk_user_id": "user_2ABC123DEF456"
        }

        # Act
        response: Response = client.post("/api/auth/user", json=user_data, headers=auth_headers)

        # Assert
        assert response.status_code == 201
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert "id" in data
        assert data["display_name"] == "John Doe"
        assert data["clerk_user_id"] == "user_2ABC123DEF456"
        assert "created_at" in data
        assert "last_login_at" in data

        # Verify UUID format for id
        import uuid
        uuid.UUID(data["id"])

    def test_create_user_with_email(self, client: TestClient, auth_headers: dict):
        """Test user creation with email."""
        # Arrange
        user_data = {
            "display_name": "Jane Smith",
            "clerk_user_id": "user_2XYZ789ABC123",
            "email": "jane@example.com"
        }

        # Act
        response: Response = client.post("/api/auth/user", json=user_data, headers=auth_headers)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "jane@example.com"

    def test_create_user_missing_required_fields(self, client: TestClient, auth_headers: dict):
        """Test user creation with missing required fields."""
        # Arrange
        user_data = {
            "display_name": "Incomplete User"
            # Missing clerk_user_id
        }

        # Act
        response: Response = client.post("/api/auth/user", json=user_data, headers=auth_headers)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_create_user_invalid_email(self, client: TestClient, auth_headers: dict):
        """Test user creation with invalid email format."""
        # Arrange
        user_data = {
            "display_name": "Bad Email User",
            "clerk_user_id": "user_2BAD123EMAIL",
            "email": "not-an-email"
        }

        # Act
        response: Response = client.post("/api/auth/user", json=user_data, headers=auth_headers)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_create_user_unauthorized(self, client: TestClient):
        """Test user creation without authentication."""
        # Arrange
        user_data = {
            "display_name": "Unauthorized User",
            "clerk_user_id": "user_2UNAUTH123"
        }

        # Act
        response: Response = client.post("/api/auth/user", json=user_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["error"] == "unauthorized"

    def test_create_user_invalid_token(self, client: TestClient):
        """Test user creation with invalid token."""
        # Arrange
        user_data = {
            "display_name": "Invalid Token User",
            "clerk_user_id": "user_2INVALID123"
        }
        headers = {"Authorization": "Bearer invalid.token.here"}

        # Act
        response: Response = client.post("/api/auth/user", json=user_data, headers=headers)

        # Assert
        assert response.status_code == 401

    def test_update_existing_user(self, client: TestClient, auth_headers: dict):
        """Test updating an existing user (should return 200)."""
        # First create a user
        user_data = {
            "display_name": "Original Name",
            "clerk_user_id": "user_2UPDATE123"
        }

        create_response = client.post("/api/auth/user", json=user_data, headers=auth_headers)
        assert create_response.status_code == 201

        # Update the same user
        updated_data = {
            "display_name": "Updated Name",
            "clerk_user_id": "user_2UPDATE123"
        }

        # Act
        response: Response = client.post("/api/auth/user", json=updated_data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Name"


class TestGetCurrentUser:
    """Test cases for GET /api/auth/user endpoint."""

    def test_get_current_user_success(self, client: TestClient, auth_headers: dict):
        """Test retrieving current user profile."""
        # First create a user
        user_data = {
            "display_name": "Get User Test",
            "clerk_user_id": "user_2GET123"
        }
        client.post("/api/auth/user", json=user_data, headers=auth_headers)

        # Act
        response: Response = client.get("/api/auth/user", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["display_name"] == "Get User Test"
        assert data["clerk_user_id"] == "user_2GET123"

    def test_get_user_unauthorized(self, client: TestClient):
        """Test retrieving user without authentication."""
        # Act
        response: Response = client.get("/api/auth/user")

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["error"] == "unauthorized"

    def test_get_user_not_found(self, client: TestClient, auth_headers: dict):
        """Test retrieving non-existent user."""
        # Act (without creating user first)
        response: Response = client.get("/api/auth/user", headers=auth_headers)

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"] == "not_found"

    def test_user_response_schema(self, client: TestClient, auth_headers: dict):
        """Test that response matches UserResponse schema."""
        # Arrange - create user first
        user_data = {
            "display_name": "Schema Test User",
            "clerk_user_id": "user_2SCHEMA123",
            "email": "schema@test.com"
        }
        client.post("/api/auth/user", json=user_data, headers=auth_headers)

        # Act
        response: Response = client.get("/api/auth/user", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Required fields from UserResponse schema
        required_fields = ["id", "clerk_user_id", "display_name", "created_at"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Optional fields
        optional_fields = ["email", "avatar_url", "last_login_at"]
        for field in optional_fields:
            if field in data:
                assert data[field] is None or isinstance(data[field], str)

        # Field types
        assert isinstance(data["id"], str)
        assert isinstance(data["clerk_user_id"], str)
        assert isinstance(data["display_name"], str)
        assert isinstance(data["created_at"], str)

        # Verify UUID format
        import uuid
        uuid.UUID(data["id"])

        # Verify datetime format
        from datetime import datetime
        datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))