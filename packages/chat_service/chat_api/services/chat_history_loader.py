"""
PostgreSQL Chat History Loader
Liest aus den gleichen Tabellen wie das Frontend (Drizzle Schema)
"""
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from chat_api.config import settings
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ChatHistoryLoader:
    """Lädt Chat History aus der shared PostgreSQL Datenbank"""

    def __init__(self):
        """Initialisiere PostgreSQL Connection"""
        self.engine = create_engine(
            settings.database_url,
            poolclass=NullPool,
            echo=False
        )
        logger.info(f"✅ ChatHistoryLoader initialisiert: {settings.POSTGRES_HOST}")

    def get_chat_history(self, chat_id: str) -> List[Dict[str, str]]:
        """
        Lade Chat History für einen Chat aus PostgreSQL

        Liest aus den Drizzle-Tabellen:
        - bgb_messages: Alle Messages eines Chats

        Args:
            chat_id: UUID des Chats (vom Frontend erstellt)

        Returns:
            Liste von Messages im Format: [{"role": "user", "content": "..."}, ...]
        """
        try:
            with self.engine.connect() as conn:
                # Query Messages aus der Drizzle-Tabelle
                query = text("""
                    SELECT role, content, thinking_content, created_at
                    FROM bgb_messages
                    WHERE chat_id = :chat_id
                    ORDER BY created_at ASC
                """)

                result = conn.execute(query, {"chat_id": chat_id})
                rows = result.fetchall()

                # Konvertiere zu Message Format für Qwen Agent
                messages = []
                for row in rows:
                    role, content, thinking_content, created_at = row

                    # Hauptnachricht hinzufügen
                    messages.append({
                        "role": role,
                        "content": content
                    })

                    # Optional: Thinking Content als separate Info loggen
                    if thinking_content:
                        logger.debug(f"💭 Thinking für Message: {thinking_content[:50]}...")

                logger.info(f"📚 Geladen: {len(messages)} Messages für Chat {chat_id}")
                return messages

        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Chat History: {e}")
            # Bei Fehler: Leere History zurückgeben (Chat kann trotzdem weitergehen)
            return []

    def chat_exists(self, chat_id: str) -> bool:
        """Prüfe ob ein Chat existiert"""
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT COUNT(*) FROM bgb_chats WHERE id = :chat_id
                """)
                result = conn.execute(query, {"chat_id": chat_id})
                count = result.scalar()
                return count > 0
        except Exception as e:
            logger.error(f"❌ Fehler bei chat_exists Check: {e}")
            return False

    def get_chat_info(self, chat_id: str) -> Optional[Dict]:
        """Hole Chat Metadaten"""
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT id, user_id, title, created_at, updated_at
                    FROM bgb_chats
                    WHERE id = :chat_id
                """)
                result = conn.execute(query, {"chat_id": chat_id})
                row = result.fetchone()

                if row:
                    return {
                        "id": str(row[0]),
                        "user_id": row[1],
                        "title": row[2],
                        "created_at": row[3],
                        "updated_at": row[4]
                    }
                return None
        except Exception as e:
            logger.error(f"❌ Fehler bei get_chat_info: {e}")
            return None

    def health_check(self) -> bool:
        """Prüfe Datenbankverbindung"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"❌ PostgreSQL Health Check Failed: {e}")
            return False

    def close(self):
        """Schließe DB Connection"""
        self.engine.dispose()
        logger.info("✅ ChatHistoryLoader closed")


# Singleton Instance
chat_history_loader = ChatHistoryLoader()

