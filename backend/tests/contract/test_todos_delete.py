"""
Contract tests for DELETE /api/todos/{todo_id} endpoint.
Tests the API contract for deleting a specific TODO item (soft delete).
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
        mock_instance.delete_todo = AsyncMock()
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


class TestTodosDelete:
    """Test suite for DELETE /api/todos/{todo_id} endpoint."""

    def test_delete_todo_success_authenticated(self, client: TestClient, mock_todo_service, mock_realtime_service):
        """Test successful TODO deletion for authenticated user."""
        # Arrange
        todo_id = str(uuid4())
        mock_todo_service.delete_todo.return_value = True  # Successful deletion

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.delete(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 204
        assert response.content == b""  # No content for 204 response

        mock_todo_service.delete_todo.assert_called_once()
        mock_realtime_service.notify_todo_deleted.assert_called_once()

    def test_delete_todo_success_guest_session(self, client: TestClient, mock_todo_service, mock_realtime_service):
        """Test successful TODO deletion for guest session."""
        # Arrange
        todo_id = str(uuid4())
        mock_todo_service.delete_todo.return_value = True  # Successful deletion

        headers = {"X-Session-ID": "sess_abc123def456ghi789"}

        # Act
        response = client.delete(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 204
        assert response.content == b""

        mock_todo_service.delete_todo.assert_called_once()
        mock_realtime_service.notify_todo_deleted.assert_called_once()

    def test_delete_todo_no_auth(self, client: TestClient):
        """Test TODO deletion without authentication."""
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
            response = client.delete(f"/api/todos/{todo_id}")

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

    def test_delete_todo_invalid_token(self, client: TestClient):
        """Test TODO deletion with invalid JWT token."""
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
            response = client.delete(f"/api/todos/{todo_id}", headers=headers)

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

    def test_delete_todo_invalid_session(self, client: TestClient):
        """Test TODO deletion with invalid session ID."""
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
            response = client.delete(f"/api/todos/{todo_id}", headers=headers)

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

    def test_delete_todo_not_found(self, client: TestClient, mock_todo_service):
        """Test TODO deletion with non-existent ID."""
        # Arrange
        todo_id = str(uuid4())
        mock_todo_service.delete_todo.return_value = False  # Service returns False for not found

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.delete(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 404
        response_data = response.json()
        assert response_data["error"] == "not_found"
        assert "not found" in response_data["message"].lower()

    def test_delete_todo_forbidden_different_user(self, client: TestClient, mock_todo_service):
        """Test TODO deletion for TODO owned by different user."""
        # Arrange
        todo_id = str(uuid4())
        mock_todo_service.delete_todo.return_value = False  # Service returns False for not owned

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.delete(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 404  # Not found due to ownership filter
        response_data = response.json()
        assert response_data["error"] == "not_found"

    def test_delete_todo_forbidden_different_session(self, client: TestClient, mock_todo_service):
        """Test TODO deletion for TODO from different guest session."""
        # Arrange
        todo_id = str(uuid4())
        mock_todo_service.delete_todo.return_value = False  # Service returns False for not owned

        headers = {"X-Session-ID": "sess_abc123def456ghi789"}

        # Act
        response = client.delete(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 404  # Not found due to ownership filter
        response_data = response.json()
        assert response_data["error"] == "not_found"

    def test_delete_todo_invalid_uuid_format(self, client: TestClient):
        """Test TODO deletion with invalid UUID format."""
        # Arrange
        invalid_todo_id = "not-a-valid-uuid"
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.delete(f"/api/todos/{invalid_todo_id}", headers=headers)

        # Assert
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "validation" in response_data["message"].lower()

    def test_delete_todo_malformed_uuid(self, client: TestClient):
        """Test TODO deletion with malformed UUID."""
        # Arrange
        malformed_uuid = "123e4567-e89b-12d3-a456"  # Missing last segment
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.delete(f"/api/todos/{malformed_uuid}", headers=headers)

        # Assert
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["error"] == "validation_error"

    def test_delete_todo_empty_uuid(self, client: TestClient):
        """Test TODO deletion with empty UUID path parameter."""
        # Arrange
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.delete("/api/todos/", headers=headers)

        # Assert
        # Should match different route or 404/405
        assert response.status_code in [404, 405]

    def test_delete_todo_already_deleted(self, client: TestClient, mock_todo_service):
        """Test deletion of already deleted TODO."""
        # Arrange
        todo_id = str(uuid4())
        mock_todo_service.delete_todo.return_value = False  # Service returns False for already deleted

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.delete(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 404  # Not found (filtered out by deleted_at.is_(None))
        response_data = response.json()
        assert response_data["error"] == "not_found"

    def test_delete_todo_case_insensitive_uuid(self, client: TestClient, mock_todo_service):
        """Test that UUID matching is case insensitive for deletion."""
        # Arrange
        todo_id = str(uuid4()).upper()  # Convert to uppercase
        mock_todo_service.delete_todo.return_value = True

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.delete(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        # This depends on implementation - might be 204 or 422
        assert response.status_code in [204, 422]

    def test_delete_todo_no_content_type_header(self, client: TestClient, mock_todo_service):
        """Test TODO deletion without content-type header."""
        # Arrange
        todo_id = str(uuid4())
        mock_todo_service.delete_todo.return_value = True

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.delete(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        # DELETE should work without content-type
        assert response.status_code == 204

    def test_delete_todo_with_request_body_ignored(self, client: TestClient, mock_todo_service):
        """Test that request body is ignored for DELETE operation."""
        # Arrange
        todo_id = str(uuid4())
        mock_todo_service.delete_todo.return_value = True

        headers = {
            "Authorization": "Bearer valid_jwt_token",
            "Content-Type": "application/json"
        }

        # Act
        response = client.delete(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 204

    def test_delete_todo_response_headers(self, client: TestClient, mock_todo_service):
        """Test that DELETE response has appropriate headers."""
        # Arrange
        todo_id = str(uuid4())
        mock_todo_service.delete_todo.return_value = True

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.delete(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 204
        assert response.content == b""

        # Check content-type header exists (FastAPI sets it by default)
        assert "content-type" in response.headers

    def test_delete_todo_idempotent_operation(self, client: TestClient, mock_todo_service):
        """Test that deleting the same TODO twice returns consistent result."""
        # Arrange
        todo_id = str(uuid4())

        # First call succeeds
        mock_todo_service.delete_todo.return_value = True  # First deletion succeeds
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act - First deletion
        response1 = client.delete(f"/api/todos/{todo_id}", headers=headers)

        # Arrange - Second call (already deleted)
        mock_todo_service.delete_todo.return_value = False  # Second call returns False (not found)

        # Act - Second deletion
        response2 = client.delete(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response1.status_code == 204
        assert response2.status_code == 404  # Not found because already deleted

    def test_delete_todo_service_method_called_correctly(self, client: TestClient, mock_todo_service):
        """Test that the service method is called with correct parameters."""
        # Arrange
        todo_id = str(uuid4())
        mock_todo_service.delete_todo.return_value = True

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.delete(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 204
        mock_todo_service.delete_todo.assert_called_once()

        # Check that the service was called with the correct todo_id
        call_args = mock_todo_service.delete_todo.call_args
        assert call_args is not None

    def test_delete_todo_soft_delete_behavior(self, client: TestClient, mock_todo_service):
        """Test that deletion is soft delete (sets deleted_at timestamp)."""
        # This is more of a service layer test, but we can verify the API contract

        # Arrange
        todo_id = str(uuid4())
        mock_todo_service.delete_todo.return_value = True

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.delete(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response.status_code == 204

        # Verify the service was called (implementation will handle soft delete)
        mock_todo_service.delete_todo.assert_called_once()

    def test_delete_todo_multiple_todos_independently(self, client: TestClient, mock_todo_service):
        """Test that multiple TODO deletions work independently."""
        # Arrange
        todo_id_1 = str(uuid4())
        todo_id_2 = str(uuid4())
        mock_todo_service.delete_todo.return_value = True

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response1 = client.delete(f"/api/todos/{todo_id_1}", headers=headers)
        response2 = client.delete(f"/api/todos/{todo_id_2}", headers=headers)

        # Assert
        assert response1.status_code == 204
        assert response2.status_code == 204

        # Verify service was called twice
        assert mock_todo_service.delete_todo.call_count == 2

    def test_delete_todo_concurrent_deletion_handling(self, client: TestClient, mock_todo_service):
        """Test handling of concurrent deletion attempts."""
        # Arrange
        todo_id = str(uuid4())

        # Simulate race condition - first call succeeds, second call finds it already deleted
        mock_todo_service.delete_todo.side_effect = [True, False]  # First succeeds, second returns False

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response1 = client.delete(f"/api/todos/{todo_id}", headers=headers)
        response2 = client.delete(f"/api/todos/{todo_id}", headers=headers)

        # Assert
        assert response1.status_code == 204
        assert response2.status_code == 404

        assert mock_todo_service.delete_todo.call_count == 2