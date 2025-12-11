"""
Rate Limiting Middleware
========================

Configurable rate limiting for API endpoints using slowapi.

Features:
- Per-IP rate limiting
- Per-API-key rate limiting (when auth is enabled)
- Configurable limits per endpoint
- Retry-After headers
"""

from typing import Callable

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from kai_erp.config import get_config


def get_client_identifier(request: Request) -> str:
    """
    Get client identifier for rate limiting.
    
    Uses API key if present in header, otherwise falls back to IP address.
    This allows different rate limits for authenticated vs anonymous requests.
    """
    # Check for API key first
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key}"
    
    # Fall back to IP address
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=["100/minute", "1000/hour"],
    storage_uri="memory://",  # In-memory storage (use Redis in production for multi-instance)
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    
    Returns a JSON response with details about the rate limit.
    """
    # Parse retry-after from exception
    retry_after = getattr(exc, "retry_after", 60)
    
    response = JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": f"Rate limit exceeded. Please retry after {retry_after} seconds.",
            "retry_after": retry_after,
        },
    )
    
    # Add Retry-After header
    response.headers["Retry-After"] = str(retry_after)
    
    return response


# Rate limit decorators for different endpoint types
def standard_limit() -> Callable:
    """Standard rate limit for most endpoints: 60 requests/minute."""
    return limiter.limit("60/minute")


def search_limit() -> Callable:
    """Rate limit for search endpoints: 30 requests/minute."""
    return limiter.limit("30/minute")


def heavy_limit() -> Callable:
    """Rate limit for heavy/expensive endpoints: 10 requests/minute."""
    return limiter.limit("10/minute")


def admin_limit() -> Callable:
    """Rate limit for admin endpoints: 20 requests/minute."""
    return limiter.limit("20/minute")
