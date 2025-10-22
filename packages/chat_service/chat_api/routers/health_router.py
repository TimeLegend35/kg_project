"""
Health Router - System Health Checks
Prüft Status von API, PostgreSQL (shared!), Ollama, Solr und Blazegraph
"""
from fastapi import APIRouter
from chat_api.config import settings
from chat_api.services.chat_history_loader import chat_history_loader
from datetime import datetime
import httpx
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    """
    Basis Health Check

    ### Returns
    Status der API mit Version und Timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.API_VERSION,
        "service": "bgb-chat-api"
    }


@router.get("/detailed")
async def detailed_health_check():
    """
    Detaillierter Health Check aller Services

    Prüft:
    - PostgreSQL (Shared DB mit Frontend!)
    - Ollama (Qwen Agent)
    - Solr (Search Index)
    - Blazegraph (SPARQL Endpoint)

    ### Returns
    Status aller Services mit overall Status
    """

    health = {
        "api": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.API_VERSION
    }

    # PostgreSQL Check (Shared DB!)
    try:
        is_healthy = chat_history_loader.health_check()
        health["postgres"] = "healthy" if is_healthy else "unhealthy"
        health["postgres_note"] = "Shared DB with Frontend (Drizzle tables)"
        logger.info(f"PostgreSQL (Shared): {health['postgres']}")
    except Exception as e:
        health["postgres"] = f"error: {str(e)}"
        logger.error(f"PostgreSQL Check Failed: {e}")

    # Ollama Check
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            health["ollama"] = "healthy" if response.status_code == 200 else "unhealthy"
            logger.info(f"Ollama: {health['ollama']}")
    except Exception as e:
        health["ollama"] = f"error: {str(e)}"
        logger.error(f"Ollama Check Failed: {e}")

    # Solr Check
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.SOLR_URL}/admin/ping")
            health["solr"] = "healthy" if response.status_code == 200 else "unhealthy"
            logger.info(f"Solr: {health['solr']}")
    except Exception as e:
        health["solr"] = f"error: {str(e)}"
        logger.error(f"Solr Check Failed: {e}")

    # Blazegraph Check
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(settings.BLAZEGRAPH_URL)
            health["blazegraph"] = "healthy" if response.status_code == 200 else "unhealthy"
            logger.info(f"Blazegraph: {health['blazegraph']}")
    except Exception as e:
        health["blazegraph"] = f"error: {str(e)}"
        logger.error(f"Blazegraph Check Failed: {e}")

    # Overall Status
    service_statuses = [
        v for k, v in health.items()
        if k not in ["timestamp", "api", "version", "postgres_note"]
    ]

    overall_status = "healthy" if all(
        status == "healthy" for status in service_statuses
    ) else "degraded"

    health["overall"] = overall_status
    logger.info(f"Overall Health: {overall_status}")

    return health

