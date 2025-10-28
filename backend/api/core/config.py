"""Configuration management for the API"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    db_url: str = os.getenv(
        "DB_URL",
        "postgresql+psycopg://bgb_user:bgb_password@localhost:5432/bgb_chat"
    )
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_echo: bool = False

    # API
    api_title: str = "BGB AI Chat API"
    api_version: str = "1.0.0"
    api_prefix: str = "/api/v1"

    # Security (POC: keine JWT-Auth genutzt)
    jwt_secret: str = os.getenv("JWT_SECRET", "CHANGE-ME-IN-PRODUCTION")
    api_key: Optional[str] = os.getenv("API_KEY", None)

    # Agent Service
    agent_service_mode: str = os.getenv("AGENT_SERVICE_MODE", "inproc")  # "inproc" or "http"
    agent_service_url: Optional[str] = os.getenv("AGENT_SERVICE_URL", None)

    # Google Gemini
    # Mache den Key effektiv mandatory (leer => nicht nutzbar, API markiert Gemini als unavailable)
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    # Robustes Parsing für optionale numerische Settings
    try:
        gemini_temperature: float = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))
    except ValueError:
        gemini_temperature: float = 0.7
    try:
        gemini_max_output_tokens: int = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "8192"))
    except ValueError:
        gemini_max_output_tokens: int = 8192
    enable_thinking: bool = os.getenv("ENABLE_THINKING", "true").lower() in {"1", "true", "yes", "y"}

    # Timeouts (milliseconds)
    agent_call_timeout_ms: int = int(os.getenv("AGENT_CALL_TIMEOUT_MS", "120000"))  # 2 min

    # Rate Limiting
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    rate_limit_window_seconds: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Redis (optional, for caching)
    redis_url: Optional[str] = os.getenv("REDIS_URL", None)

    # Content Limits
    max_content_size_kb: int = 16
    max_params_size_kb: int = 8

    # Streaming
    sse_keepalive_seconds: int = 15

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
