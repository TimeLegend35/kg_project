"""Health check routes"""
from fastapi import APIRouter
from datetime import datetime
from sqlalchemy import text

from ..schemas.schemas import HealthResponse, ReadinessResponse
from ..core.config import get_settings
from ..store.database import engine

router = APIRouter()
settings = get_settings()


@router.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version=settings.api_version,
        timestamp=datetime.utcnow()
    )


@router.get("/readyz", response_model=ReadinessResponse)
async def readiness_check():
    """Readiness check endpoint"""
    checks = {}

    # Check database connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False

    ready = all(checks.values()) if checks else False

    return ReadinessResponse(
        ready=ready,
        checks=checks
    )


@router.get("/version")
async def version():
    """Version endpoint"""
    return {
        "version": settings.api_version,
        "api_title": settings.api_title
    }
