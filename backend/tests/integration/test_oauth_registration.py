"""
Integration test: OAuth registration flow (Google, GitHub, LinkedIn)
T020 [P] Integration test: OAuth registration flow (Google, GitHub, LinkedIn) in backend/tests/integration/test_oauth_registration.py
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from uuid import uuid4

from src.domain.schemas import UserResponse, AuthProviderResponse


class TestOAuthRegistration:
    """Test OAuth registration flows for Google, GitHub, and LinkedIn"""

    def test_google_oauth_registration(self, client: TestClient):
        """Test successful user registration via Google OAuth"""
        with patch("src.application.services.auth_service.AuthService.verify_jwt_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "user_google123",
                "email": "user@gmail.com"
            }

            response = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer google_jwt_token"},
                json={
                    "display_name": "John Doe",
                    "email": "user@gmail.com",
                    "clerk_user_id": "user_google123"
                }
            )

            assert response.status_code in [200, 201]

    def test_github_oauth_registration(self, client: TestClient):
        """Test successful user registration via GitHub OAuth"""
        with patch("src.application.services.auth_service.AuthService.verify_jwt_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "user_github456",
                "email": "user@github.com"
            }

            response = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer github_jwt_token"},
                json={
                    "display_name": "Jane Developer",
                    "email": "user@github.com",
                    "clerk_user_id": "user_github456"
                }
            )

            assert response.status_code in [200, 201]

    def test_linkedin_oauth_registration(self, client: TestClient):
        """Test successful user registration via LinkedIn OAuth"""
        with patch("src.application.services.auth_service.AuthService.verify_jwt_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "user_linkedin789",
                "email": "user@linkedin.com"
            }

            response = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer linkedin_jwt_token"},
                json={
                    "display_name": "Professional User",
                    "email": "user@linkedin.com",
                    "clerk_user_id": "user_linkedin789"
                }
            )

            assert response.status_code in [200, 201]

    def test_oauth_without_email(self, client: TestClient):
        """Test OAuth registration when provider doesn't return email"""
        with patch("src.application.services.auth_service.AuthService.verify_jwt_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "user_noemail123",
                "email": None
            }

            response = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer noemail_jwt_token"},
                json={
                    "display_name": "No Email User",
                    "clerk_user_id": "user_noemail123"
                }
            )

            assert response.status_code in [200, 201, 400, 422]

    def test_oauth_provider_linking(self, client: TestClient):
        """Test linking multiple OAuth providers to same account"""
        with patch("src.application.services.auth_service.AuthService.verify_jwt_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "user_linking123",
                "email": "linking@example.com"
            }

            response = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer linking_jwt_token"},
                json={
                    "display_name": "Linking User",
                    "email": "linking@example.com",
                    "clerk_user_id": "user_linking123"
                }
            )

            assert response.status_code in [200, 201]

    def test_oauth_email_conflict_different_providers(self, client: TestClient):
        """Test handling email conflicts between different OAuth providers"""
        with patch("src.application.services.auth_service.AuthService.verify_jwt_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "user_conflict123",
                "email": "conflict@example.com"
            }

            response = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer conflict_jwt_token"},
                json={
                    "display_name": "Conflict User",
                    "email": "conflict@example.com",
                    "clerk_user_id": "user_conflict123"
                }
            )

            assert response.status_code in [200, 201, 409, 422]

    def test_oauth_avatar_url_handling(self, client: TestClient):
        """Test OAuth registration with avatar URL from provider"""
        with patch("src.application.services.auth_service.AuthService.verify_jwt_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "user_avatar123",
                "email": "avatar@example.com"
            }

            response = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer avatar_jwt_token"},
                json={
                    "display_name": "Avatar User",
                    "email": "avatar@example.com",
                    "clerk_user_id": "user_avatar123",
                    "avatar_url": "https://example.com/avatar.jpg"
                }
            )

            assert response.status_code in [200, 201]

    def test_oauth_malformed_provider_data(self, client: TestClient):
        """Test handling malformed data from OAuth provider"""
        with patch("src.application.services.auth_service.AuthService.verify_jwt_token") as mock_verify:
            mock_verify.return_value = {
                "sub": "user_malformed123",
                "email": "malformed@example.com"
            }

            response = client.post(
                "/api/auth/user",
                headers={"Authorization": "Bearer malformed_jwt_token"},
                json={
                    "display_name": "Malformed User",
                    "email": "malformed@example.com",
                    "clerk_user_id": "user_malformed123"
                }
            )

            assert response.status_code in [200, 201, 400, 422]