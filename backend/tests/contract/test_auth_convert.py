"""
Contract tests for POST /api/auth/convert-session endpoint.
Tests the API contract for converting guest session to registered user.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4


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
def mock_todo_service():
    """Mock todo service for testing."""
    with patch("src.api.routes.auth.TodoService") as mock_class:
        mock_instance = Mock()
        # Mock async methods with AsyncMock
        mock_instance.migrate_session_todos_to_user = AsyncMock()
        mock_class.return_value = mock_instance
        yield mock_instance


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

    def test_convert_session_success(self, client: TestClient, mock_user_service, mock_todo_service, valid_session_id):
        """Test successful session conversion."""
        # Arrange
        from uuid import UUID
        from src.main import app
        from src.api.middleware.auth import require_user

        # Use the default user_id from conftest.py
        user_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        # Mock user service
        mock_user = Mock()
        mock_user.id = user_id
        mock_user_service.get_user_by_id.return_value = mock_user

        # Mock todo service
        mock_todo_service.migrate_session_todos_to_user.return_value = 5

        request_data = {"session_id": valid_session_id}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.post("/api/auth/convert-session", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json() == {"migrated_todos_count": 5}
        mock_user_service.get_user_by_id.assert_called_once_with(user_id)
        mock_todo_service.migrate_session_todos_to_user.assert_called_once_with(valid_session_id, user_id)

    def test_convert_session_missing_auth(self, client: TestClient, valid_session_id):
        """Test conversion without authentication."""
        from src.main import app
        from src.api.middleware.auth import require_user

        # Arrange
        def raise_permission_error():
            raise PermissionError("User authentication required")

        # Override dependency to simulate no authentication
        app.dependency_overrides[require_user] = raise_permission_error

        try:
            request_data = {"session_id": valid_session_id}

            # Act
            response = client.post("/api/auth/convert-session", json=request_data)

            # Assert
            assert response.status_code == 403  # FastAPI converts PermissionError to 403
            response_data = response.json()
            assert response_data["error"] == "forbidden"
            assert "access denied" in response_data["message"].lower()
        finally:
            # Clean up override
            if require_user in app.dependency_overrides:
                del app.dependency_overrides[require_user]

    def test_convert_session_invalid_token(self, client: TestClient, valid_session_id):
        """Test conversion with invalid JWT token."""
        from src.main import app
        from src.api.middleware.auth import require_user

        # Arrange
        def raise_permission_error():
            raise PermissionError("User authentication required")

        # Override dependency to simulate invalid token
        app.dependency_overrides[require_user] = raise_permission_error

        try:
            request_data = {"session_id": valid_session_id}
            headers = {"Authorization": "Bearer invalid_jwt_token"}

            # Act
            response = client.post("/api/auth/convert-session", json=request_data, headers=headers)

            # Assert
            assert response.status_code == 403  # FastAPI converts PermissionError to 403
            response_data = response.json()
            assert response_data["error"] == "forbidden"
        finally:
            # Clean up override
            if require_user in app.dependency_overrides:
                del app.dependency_overrides[require_user]

    def test_convert_session_missing_session_id(self, client: TestClient):
        """Test conversion without session_id in request body."""
        # Arrange
        request_data = {}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.post("/api/auth/convert-session", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["error"] == "validation_error"

    def test_convert_session_empty_session_id(self, client: TestClient):
        """Test conversion with empty session_id."""
        # Arrange
        request_data = {"session_id": ""}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.post("/api/auth/convert-session", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["error"] == "validation_error"

    def test_convert_session_invalid_session_id(self, client: TestClient, mock_user_service, mock_todo_service):
        """Test conversion with non-existent session_id."""
        # Arrange
        from uuid import UUID

        # Use the default user_id from conftest.py
        user_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        # Mock user service
        mock_user = Mock()
        mock_user.id = user_id
        mock_user_service.get_user_by_id.return_value = mock_user

        # Mock todo service to raise exception for non-existent session
        mock_todo_service.migrate_session_todos_to_user.side_effect = ValueError("Session not found")

        request_data = {"session_id": "sess_nonexistent"}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.post("/api/auth/convert-session", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "bad_request"
        assert "session not found" in response_data["message"].lower()

    def test_convert_session_already_converted(self, client: TestClient, mock_user_service, mock_todo_service, valid_session_id):
        """Test conversion of already converted session."""
        # Arrange
        from uuid import UUID

        # Use the default user_id from conftest.py
        user_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        # Mock user service
        mock_user = Mock()
        mock_user.id = user_id
        mock_user_service.get_user_by_id.return_value = mock_user

        # Mock todo service to raise exception for already converted session
        mock_todo_service.migrate_session_todos_to_user.side_effect = ValueError("Session already converted")

        request_data = {"session_id": valid_session_id}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.post("/api/auth/convert-session", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "bad_request"
        assert "session already converted" in response_data["message"].lower()

    def test_convert_session_no_todos_migrated(self, client: TestClient, mock_user_service, mock_todo_service, valid_session_id):
        """Test conversion when session has no TODOs."""
        # Arrange
        from uuid import uuid4
        user_id = uuid4()

        # Mock user service
        mock_user = Mock()
        mock_user.id = user_id
        mock_user_service.get_user_by_id.return_value = mock_user

        # Mock todo service
        mock_todo_service.migrate_session_todos_to_user.return_value = 0

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
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["error"] == "validation_error"

    def test_convert_session_extra_fields_ignored(self, client: TestClient, mock_user_service, mock_todo_service, valid_session_id):
        """Test that extra fields in request body are ignored."""
        # Arrange
        from uuid import uuid4
        user_id = uuid4()

        # Mock user service
        mock_user = Mock()
        mock_user.id = user_id
        mock_user_service.get_user_by_id.return_value = mock_user

        # Mock todo service
        mock_todo_service.migrate_session_todos_to_user.return_value = 3

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

    def test_convert_session_response_schema(self, client: TestClient, mock_user_service, mock_todo_service, valid_session_id):
        """Test that response matches expected schema."""
        # Arrange
        from uuid import uuid4
        user_id = uuid4()

        # Mock user service
        mock_user = Mock()
        mock_user.id = user_id
        mock_user_service.get_user_by_id.return_value = mock_user

        # Mock todo service
        mock_todo_service.migrate_session_todos_to_user.return_value = 7

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
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["error"] == "validation_error"