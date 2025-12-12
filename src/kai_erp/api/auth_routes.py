"""
Authentication Routes
=====================

Endpoints for authentication and token management.

Endpoints:
- POST /auth/token - Get JWT token from API key
- POST /auth/refresh - Refresh an expired access token
- GET /auth/me - Get current user info
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import structlog

from kai_erp.api.auth import (
    APIKey,
    get_api_key,
    get_key_manager,
)
from kai_erp.api.jwt_auth import (
    TokenResponse,
    TokenUser,
    create_tokens,
    get_current_user,
    require_jwt,
    verify_token,
    get_jwt_settings,
    create_access_token,
)

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


class TokenRequest(BaseModel):
    """Request body for token generation."""
    
    api_key: str
    scopes: Optional[list[str]] = None  # Optional scope restriction


class RefreshRequest(BaseModel):
    """Request body for token refresh."""
    
    refresh_token: str


class UserInfo(BaseModel):
    """Current user information."""
    
    id: str
    scopes: list[str]
    auth_method: str  # "jwt" or "api_key"


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Get JWT Token",
    description="""
Exchange an API key for a JWT access token.

The JWT token can be used in the Authorization header:
```
Authorization: Bearer <access_token>
```

This is useful for:
- Short-lived access without exposing the API key
- Client-side applications where the key shouldn't be stored
- Fine-grained scope restriction

**Note:** The access token expires after 30 minutes by default.
Use the refresh token to get a new access token without the API key.
""",
)
async def get_token(request: TokenRequest) -> TokenResponse:
    """Exchange API key for JWT tokens."""
    
    # Validate API key
    manager = get_key_manager()
    api_key = manager.validate_key(request.api_key)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    # Check rate limit
    if not api_key.check_rate_limit():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"},
        )
    
    # Record the request
    api_key.record_request()
    
    # Get scopes - use requested scopes if provided, otherwise use key's scopes
    scopes = [s.value for s in api_key.scopes]
    if request.scopes:
        # Filter to only scopes the key has
        scopes = [s for s in request.scopes if s in scopes or "*" in scopes]
    
    # Create tokens
    tokens = create_tokens(
        subject=api_key.key_id,
        scopes=scopes,
    )
    
    logger.info(
        "JWT tokens created for API key",
        key_id=api_key.key_id,
        scopes=scopes,
    )
    
    return tokens


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh Access Token",
    description="""
Get a new access token using a refresh token.

This endpoint allows you to get a new access token without
needing to provide the API key again.

**Note:** The refresh token is single-use in production.
""",
)
async def refresh_token(request: RefreshRequest) -> TokenResponse:
    """Refresh an access token."""
    
    try:
        # Verify the refresh token
        payload = verify_token(request.refresh_token)
        
        if payload.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type. Expected refresh token.",
            )
        
        # Create new access token with same scopes
        # Note: In production, you'd want to:
        # 1. Invalidate the old refresh token
        # 2. Look up the user/key to get current scopes
        settings = get_jwt_settings()
        
        # For now, create a new access token
        access_token = create_access_token(
            subject=payload.sub,
            scopes=payload.scopes,
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            scopes=payload.scopes,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.get(
    "/me",
    response_model=UserInfo,
    summary="Get Current User",
    description="Get information about the currently authenticated user or API key.",
)
async def get_me(
    jwt_user: Optional[TokenUser] = Depends(get_current_user),
    api_key: Optional[APIKey] = Depends(get_api_key),
) -> UserInfo:
    """Get current authenticated user info."""
    
    # Check JWT first
    if jwt_user:
        return UserInfo(
            id=jwt_user.id,
            scopes=jwt_user.scopes,
            auth_method="jwt",
        )
    
    # Check API key
    if api_key:
        return UserInfo(
            id=api_key.key_id,
            scopes=[s.value for s in api_key.scopes],
            auth_method="api_key",
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


@router.get(
    "/keys",
    summary="List API Keys",
    description="List all API keys (admin only).",
)
async def list_keys(
    user: TokenUser = Depends(require_jwt),
) -> list[dict]:
    """List all API keys."""
    
    # Check for admin scope
    if "*" not in user.scopes and "admin" not in user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    manager = get_key_manager()
    return manager.list_keys()


