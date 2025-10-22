"""
Chat Service - Streaming Chat Service mit Shared PostgreSQL
Frontend speichert in PostgreSQL (Drizzle ORM)
Backend liest aus PostgreSQL (SQLAlchemy)
"""
import sys
from typing import AsyncIterator
import logging
import json

# Add parent repo to path to access langchain_service
from chat_api.config import settings
sys.path.append(str(settings.langchain_service_path.parent))

from langchain_service.qwen_agent_bgb import QwenAgentBGB
from chat_api.models.chat_models import ChatChunk, ToolCall, ToolResult
from chat_api.services.chat_history_loader import chat_history_loader

logger = logging.getLogger(__name__)


class ChatService:
    """Streaming Service - lädt History aus shared PostgreSQL"""

    def __init__(self):
        """Initialisiere Qwen Agent und History Loader"""
        self.agent = self._create_agent()
        self.history_loader = chat_history_loader

    def _create_agent(self) -> QwenAgentBGB:
        """Erstelle Qwen Agent mit Konfiguration"""
        logger.info(f"🤖 Erstelle Qwen Agent: {settings.OLLAMA_MODEL}")
        return QwenAgentBGB(
            model_server=f"{settings.OLLAMA_BASE_URL}/v1",
            enable_thinking=settings.ENABLE_THINKING
        )

    async def stream_response(
        self,
        chat_id: str,
        message: str
    ) -> AsyncIterator[ChatChunk]:
        """
        Stream Agent Response - lädt History aus shared PostgreSQL

        Backend lädt automatisch die komplette Chat History aus der PostgreSQL,
        in die das Frontend schreibt (gleiche Drizzle-Tabellen).

        Args:
            chat_id: UUID des Chats (vom Frontend erstellt)
            message: Neue User Message

        Yields:
            ChatChunk: Streaming Chunks (text, tool_call, tool_result, thinking, done)
        """
        logger.info(f"💬 Stream Chat Request")
        logger.info(f"🆔 Chat ID: {chat_id}")
        logger.info(f"📝 User Message: {message[:100]}...")

        try:
            # Lade History aus PostgreSQL (gleiche DB wie Frontend!)
            history = self.history_loader.get_chat_history(chat_id)
            logger.info(f"📚 Geladen: {len(history)} Messages aus PostgreSQL")

            # Build messages array mit System Prompt
            messages = []

            # System Prompt immer als erstes
            messages.append({
                "role": "system",
                "content": """Du bist ein hilfreicher Assistent für das deutsche Bürgerliche Gesetzbuch (BGB).

Du hast Zugang zu folgenden Funktionen:
- bgb_solr_search: Suche nach BGB-Paragraphen und rechtlichen Konzepten
- explore_bgb_entity_with_sparql: Detailanalyse von spezifischen BGB-Entitäten

WICHTIGE REGELN:
- Vermeide IDENTISCHE Abfragen: Nutze unterschiedliche Suchbegriffe
- Bei mehreren Aufrufen: Verwende verwandte aber VERSCHIEDENE Begriffe
- Maximal 3 Aufrufe pro Funktion pro Anfrage!
- Nutze den KOMPLETTEN Kontext der vorherigen Nachrichten!

Antworte immer auf Deutsch und nutze die verfügbaren Funktionen für aktuelle, genaue Informationen."""
            })

            # Füge die komplette History aus PostgreSQL hinzu
            if history:
                logger.info(f"📚 Verwende {len(history)} Messages aus PostgreSQL für Kontext")
                messages.extend(history)

            # Füge die neue User Message hinzu
            messages.append({
                "role": "user",
                "content": message
            })

            logger.info(f"📋 Total Messages für Agent: {len(messages)} (System + {len(history)} History + neue Message)")

            # Step 1: Initial model response
            responses = []
            for response_batch in self.agent.llm.chat(
                messages=messages,
                functions=self.agent.functions
            ):
                responses = response_batch

            messages.extend(responses)

            # Stream Responses zum Client
            for response in responses:
                # Thinking Content
                if settings.ENABLE_THINKING and response.get("reasoning_content"):
                    thinking = response["reasoning_content"]
                    logger.info(f"🧠 Reasoning: {thinking[:100]}...")
                    yield ChatChunk(
                        type="thinking",
                        thinking_content=thinking
                    )

                # Assistant Text Content (ohne Tool Call)
                if response.get("content") and not response.get("function_call"):
                    yield ChatChunk(
                        type="text",
                        content=response["content"]
                    )

                # Tool Call
                if fn_call := response.get("function_call"):
                    fn_name: str = fn_call['name']
                    fn_args: dict = json.loads(fn_call["arguments"])

                    logger.info(f"🛠️ Tool Call: {fn_name}")
                    logger.info(f"📋 Arguments: {fn_args}")

                    # Stream Tool Call Start
                    tool_call_id = f"call_{len(messages)}"
                    yield ChatChunk(
                        type="tool_call",
                        tool_call=ToolCall(
                            id=tool_call_id,
                            name=fn_name,
                            arguments=fn_args,
                            status="running"
                        )
                    )

                    # Execute Tool
                    fn_res: str = json.dumps(
                        self.agent.get_function_by_name(fn_name)(**fn_args)
                    )

                    logger.info(f"✅ Tool Result: {fn_res[:150]}...")

                    # Stream Tool Result
                    yield ChatChunk(
                        type="tool_result",
                        tool_result=ToolResult(
                            tool_call_id=tool_call_id,
                            output=fn_res,
                            metadata={"tool_name": fn_name}
                        )
                    )

                    # Add function result to messages
                    messages.append({
                        "role": "function",
                        "name": fn_name,
                        "content": fn_res,
                    })

            # Step 2: Get final response after tool calls
            if any(msg.get("function_call") for msg in responses):
                logger.info("🔄 Getting final response after tool calls...")

                final_responses = []
                for response_batch in self.agent.llm.chat(
                    messages=messages,
                    functions=self.agent.functions
                ):
                    final_responses = response_batch

                messages.extend(final_responses)

                # Stream Final Response
                for response in final_responses:
                    if response.get("content") and not response.get("function_call"):
                        yield ChatChunk(
                            type="text",
                            content=response["content"]
                        )

            # Done
            logger.info(f"✅ Chat abgeschlossen")
            yield ChatChunk(type="done")

        except Exception as e:
            logger.error(f"❌ Fehler im Chat Service: {e}", exc_info=True)
            yield ChatChunk(
                type="error",
                content=f"Ein Fehler ist aufgetreten: {str(e)}"
            )

