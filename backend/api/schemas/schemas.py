"""Pydantic schemas for request/response validation"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# Enums
class MessageRoleEnum(str, Enum):
    """Message role enum"""
    user = "user"
    assistant = "assistant"
    tool = "tool"


# Thread Schemas
class ThreadCreate(BaseModel):
    """Schema for creating a thread"""
    title: Optional[str] = Field(None, max_length=500)
    thread_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ThreadResponse(BaseModel):
    """Schema for thread response"""
    id: UUID
    title: Optional[str]
    thread_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ThreadListResponse(BaseModel):
    """Schema for list of threads"""
    threads: List[ThreadResponse]
    cursor: Optional[datetime] = None


# Message Schemas
class MessageResponse(BaseModel):
    """Schema for message response"""
    id: int
    thread_id: UUID
    role: MessageRoleEnum
    content: str
    agent_name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    usage: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Schema for list of messages"""
    messages: List[MessageResponse]


class MessageCreate(BaseModel):
    """Schema for creating a message (sending user input)"""
    agent: str = Field(..., description="Agent to use (qwen or gemini)")
    input: str = Field(..., min_length=1, max_length=16384, description="User input text")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional parameters")
    stream: bool = Field(default=False, description="Enable streaming response")

    @field_validator('input')
    @classmethod
    def validate_input_size(cls, v: str) -> str:
        """Validate input size"""
        if len(v.encode('utf-8')) > 16 * 1024:  # 16KB
            raise ValueError("Input exceeds maximum size of 16KB")
        return v

    @field_validator('agent')
    @classmethod
    def validate_agent(cls, v: str) -> str:
        """Validate agent name"""
        if v.lower() not in ['qwen', 'gemini']:
            raise ValueError("Agent must be 'qwen' or 'gemini'")
        return v.lower()


class MessageCreateResponse(BaseModel):
    """Schema for non-streaming message response"""
    message: MessageResponse
    usage: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    meta: Optional[Dict[str, Any]] = None


# Agent Schemas
class AgentInfo(BaseModel):
    """Schema for agent information"""
    name: str
    description: str
    available: bool


class AgentListResponse(BaseModel):
    """Schema for list of agents"""
    agents: List[AgentInfo]


# Health Schemas
class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    version: str
    timestamp: datetime


class ReadinessResponse(BaseModel):
    """Schema for readiness check response"""
    ready: bool
    checks: Dict[str, bool]


# Error Schema
class ErrorResponse(BaseModel):
    """Schema for error response"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: str
"""Data store components"""

