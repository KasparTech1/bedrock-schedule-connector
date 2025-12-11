"""
API Authentication & Authorization
==================================

Provides API key authentication for external access to kai_erp connectors.

Features:
- API key validation
- Rate limiting per key
- Scope-based permissions
- Usage tracking
"""

import hashlib
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from functools import lru_cache
from typing import Optional

from fastapi import Depends, HTTPException, Header, Security
from fastapi.security import APIKeyHeader
import structlog

logger = structlog.get_logger(__name__)


class APIScope(str, Enum):
    """Permission scopes for API keys."""
    
    # Read-only scopes
    READ_CUSTOMERS = "customers:read"
    READ_ORDERS = "orders:read"
    READ_INVENTORY = "inventory:read"
    READ_SCHEDULE = "schedule:read"
    READ_JOBS = "jobs:read"
    
    # Write scopes (future)
    WRITE_ORDERS = "orders:write"
    
    # Admin scopes
    ADMIN = "admin"
    ALL = "*"


@dataclass
class APIKey:
    """API key configuration."""
    
    key_id: str  # Public identifier (e.g., "kai_live_abc123")
    key_hash: str  # SHA256 hash of the actual key
    name: str  # Human-readable name
    owner: str  # Owner email or identifier
    
    # Permissions
    scopes: list[APIScope] = field(default_factory=lambda: [APIScope.ALL])
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_day: int = 10000
    
    # Status
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    
    # Usage tracking
    total_requests: int = 0
    requests_this_minute: int = 0
    requests_today: int = 0
    minute_reset_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    day_reset_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0))
    
    def check_rate_limit(self) -> bool:
        """Check if request is within rate limits."""
        now = datetime.now(timezone.utc)
        
        # Reset minute counter if needed
        if (now - self.minute_reset_at).total_seconds() > 60:
            self.requests_this_minute = 0
            self.minute_reset_at = now
        
        # Reset day counter if needed
        if now.date() > self.day_reset_at.date():
            self.requests_today = 0
            self.day_reset_at = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return (
            self.requests_this_minute < self.rate_limit_per_minute and
            self.requests_today < self.rate_limit_per_day
        )
    
    def record_request(self):
        """Record a successful request."""
        self.total_requests += 1
        self.requests_this_minute += 1
        self.requests_today += 1
        self.last_used_at = datetime.now(timezone.utc)
    
    def has_scope(self, required_scope: APIScope) -> bool:
        """Check if key has required scope."""
        if APIScope.ALL in self.scopes or APIScope.ADMIN in self.scopes:
            return True
        return required_scope in self.scopes


class APIKeyManager:
    """
    Manages API keys for external access.
    
    In production, this would be backed by a database.
    For now, uses in-memory storage with optional config file.
    """
    
    def __init__(self):
        self._keys: dict[str, APIKey] = {}
        self._hash_to_key: dict[str, str] = {}  # hash -> key_id
        self._load_default_keys()
    
    def _load_default_keys(self):
        """Load default API keys (for development)."""
        # Create a default development key
        dev_key = self.create_key(
            name="Development Key",
            owner="dev@localhost",
            scopes=[APIScope.ALL],
            rate_limit_per_minute=120,
            rate_limit_per_day=50000,
        )
        logger.info(
            "Default development API key created",
            key_id=dev_key[0],
            # Note: Only log the key in development!
            secret_key=dev_key[1],
        )
    
    def create_key(
        self,
        name: str,
        owner: str,
        scopes: list[APIScope] = None,
        rate_limit_per_minute: int = 60,
        rate_limit_per_day: int = 10000,
        expires_in_days: Optional[int] = None,
    ) -> tuple[str, str]:
        """
        Create a new API key.
        
        Returns:
            Tuple of (key_id, secret_key)
            The secret_key is only shown once!
        """
        # Generate key ID and secret
        key_id = f"kai_{'live' if not expires_in_days else 'temp'}_{secrets.token_hex(8)}"
        secret_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(secret_key.encode()).hexdigest()
        
        # Create key object
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            owner=owner,
            scopes=scopes or [APIScope.ALL],
            rate_limit_per_minute=rate_limit_per_minute,
            rate_limit_per_day=rate_limit_per_day,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_in_days) if expires_in_days else None,
        )
        
        self._keys[key_id] = api_key
        self._hash_to_key[key_hash] = key_id
        
        return key_id, secret_key
    
    def validate_key(self, secret_key: str) -> Optional[APIKey]:
        """Validate an API key and return the key object if valid."""
        key_hash = hashlib.sha256(secret_key.encode()).hexdigest()
        
        key_id = self._hash_to_key.get(key_hash)
        if not key_id:
            return None
        
        api_key = self._keys.get(key_id)
        if not api_key:
            return None
        
        # Check if active
        if not api_key.is_active:
            return None
        
        # Check if expired
        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            return None
        
        return api_key
    
    def get_key(self, key_id: str) -> Optional[APIKey]:
        """Get key by ID."""
        return self._keys.get(key_id)
    
    def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        api_key = self._keys.get(key_id)
        if api_key:
            api_key.is_active = False
            return True
        return False
    
    def list_keys(self) -> list[dict]:
        """List all API keys (without secrets)."""
        return [
            {
                "key_id": k.key_id,
                "name": k.name,
                "owner": k.owner,
                "scopes": [s.value for s in k.scopes],
                "is_active": k.is_active,
                "created_at": k.created_at.isoformat(),
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                "total_requests": k.total_requests,
                "rate_limit_per_minute": k.rate_limit_per_minute,
                "rate_limit_per_day": k.rate_limit_per_day,
            }
            for k in self._keys.values()
        ]


# Global instance
_key_manager: Optional[APIKeyManager] = None


def get_key_manager() -> APIKeyManager:
    """Get the global API key manager."""
    global _key_manager
    if _key_manager is None:
        _key_manager = APIKeyManager()
    return _key_manager


# FastAPI Security Scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> Optional[APIKey]:
    """
    Dependency to validate API key from header.
    
    Usage:
        @app.get("/customers")
        async def get_customers(key: APIKey = Depends(require_api_key)):
            ...
    """
    if not api_key:
        return None
    
    manager = get_key_manager()
    validated_key = manager.validate_key(api_key)
    
    if validated_key:
        # Check rate limit
        if not validated_key.check_rate_limit():
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": "60"}
            )
        
        # Record the request
        validated_key.record_request()
    
    return validated_key


async def require_api_key(
    api_key: Optional[APIKey] = Depends(get_api_key),
) -> APIKey:
    """Require a valid API key (raises 401 if missing/invalid)."""
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "API key required. Pass via X-API-Key header."}
        )
    return api_key


def require_scope(scope: APIScope):
    """
    Dependency factory to require a specific scope.
    
    Usage:
        @app.get("/customers")
        async def get_customers(key: APIKey = Depends(require_scope(APIScope.READ_CUSTOMERS))):
            ...
    """
    async def _check_scope(api_key: APIKey = Depends(require_api_key)) -> APIKey:
        if not api_key.has_scope(scope):
            raise HTTPException(
                status_code=403,
                detail=f"Missing required scope: {scope.value}"
            )
        return api_key
    
    return _check_scope


# Optional: Make API key optional (for internal access)
async def optional_api_key(
    api_key: Optional[APIKey] = Depends(get_api_key),
) -> Optional[APIKey]:
    """API key is optional - returns None if not provided."""
    return api_key
