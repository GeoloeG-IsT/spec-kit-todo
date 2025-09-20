"""
Contract tests for PUT /api/todos/bulk endpoint.
Tests the API contract for bulk updating TODO items.
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
def sample_todo_ids():
    """Sample TODO IDs for bulk operations."""
    return [str(uuid4()) for _ in range(3)]


class TestTodosBulk:
    """Test suite for PUT /api/todos/bulk endpoint."""

    def test_bulk_update_success_authenticated(self, client: TestClient, mock_todo_service, sample_todo_ids):
        """Test successful bulk TODO update for authenticated user."""
        # Arrange
        mock_todo_service.bulk_update_todos.return_value = {"updated_count": 3}

        request_data = {
            "todo_ids": sample_todo_ids,
            "completed": True,
            "priority": "high"
        }

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        assert "updated_count" in response_data
        assert response_data["updated_count"] == 3

        mock_todo_service.bulk_update_todos.assert_called_once()

    def test_bulk_update_success_guest_session(self, client: TestClient, mock_todo_service, sample_todo_ids):
        """Test successful bulk TODO update for guest session."""
        # Arrange
        mock_todo_service.bulk_update_todos.return_value = {"updated_count": 2}

        request_data = {
            "todo_ids": sample_todo_ids[:2],
            "completed": False
        }

        headers = {"X-Session-ID": "sess_abc123def456ghi789"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 2

    def test_bulk_update_mark_completed(self, client: TestClient, mock_todo_service, sample_todo_ids):
        """Test bulk marking TODOs as completed."""
        # Arrange
        mock_todo_service.bulk_update_todos.return_value = {"updated_count": 3}

        request_data = {
            "todo_ids": sample_todo_ids,
            "completed": True
        }

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 3

    def test_bulk_update_change_priority(self, client: TestClient, mock_todo_service, sample_todo_ids):
        """Test bulk priority change."""
        # Arrange
        mock_todo_service.bulk_update_todos.return_value = {"updated_count": 3}

        request_data = {
            "todo_ids": sample_todo_ids,
            "priority": "low"
        }

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 3

    def test_bulk_update_both_completed_and_priority(self, client: TestClient, mock_todo_service, sample_todo_ids):
        """Test bulk update with both completed status and priority."""
        # Arrange
        mock_todo_service.bulk_update_todos.return_value = {"updated_count": 3}

        request_data = {
            "todo_ids": sample_todo_ids,
            "completed": True,
            "priority": "high"
        }

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 3

    def test_bulk_update_no_auth(self, client: TestClient, sample_todo_ids):
        """Test bulk TODO update without authentication."""
        # Arrange
        request_data = {
            "todo_ids": sample_todo_ids,
            "completed": True
        }

        # Act
        response = client.put("/api/todos/bulk", json=request_data)

        # Assert
        assert response.status_code == 401
        response_data = response.json()
        assert response_data["error"] == "unauthorized"
        assert "authentication required" in response_data["message"].lower()

    def test_bulk_update_invalid_token(self, client: TestClient, sample_todo_ids):
        """Test bulk TODO update with invalid JWT token."""
        # Arrange
        request_data = {
            "todo_ids": sample_todo_ids,
            "completed": True
        }
        headers = {"Authorization": "Bearer invalid_jwt_token"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 401
        response_data = response.json()
        assert response_data["error"] == "unauthorized"

    def test_bulk_update_invalid_session(self, client: TestClient, sample_todo_ids):
        """Test bulk TODO update with invalid session ID."""
        # Arrange
        request_data = {
            "todo_ids": sample_todo_ids,
            "completed": True
        }
        headers = {"X-Session-ID": "invalid_session"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 401
        response_data = response.json()
        assert response_data["error"] == "unauthorized"

    def test_bulk_update_missing_todo_ids(self, client: TestClient):
        """Test bulk update without todo_ids field."""
        # Arrange
        request_data = {
            "completed": True
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "todo_ids" in response_data["message"].lower()

    def test_bulk_update_empty_todo_ids(self, client: TestClient):
        """Test bulk update with empty todo_ids array."""
        # Arrange
        request_data = {
            "todo_ids": [],
            "completed": True
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "todo_ids" in response_data["message"].lower()

    def test_bulk_update_invalid_todo_id_format(self, client: TestClient):
        """Test bulk update with invalid UUID format in todo_ids."""
        # Arrange
        request_data = {
            "todo_ids": ["not-a-valid-uuid", str(uuid4())],
            "completed": True
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "uuid" in response_data["message"].lower()

    def test_bulk_update_duplicate_todo_ids(self, client: TestClient, mock_todo_service):
        """Test bulk update with duplicate TODO IDs."""
        # Arrange
        todo_id = str(uuid4())
        mock_todo_service.bulk_update_todos.return_value = {"updated_count": 1}  # Only one unique update

        request_data = {
            "todo_ids": [todo_id, todo_id, todo_id],
            "completed": True
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        # Should handle duplicates gracefully
        assert response.status_code == 200
        response_data = response.json()
        # Updated count might be 1 (deduplicated) or 3 (allowing duplicates)
        assert response_data["updated_count"] >= 1

    def test_bulk_update_invalid_priority(self, client: TestClient, sample_todo_ids):
        """Test bulk update with invalid priority value."""
        # Arrange
        request_data = {
            "todo_ids": sample_todo_ids,
            "priority": "invalid"
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "priority" in response_data["message"].lower()

    def test_bulk_update_all_priorities(self, client: TestClient, mock_todo_service, sample_todo_ids):
        """Test bulk update with all valid priority values."""
        priorities = ["low", "medium", "high"]

        for priority in priorities:
            # Arrange
            mock_todo_service.bulk_update_todos.return_value = {"updated_count": 3}

            request_data = {
                "todo_ids": sample_todo_ids,
                "priority": priority
            }
            headers = {"Authorization": "Bearer valid_jwt_token"}

            # Act
            response = client.put("/api/todos/bulk", json=request_data, headers=headers)

            # Assert
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["updated_count"] == 3

    def test_bulk_update_no_update_fields(self, client: TestClient, sample_todo_ids):
        """Test bulk update with only todo_ids (no fields to update)."""
        # Arrange
        request_data = {
            "todo_ids": sample_todo_ids
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        # Should be an error - at least one field must be provided to update
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"

    def test_bulk_update_some_todos_not_found(self, client: TestClient, mock_todo_service, sample_todo_ids):
        """Test bulk update when some TODOs don't exist."""
        # Arrange
        # Only 2 out of 3 TODOs found/updated
        mock_todo_service.bulk_update_todos.return_value = {"updated_count": 2}

        request_data = {
            "todo_ids": sample_todo_ids,
            "completed": True
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        # Should be success with partial update count
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 2

    def test_bulk_update_forbidden_todos(self, client: TestClient, mock_todo_service, sample_todo_ids):
        """Test bulk update when user doesn't own some TODOs."""
        # Arrange
        mock_todo_service.bulk_update_todos.side_effect = PermissionError("Access denied to some TODOs")

        request_data = {
            "todo_ids": sample_todo_ids,
            "completed": True
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 403
        response_data = response.json()
        assert response_data["error"] == "forbidden"

    def test_bulk_update_malformed_json(self, client: TestClient):
        """Test bulk update with malformed JSON."""
        # Arrange
        headers = {
            "Authorization": "Bearer valid_jwt_token",
            "Content-Type": "application/json"
        }

        # Act
        response = client.put("/api/todos/bulk", data="invalid json", headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"

    def test_bulk_update_zero_updated(self, client: TestClient, mock_todo_service, sample_todo_ids):
        """Test bulk update when no TODOs are actually updated."""
        # Arrange
        mock_todo_service.bulk_update_todos.return_value = {"updated_count": 0}

        request_data = {
            "todo_ids": sample_todo_ids,
            "completed": True
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 0

    def test_bulk_update_large_number_of_todos(self, client: TestClient, mock_todo_service):
        """Test bulk update with a large number of TODOs."""
        # Arrange
        large_todo_list = [str(uuid4()) for _ in range(100)]
        mock_todo_service.bulk_update_todos.return_value = {"updated_count": 100}

        request_data = {
            "todo_ids": large_todo_list,
            "completed": True
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 100

    def test_bulk_update_response_schema_validation(self, client: TestClient, mock_todo_service, sample_todo_ids):
        """Test that response matches expected schema exactly."""
        # Arrange
        mock_todo_service.bulk_update_todos.return_value = {"updated_count": 3}

        request_data = {
            "todo_ids": sample_todo_ids,
            "completed": True
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        # Check response structure
        assert isinstance(response_data, dict)
        assert "updated_count" in response_data
        assert isinstance(response_data["updated_count"], int)
        assert response_data["updated_count"] >= 0

        # Check no extra fields
        assert len(response_data) == 1

    def test_bulk_update_extra_fields_ignored(self, client: TestClient, mock_todo_service, sample_todo_ids):
        """Test that extra fields in request body are ignored."""
        # Arrange
        mock_todo_service.bulk_update_todos.return_value = {"updated_count": 3}

        request_data = {
            "todo_ids": sample_todo_ids,
            "completed": True,
            "extra_field": "should_be_ignored",
            "another_field": 123
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 3

    def test_bulk_update_single_todo(self, client: TestClient, mock_todo_service):
        """Test bulk update with single TODO (edge case)."""
        # Arrange
        single_todo_id = [str(uuid4())]
        mock_todo_service.bulk_update_todos.return_value = {"updated_count": 1}

        request_data = {
            "todo_ids": single_todo_id,
            "completed": True
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/bulk", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 1

    def test_bulk_update_content_type_validation(self, client: TestClient, sample_todo_ids):
        """Test that endpoint requires application/json content type."""
        # Arrange
        request_data = f'{{"todo_ids": {sample_todo_ids}, "completed": true}}'
        headers = {
            "Authorization": "Bearer valid_jwt_token",
            "Content-Type": "text/plain"
        }

        # Act
        response = client.put("/api/todos/bulk", data=request_data, headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"