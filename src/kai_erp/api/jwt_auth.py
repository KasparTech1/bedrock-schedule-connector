"""
JWT Authentication
==================

JWT-based authentication for the KAI ERP Connector API.

Supports:
- JWT token generation and validation
- Configurable expiration
- Scope-based authorization
- Refresh token flow

Usage:
    1. Client authenticates with credentials
    2. Server returns JWT access token (and optional refresh token)
    3. Client includes token in Authorization: Bearer <token> header
    4. Server validates token on each request
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
import structlog

from kai_erp.config import get_config
from kai_erp.api.auth import APIScope

logger = structlog.get_logger(__name__)


# JWT Configuration
class JWTSettings(BaseModel):
    """JWT configuration settings."""
    
    # Secret key for signing tokens - MUST be set in production via JWT_SECRET env var
    secret_key: str = "dev-secret-key-change-in-production"
    
    # Algorithm for signing
    algorithm: str = "HS256"
    
    # Token expiration times
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Issuer claim
    issuer: str = "kai-erp-connector"


# Load settings from environment
def get_jwt_settings() -> JWTSettings:
    """Get JWT settings from environment."""
    import os
    return JWTSettings(
        secret_key=os.getenv("JWT_SECRET", "dev-secret-key-change-in-production"),
        access_token_expire_minutes=int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "30")),
        refresh_token_expire_days=int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7")),
    )


# Token Models
class TokenPayload(BaseModel):
    """JWT token payload."""
    
    sub: str  # Subject (user ID or API key ID)
    scopes: list[str] = []  # Permission scopes
    exp: datetime  # Expiration time
    iat: datetime  # Issued at
    iss: str  # Issuer
    type: str = "access"  # Token type: "access" or "refresh"


class TokenResponse(BaseModel):
    """Response containing JWT tokens."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until expiration
    refresh_token: Optional[str] = None
    scopes: list[str] = []


class TokenUser(BaseModel):
    """Authenticated user/client from JWT."""
    
    id: str
    scopes: list[str]
    token_type: str


# JWT Functions
def create_access_token(
    subject: str,
    scopes: list[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: User ID or API key ID
        scopes: Permission scopes
        expires_delta: Custom expiration time
        
    Returns:
        Encoded JWT token
    """
    settings = get_jwt_settings()
    
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    
    payload = {
        "sub": subject,
        "scopes": scopes or [],
        "exp": expire,
        "iat": now,
        "iss": settings.issuer,
        "type": "access",
    }
    
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(subject: str) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        subject: User ID or API key ID
        
    Returns:
        Encoded JWT refresh token
    """
    settings = get_jwt_settings()
    
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.refresh_token_expire_days)
    
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": now,
        "iss": settings.issuer,
        "type": "refresh",
    }
    
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def verify_token(token: str) -> TokenPayload:
    """
    Verify and decode a JWT token.
    
    Args:
        token: Encoded JWT token
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    settings = get_jwt_settings()
    
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            issuer=settings.issuer,
        )
        
        return TokenPayload(
            sub=payload["sub"],
            scopes=payload.get("scopes", []),
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            iss=payload["iss"],
            type=payload.get("type", "access"),
        )
        
    except JWTError as e:
        logger.warning("JWT validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_tokens(
    subject: str,
    scopes: list[str] = None,
) -> TokenResponse:
    """
    Create both access and refresh tokens.
    
    Args:
        subject: User ID or API key ID
        scopes: Permission scopes
        
    Returns:
        TokenResponse with access and refresh tokens
    """
    settings = get_jwt_settings()
    
    access_token = create_access_token(subject, scopes)
    refresh_token = create_refresh_token(subject)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        refresh_token=refresh_token,
        scopes=scopes or [],
    )


# FastAPI Dependencies
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[TokenUser]:
    """
    Get current user from JWT token (optional).
    
    Returns None if no token provided.
    """
    if not credentials:
        return None
    
    payload = verify_token(credentials.credentials)
    
    if payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return TokenUser(
        id=payload.sub,
        scopes=payload.scopes,
        token_type=payload.type,
    )


async def require_jwt(
    user: Optional[TokenUser] = Depends(get_current_user),
) -> TokenUser:
    """
    Require a valid JWT token.
    
    Raises 401 if token is missing or invalid.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_jwt_scope(scope: str):
    """
    Dependency factory to require a specific scope in JWT.
    
    Usage:
        @app.get("/admin")
        async def admin_endpoint(user: TokenUser = Depends(require_jwt_scope("admin"))):
            ...
    """
    async def _check_scope(user: TokenUser = Depends(require_jwt)) -> TokenUser:
        # Check for wildcard or admin scope
        if "*" in user.scopes or "admin" in user.scopes:
            return user
        
        if scope not in user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: {scope}",
            )
        return user
    
    return _check_scope


# Combined Auth (API Key OR JWT)
async def get_authenticated_user(
    jwt_user: Optional[TokenUser] = Depends(get_current_user),
    # API key validation is handled separately in auth.py
) -> Optional[TokenUser]:
    """
    Get authenticated user from either JWT or API key.
    
    This allows endpoints to accept both authentication methods.
    """
    return jwt_user
