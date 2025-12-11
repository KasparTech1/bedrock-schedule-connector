"""
Error Handling
==============

Structured error responses and exception handlers for the API.

Provides:
- Consistent error format across all endpoints
- Error codes for programmatic handling
- Detailed messages for debugging
"""

from enum import Enum
from typing import Any, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import structlog

logger = structlog.get_logger(__name__)


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""
    
    # Authentication errors (401)
    AUTH_REQUIRED = "auth_required"
    AUTH_INVALID = "auth_invalid"
    TOKEN_EXPIRED = "token_expired"
    
    # Authorization errors (403)
    FORBIDDEN = "forbidden"
    SCOPE_REQUIRED = "scope_required"
    
    # Not found errors (404)
    NOT_FOUND = "not_found"
    RESOURCE_NOT_FOUND = "resource_not_found"
    
    # Validation errors (422)
    VALIDATION_ERROR = "validation_error"
    INVALID_PARAMETER = "invalid_parameter"
    MISSING_PARAMETER = "missing_parameter"
    
    # Rate limiting (429)
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    
    # Server errors (500)
    INTERNAL_ERROR = "internal_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    UPSTREAM_ERROR = "upstream_error"
    
    # Business logic errors (400)
    BAD_REQUEST = "bad_request"
    VOLUME_EXCEEDED = "volume_exceeded"


class ErrorDetail(BaseModel):
    """Structured error detail."""
    
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class APIError(BaseModel):
    """Standard API error response."""
    
    error: ErrorCode
    message: str
    details: Optional[list[ErrorDetail]] = None
    request_id: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "validation_error",
                "message": "Invalid input parameters",
                "details": [
                    {"field": "work_center", "message": "Must be alphanumeric"}
                ]
            }
        }
    }


class APIException(Exception):
    """Base exception for API errors."""
    
    def __init__(
        self,
        error: ErrorCode,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[list[ErrorDetail]] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        self.error = error
        self.message = message
        self.status_code = status_code
        self.details = details
        self.headers = headers
        super().__init__(message)
    
    def to_response(self, request_id: Optional[str] = None) -> JSONResponse:
        """Convert to JSONResponse."""
        content = APIError(
            error=self.error,
            message=self.message,
            details=self.details,
            request_id=request_id,
        ).model_dump()
        
        return JSONResponse(
            status_code=self.status_code,
            content=content,
            headers=self.headers,
        )


# Common exception classes
class AuthenticationError(APIException):
    """Authentication required or failed."""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            error=ErrorCode.AUTH_REQUIRED,
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(APIException):
    """Insufficient permissions."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            error=ErrorCode.FORBIDDEN,
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class NotFoundError(APIException):
    """Resource not found."""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            error=ErrorCode.RESOURCE_NOT_FOUND,
            message=f"{resource} not found: {identifier}",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ValidationError(APIException):
    """Input validation failed."""
    
    def __init__(self, message: str, details: Optional[list[ErrorDetail]] = None):
        super().__init__(
            error=ErrorCode.VALIDATION_ERROR,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class RateLimitError(APIException):
    """Rate limit exceeded."""
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            error=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": str(retry_after)},
        )


class ServiceUnavailableError(APIException):
    """Service is unavailable."""
    
    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(
            error=ErrorCode.SERVICE_UNAVAILABLE,
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class VolumeExceededError(APIException):
    """Query volume exceeds limits."""
    
    def __init__(self, estimated: int, limit: int):
        super().__init__(
            error=ErrorCode.VOLUME_EXCEEDED,
            message=f"Query would return ~{estimated:,} records, exceeding limit of {limit:,}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=[
                ErrorDetail(
                    message="Add filters to reduce result size",
                    code="suggestion",
                )
            ],
        )


def setup_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers on the FastAPI app."""
    
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
        """Handle custom API exceptions."""
        request_id = request.headers.get("X-Request-ID")
        logger.warning(
            "API exception",
            error=exc.error.value,
            message=exc.message,
            status_code=exc.status_code,
            request_id=request_id,
        )
        return exc.to_response(request_id)
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        details = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            details.append(ErrorDetail(
                field=field,
                message=error["msg"],
                code=error["type"],
            ))
        
        request_id = request.headers.get("X-Request-ID")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=APIError(
                error=ErrorCode.VALIDATION_ERROR,
                message="Invalid input parameters",
                details=details,
                request_id=request_id,
            ).model_dump(),
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        request_id = request.headers.get("X-Request-ID")
        logger.exception(
            "Unhandled exception",
            error=str(exc),
            request_id=request_id,
        )
        
        # Don't expose internal errors in production
        message = "An internal error occurred"
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIError(
                error=ErrorCode.INTERNAL_ERROR,
                message=message,
                request_id=request_id,
            ).model_dump(),
        )
