"""Stream endpoint for frontend - simplified SSE streaming"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, AsyncIterator
from sqlalchemy.orm import Session
import json
import asyncio
import logging

from ..store.database import get_db
from ..store.repository import ThreadRepository, MessageRepository
from ..store.models import MessageRole
from ..services.chat import run_agent

router = APIRouter(prefix="/stream", tags=["stream"])
logger = logging.getLogger(__name__)


class StreamChatRequest(BaseModel):
    """Request for streaming chat"""
    thread_id: Optional[str] = Field(None, description="Thread ID (optional, will create new if not provided)")
    agent: str = Field("qwen", description="Agent to use (qwen or gemini)")
    message: str = Field(..., min_length=1, max_length=16384, description="User message")
    params: Optional[dict] = Field(default_factory=dict, description="Additional parameters")


class StreamChatMetadata(BaseModel):
    """Metadata for stream response"""
    thread_id: str
    message_id: Optional[int] = None


async def _stream_chat_response(
    request: StreamChatRequest,
    db: Session
) -> AsyncIterator[str]:
    """Generate SSE stream for chat response"""

    try:
        # Get or create thread
        thread_repo = ThreadRepository(db)
        msg_repo = MessageRepository(db)

        if request.thread_id:
            # Use existing thread
            try:
                import uuid
                thread_id = uuid.UUID(request.thread_id)
                thread = thread_repo.get_by_id_or_raise(thread_id)
            except ValueError:
                yield _format_sse_event("error", {"message": "Invalid thread_id format"})
                return
        else:
            # Create new thread
            thread = thread_repo.create(title=f"Chat: {request.message[:50]}...")
            db.commit()
            thread_id = thread.id

        # Send thread metadata
        yield _format_sse_event("metadata", {
            "thread_id": str(thread_id)
        })

        # Get message history
        history = msg_repo.list_by_thread(thread_id)

        # Convert to agent message format
        agent_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in history
        ]

        # Add new user message
        agent_messages.append({
            "role": "user",
            "content": request.message
        })

        # Persist user message
        user_msg = msg_repo.create(
            thread_id=thread_id,
            role=MessageRole.user,
            content=request.message
        )
        db.commit()
        db.refresh(user_msg)

        # Send start event
        yield _format_sse_event("start", {
            "role": "assistant",
            "agent": request.agent
        })

        # Send thinking event
        yield _format_sse_event("thinking", {"status": "processing"})

        # Call agent (non-streaming, then simulate streaming)
        # Add thread_id to params for PostgresSaver
        agent_params = request.params or {}
        agent_params["thread_id"] = str(thread_id)

        try:
            result = run_agent(
                agent=request.agent,
                messages=agent_messages,
                params=agent_params,
                stream=False
            )

            # Persist assistant message BEFORE streaming
            # This ensures the message is saved even if streaming is interrupted
            content = result["content"]
            assistant_msg = msg_repo.create(
                thread_id=thread_id,
                role=MessageRole.assistant,
                content=content,
                agent_name=request.agent,
                tool_calls=result.get("tool_calls"),
                usage=result.get("usage")
            )

            # Update thread timestamp
            thread_repo.update_timestamp(thread_id)
            db.commit()
            db.refresh(assistant_msg)

            # Stream tool calls FIRST (during thinking phase)
            if result.get("tool_calls"):
                for tool_call in result["tool_calls"]:
                    yield _format_sse_event("tool_call", tool_call)
                    await asyncio.sleep(0.1)  # Small delay to show tool execution

            # Thinking done
            yield _format_sse_event("thinking", {"status": "done"})

            # Stream tokens in chunks for UI effect
            chunk_size = 5  # Characters per chunk
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i+chunk_size]
                yield _format_sse_event("token", {"token": chunk})
                await asyncio.sleep(0.02)  # Small delay for realistic streaming

            # Send usage if available
            if result.get("usage"):
                yield _format_sse_event("usage", result["usage"])


            # Send done event
            yield _format_sse_event("done", {
                "message_id": assistant_msg.id,
                "thread_id": str(thread_id),
                "content": content
            })

        except Exception as e:
            logger.error(f"Agent execution error: {e}", exc_info=True)
            db.rollback()
            yield _format_sse_event("error", {
                "message": f"Agent execution failed: {str(e)}"
            })

    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        db.rollback()
        yield _format_sse_event("error", {
            "message": f"Stream error: {str(e)}"
        })


def _format_sse_event(event_type: str, data: dict) -> str:
    """Format data as Server-Sent Event"""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


@router.post("/chat")
async def stream_chat(
    request: StreamChatRequest,
    db: Session = Depends(get_db)
):
    """
    Stream chat endpoint for frontend.

    Returns SSE stream with the following events:
    - metadata: Thread metadata (thread_id)
    - start: Stream started (role, agent)
    - token: Token chunk (token)
    - tool_call: Tool call information (optional)
    - usage: Usage statistics (optional)
    - done: Stream completed (message_id, thread_id, content)
    - error: Error occurred (message)
    """
    return StreamingResponse(
        _stream_chat_response(request, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/health")
async def stream_health():
    """Health check for stream endpoint"""
    return {"status": "ok", "streaming": "enabled"}
