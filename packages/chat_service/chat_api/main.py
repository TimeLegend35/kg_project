"""
FastAPI Main Application - BGB Legal Chat API
Integriert alle Router und Middleware für den Chat Service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from chat_api.config import settings
from chat_api.routers import chat_router, health_router
import logging
from contextlib import asynccontextmanager

# Logging Setup
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Lifecycle Management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup und Shutdown Events"""
    # ============================================
    # Startup
    # ============================================
    logger.info("=" * 60)
    logger.info("🚀 Starting BGB Chat API (Stateless - Frontend manages history)")
    logger.info("=" * 60)
    logger.info(f"🤖 Ollama: {settings.OLLAMA_BASE_URL}")
    logger.info(f"🧠 Model: {settings.OLLAMA_MODEL}")
    logger.info(f"💭 Thinking Mode: {settings.ENABLE_THINKING}")
    logger.info(f"🔍 Solr: {settings.SOLR_URL}")
    logger.info(f"🔗 Blazegraph: {settings.BLAZEGRAPH_URL}")
    logger.info("=" * 60)
    logger.info("✅ API Ready!")
    logger.info(f"📚 Docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    logger.info("=" * 60)

    yield

    # ============================================
    # Shutdown
    # ============================================
    logger.info("=" * 60)
    logger.info("🛑 Shutting down BGB Chat API...")
    logger.info("✅ Cleanup completed")
    logger.info("=" * 60)


# FastAPI App
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="""
## 🎯 BGB Legal Chat API - Stateless Streaming Service

AI-powered Legal Assistant für das deutsche Bürgerliche Gesetzbuch (BGB) mit Qwen-Agent.

### Architecture
**Backend (FastAPI)**: Stateless - nur Chat Streaming mit Tools  
**Frontend (Next.js)**: Verwaltet Chat History mit Drizzle ORM + PostgreSQL

### Features
- ✅ **Streaming Chat** mit Server-Sent Events (SSE)
- ✅ **Tool Calls** transparent zum Frontend (Solr + SPARQL)
- ✅ **Thinking Mode** für Reasoning Traces
- ✅ **Stateless** - keine Backend-Persistence

### Quick Start
```bash
# Stream Chat (Frontend sendet History mit)
POST /chat/stream
{
  "message": "Was ist ein Kaufvertrag?",
  "history": []
}
```

### Tools
Der Agent hat Zugriff auf:
- **bgb_solr_search**: Volltextsuche in BGB-Artikeln
- **explore_bgb_entity_with_sparql**: Detailanalyse über Knowledge Graph
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ============================================
# Middleware
# ============================================

# CORS für Next.js Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# GZip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ============================================
# Router registrieren
# ============================================
app.include_router(health_router.router)
app.include_router(chat_router.router)

# ============================================
# Root Endpoint
# ============================================
@app.get("/")
async def root():
    """
    API Root - Übersicht der verfügbaren Endpoints
    """
    return {
        "message": "BGB Legal Chat API - Stateless Streaming Service",
        "version": settings.API_VERSION,
        "status": "running",
        "note": "Frontend manages chat history with Drizzle ORM",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "health_detailed": "/health/detailed",
            "chat_stream": "POST /chat/stream"
        },
        "tools": [
            "bgb_solr_search",
            "explore_bgb_entity_with_sparql"
        ]
    }


# ============================================
# Run Server (für direkte Ausführung)
# ============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG
    )

