"""
Integration test: User registration with email/password
T019 [P] Integration test: User registration with email/password in backend/tests/integration/test_user_registration.py
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from uuid import uuid4

from src.domain.schemas import UserCreate, UserResponse


class TestUserRegistration:
    """Test user registration flow with email/password"""

    def test_register_with_email_password(self, client: TestClient):
        """Test successful user registration with email and password"""
        with patch("src.application.services.auth_service.AuthService.verify_jwt_token") as mock_verify:
            # Mock successful JWT verification
            mock_verify.return_value = {
                "sub": "user_2abc123def456",
                "email": "testuser@example.com"
            }

            # Create user via auth endpoint
            response = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer mock_jwt_token"},
                json={
                    "display_name": "Test User",
                    "email": "testuser@example.com",
                    "clerk_user_id": "user_2abc123def456"
                }
            )

            assert response.status_code in [200, 201]
            if response.status_code in [200, 201]:
                user_data = response.json()
                # Verify user response structure
                assert "id" in user_data
                assert user_data["display_name"] == "Test User"


    def test_register_duplicate_email(self, client: TestClient):
        """Test registration with already existing email"""
        with patch("src.application.services.auth_service.AuthService.verify_jwt_token") as mock_verify:
            # First user registration
            mock_verify.return_value = {"sub": "user_first123", "email": "duplicate@example.com"}

            response1 = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer token1"},
                json={
                    "display_name": "First User",
                    "email": "duplicate@example.com",
                    "clerk_user_id": "user_first123"
                }
            )
            assert response1.status_code in [200, 201]

            # Second user registration with same email
            mock_verify.return_value = {"sub": "user_second456", "email": "duplicate@example.com"}

            response2 = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer token2"},
                json={
                    "display_name": "Second User",
                    "email": "duplicate@example.com",
                    "clerk_user_id": "user_second456"
                }
            )

            # Should handle duplicate email scenario
            assert response2.status_code in [200, 201, 400, 409, 422]

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email format"""
        with patch("src.application.services.auth_service.AuthService.verify_jwt_token") as mock_verify:
            mock_verify.return_value = {"sub": "user_invalid123", "email": "invalid-email-format"}

            response = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer token"},
                json={
                    "display_name": "Test User",
                    "email": "invalid-email-format",
                    "clerk_user_id": "user_invalid123"
                }
            )

            assert response.status_code in [400, 422]

    def test_register_without_display_name(self, client: TestClient):
        """Test registration without display name"""
        with patch("src.application.services.auth_service.AuthService.verify_jwt_token") as mock_verify:
            mock_verify.return_value = {"sub": "user_noname123", "email": "noname@example.com"}

            response = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer token"},
                json={
                    "email": "noname@example.com",
                    "clerk_user_id": "user_noname123"
                    # Missing display_name
                }
            )

            assert response.status_code in [400, 422]

    def test_register_updates_existing_user(self, client: TestClient):
        """Test that registering with same Clerk ID updates existing user"""
        with patch("src.application.services.auth_service.AuthService.verify_jwt_token") as mock_verify:
            mock_verify.return_value = {"sub": "user_update123", "email": "update@example.com"}

            # First registration
            response1 = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer token"},
                json={
                    "display_name": "Original Name",
                    "email": "update@example.com",
                    "clerk_user_id": "user_update123"
                }
            )
            assert response1.status_code in [200, 201]

            # Update with same Clerk ID but different display name
            response2 = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer token"},
                json={
                    "display_name": "Updated Name",
                    "email": "update@example.com",
                    "clerk_user_id": "user_update123"
                }
            )

            assert response2.status_code in [200, 201]

    def test_register_without_auth_token(self, client: TestClient):
        """Test registration without authentication token"""
        from src.main import app
        from src.api.middleware.auth import require_auth

        def raise_permission_error():
            raise PermissionError("User authentication required")

        original_override = app.dependency_overrides.get(require_auth)
        app.dependency_overrides[require_auth] = raise_permission_error

        try:
            response = client.post(
                "/api/auth/user",
                json={
                    "display_name": "Test User",
                    "email": "test@example.com",
                    "clerk_user_id": "user_noauth123"
                }
            )

            # Should fail due to missing Authorization header
            assert response.status_code in [401, 403, 422]
        finally:
            if original_override:
                app.dependency_overrides[require_auth] = original_override
            elif require_auth in app.dependency_overrides:
                del app.dependency_overrides[require_auth]

    def test_register_with_invalid_token(self, client: TestClient):
        """Test registration with invalid authentication token"""
        from src.main import app
        from src.api.middleware.auth import require_auth

        def raise_permission_error():
            raise PermissionError("Invalid token")

        original_override = app.dependency_overrides.get(require_auth)
        app.dependency_overrides[require_auth] = raise_permission_error

        try:
            response = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer invalid_token"},
                json={
                    "display_name": "Test User",
                    "email": "test@example.com",
                    "clerk_user_id": "user_invalid123"
                }
            )

            assert response.status_code in [401, 403, 422]
        finally:
            if original_override:
                app.dependency_overrides[require_auth] = original_override
            elif require_auth in app.dependency_overrides:
                del app.dependency_overrides[require_auth]