"""
Contract tests for POST /api/auth/session endpoint.

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


class TestCreateGuestSession:
    """Test cases for POST /api/auth/session endpoint."""

    def test_create_session_success(self, client: TestClient):
        """Test successful guest session creation."""
        # Arrange
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

        # Verify ISO datetime format
        from datetime import datetime
        datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        datetime.fromisoformat(data["last_accessed_at"].replace("Z", "+00:00"))

    def test_create_session_minimal_data(self, client: TestClient):
        """Test session creation with minimal required data."""
        # Arrange
        session_data = {}

        # Act
        response: Response = client.post("/api/auth/session", json=session_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "created_at" in data
        assert "last_accessed_at" in data

    def test_create_session_with_user_agent_only(self, client: TestClient):
        """Test session creation with only user agent."""
        # Arrange
        session_data = {
            "user_agent": "Mozilla/5.0 Custom Browser"
        }

        # Act
        response: Response = client.post("/api/auth/session", json=session_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "id" in data

    def test_create_session_invalid_json(self, client: TestClient):
        """Test session creation with invalid JSON."""
        # Act
        response: Response = client.post(
            "/api/auth/session",
            data="invalid json",
            headers={"content-type": "application/json"}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
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
        assert response.status_code == 400

    def test_create_session_empty_request_body(self, client: TestClient):
        """Test session creation with empty request body."""
        # Act
        response: Response = client.post("/api/auth/session")

        # Assert
        # Should still work as all fields are optional
        assert response.status_code == 201
        data = response.json()
        assert "id" in data

    def test_session_id_uniqueness(self, client: TestClient):
        """Test that each session gets a unique ID."""
        # Arrange
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

    def test_session_response_schema(self, client: TestClient):
        """Test that response matches the SessionResponse schema."""
        # Arrange
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

    def test_create_session_long_user_agent(self, client: TestClient):
        """Test session creation with very long user agent string."""
        # Arrange
        long_user_agent = "Mozilla/5.0 " + "A" * 2000  # Very long user agent
        session_data = {"user_agent": long_user_agent}

        # Act
        response: Response = client.post("/api/auth/session", json=session_data)

        # Assert
        # Should handle long user agents gracefully
        assert response.status_code in [201, 400]  # Either succeed or validate length

    def test_create_session_invalid_ip_address(self, client: TestClient):
        """Test session creation with invalid IP address format."""
        # Arrange
        session_data = {
            "user_agent": "Test Browser",
            "ip_address": "not.an.ip.address"
        }

        # Act
        response: Response = client.post("/api/auth/session", json=session_data)

        # Assert
        # Should either accept as string or validate IP format
        assert response.status_code in [201, 400]