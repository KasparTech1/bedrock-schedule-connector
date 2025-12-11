"""
API Middleware
==============

Middleware components for the FastAPI application.

Includes:
- Rate limiting
- Request logging
- Error handling
"""

import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.
    
    Limits requests per IP address using a sliding window algorithm.
    
    Note: For production with multiple instances, use Redis-based
    rate limiting (e.g., slowapi with Redis backend).
    
    Configuration:
        - requests_per_minute: Max requests allowed per minute per IP
        - requests_per_hour: Max requests allowed per hour per IP
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        exclude_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/redoc", "/openapi.json"]
        
        # Store request timestamps per IP
        # Format: {ip: [timestamp1, timestamp2, ...]}
        self._requests: dict[str, list[float]] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request with rate limiting."""
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check rate limits
        now = time.time()
        is_allowed, retry_after = self._check_rate_limit(client_ip, now)
        
        if not is_allowed:
            logger.warning(
                "Rate limit exceeded",
                client_ip=client_ip,
                path=request.url.path,
                retry_after=retry_after,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please slow down.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )
        
        # Record this request
        self._record_request(client_ip, now)
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self._get_remaining_requests(client_ip, now)
        )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, handling proxies."""
        # Check for forwarded headers (behind reverse proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first IP (original client)
            return forwarded.split(",")[0].strip()
        
        # Fall back to direct client
        return request.client.host if request.client else "unknown"
    
    def _check_rate_limit(self, client_ip: str, now: float) -> tuple[bool, int]:
        """
        Check if request is within rate limits.
        
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        # Clean old entries first
        self._cleanup_old_requests(client_ip, now)
        
        requests = self._requests[client_ip]
        
        # Check per-minute limit
        minute_ago = now - 60
        minute_requests = sum(1 for ts in requests if ts > minute_ago)
        
        if minute_requests >= self.requests_per_minute:
            # Find when the oldest request in the window expires
            oldest_in_minute = min((ts for ts in requests if ts > minute_ago), default=now)
            retry_after = int(60 - (now - oldest_in_minute)) + 1
            return False, retry_after
        
        # Check per-hour limit
        hour_ago = now - 3600
        hour_requests = sum(1 for ts in requests if ts > hour_ago)
        
        if hour_requests >= self.requests_per_hour:
            oldest_in_hour = min((ts for ts in requests if ts > hour_ago), default=now)
            retry_after = int(3600 - (now - oldest_in_hour)) + 1
            return False, retry_after
        
        return True, 0
    
    def _record_request(self, client_ip: str, now: float):
        """Record a request timestamp."""
        self._requests[client_ip].append(now)
    
    def _cleanup_old_requests(self, client_ip: str, now: float):
        """Remove request timestamps older than 1 hour."""
        hour_ago = now - 3600
        self._requests[client_ip] = [
            ts for ts in self._requests[client_ip] if ts > hour_ago
        ]
    
    def _get_remaining_requests(self, client_ip: str, now: float) -> int:
        """Get remaining requests in current minute window."""
        minute_ago = now - 60
        minute_requests = sum(1 for ts in self._requests[client_ip] if ts > minute_ago)
        return max(0, self.requests_per_minute - minute_requests)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging all API requests.
    
    Logs request method, path, status code, and duration.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        start_time = time.time()
        
        # Get client info
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip and request.client:
            client_ip = request.client.host
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log based on status code
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": client_ip,
        }
        
        if response.status_code >= 500:
            logger.error("Request error", **log_data)
        elif response.status_code >= 400:
            logger.warning("Request failed", **log_data)
        else:
            logger.info("Request completed", **log_data)
        
        return response
