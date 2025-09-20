"""
Contract tests for POST /api/auth/convert-session endpoint.
Tests the API contract for converting guest session to registered user.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from uuid import uuid4


@pytest.fixture
def mock_auth_service():
    """Mock auth service for testing."""
    with patch("src.api.routes.auth.auth_service") as mock:
        yield mock


@pytest.fixture
def mock_clerk_user():
    """Mock Clerk user data."""
    return {
        "id": "user_2ABC123DEF456",
        "email_addresses": [{"email_address": "test@example.com"}],
        "first_name": "John",
        "last_name": "Doe",
        "image_url": "https://images.clerk.dev/uploaded/img_..."
    }


@pytest.fixture
def valid_session_id():
    """Valid session ID for testing."""
    return "sess_abc123def456ghi789"


class TestAuthConvertSession:
    """Test suite for POST /api/auth/convert-session endpoint."""

    def test_convert_session_success(self, client: TestClient, mock_auth_service, valid_session_id):
        """Test successful session conversion."""
        # Arrange
        mock_auth_service.convert_guest_session.return_value = {"migrated_todos_count": 5}

        request_data = {"session_id": valid_session_id}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.post("/api/auth/convert-session", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json() == {"migrated_todos_count": 5}
        mock_auth_service.convert_guest_session.assert_called_once()

    def test_convert_session_missing_auth(self, client: TestClient, valid_session_id):
        """Test conversion without authentication."""
        # Arrange
        request_data = {"session_id": valid_session_id}

        # Act
        response = client.post("/api/auth/convert-session", json=request_data)

        # Assert
        assert response.status_code == 401
        response_data = response.json()
        assert response_data["error"] == "unauthorized"
        assert "authentication required" in response_data["message"].lower()

    def test_convert_session_invalid_token(self, client: TestClient, valid_session_id):
        """Test conversion with invalid JWT token."""
        # Arrange
        request_data = {"session_id": valid_session_id}
        headers = {"Authorization": "Bearer invalid_jwt_token"}

        # Act
        response = client.post("/api/auth/convert-session", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 401
        response_data = response.json()
        assert response_data["error"] == "unauthorized"

    def test_convert_session_missing_session_id(self, client: TestClient):
        """Test conversion without session_id in request body."""
        # Arrange
        request_data = {}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.post("/api/auth/convert-session", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "session_id" in response_data["message"].lower()

    def test_convert_session_empty_session_id(self, client: TestClient):
        """Test conversion with empty session_id."""
        # Arrange
        request_data = {"session_id": ""}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.post("/api/auth/convert-session", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"

    def test_convert_session_invalid_session_id(self, client: TestClient, mock_auth_service):
        """Test conversion with non-existent session_id."""
        # Arrange
        mock_auth_service.convert_guest_session.side_effect = ValueError("Session not found")

        request_data = {"session_id": "sess_nonexistent"}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.post("/api/auth/convert-session", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 404
        response_data = response.json()
        assert response_data["error"] == "not_found"
        assert "session not found" in response_data["message"].lower()

    def test_convert_session_already_converted(self, client: TestClient, mock_auth_service, valid_session_id):
        """Test conversion of already converted session."""
        # Arrange
        mock_auth_service.convert_guest_session.side_effect = ValueError("Session already converted")

        request_data = {"session_id": valid_session_id}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.post("/api/auth/convert-session", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "bad_request"
        assert "already converted" in response_data["message"].lower()

    def test_convert_session_no_todos_migrated(self, client: TestClient, mock_auth_service, valid_session_id):
        """Test conversion when session has no TODOs."""
        # Arrange
        mock_auth_service.convert_guest_session.return_value = {"migrated_todos_count": 0}

        request_data = {"session_id": valid_session_id}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.post("/api/auth/convert-session", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json() == {"migrated_todos_count": 0}

    def test_convert_session_malformed_request_body(self, client: TestClient):
        """Test conversion with malformed JSON request body."""
        # Arrange
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.post(
            "/api/auth/convert-session",
            data="invalid json",
            headers={**headers, "Content-Type": "application/json"}
        )

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"

    def test_convert_session_extra_fields_ignored(self, client: TestClient, mock_auth_service, valid_session_id):
        """Test that extra fields in request body are ignored."""
        # Arrange
        mock_auth_service.convert_guest_session.return_value = {"migrated_todos_count": 3}

        request_data = {
            "session_id": valid_session_id,
            "extra_field": "should_be_ignored",
            "another_field": 123
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.post("/api/auth/convert-session", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json() == {"migrated_todos_count": 3}

    def test_convert_session_response_schema(self, client: TestClient, mock_auth_service, valid_session_id):
        """Test that response matches expected schema."""
        # Arrange
        mock_auth_service.convert_guest_session.return_value = {"migrated_todos_count": 7}

        request_data = {"session_id": valid_session_id}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.post("/api/auth/convert-session", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Check response schema
        assert isinstance(response_data, dict)
        assert "migrated_todos_count" in response_data
        assert isinstance(response_data["migrated_todos_count"], int)
        assert response_data["migrated_todos_count"] >= 0

        # Check no extra fields
        assert len(response_data) == 1

    def test_convert_session_content_type_validation(self, client: TestClient, valid_session_id):
        """Test that endpoint requires application/json content type."""
        # Arrange
        request_data = f'{{"session_id": "{valid_session_id}"}}'
        headers = {
            "Authorization": "Bearer valid_jwt_token",
            "Content-Type": "text/plain"
        }

        # Act
        response = client.post("/api/auth/convert-session", data=request_data, headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"