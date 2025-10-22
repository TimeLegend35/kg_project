"""
Chat Router - Streaming Chat mit Shared PostgreSQL
Frontend speichert in PostgreSQL, Backend liest automatisch daraus
"""
from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse
from chat_api.models.chat_models import ChatRequest
from chat_api.services.chat_service import ChatService
from typing import AsyncIterator
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service() -> ChatService:
    """Dependency Injection für ChatService"""
    return ChatService()


@router.post("/stream", response_class=EventSourceResponse)
async def stream_chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service)
):
    """
    Stream Chat mit Server-Sent Events (SSE)

    **Backend lädt History automatisch aus PostgreSQL!**
    Frontend sendet nur chat_id und message, Backend holt den Rest.

    ### Request Body
    - **chat_id**: UUID des Chats (vom Frontend erstellt)
    - **message**: User Message (String)
    - **stream**: true für Streaming (default: true)

    ### Backend macht automatisch:
    1. Lädt komplette Chat History aus PostgreSQL (gleiche Drizzle-Tabellen)
    2. Fügt System Prompt hinzu
    3. Fügt History hinzu (voller Kontext!)
    4. Fügt neue User Message hinzu
    5. Streamt Response

    ### Response
    Server-Sent Events Stream mit ChatChunks:
    - `type: "thinking"` → Qwen Reasoning Trace
    - `type: "text"` → LLM Token/Text
    - `type: "tool_call"` → Tool wird ausgeführt
    - `type: "tool_result"` → Tool Ergebnis
    - `type: "done"` → Stream beendet
    - `type: "error"` → Fehler aufgetreten

    ### Beispiel mit curl:
    ```bash
    curl -N http://localhost:8000/chat/stream \\
      -H "Content-Type: application/json" \\
      -d '{"chat_id": "abc-123-def-456", "message": "Was ist ein Kaufvertrag?"}'
    ```
    """

    logger.info(f"📨 Stream Request")
    logger.info(f"🆔 Chat ID: {request.chat_id}")
    logger.info(f"💬 Message: {request.message[:50]}...")

    async def event_generator() -> AsyncIterator[dict]:
        """Generator für Server-Sent Events"""
        try:
            async for chunk in service.stream_response(
                chat_id=request.chat_id,
                message=request.message
            ):
                yield {
                    "event": "message",
                    "data": chunk.model_dump_json()
                }
        except Exception as e:
            logger.error(f"❌ Stream Error: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": f'{{"type": "error", "content": "{str(e)}"}}'
            }

    return EventSourceResponse(event_generator())

