"""Authentication and authorization middleware"""
from typing import Optional
from fastapi import Security, HTTPException, status, Request
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta

from api.core.config import get_settings
from api.core.errors import UnauthorizedError

settings = get_settings()

# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# JWT Bearer authentication
bearer_scheme = HTTPBearer(auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Verify API key authentication.

    Returns the API key if valid, raises UnauthorizedError otherwise.
    """
    # If no API key is configured, skip authentication (dev mode)
    if not settings.api_key:
        return "dev-mode"

    if not api_key:
        raise UnauthorizedError(
            message="API key required",
            details={"header": "X-API-Key"}
        )

    if api_key != settings.api_key:
        raise UnauthorizedError(
            message="Invalid API key"
        )

    return api_key


async def verify_jwt(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> dict:
    """
    Verify JWT token authentication.

    Returns the decoded token payload if valid, raises UnauthorizedError otherwise.
    """
    if not credentials:
        raise UnauthorizedError(
            message="Bearer token required",
            details={"header": "Authorization"}
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError(
            message="Token expired"
        )
    except jwt.InvalidTokenError:
        raise UnauthorizedError(
            message="Invalid token"
        )


def create_jwt_token(payload: dict, expires_in_hours: int = 24) -> str:
    """
    Create a JWT token.

    Args:
        payload: Token payload
        expires_in_hours: Token expiration time in hours

    Returns:
        Encoded JWT token
    """
    payload = payload.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=expires_in_hours)

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm="HS256"
    )


# Use API key auth by default (simpler for initial setup)
async def get_current_user(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Get current authenticated user.
    For POC - authentication is optional, returns 'anonymous' if no key provided.
    """
    # If no API key is configured or provided, allow anonymous access (POC mode)
    if not settings.api_key or not api_key:
        return "anonymous"

    # If API key is configured and provided, verify it
    if api_key != settings.api_key:
        raise UnauthorizedError(message="Invalid API key")

    return api_key
"""Service components"""

