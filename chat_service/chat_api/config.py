"""
Zentrale Konfiguration für Chat API
Lädt Environment Variables und stellt Settings bereit
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union
import os
from pathlib import Path

# Root des gesamten Projekts (3 Ebenen hoch: chat_service/chat_api -> chat_service -> packages -> kg_project)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class Settings(BaseSettings):
    """Zentrale Anwendungskonfiguration"""

    # API Settings
    API_TITLE: str = "BGB Legal Chat API"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False

    # Database Settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "bgb_chat"
    POSTGRES_USER: str = "bgb_user"
    POSTGRES_PASSWORD: str = "bgb_secure_password_2024"

    # Qwen Agent Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:14B"
    OLLAMA_TEMPERATURE: float = 0.7
    ENABLE_THINKING: bool = True

    # External Services
    SOLR_URL: str = "http://localhost:8984/solr/bgb_core"
    BLAZEGRAPH_URL: str = "http://localhost:9999/bigdata/sparql"

    # CORS - als String, wird später geparst
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"


    @property
    def database_url(self) -> str:
        """Konstruiere PostgreSQL Connection URL"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def async_database_url(self) -> str:
        """Async PostgreSQL URL"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse CORS Origins aus kommagetrennte String"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(',')]

    @property
    def langchain_service_path(self) -> Path:
        """Path zum langchain_service im Parent-Repo"""
        return PROJECT_ROOT / "langchain_service"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Singleton Instance
settings = Settings()

