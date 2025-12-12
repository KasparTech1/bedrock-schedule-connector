"""
Authentication Tests
====================

Tests for API key and JWT authentication.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from kai_erp.api.main import app
from kai_erp.api.auth import (
    APIKey,
    APIKeyManager,
    APIScope,
    get_key_manager,
)
from kai_erp.api.jwt_auth import (
    create_access_token,
    create_refresh_token,
    create_tokens,
    verify_token,
    TokenPayload,
)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def key_manager():
    """Create a fresh key manager for testing."""
    return APIKeyManager()


class TestAPIKeyManager:
    """Tests for APIKeyManager."""
    
    def test_create_key_returns_tuple(self, key_manager):
        """Creating a key should return (key_id, secret_key)."""
        key_id, secret_key = key_manager.create_key(
            name="Test Key",
            owner="test@example.com",
        )
        
        assert key_id.startswith("kai_live_")
        assert len(secret_key) > 20
    
    def test_validate_key_success(self, key_manager):
        """Valid key should be validated successfully."""
        key_id, secret_key = key_manager.create_key(
            name="Test Key",
            owner="test@example.com",
        )
        
        validated = key_manager.validate_key(secret_key)
        
        assert validated is not None
        assert validated.key_id == key_id
        assert validated.name == "Test Key"
    
    def test_validate_key_invalid(self, key_manager):
        """Invalid key should return None."""
        result = key_manager.validate_key("invalid_key_here")
        assert result is None
    
    def test_validate_key_inactive(self, key_manager):
        """Inactive key should return None."""
        key_id, secret_key = key_manager.create_key(
            name="Test Key",
            owner="test@example.com",
        )
        
        # Revoke the key
        key_manager.revoke_key(key_id)
        
        result = key_manager.validate_key(secret_key)
        assert result is None
    
    def test_validate_key_expired(self, key_manager):
        """Expired key should return None."""
        key_id, secret_key = key_manager.create_key(
            name="Test Key",
            owner="test@example.com",
            expires_in_days=0,  # Already expired
        )
        
        # Manually set expiration to past
        api_key = key_manager.get_key(key_id)
        api_key.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        
        result = key_manager.validate_key(secret_key)
        assert result is None
    
    def test_key_has_scope(self, key_manager):
        """Key should correctly report scope membership."""
        key_id, _ = key_manager.create_key(
            name="Test Key",
            owner="test@example.com",
            scopes=[APIScope.READ_CUSTOMERS, APIScope.READ_ORDERS],
        )
        
        api_key = key_manager.get_key(key_id)
        
        assert api_key.has_scope(APIScope.READ_CUSTOMERS)
        assert api_key.has_scope(APIScope.READ_ORDERS)
        assert not api_key.has_scope(APIScope.READ_INVENTORY)
    
    def test_key_all_scope_grants_everything(self, key_manager):
        """Key with ALL scope should have access to everything."""
        key_id, _ = key_manager.create_key(
            name="Admin Key",
            owner="admin@example.com",
            scopes=[APIScope.ALL],
        )
        
        api_key = key_manager.get_key(key_id)
        
        assert api_key.has_scope(APIScope.READ_CUSTOMERS)
        assert api_key.has_scope(APIScope.READ_INVENTORY)
        assert api_key.has_scope(APIScope.ADMIN)


class TestAPIKeyRateLimiting:
    """Tests for API key rate limiting."""
    
    def test_rate_limit_allows_within_limit(self, key_manager):
        """Requests within rate limit should be allowed."""
        key_id, _ = key_manager.create_key(
            name="Test Key",
            owner="test@example.com",
            rate_limit_per_minute=10,
        )
        
        api_key = key_manager.get_key(key_id)
        
        for _ in range(10):
            assert api_key.check_rate_limit()
            api_key.record_request()
    
    def test_rate_limit_blocks_over_limit(self, key_manager):
        """Requests over rate limit should be blocked."""
        key_id, _ = key_manager.create_key(
            name="Test Key",
            owner="test@example.com",
            rate_limit_per_minute=5,
        )
        
        api_key = key_manager.get_key(key_id)
        
        # Use up the limit
        for _ in range(5):
            api_key.record_request()
        
        assert not api_key.check_rate_limit()


class TestJWTAuth:
    """Tests for JWT authentication."""
    
    def test_create_access_token(self):
        """Should create a valid access token."""
        token = create_access_token(
            subject="user123",
            scopes=["read", "write"],
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_verify_token_success(self):
        """Should verify a valid token."""
        token = create_access_token(
            subject="user123",
            scopes=["read", "write"],
        )
        
        payload = verify_token(token)
        
        assert payload.sub == "user123"
        assert "read" in payload.scopes
        assert "write" in payload.scopes
        assert payload.type == "access"
    
    def test_verify_token_invalid(self):
        """Should reject an invalid token."""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid.token.here")
        
        assert exc_info.value.status_code == 401
    
    def test_create_refresh_token(self):
        """Should create a refresh token."""
        token = create_refresh_token(subject="user123")
        
        payload = verify_token(token)
        
        assert payload.sub == "user123"
        assert payload.type == "refresh"
    
    def test_create_tokens_returns_both(self):
        """create_tokens should return access and refresh tokens."""
        response = create_tokens(
            subject="user123",
            scopes=["read"],
        )
        
        assert response.access_token is not None
        assert response.refresh_token is not None
        assert response.token_type == "bearer"
        assert response.expires_in > 0
        assert "read" in response.scopes


class TestAuthEndpoints:
    """Tests for authentication API endpoints."""
    
    def test_auth_token_with_valid_key(self, client):
        """Should return JWT tokens for valid API key."""
        # Get the default dev key
        manager = get_key_manager()
        _, secret_key = manager.create_key(
            name="Test Key",
            owner="test@example.com",
        )
        
        response = client.post(
            "/auth/token",
            json={"api_key": secret_key},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_auth_token_with_invalid_key(self, client):
        """Should return 401 for invalid API key."""
        response = client.post(
            "/auth/token",
            json={"api_key": "invalid_key_here"},
        )
        
        assert response.status_code == 401
    
    def test_auth_me_with_jwt(self, client):
        """Should return user info with valid JWT."""
        # Get a token first
        manager = get_key_manager()
        _, secret_key = manager.create_key(
            name="Test Key",
            owner="test@example.com",
        )
        
        # Get JWT
        token_response = client.post(
            "/auth/token",
            json={"api_key": secret_key},
        )
        access_token = token_response.json()["access_token"]
        
        # Use JWT to get user info
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["auth_method"] == "jwt"
    
    def test_auth_me_with_api_key(self, client):
        """Should return user info with valid API key."""
        manager = get_key_manager()
        _, secret_key = manager.create_key(
            name="Test Key",
            owner="test@example.com",
        )
        
        response = client.get(
            "/auth/me",
            headers={"X-API-Key": secret_key},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["auth_method"] == "api_key"
    
    def test_auth_me_without_auth(self, client):
        """Should return 401 without authentication."""
        response = client.get("/auth/me")
        assert response.status_code == 401
    
    def test_auth_refresh_with_valid_token(self, client):
        """Should refresh token successfully."""
        # Get initial tokens
        manager = get_key_manager()
        _, secret_key = manager.create_key(
            name="Test Key",
            owner="test@example.com",
        )
        
        token_response = client.post(
            "/auth/token",
            json={"api_key": secret_key},
        )
        refresh_token = token_response.json()["refresh_token"]
        
        # Refresh
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    def test_auth_refresh_with_access_token_fails(self, client):
        """Should fail when using access token as refresh token."""
        manager = get_key_manager()
        _, secret_key = manager.create_key(
            name="Test Key",
            owner="test@example.com",
        )
        
        token_response = client.post(
            "/auth/token",
            json={"api_key": secret_key},
        )
        access_token = token_response.json()["access_token"]
        
        # Try to use access token as refresh token
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": access_token},
        )
        
        assert response.status_code == 400


