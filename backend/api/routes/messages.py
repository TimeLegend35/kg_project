"""Message management routes"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Optional, AsyncIterator
from uuid import UUID
from sqlalchemy.orm import Session
import json
import asyncio
import logging

from ..schemas.schemas import (
    MessageCreate,
    MessageCreateResponse,
    MessageListResponse,
    MessageResponse
)
from ..store.database import get_db
from ..store.repository import ThreadRepository, MessageRepository
from ..store.models import MessageRole
from ..services.chat import run_agent
from ..core.errors import ValidationError

router = APIRouter(prefix="/threads/{thread_id}/messages", tags=["messages"])
logger = logging.getLogger(__name__)


@router.get("", response_model=MessageListResponse)
async def list_messages(
    thread_id: UUID,
    limit: Optional[int] = Query(default=None, ge=1, le=1000),
    before_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db)
):
    """List messages in a thread"""
    # Verify thread exists
    thread_repo = ThreadRepository(db)
    thread_repo.get_by_id_or_raise(thread_id)

    # Get messages
    msg_repo = MessageRepository(db)
    messages = msg_repo.list_by_thread(
        thread_id=thread_id,
        limit=limit,
        before_id=before_id
    )

    return MessageListResponse(messages=messages)


@router.post("", response_model=MessageCreateResponse)
async def create_message(
    thread_id: UUID,
    message_data: MessageCreate,
    db: Session = Depends(get_db)
):
    """Create a message (send user input and get agent response)"""

    # Check if streaming is requested
    if message_data.stream:
        # Return SSE stream
        return StreamingResponse(
            _stream_message_response(thread_id, message_data, db),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
    else:
        # Non-streaming response
        return await _create_message_non_stream(thread_id, message_data, db)


async def _create_message_non_stream(
    thread_id: UUID,
    message_data: MessageCreate,
    db: Session
) -> MessageCreateResponse:
    """Handle non-streaming message creation"""

    # Verify thread exists
    thread_repo = ThreadRepository(db)
    thread_repo.get_by_id_or_raise(thread_id)

    # Get message history
    msg_repo = MessageRepository(db)
    history = msg_repo.list_by_thread(thread_id)

    # Convert to agent message format
    agent_messages = [
        {"role": msg.role.value, "content": msg.content}
        for msg in history
    ]

    # Add new user message
    agent_messages.append({
        "role": "user",
        "content": message_data.input
    })

    # Persist user message
    user_msg = msg_repo.create(
        thread_id=thread_id,
        role=MessageRole.user,
        content=message_data.input
    )

    # Call agent
    try:
        result = run_agent(
            agent=message_data.agent,
            messages=agent_messages,
            params=message_data.params,
            stream=False
        )
    except Exception as e:
        db.rollback()
        raise

    # Persist assistant message
    assistant_msg = msg_repo.create(
        thread_id=thread_id,
        role=MessageRole.assistant,
        content=result["content"],
        agent_name=message_data.agent,
        tool_calls=result.get("tool_calls"),
        usage=result.get("usage")
    )

    # Update thread timestamp
    thread_repo.update_timestamp(thread_id)

    # Commit transaction
    db.commit()

    # Refresh to get all fields
    db.refresh(assistant_msg)

    return MessageCreateResponse(
        message=MessageResponse.model_validate(assistant_msg),
        usage=result.get("usage"),
        tool_calls=result.get("tool_calls"),
        meta={"agent": message_data.agent}
    )


async def _stream_message_response(
    thread_id: UUID,
    message_data: MessageCreate,
    db: Session
) -> AsyncIterator[str]:
    """Handle streaming message creation with SSE"""

    try:
        # Verify thread exists
        thread_repo = ThreadRepository(db)
        thread_repo.get_by_id_or_raise(thread_id)

        # Get message history
        msg_repo = MessageRepository(db)
        history = msg_repo.list_by_thread(thread_id)

        # Convert to agent message format
        agent_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in history
        ]

        # Add new user message
        agent_messages.append({
            "role": "user",
            "content": message_data.input
        })

        # Persist user message
        user_msg = msg_repo.create(
            thread_id=thread_id,
            role=MessageRole.user,
            content=message_data.input
        )
        db.commit()

        # Send initial message event
        yield _format_sse_event("message", {
            "role": "assistant",
            "partial": True
        })

        # For now, streaming is not fully implemented in agents
        # So we fall back to non-streaming and send the complete response
        result = run_agent(
            agent=message_data.agent,
            messages=agent_messages,
            params=message_data.params,
            stream=False
        )

        # Simulate token streaming by splitting the response
        content = result["content"]
        for i in range(0, len(content), 10):  # Send 10 chars at a time
            chunk = content[i:i+10]
            yield _format_sse_event("token", {"token": chunk})
            await asyncio.sleep(0.01)  # Small delay for realistic streaming

        # Send usage if available
        if result.get("usage"):
            yield _format_sse_event("usage", result["usage"])

        # Send tool calls if available
        if result.get("tool_calls"):
            for tool_call in result["tool_calls"]:
                yield _format_sse_event("tool_call", tool_call)

        # Persist assistant message
        assistant_msg = msg_repo.create(
            thread_id=thread_id,
            role=MessageRole.assistant,
            content=content,
            agent_name=message_data.agent,
            tool_calls=result.get("tool_calls"),
            usage=result.get("usage")
        )

        # Update thread timestamp
        thread_repo.update_timestamp(thread_id)
        db.commit()

        # Send final done event
        yield _format_sse_event("done", {
            "final": True,
            "content": content,
            "message_id": assistant_msg.id
        })

    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        db.rollback()
        yield _format_sse_event("error", {
            "message": str(e)
        })


def _format_sse_event(event_type: str, data: dict) -> str:
    """Format data as Server-Sent Event"""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
