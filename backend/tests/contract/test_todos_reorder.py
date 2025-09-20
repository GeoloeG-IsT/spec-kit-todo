"""
Contract tests for PUT /api/todos/reorder endpoint.
Tests the API contract for reordering TODO items.
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
def sample_todo_orders():
    """Sample TODO reorder data for testing."""
    return [
        {"todo_id": str(uuid4()), "order_index": 0},
        {"todo_id": str(uuid4()), "order_index": 1},
        {"todo_id": str(uuid4()), "order_index": 2}
    ]


class TestTodosReorder:
    """Test suite for PUT /api/todos/reorder endpoint."""

    def test_reorder_todos_success_authenticated(self, client: TestClient, mock_todo_service, sample_todo_orders):
        """Test successful TODO reordering for authenticated user."""
        # Arrange
        mock_todo_service.reorder_todos.return_value = {"updated_count": 3}

        request_data = {
            "todo_orders": sample_todo_orders
        }

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        assert "updated_count" in response_data
        assert response_data["updated_count"] == 3

        mock_todo_service.reorder_todos.assert_called_once()

    def test_reorder_todos_success_guest_session(self, client: TestClient, mock_todo_service, sample_todo_orders):
        """Test successful TODO reordering for guest session."""
        # Arrange
        mock_todo_service.reorder_todos.return_value = {"updated_count": 2}

        request_data = {
            "todo_orders": sample_todo_orders[:2]
        }

        headers = {"X-Session-ID": "sess_abc123def456ghi789"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 2

    def test_reorder_todos_reverse_order(self, client: TestClient, mock_todo_service):
        """Test reordering TODOs in reverse order."""
        # Arrange
        reverse_order = [
            {"todo_id": str(uuid4()), "order_index": 2},
            {"todo_id": str(uuid4()), "order_index": 1},
            {"todo_id": str(uuid4()), "order_index": 0}
        ]

        mock_todo_service.reorder_todos.return_value = {"updated_count": 3}

        request_data = {
            "todo_orders": reverse_order
        }

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 3

    def test_reorder_todos_large_indices(self, client: TestClient, mock_todo_service):
        """Test reordering with large order indices."""
        # Arrange
        large_indices = [
            {"todo_id": str(uuid4()), "order_index": 1000},
            {"todo_id": str(uuid4()), "order_index": 2000},
            {"todo_id": str(uuid4()), "order_index": 3000}
        ]

        mock_todo_service.reorder_todos.return_value = {"updated_count": 3}

        request_data = {
            "todo_orders": large_indices
        }

        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 3

    def test_reorder_todos_no_auth(self, client: TestClient, sample_todo_orders):
        """Test TODO reordering without authentication."""
        # Arrange
        request_data = {
            "todo_orders": sample_todo_orders
        }

        # Act
        response = client.put("/api/todos/reorder", json=request_data)

        # Assert
        assert response.status_code == 401
        response_data = response.json()
        assert response_data["error"] == "unauthorized"
        assert "authentication required" in response_data["message"].lower()

    def test_reorder_todos_invalid_token(self, client: TestClient, sample_todo_orders):
        """Test TODO reordering with invalid JWT token."""
        # Arrange
        request_data = {
            "todo_orders": sample_todo_orders
        }
        headers = {"Authorization": "Bearer invalid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 401
        response_data = response.json()
        assert response_data["error"] == "unauthorized"

    def test_reorder_todos_invalid_session(self, client: TestClient, sample_todo_orders):
        """Test TODO reordering with invalid session ID."""
        # Arrange
        request_data = {
            "todo_orders": sample_todo_orders
        }
        headers = {"X-Session-ID": "invalid_session"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 401
        response_data = response.json()
        assert response_data["error"] == "unauthorized"

    def test_reorder_todos_missing_todo_orders(self, client: TestClient):
        """Test reordering without todo_orders field."""
        # Arrange
        request_data = {}
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "todo_orders" in response_data["message"].lower()

    def test_reorder_todos_empty_todo_orders(self, client: TestClient):
        """Test reordering with empty todo_orders array."""
        # Arrange
        request_data = {
            "todo_orders": []
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "todo_orders" in response_data["message"].lower()

    def test_reorder_todos_invalid_todo_id_format(self, client: TestClient):
        """Test reordering with invalid UUID format in todo_id."""
        # Arrange
        request_data = {
            "todo_orders": [
                {"todo_id": "not-a-valid-uuid", "order_index": 0},
                {"todo_id": str(uuid4()), "order_index": 1}
            ]
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "uuid" in response_data["message"].lower()

    def test_reorder_todos_missing_todo_id(self, client: TestClient):
        """Test reordering with missing todo_id field."""
        # Arrange
        request_data = {
            "todo_orders": [
                {"order_index": 0},  # Missing todo_id
                {"todo_id": str(uuid4()), "order_index": 1}
            ]
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "todo_id" in response_data["message"].lower()

    def test_reorder_todos_missing_order_index(self, client: TestClient):
        """Test reordering with missing order_index field."""
        # Arrange
        request_data = {
            "todo_orders": [
                {"todo_id": str(uuid4())},  # Missing order_index
                {"todo_id": str(uuid4()), "order_index": 1}
            ]
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "order_index" in response_data["message"].lower()

    def test_reorder_todos_negative_order_index(self, client: TestClient):
        """Test reordering with negative order_index."""
        # Arrange
        request_data = {
            "todo_orders": [
                {"todo_id": str(uuid4()), "order_index": -1},
                {"todo_id": str(uuid4()), "order_index": 0}
            ]
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"
        assert "order_index" in response_data["message"].lower()

    def test_reorder_todos_duplicate_todo_ids(self, client: TestClient, mock_todo_service):
        """Test reordering with duplicate TODO IDs."""
        # Arrange
        todo_id = str(uuid4())
        mock_todo_service.reorder_todos.return_value = {"updated_count": 1}

        request_data = {
            "todo_orders": [
                {"todo_id": todo_id, "order_index": 0},
                {"todo_id": todo_id, "order_index": 1}  # Duplicate
            ]
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        # Should handle duplicates - could be error or deduplicated
        assert response.status_code in [200, 400]

    def test_reorder_todos_duplicate_order_indices(self, client: TestClient, mock_todo_service):
        """Test reordering with duplicate order indices."""
        # Arrange
        mock_todo_service.reorder_todos.return_value = {"updated_count": 2}

        request_data = {
            "todo_orders": [
                {"todo_id": str(uuid4()), "order_index": 0},
                {"todo_id": str(uuid4()), "order_index": 0}  # Duplicate index
            ]
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        # Should be allowed - backend will handle tie-breaking
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 2

    def test_reorder_todos_non_sequential_indices(self, client: TestClient, mock_todo_service):
        """Test reordering with non-sequential order indices."""
        # Arrange
        mock_todo_service.reorder_todos.return_value = {"updated_count": 3}

        request_data = {
            "todo_orders": [
                {"todo_id": str(uuid4()), "order_index": 5},
                {"todo_id": str(uuid4()), "order_index": 10},
                {"todo_id": str(uuid4()), "order_index": 15}
            ]
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 3

    def test_reorder_todos_some_not_found(self, client: TestClient, mock_todo_service):
        """Test reordering when some TODOs don't exist."""
        # Arrange
        # Only 2 out of 3 TODOs found/updated
        mock_todo_service.reorder_todos.return_value = {"updated_count": 2}

        request_data = {
            "todo_orders": [
                {"todo_id": str(uuid4()), "order_index": 0},
                {"todo_id": str(uuid4()), "order_index": 1},
                {"todo_id": str(uuid4()), "order_index": 2}  # This one doesn't exist
            ]
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 2

    def test_reorder_todos_forbidden(self, client: TestClient, mock_todo_service, sample_todo_orders):
        """Test reordering when user doesn't own some TODOs."""
        # Arrange
        mock_todo_service.reorder_todos.side_effect = PermissionError("Access denied to some TODOs")

        request_data = {
            "todo_orders": sample_todo_orders
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 403
        response_data = response.json()
        assert response_data["error"] == "forbidden"

    def test_reorder_todos_malformed_json(self, client: TestClient):
        """Test reordering with malformed JSON."""
        # Arrange
        headers = {
            "Authorization": "Bearer valid_jwt_token",
            "Content-Type": "application/json"
        }

        # Act
        response = client.put("/api/todos/reorder", data="invalid json", headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"

    def test_reorder_todos_zero_updated(self, client: TestClient, mock_todo_service, sample_todo_orders):
        """Test reordering when no TODOs are actually updated."""
        # Arrange
        mock_todo_service.reorder_todos.return_value = {"updated_count": 0}

        request_data = {
            "todo_orders": sample_todo_orders
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 0

    def test_reorder_single_todo(self, client: TestClient, mock_todo_service):
        """Test reordering with single TODO (edge case)."""
        # Arrange
        mock_todo_service.reorder_todos.return_value = {"updated_count": 1}

        request_data = {
            "todo_orders": [
                {"todo_id": str(uuid4()), "order_index": 0}
            ]
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 1

    def test_reorder_todos_response_schema_validation(self, client: TestClient, mock_todo_service, sample_todo_orders):
        """Test that response matches expected schema exactly."""
        # Arrange
        mock_todo_service.reorder_todos.return_value = {"updated_count": 3}

        request_data = {
            "todo_orders": sample_todo_orders
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

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

    def test_reorder_todos_extra_fields_ignored(self, client: TestClient, mock_todo_service, sample_todo_orders):
        """Test that extra fields in request body are ignored."""
        # Arrange
        mock_todo_service.reorder_todos.return_value = {"updated_count": 3}

        request_data = {
            "todo_orders": sample_todo_orders,
            "extra_field": "should_be_ignored",
            "another_field": 123
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 3

    def test_reorder_todos_extra_fields_in_orders_ignored(self, client: TestClient, mock_todo_service):
        """Test that extra fields in todo_orders items are ignored."""
        # Arrange
        mock_todo_service.reorder_todos.return_value = {"updated_count": 2}

        request_data = {
            "todo_orders": [
                {
                    "todo_id": str(uuid4()),
                    "order_index": 0,
                    "extra_field": "ignored"
                },
                {
                    "todo_id": str(uuid4()),
                    "order_index": 1,
                    "title": "should_be_ignored"
                }
            ]
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] == 2

    def test_reorder_todos_wrong_data_types(self, client: TestClient):
        """Test reordering with wrong data types."""
        # Arrange
        request_data = {
            "todo_orders": [
                {"todo_id": str(uuid4()), "order_index": "not_a_number"},
                {"todo_id": 123, "order_index": 1}  # todo_id should be string
            ]
        }
        headers = {"Authorization": "Bearer valid_jwt_token"}

        # Act
        response = client.put("/api/todos/reorder", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"

    def test_reorder_todos_content_type_validation(self, client: TestClient, sample_todo_orders):
        """Test that endpoint requires application/json content type."""
        # Arrange
        import json
        request_data = json.dumps({"todo_orders": sample_todo_orders})
        headers = {
            "Authorization": "Bearer valid_jwt_token",
            "Content-Type": "text/plain"
        }

        # Act
        response = client.put("/api/todos/reorder", data=request_data, headers=headers)

        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"] == "validation_error"