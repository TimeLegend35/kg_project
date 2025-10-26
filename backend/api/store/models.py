"""SQLAlchemy database models"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Text, DateTime, ForeignKey, BigInteger, Enum as SQLEnum, Index, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
import uuid
import enum


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class MessageRole(str, enum.Enum):
    """Message role enumeration"""
    user = "user"
    assistant = "assistant"
    tool = "tool"


class Thread(Base):
    """Thread model - represents a conversation thread"""
    __tablename__ = "threads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    thread_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )

    # Indexes
    __table_args__ = (
        Index("ix_threads_updated_at", "updated_at"),
        Index("ix_threads_deleted_at", "deleted_at"),
    )

    def __repr__(self):
        return f"<Thread(id={self.id}, title={self.title})>"


class Message(Base):
    """Message model - represents a message in a thread"""
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False
    )
    role: Mapped[MessageRole] = mapped_column(
        SQLEnum(MessageRole, name="message_role_enum"),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    agent_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tool_calls: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    usage: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Relationships
    thread: Mapped["Thread"] = relationship("Thread", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index("ix_messages_thread_id_created_at", "thread_id", "created_at"),
    )

    def __repr__(self):
        return f"<Message(id={self.id}, thread_id={self.thread_id}, role={self.role})>"

