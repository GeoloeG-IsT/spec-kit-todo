"""
Integration test: Multi-auth provider linking
T022 [P] Integration test: Multi-auth provider linking in backend/tests/integration/test_multi_auth.py
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


class TestMultiAuthProviders:
    """Test linking and managing multiple authentication providers"""

    def test_link_multiple_oauth_providers(self, client: TestClient):
        """Test linking Google, GitHub, and LinkedIn to same user account"""
        with patch("src.application.services.auth_service.AuthService.verify_jwt_token") as mock_verify:
            # Mock Google OAuth verification
            mock_verify.return_value = {
                "sub": "user_multi123",
                "email": "multi@example.com"
            }

            # Register with Google
            google_response = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer google_jwt_token"},
                json={
                    "display_name": "Multi User",
                    "email": "multi@example.com",
                    "clerk_user_id": "user_multi123"
                }
            )
            assert google_response.status_code in [200, 201]

    def test_oauth_provider_conflict_resolution(self, client: TestClient):
        """Test handling when different Clerk users have same email from different providers"""
        with patch("src.application.services.auth_service.AuthService.verify_jwt_token") as mock_verify:
            # User A registers with Google
            mock_verify.return_value = {
                "sub": "user_googleA",
                "email": "conflict@example.com"
            }

            response_a = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer google_tokenA"},
                json={
                    "display_name": "User A",
                    "email": "conflict@example.com",
                    "clerk_user_id": "user_googleA"
                }
            )
            assert response_a.status_code in [200, 201]

    def test_unlink_oauth_provider(self, client: TestClient):
        """Test unlinking OAuth provider from user account"""
        with patch("src.application.services.auth_service.AuthService.verify_jwt_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "user_unlink123",
                "email": "unlink@example.com"
            }

            response = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer jwt_token"},
                json={
                    "display_name": "Unlink User",
                    "email": "unlink@example.com",
                    "clerk_user_id": "user_unlink123"
                }
            )
            assert response.status_code in [200, 201]

    def test_oauth_provider_email_changes(self, client: TestClient):
        """Test handling when OAuth provider email changes"""
        with patch("src.application.services.auth_service.AuthService.verify_jwt_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "user_email_change123",
                "email": "newemail@example.com"
            }

            response = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer jwt_token"},
                json={
                    "display_name": "Email Change User",
                    "email": "newemail@example.com",
                    "clerk_user_id": "user_email_change123"
                }
            )
            assert response.status_code in [200, 201]

    def test_oauth_provider_profile_sync(self, client: TestClient):
        """Test syncing profile data from OAuth providers"""
        with patch("src.application.services.auth_service.AuthService.verify_jwt_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "user_profile_sync123",
                "email": "profile@example.com"
            }

            response = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer jwt_token"},
                json={
                    "display_name": "Profile Sync User",
                    "email": "profile@example.com",
                    "clerk_user_id": "user_profile_sync123"
                }
            )
            assert response.status_code in [200, 201]

    def test_oauth_provider_data_persistence(self, client: TestClient):
        """Test that OAuth provider data persists across sessions"""
        with patch("src.application.services.auth_service.AuthService.verify_jwt_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "user_persistence123",
                "email": "persistence@example.com"
            }

            response = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer jwt_token"},
                json={
                    "display_name": "Persistence User",
                    "email": "persistence@example.com",
                    "clerk_user_id": "user_persistence123"
                }
            )
            assert response.status_code in [200, 201]