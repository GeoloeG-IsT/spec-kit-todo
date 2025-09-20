"""
Contract tests for POST /api/auth/session endpoint.

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
def mock_session_service():
    """Mock session service for testing."""
    with patch("src.api.routes.auth.SessionService") as mock_class:
        mock_instance = Mock()
        # Mock async methods with AsyncMock
        mock_instance.create_session = AsyncMock()
        mock_instance.get_session_by_id = AsyncMock()
        mock_instance.validate_session = AsyncMock()
        mock_instance.update_session_access = AsyncMock()
        mock_instance.delete_session = AsyncMock()
        mock_instance.cleanup_old_sessions = AsyncMock()
        mock_instance.get_session_stats = AsyncMock()
        mock_instance.is_session_valid = AsyncMock()
        mock_class.return_value = mock_instance
        yield mock_instance


class TestCreateGuestSession:
    """Test cases for POST /api/auth/session endpoint."""

    def test_create_session_success(self, client: TestClient, mock_session_service):
        """Test successful guest session creation."""
        # Arrange
        session_id = "sess_" + str(uuid4())
        mock_session = Mock()
        mock_session.id = session_id
        mock_session.created_at = datetime.now()
        mock_session.last_accessed_at = datetime.now()

        mock_session_service.create_session.return_value = mock_session

        session_data = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "ip_address": "192.168.1.100"
        }

        # Act
        response: Response = client.post("/api/auth/session", json=session_data)

        # Assert
        assert response.status_code == 201
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert "id" in data
        assert "created_at" in data
        assert "last_accessed_at" in data
        assert isinstance(data["id"], str)
        assert len(data["id"]) > 0

        mock_session_service.create_session.assert_called_once()

    def test_create_session_minimal_data(self, client: TestClient, mock_session_service):
        """Test session creation with minimal required data."""
        # Arrange
        session_id = "sess_" + str(uuid4())
        mock_session = Mock()
        mock_session.id = session_id
        mock_session.created_at = datetime.now()
        mock_session.last_accessed_at = datetime.now()

        mock_session_service.create_session.return_value = mock_session

        session_data = {}

        # Act
        response: Response = client.post("/api/auth/session", json=session_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "created_at" in data
        assert "last_accessed_at" in data

        mock_session_service.create_session.assert_called_once()

    def test_create_session_with_user_agent_only(self, client: TestClient, mock_session_service):
        """Test session creation with only user agent."""
        # Arrange
        session_id = "sess_" + str(uuid4())
        mock_session = Mock()
        mock_session.id = session_id
        mock_session.created_at = datetime.now()
        mock_session.last_accessed_at = datetime.now()

        mock_session_service.create_session.return_value = mock_session

        session_data = {
            "user_agent": "Mozilla/5.0 Custom Browser"
        }

        # Act
        response: Response = client.post("/api/auth/session", json=session_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "id" in data

        mock_session_service.create_session.assert_called_once()

    def test_create_session_invalid_json(self, client: TestClient):
        """Test session creation with invalid JSON."""
        # Act
        response: Response = client.post(
            "/api/auth/session",
            data="invalid json",
            headers={"content-type": "application/json"}
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "validation_error"
        assert "message" in data

    def test_create_session_wrong_content_type(self, client: TestClient):
        """Test session creation with wrong content type."""
        # Act
        response: Response = client.post(
            "/api/auth/session",
            data="user_agent=browser",
            headers={"content-type": "application/x-www-form-urlencoded"}
        )

        # Assert
        assert response.status_code == 422

    def test_create_session_empty_request_body(self, client: TestClient, mock_session_service):
        """Test session creation with empty request body."""
        # Arrange
        session_id = "sess_" + str(uuid4())
        mock_session = Mock()
        mock_session.id = session_id
        mock_session.created_at = datetime.now()
        mock_session.last_accessed_at = datetime.now()

        mock_session_service.create_session.return_value = mock_session

        # Act
        response: Response = client.post("/api/auth/session", json={})

        # Assert
        # Should work with empty JSON as all fields are optional
        assert response.status_code == 201
        data = response.json()
        assert "id" in data

        mock_session_service.create_session.assert_called_once()

    def test_session_id_uniqueness(self, client: TestClient, mock_session_service):
        """Test that each session gets a unique ID."""
        # Arrange
        session_id1 = "sess_" + str(uuid4())
        session_id2 = "sess_" + str(uuid4())

        mock_session1 = Mock()
        mock_session1.id = session_id1
        mock_session1.created_at = datetime.now()
        mock_session1.last_accessed_at = datetime.now()

        mock_session2 = Mock()
        mock_session2.id = session_id2
        mock_session2.created_at = datetime.now()
        mock_session2.last_accessed_at = datetime.now()

        mock_session_service.create_session.side_effect = [mock_session1, mock_session2]

        session_data = {"user_agent": "Test Browser"}

        # Act
        response1: Response = client.post("/api/auth/session", json=session_data)
        response2: Response = client.post("/api/auth/session", json=session_data)

        # Assert
        assert response1.status_code == 201
        assert response2.status_code == 201

        data1 = response1.json()
        data2 = response2.json()

        assert data1["id"] != data2["id"]
        assert mock_session_service.create_session.call_count == 2

    def test_session_response_schema(self, client: TestClient, mock_session_service):
        """Test that response matches the SessionResponse schema."""
        # Arrange
        session_id = "sess_" + str(uuid4())
        mock_session = Mock()
        mock_session.id = session_id
        mock_session.created_at = datetime.now()
        mock_session.last_accessed_at = datetime.now()

        mock_session_service.create_session.return_value = mock_session

        session_data = {
            "user_agent": "Schema Test Browser",
            "ip_address": "10.0.0.1"
        }

        # Act
        response: Response = client.post("/api/auth/session", json=session_data)

        # Assert
        assert response.status_code == 201
        data = response.json()

        # Required fields from SessionResponse schema
        required_fields = ["id", "created_at", "last_accessed_at"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Field types
        assert isinstance(data["id"], str)
        assert isinstance(data["created_at"], str)
        assert isinstance(data["last_accessed_at"], str)

        # No extra fields
        assert len(data) == len(required_fields)

        mock_session_service.create_session.assert_called_once()

    def test_create_session_long_user_agent(self, client: TestClient, mock_session_service):
        """Test session creation with very long user agent string."""
        # Arrange
        session_id = "sess_" + str(uuid4())
        mock_session = Mock()
        mock_session.id = session_id
        mock_session.created_at = datetime.now()
        mock_session.last_accessed_at = datetime.now()

        mock_session_service.create_session.return_value = mock_session

        long_user_agent = "Mozilla/5.0 " + "A" * 2000  # Very long user agent
        session_data = {"user_agent": long_user_agent}

        # Act
        response: Response = client.post("/api/auth/session", json=session_data)

        # Assert
        # Should handle long user agents gracefully
        assert response.status_code in [201, 422]  # Either succeed or validate length

        if response.status_code == 201:
            mock_session_service.create_session.assert_called_once()

    def test_create_session_invalid_ip_address(self, client: TestClient, mock_session_service):
        """Test session creation with invalid IP address format."""
        # Arrange
        session_id = "sess_" + str(uuid4())
        mock_session = Mock()
        mock_session.id = session_id
        mock_session.created_at = datetime.now()
        mock_session.last_accessed_at = datetime.now()

        mock_session_service.create_session.return_value = mock_session

        session_data = {
            "user_agent": "Test Browser",
            "ip_address": "not.an.ip.address"
        }

        # Act
        response: Response = client.post("/api/auth/session", json=session_data)

        # Assert
        # Should either accept as string or validate IP format
        assert response.status_code in [201, 422]

        if response.status_code == 201:
            mock_session_service.create_session.assert_called_once()