"""
Contract tests for /api/auth/user endpoints.

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
def mock_clerk_token():
    """Mock Clerk JWT token for testing."""
    return "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test.token"


@pytest.fixture
def mock_user_service():
    """Mock user service for testing."""
    with patch("src.api.routes.auth.UserService") as mock_class:
        mock_instance = Mock()
        # Mock async methods with AsyncMock
        mock_instance.get_user_by_id = AsyncMock()
        mock_instance.create_or_update_user = AsyncMock()
        mock_instance.get_user_by_clerk_id = AsyncMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def auth_headers(mock_clerk_token):
    """Authentication headers with mock token."""
    return {"Authorization": f"Bearer {mock_clerk_token}"}


class TestCreateOrUpdateUser:
    """Test cases for POST /api/auth/user endpoint."""

    def test_create_user_success(self, client: TestClient, auth_headers: dict, mock_user_service):
        """Test successful user creation."""
        # Arrange
        user_id = uuid4()
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.display_name = "John Doe"
        mock_user.clerk_user_id = "user_2ABC123DEF456"
        mock_user.email = None
        mock_user.avatar_url = None
        mock_user.created_at = datetime.now()
        mock_user.last_login_at = None

        mock_user_service.create_or_update_user.return_value = (mock_user, True)
        mock_user_service.to_response.return_value = Mock(
            model_dump_json=Mock(return_value='{"id": "' + str(user_id) + '", "display_name": "John Doe", "clerk_user_id": "user_2ABC123DEF456", "email": null, "avatar_url": null, "created_at": "2023-01-01T00:00:00Z", "last_login_at": null}')
        )

        user_data = {
            "display_name": "John Doe",
            "clerk_user_id": "user_2ABC123DEF456"
        }

        # Act
        response: Response = client.post("/api/auth/user", json=user_data, headers=auth_headers)

        # Assert
        assert response.status_code == 201
        assert response.headers["content-type"] == "application/json"

        mock_user_service.create_or_update_user.assert_called_once()
        mock_user_service.to_response.assert_called_once_with(mock_user)

    def test_create_user_with_email(self, client: TestClient, auth_headers: dict, mock_user_service):
        """Test user creation with email."""
        # Arrange
        user_id = uuid4()
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.display_name = "Jane Smith"
        mock_user.clerk_user_id = "user_2XYZ789ABC123"
        mock_user.email = "jane@example.com"
        mock_user.avatar_url = None
        mock_user.created_at = datetime.now()
        mock_user.last_login_at = None

        mock_user_service.create_or_update_user.return_value = (mock_user, True)
        mock_user_service.to_response.return_value = Mock(
            model_dump_json=Mock(return_value='{"id": "' + str(user_id) + '", "display_name": "Jane Smith", "clerk_user_id": "user_2XYZ789ABC123", "email": "jane@example.com", "avatar_url": null, "created_at": "2023-01-01T00:00:00Z", "last_login_at": null}')
        )

        user_data = {
            "display_name": "Jane Smith",
            "clerk_user_id": "user_2XYZ789ABC123",
            "email": "jane@example.com"
        }

        # Act
        response: Response = client.post("/api/auth/user", json=user_data, headers=auth_headers)

        # Assert
        assert response.status_code == 201
        mock_user_service.create_or_update_user.assert_called_once()
        mock_user_service.to_response.assert_called_once_with(mock_user)

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
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "validation_error"

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
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "validation_error"

    def test_create_user_unauthorized(self, client: TestClient):
        """Test user creation without authentication."""
        from src.main import app
        from src.api.middleware.auth import require_auth

        # Arrange
        def raise_permission_error():
            raise PermissionError("User authentication required")

        # Clear existing override and set our custom one
        original_override = app.dependency_overrides.get(require_auth)
        app.dependency_overrides[require_auth] = raise_permission_error

        try:
            user_data = {
                "display_name": "Unauthorized User",
                "clerk_user_id": "user_2UNAUTH123"
            }

            # Act
            response: Response = client.post("/api/auth/user", json=user_data)

            # Assert
            assert response.status_code == 403  # FastAPI converts PermissionError to 403
            data = response.json()
            assert data["error"] == "forbidden"
        finally:
            # Restore original override
            if original_override:
                app.dependency_overrides[require_auth] = original_override
            elif require_auth in app.dependency_overrides:
                del app.dependency_overrides[require_auth]

    def test_create_user_invalid_token(self, client: TestClient):
        """Test user creation with invalid token."""
        from src.main import app
        from src.api.middleware.auth import require_auth

        # Arrange
        def raise_permission_error():
            raise PermissionError("Invalid token")

        # Clear existing override and set our custom one
        original_override = app.dependency_overrides.get(require_auth)
        app.dependency_overrides[require_auth] = raise_permission_error

        try:
            user_data = {
                "display_name": "Invalid Token User",
                "clerk_user_id": "user_2INVALID123"
            }
            headers = {"Authorization": "Bearer invalid.token.here"}

            # Act
            response: Response = client.post("/api/auth/user", json=user_data, headers=headers)

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

    def test_update_existing_user(self, client: TestClient, auth_headers: dict, mock_user_service):
        """Test updating an existing user (should return 200)."""
        # Arrange
        user_id = uuid4()
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.display_name = "Updated Name"
        mock_user.clerk_user_id = "user_2UPDATE123"
        mock_user.email = None
        mock_user.avatar_url = None
        mock_user.created_at = datetime.now()
        mock_user.last_login_at = None

        # Mock update scenario (user already exists)
        mock_user_service.create_or_update_user.return_value = (mock_user, False)
        mock_user_service.to_response.return_value = Mock(
            model_dump_json=Mock(return_value='{"id": "' + str(user_id) + '", "display_name": "Updated Name", "clerk_user_id": "user_2UPDATE123", "email": null, "avatar_url": null, "created_at": "2023-01-01T00:00:00Z", "last_login_at": null}')
        )

        user_data = {
            "display_name": "Updated Name",
            "clerk_user_id": "user_2UPDATE123"
        }

        # Act
        response: Response = client.post("/api/auth/user", json=user_data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        mock_user_service.create_or_update_user.assert_called_once()
        mock_user_service.to_response.assert_called_once_with(mock_user)


class TestGetCurrentUser:
    """Test cases for GET /api/auth/user endpoint."""

    def test_get_current_user_success(self, client: TestClient, auth_headers: dict, mock_user_service):
        """Test retrieving current user profile."""
        # Arrange
        user_id = uuid4()
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.display_name = "Get User Test"
        mock_user.clerk_user_id = "user_2GET123"
        mock_user.email = None
        mock_user.avatar_url = None
        mock_user.created_at = datetime.now()
        mock_user.last_login_at = None

        mock_user_service.get_user_by_id.return_value = mock_user
        mock_user_response = Mock()
        mock_user_response.id = str(user_id)
        mock_user_response.display_name = "Get User Test"
        mock_user_response.clerk_user_id = "user_2GET123"
        mock_user_response.email = None
        mock_user_response.avatar_url = None
        mock_user_response.created_at = "2023-01-01T00:00:00Z"
        mock_user_response.last_login_at = None
        mock_user_service.to_response.return_value = mock_user_response

        # Act
        response: Response = client.get("/api/auth/user", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["display_name"] == "Get User Test"
        assert data["clerk_user_id"] == "user_2GET123"
        mock_user_service.get_user_by_id.assert_called_once()
        mock_user_service.to_response.assert_called_once_with(mock_user)

    def test_get_user_unauthorized(self, client: TestClient):
        """Test retrieving user without authentication."""
        from src.main import app
        from src.api.middleware.auth import require_user

        # Arrange
        def raise_permission_error():
            raise PermissionError("User authentication required")

        # Clear existing override and set our custom one
        original_override = app.dependency_overrides.get(require_user)
        app.dependency_overrides[require_user] = raise_permission_error

        try:
            # Act
            response: Response = client.get("/api/auth/user")

            # Assert
            assert response.status_code == 403  # FastAPI converts PermissionError to 403
            data = response.json()
            assert data["error"] == "forbidden"
        finally:
            # Restore original override
            if original_override:
                app.dependency_overrides[require_user] = original_override
            elif require_user in app.dependency_overrides:
                del app.dependency_overrides[require_user]

    def test_get_user_not_found(self, client: TestClient, auth_headers: dict, mock_user_service):
        """Test retrieving non-existent user."""
        # Arrange
        mock_user_service.get_user_by_id.return_value = None

        # Act
        response: Response = client.get("/api/auth/user", headers=auth_headers)

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"] == "not_found"
        mock_user_service.get_user_by_id.assert_called_once()

    def test_user_response_schema(self, client: TestClient, auth_headers: dict, mock_user_service):
        """Test that response matches UserResponse schema."""
        # Arrange
        user_id = uuid4()
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.display_name = "Schema Test User"
        mock_user.clerk_user_id = "user_2SCHEMA123"
        mock_user.email = "schema@test.com"
        mock_user.avatar_url = None
        from datetime import datetime
        mock_user.created_at = datetime.now()
        mock_user.last_login_at = None

        mock_user_service.get_user_by_id.return_value = mock_user
        mock_user_response = Mock()
        mock_user_response.id = str(user_id)
        mock_user_response.display_name = "Schema Test User"
        mock_user_response.clerk_user_id = "user_2SCHEMA123"
        mock_user_response.email = "schema@test.com"
        mock_user_response.avatar_url = None
        mock_user_response.created_at = "2023-01-01T00:00:00Z"
        mock_user_response.last_login_at = None
        mock_user_service.to_response.return_value = mock_user_response

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
        datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))

        mock_user_service.get_user_by_id.assert_called_once()
        mock_user_service.to_response.assert_called_once_with(mock_user)