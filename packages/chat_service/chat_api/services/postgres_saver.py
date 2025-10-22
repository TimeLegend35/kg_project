"""
PostgreSQL Saver Integration für LangGraph Checkpoints
Ermöglicht Chat-Persistence über Sessions hinweg
"""
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg2.pool import SimpleConnectionPool
from chat_api.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ChatPersistence:
    """Wrapper für LangGraph PostgresSaver mit Singleton Pattern"""

    _instance: Optional['ChatPersistence'] = None
    _pool: Optional[SimpleConnectionPool] = None
    _saver: Optional[PostgresSaver] = None

    def __new__(cls):
        """Singleton Pattern - nur eine Instanz"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialisiere Connection Pool und Saver"""
        if self._pool is None:
            self._initialize_pool()
            self._initialize_saver()

    def _initialize_pool(self):
        """Erstelle PostgreSQL Connection Pool"""
        try:
            self._pool = SimpleConnectionPool(
                minconn=1,
                maxconn=20,
                dsn=settings.database_url,
                connect_timeout=10
            )
            logger.info("✅ PostgreSQL Connection Pool erstellt")
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Connection Pools: {e}")
            raise

    def _initialize_saver(self):
        """Initialisiere PostgresSaver und erstelle Tabellen"""
        try:
            self._saver = PostgresSaver(self._pool)
            self._saver.setup()
            logger.info("✅ PostgresSaver initialisiert und Tabellen erstellt")
        except Exception as e:
            logger.error(f"❌ Fehler bei PostgresSaver Initialisierung: {e}")
            raise

    def get_saver(self) -> PostgresSaver:
        """Gibt PostgresSaver Instanz zurück"""
        if self._saver is None:
            raise RuntimeError("PostgresSaver nicht initialisiert")
        return self._saver

    def close(self):
        """Schließe alle Connections"""
        if self._pool:
            self._pool.closeall()
            logger.info("✅ PostgreSQL Connection Pool geschlossen")

    def health_check(self) -> bool:
        """Prüfe Datenbankverbindung"""
        try:
            conn = self._pool.getconn()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self._pool.putconn(conn)
            return result[0] == 1
        except Exception as e:
            logger.error(f"❌ Health Check fehlgeschlagen: {e}")
            return False


# Singleton Instance - wird beim Import erstellt
chat_persistence = ChatPersistence()
"""Services Package"""

