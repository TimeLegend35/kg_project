"""
Chat Models - Pydantic Models für Chat-Operationen
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional, Any, List
from datetime import datetime
from uuid import uuid4


# ============================================
# Tool Models
# ============================================
class ToolCall(BaseModel):
    """Repräsentiert einen Tool-Aufruf vom Qwen Agent"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    arguments: dict[str, Any]
    status: Literal["pending", "running", "completed", "failed"] = "pending"


class ToolResult(BaseModel):
    """Ergebnis eines Tool-Aufrufs"""
    tool_call_id: str
    output: str
    metadata: Optional[dict[str, Any]] = None


# ============================================
# Message Models
# ============================================
class ChatMessage(BaseModel):
    """Eine Chat-Nachricht"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: Literal["user", "assistant", "system", "function"]
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    tool_results: Optional[List[ToolResult]] = None
    thinking_content: Optional[str] = None  # Qwen Thinking Mode
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "Wann ist ein Kaufvertrag wirksam?",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


# ============================================
# Request/Response Models
# ============================================
class ChatRequest(BaseModel):
    """Request für neuen Chat - Backend lädt History aus PostgreSQL"""
    chat_id: str  # UUID des Chats
    message: str
    stream: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "chat_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Was ist ein Kaufvertrag?",
                "stream": True
            }
        }


class ChatChunk(BaseModel):
    """Ein Streaming-Chunk vom Qwen Agent"""
    type: Literal["text", "tool_call", "tool_result", "thinking", "done", "error"]
    content: Optional[str] = None
    tool_call: Optional[ToolCall] = None
    tool_result: Optional[ToolResult] = None
    thinking_content: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

    def to_sse_format(self) -> str:
        """Konvertiere zu Server-Sent Event Format"""
        return f"data: {self.model_dump_json()}\n\n"


class ChatHistoryResponse(BaseModel):
    """Response mit Chat-Historie"""
    session_id: str
    messages: List[ChatMessage]
    total_messages: int
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "messages": [],
                "total_messages": 5,
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }

