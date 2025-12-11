"""
Authentication & Token Management
=================================

Handles OAuth2 token acquisition and refresh for SyteLine 10 REST APIs.

Key features:
- Token caching with automatic refresh
- Thread-safe token access
- Retry on 401 errors
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
import structlog

from kai_erp.config import SyteLineConfig
from kai_erp.core.types import AuthenticationError, TokenInfo

logger = structlog.get_logger(__name__)


class TokenManager:
    """
    Manages OAuth2 tokens for SyteLine REST API access.
    
    Tokens are cached and automatically refreshed before expiry.
    Thread-safe for concurrent async access.
    
    Example:
        async with TokenManager(config) as token_mgr:
            token = await token_mgr.get_token()
            headers = {"Authorization": f"Bearer {token}"}
    """
    
    # Refresh token this many minutes before expiry
    REFRESH_BUFFER_MINUTES = 5
    
    # Token lifetime (SyteLine tokens last 60 minutes)
    TOKEN_LIFETIME_MINUTES = 60
    
    def __init__(self, config: SyteLineConfig):
        """
        Initialize token manager.
        
        Args:
            config: SyteLine configuration with credentials
        """
        self.config = config
        self._token: Optional[TokenInfo] = None
        self._lock = asyncio.Lock()
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self) -> "TokenManager":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def get_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.
        
        Returns:
            Valid access token string
        
        Raises:
            AuthenticationError: If token acquisition fails
        """
        async with self._lock:
            if self._should_refresh():
                await self._acquire_token()
            
            if not self._token:
                raise AuthenticationError("No token available")
            
            return self._token.access_token
    
    async def get_auth_header(self) -> dict[str, str]:
        """
        Get Authorization header with valid token.
        
        Returns:
            Dict with Authorization header
        """
        token = await self.get_token()
        return {"Authorization": f"Bearer {token}"}
    
    async def invalidate(self) -> None:
        """
        Invalidate current token (e.g., after 401 error).
        
        Next call to get_token() will acquire a new token.
        """
        async with self._lock:
            self._token = None
            logger.info("Token invalidated")
    
    def _should_refresh(self) -> bool:
        """Check if token needs refresh."""
        if not self._token:
            return True
        
        # Refresh if within buffer of expiry
        refresh_at = self._token.expires_at - timedelta(minutes=self.REFRESH_BUFFER_MINUTES)
        return datetime.now(timezone.utc) >= refresh_at
    
    async def _acquire_token(self) -> None:
        """
        Acquire a new OAuth2 token from SyteLine.
        
        SyteLine 10 uses Basic Auth to the token endpoint.
        """
        if not self._client:
            raise AuthenticationError("TokenManager not initialized (use async with)")
        
        token_url = f"{self.config.base_url}/IDORequestService/ido/token"
        
        logger.info("Acquiring new token", url=token_url)
        
        try:
            response = await self._client.post(
                token_url,
                auth=(self.config.username, self.config.password.get_secret_value()),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
                },
                data={
                    "grant_type": "password",
                    "username": self.config.username,
                    "password": self.config.password.get_secret_value(),
                    "scope": "openid"
                }
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid credentials")
            
            response.raise_for_status()
            
            data = response.json()
            
            # Calculate expiry time
            expires_in = data.get("expires_in", self.TOKEN_LIFETIME_MINUTES * 60)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            
            self._token = TokenInfo(
                access_token=data["access_token"],
                expires_at=expires_at,
                token_type=data.get("token_type", "Bearer")
            )
            
            logger.info(
                "Token acquired",
                expires_at=expires_at.isoformat(),
                expires_in_minutes=expires_in // 60
            )
            
        except httpx.HTTPStatusError as e:
            logger.error("Token acquisition failed", status=e.response.status_code)
            raise AuthenticationError(f"Token acquisition failed: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error("Token request failed", error=str(e))
            raise AuthenticationError(f"Token request failed: {e}")


class AuthenticatedClient:
    """
    HTTP client with automatic token management.
    
    Wraps httpx.AsyncClient with automatic auth header injection
    and 401 retry logic.
    
    Example:
        async with AuthenticatedClient(config) as client:
            response = await client.get("/IDORequestService/ido/load/SLJobs")
    """
    
    MAX_AUTH_RETRIES = 1
    
    def __init__(self, config: SyteLineConfig):
        """
        Initialize authenticated client.
        
        Args:
            config: SyteLine configuration
        """
        self.config = config
        self._token_manager: Optional[TokenManager] = None
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self) -> "AuthenticatedClient":
        """Async context manager entry."""
        self._token_manager = TokenManager(self.config)
        await self._token_manager.__aenter__()
        
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=httpx.Timeout(self.config.request_timeout_seconds),
            follow_redirects=True
        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
        if self._token_manager:
            await self._token_manager.__aexit__(exc_type, exc_val, exc_tb)
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """
        Make authenticated GET request with retry on 401.
        
        Args:
            url: Request URL (relative to base_url)
            **kwargs: Additional arguments passed to httpx
        
        Returns:
            HTTP response
        """
        return await self._request("GET", url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> httpx.Response:
        """Make authenticated POST request with retry on 401."""
        return await self._request("POST", url, **kwargs)
    
    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make request with auth and retry logic."""
        if not self._client or not self._token_manager:
            raise RuntimeError("Client not initialized (use async with)")
        
        for attempt in range(self.MAX_AUTH_RETRIES + 1):
            # Add auth header
            auth_header = await self._token_manager.get_auth_header()
            headers = {**kwargs.pop("headers", {}), **auth_header}
            
            response = await self._client.request(method, url, headers=headers, **kwargs)
            
            # Retry on 401 (token may have expired)
            if response.status_code == 401 and attempt < self.MAX_AUTH_RETRIES:
                logger.warning("Got 401, invalidating token and retrying")
                await self._token_manager.invalidate()
                continue
            
            return response
        
        return response  # Return last response even if 401
