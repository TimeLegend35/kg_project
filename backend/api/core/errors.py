"""Error handling and custom exceptions"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
import uuid


class APIError(Exception):
    """Base API error"""
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(APIError):
    """Resource not found error"""
    def __init__(self, message: str = "Resource not found", details: Optional[Dict] = None):
        super().__init__(
            code="not_found",
            message=message,
            details=details,
            status_code=status.HTTP_404_NOT_FOUND
        )


class ValidationError(APIError):
    """Validation error"""
    def __init__(self, message: str = "Validation failed", details: Optional[Dict] = None):
        super().__init__(
            code="validation_error",
            message=message,
            details=details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class UnauthorizedError(APIError):
    """Unauthorized access error"""
    def __init__(self, message: str = "Unauthorized", details: Optional[Dict] = None):
        super().__init__(
            code="unauthorized",
            message=message,
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class RateLimitError(APIError):
    """Rate limit exceeded error"""
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict] = None):
        super().__init__(
            code="rate_limited",
            message=message,
            details=details,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


class UpstreamError(APIError):
    """Upstream service error"""
    def __init__(self, message: str = "Upstream service error", details: Optional[Dict] = None):
        super().__init__(
            code="upstream_error",
            message=message,
            details=details,
            status_code=status.HTTP_502_BAD_GATEWAY
        )


def format_error_response(
    code: str,
    message: str,
    details: Optional[Dict] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Format error response consistently"""
    return {
        "code": code,
        "message": message,
        "details": details or {},
        "request_id": request_id or str(uuid.uuid4())
    }


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle APIError exceptions"""
    request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid.uuid4())
    
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=request_id
        )
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid.uuid4())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_error_response(
            code="internal_error",
            message="An unexpected error occurred",
            details={"error": str(exc)},
            request_id=request_id
        )
    )

