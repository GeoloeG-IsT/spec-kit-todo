import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from uuid import uuid4

from src.application.services.auth_service import AuthService
from src.domain.models.user import User
from src.domain.models.session import Session
from src.domain.schemas import SessionCreate, SessionConvertRequest


class TestAuthService:
    """Unit tests for AuthService"""

    @pytest.fixture
    def mock_session(self):
        """Mock database session"""
        session = AsyncMock()
        return session

    @pytest.fixture
    def auth_service(self):
        """AuthService instance"""
        return AuthService()

    @pytest.fixture
    def sample_session_data(self):
        """Sample session data for testing"""
        return {
            "id": "session_test123",
            "created_at": datetime.utcnow(),
            "last_accessed_at": datetime.utcnow(),
            "expires_at": None,
            "user_agent": "Mozilla/5.0 Test Browser",
            "ip_address": "192.168.1.1",
        }

    @pytest.fixture
    def sample_session(self, sample_session_data):
        """Sample Session model instance"""
        return Session(**sample_session_data)

    @pytest.fixture
    def sample_user(self):
        """Sample User model instance"""
        return User(
            id=uuid4(),
            clerk_user_id="user_test123",
            display_name="Test User",
            email="test@example.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    # TODO: AuthService doesn't have create_session method - this functionality is in a separate service
    # @pytest.mark.asyncio
    # async def test_create_session_success(self, auth_service, mock_session):
    #     pass

    # TODO: AuthService doesn't have get_session_by_id method
    # @pytest.mark.asyncio
    # async def test_get_session_by_id_success(self, auth_service, mock_session, sample_session):
    #     pass

    # TODO: AuthService doesn't have get_session_by_id method
    # @pytest.mark.asyncio
    # async def test_get_session_by_id_not_found(self, auth_service, mock_session):
    #     pass

    # TODO: AuthService doesn't have update_session_access_time method
    # @pytest.mark.asyncio
    # async def test_update_session_access_time(self, auth_service, mock_session, sample_session):
    #     pass

    # TODO: AuthService doesn't have update_session_access_time method
    # @pytest.mark.asyncio
    # async def test_update_session_access_time_not_found(self, auth_service, mock_session):
    #     pass

    @pytest.mark.asyncio
    async def test_verify_clerk_token_valid(self, auth_service):
        """Test Clerk token verification with valid token"""
        mock_token = "valid_jwt_token"
        mock_payload = {
            "sub": "user_test123",
            "email": "test@example.com",
            "given_name": "Test",
            "family_name": "User",
            "exp": 9999999999,  # Far future expiration
        }

        with patch('src.application.services.auth_service.jwt') as mock_jwt:
            # Mock JWT decode
            mock_jwt.decode.return_value = mock_payload

            result = await auth_service.verify_jwt_token(mock_token)

            assert result == mock_payload
            mock_jwt.decode.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_clerk_token_invalid(self, auth_service):
        """Test Clerk token verification with invalid token"""
        mock_token = "invalid_jwt_token"

        with patch('src.application.services.auth_service.jwt') as mock_jwt:
            mock_jwt.decode.side_effect = Exception("Invalid token")

            result = await auth_service.verify_jwt_token(mock_token)
            assert result is None

    # TODO: AuthService doesn't have convert_session_to_user method
    # @pytest.mark.asyncio
    # async def test_convert_session_to_user_success(self, auth_service, mock_session, sample_session, sample_user):
    #     pass

    # TODO: AuthService doesn't have convert_session_to_user method
    # @pytest.mark.asyncio
    # async def test_convert_session_to_user_session_not_found(self, auth_service, mock_session, sample_user):
    #     pass

    # TODO: AuthService doesn't have delete_session method
    # @pytest.mark.asyncio
    # async def test_delete_session_success(self, auth_service, mock_session, sample_session):
    #     pass

    # TODO: AuthService doesn't have delete_session method
    # @pytest.mark.asyncio
    # async def test_delete_session_not_found(self, auth_service, mock_session):
    #     pass

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, auth_service, mock_session):
        """Test cleanup of expired sessions"""
        expired_sessions = [Mock(spec=Session) for _ in range(3)]
        mock_session.exec.return_value.all.return_value = expired_sessions
        mock_session.commit = AsyncMock()

        with patch('src.application.services.auth_service.select') as mock_select, \
             patch('src.application.services.auth_service.datetime') as mock_datetime:
            mock_now = datetime.utcnow()
            mock_datetime.utcnow.return_value = mock_now

            result = await auth_service.cleanup_expired_sessions(mock_session)

            assert result == len(expired_sessions)
            for session in expired_sessions:
                mock_session.delete.assert_any_call(session)

    @pytest.mark.asyncio
    async def test_get_session_stats(self, auth_service, mock_session):
        """Test getting session statistics"""
        mock_session.exec.return_value.scalar.side_effect = [10, 5, 2]  # total, active, expired

        with patch('src.application.services.auth_service.select') as mock_select, \
             patch('src.application.services.auth_service.func') as mock_func:

            result = await auth_service.get_session_stats(mock_session)

            assert "total_sessions" in result
            assert "active_sessions" in result
            assert "expired_sessions" in result
            assert result["total_sessions"] == 10
            assert result["active_sessions"] == 5
            assert result["expired_sessions"] == 2

    @pytest.mark.asyncio
    async def test_validate_session_ownership_success(self, auth_service, mock_session, sample_session):
        """Test session ownership validation with valid session"""
        mock_session.get.return_value = sample_session

        result = await auth_service.validate_session_ownership(
            sample_session.id, "192.168.1.1", "Mozilla/5.0 Test Browser", mock_session
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_validate_session_ownership_mismatch(self, auth_service, mock_session, sample_session):
        """Test session ownership validation with mismatched details"""
        mock_session.get.return_value = sample_session

        # Different IP address
        result = await auth_service.validate_session_ownership(
            sample_session.id, "10.0.0.1", "Mozilla/5.0 Test Browser", mock_session
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_from_token_success(self, auth_service, mock_session, sample_user):
        """Test getting user from valid Clerk token"""
        mock_token = "valid_jwt_token"
        mock_payload = {"sub": sample_user.clerk_user_id}

        with patch.object(auth_service, 'verify_clerk_token') as mock_verify:
            mock_verify.return_value = mock_payload
            mock_session.exec.return_value.first.return_value = sample_user

            with patch('src.application.services.auth_service.select') as mock_select:
                result = await auth_service.get_user_from_token(mock_token, mock_session)

                assert result == sample_user
                mock_verify.assert_called_once_with(mock_token)

    @pytest.mark.asyncio
    async def test_get_user_from_token_invalid_token(self, auth_service, mock_session):
        """Test getting user from invalid token"""
        mock_token = "invalid_jwt_token"

        with patch.object(auth_service, 'verify_clerk_token') as mock_verify:
            mock_verify.return_value = None

            result = await auth_service.get_user_from_token(mock_token, mock_session)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_user_from_token_user_not_found(self, auth_service, mock_session):
        """Test getting user from token when user doesn't exist in database"""
        mock_token = "valid_jwt_token"
        mock_payload = {"sub": "nonexistent_user"}

        with patch.object(auth_service, 'verify_clerk_token') as mock_verify:
            mock_verify.return_value = mock_payload
            mock_session.exec.return_value.first.return_value = None

            with patch('src.application.services.auth_service.select') as mock_select:
                result = await auth_service.get_user_from_token(mock_token, mock_session)
                assert result is None

    @pytest.mark.asyncio
    async def test_refresh_session_success(self, auth_service, mock_session, sample_session):
        """Test session refresh"""
        mock_session.get.return_value = sample_session
        mock_session.commit = AsyncMock()

        with patch('src.application.services.auth_service.datetime') as mock_datetime:
            mock_now = datetime.utcnow()
            mock_datetime.utcnow.return_value = mock_now

            result = await auth_service.refresh_session(sample_session.id, mock_session)

            assert result.last_accessed_at == mock_now
            mock_session.commit.assert_called_once()

    @pytest.mark.parametrize("invalid_data", [
        {"user_agent": "", "ip_address": "192.168.1.1"},
        {"user_agent": "valid", "ip_address": ""},
        {"user_agent": None, "ip_address": "192.168.1.1"},
    ])
    def test_session_validation_errors(self, invalid_data):
        """Test session creation with invalid data"""
        with pytest.raises((ValueError, TypeError)):
            SessionCreate(**invalid_data)

    @pytest.mark.asyncio
    async def test_get_sessions_by_user_agent(self, auth_service, mock_session):
        """Test getting sessions by user agent pattern"""
        user_agent_pattern = "Mozilla/5.0%"
        mock_sessions = [Mock(spec=Session) for _ in range(2)]
        mock_session.exec.return_value.all.return_value = mock_sessions

        with patch('src.application.services.auth_service.select') as mock_select:
            result = await auth_service.get_sessions_by_user_agent(user_agent_pattern, mock_session)

            assert result == mock_sessions
            mock_session.exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limit_check_success(self, auth_service, mock_session):
        """Test rate limiting check for session creation"""
        ip_address = "192.168.1.1"
        mock_session.exec.return_value.scalar.return_value = 2  # Under limit

        with patch('src.application.services.auth_service.select') as mock_select, \
             patch('src.application.services.auth_service.func') as mock_func, \
             patch('src.application.services.auth_service.datetime') as mock_datetime:

            result = await auth_service.check_rate_limit(ip_address, mock_session, limit=5)
            assert result is True

    @pytest.mark.asyncio
    async def test_rate_limit_check_exceeded(self, auth_service, mock_session):
        """Test rate limiting check when limit is exceeded"""
        ip_address = "192.168.1.1"
        mock_session.exec.return_value.scalar.return_value = 6  # Over limit

        with patch('src.application.services.auth_service.select') as mock_select, \
             patch('src.application.services.auth_service.func') as mock_func, \
             patch('src.application.services.auth_service.datetime') as mock_datetime:

            result = await auth_service.check_rate_limit(ip_address, mock_session, limit=5)
            assert result is False