"""
Prometheus Metrics
==================

Application metrics for monitoring and alerting.

Metrics exposed:
- HTTP request counts and latencies
- SyteLine API call counts and latencies
- Connector execution metrics
- Error rates

Metrics endpoint: GET /metrics
"""

import time
from functools import wraps
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    REGISTRY,
)
import structlog

logger = structlog.get_logger(__name__)


# =============================================================================
# Metric Definitions
# =============================================================================

# Application info
APP_INFO = Info(
    "kai_erp_app",
    "Application information"
)

# HTTP metrics
HTTP_REQUESTS_TOTAL = Counter(
    "kai_erp_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "kai_erp_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "kai_erp_http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"]
)

# SyteLine API metrics
SYTELINE_API_CALLS_TOTAL = Counter(
    "kai_erp_syteline_api_calls_total",
    "Total SyteLine API calls",
    ["ido_name", "status"]
)

SYTELINE_API_DURATION_SECONDS = Histogram(
    "kai_erp_syteline_api_duration_seconds",
    "SyteLine API call duration in seconds",
    ["ido_name"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0)
)

SYTELINE_API_RECORDS_RETURNED = Histogram(
    "kai_erp_syteline_api_records_returned",
    "Number of records returned from SyteLine API",
    ["ido_name"],
    buckets=(1, 10, 50, 100, 500, 1000, 5000, 10000)
)

# Connector metrics
CONNECTOR_EXECUTIONS_TOTAL = Counter(
    "kai_erp_connector_executions_total",
    "Total connector executions",
    ["connector", "status"]
)

CONNECTOR_DURATION_SECONDS = Histogram(
    "kai_erp_connector_duration_seconds",
    "Connector execution duration in seconds",
    ["connector"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0)
)

# Rate limiting metrics
RATE_LIMIT_HITS_TOTAL = Counter(
    "kai_erp_rate_limit_hits_total",
    "Total rate limit hits",
    ["endpoint"]
)

# Authentication metrics
AUTH_ATTEMPTS_TOTAL = Counter(
    "kai_erp_auth_attempts_total",
    "Total authentication attempts",
    ["method", "status"]  # method: api_key, jwt; status: success, failure
)


# =============================================================================
# Metrics Middleware
# =============================================================================

class MetricsMiddleware:
    """
    Middleware to track HTTP request metrics.
    
    Tracks:
    - Request counts by method, endpoint, status
    - Request duration
    - Requests in progress
    """
    
    def __init__(self, app: FastAPI):
        self.app = app
    
    async def __call__(self, request: Request, call_next) -> Response:
        method = request.method
        # Normalize endpoint path (remove IDs for cardinality control)
        endpoint = self._normalize_path(request.url.path)
        
        # Track in-progress requests
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
        
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            status_code = str(response.status_code)
        except Exception as e:
            status_code = "500"
            raise
        finally:
            # Record metrics
            duration = time.perf_counter() - start_time
            
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            HTTP_REQUESTS_IN_PROGRESS.labels(
                method=method,
                endpoint=endpoint
            ).dec()
        
        return response
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize path to reduce cardinality.
        
        Replaces dynamic path segments with placeholders.
        """
        parts = path.split("/")
        normalized = []
        
        for part in parts:
            # Skip empty parts
            if not part:
                continue
            
            # Replace UUIDs, IDs, numbers with placeholders
            if self._looks_like_id(part):
                normalized.append("{id}")
            else:
                normalized.append(part)
        
        return "/" + "/".join(normalized) if normalized else "/"
    
    def _looks_like_id(self, part: str) -> bool:
        """Check if a path part looks like a dynamic ID."""
        # UUID pattern
        if len(part) == 36 and part.count("-") == 4:
            return True
        # Numeric ID
        if part.isdigit():
            return True
        # Short hex ID
        if len(part) >= 8 and all(c in "0123456789abcdef" for c in part.lower()):
            return True
        return False


# =============================================================================
# Metric Recording Functions
# =============================================================================

def record_syteline_call(
    ido_name: str,
    duration_seconds: float,
    records_returned: int,
    success: bool = True
) -> None:
    """Record metrics for a SyteLine API call."""
    status = "success" if success else "error"
    
    SYTELINE_API_CALLS_TOTAL.labels(ido_name=ido_name, status=status).inc()
    SYTELINE_API_DURATION_SECONDS.labels(ido_name=ido_name).observe(duration_seconds)
    
    if success:
        SYTELINE_API_RECORDS_RETURNED.labels(ido_name=ido_name).observe(records_returned)


def record_connector_execution(
    connector_name: str,
    duration_seconds: float,
    success: bool = True
) -> None:
    """Record metrics for a connector execution."""
    status = "success" if success else "error"
    
    CONNECTOR_EXECUTIONS_TOTAL.labels(connector=connector_name, status=status).inc()
    CONNECTOR_DURATION_SECONDS.labels(connector=connector_name).observe(duration_seconds)


def record_rate_limit_hit(endpoint: str) -> None:
    """Record a rate limit hit."""
    RATE_LIMIT_HITS_TOTAL.labels(endpoint=endpoint).inc()


def record_auth_attempt(method: str, success: bool) -> None:
    """Record an authentication attempt."""
    status = "success" if success else "failure"
    AUTH_ATTEMPTS_TOTAL.labels(method=method, status=status).inc()


# =============================================================================
# Metrics Endpoint
# =============================================================================

def setup_metrics(app: FastAPI) -> None:
    """
    Set up metrics collection and endpoint.
    
    Adds:
    - Metrics middleware for request tracking
    - /metrics endpoint for Prometheus scraping
    """
    # Set app info
    APP_INFO.info({
        "version": "3.0.0",
        "service": "kai-erp-connector",
    })
    
    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        """Prometheus metrics endpoint."""
        return Response(
            content=generate_latest(REGISTRY),
            media_type=CONTENT_TYPE_LATEST
        )
    
    logger.info("Metrics endpoint enabled at /metrics")


# =============================================================================
# Decorator for Timing Functions
# =============================================================================

def timed_operation(operation_name: str):
    """
    Decorator to time and record operation metrics.
    
    Usage:
        @timed_operation("fetch_customers")
        async def fetch_customers():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            success = True
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                success = False
                raise
            finally:
                duration = time.perf_counter() - start_time
                record_connector_execution(operation_name, duration, success)
        
        return wrapper
    return decorator
