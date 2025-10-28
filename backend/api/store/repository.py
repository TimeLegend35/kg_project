"""Repository pattern for data access"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from .models import Thread, Message, MessageRole
from ..core.errors import NotFoundError


class ThreadRepository:
    """Repository for Thread operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        title: Optional[str] = None,
        thread_metadata: Optional[dict] = None
    ) -> Thread:
        """Create a new thread"""
        thread = Thread(
            title=title,
            thread_metadata=thread_metadata or {}
        )
        self.db.add(thread)
        self.db.flush()
        return thread

    def get_by_id(
        self,
        thread_id: UUID,
        include_deleted: bool = False
    ) -> Optional[Thread]:
        """Get thread by ID"""
        query = self.db.query(Thread).filter(Thread.id == thread_id)

        if not include_deleted:
            query = query.filter(Thread.deleted_at.is_(None))

        return query.first()

    def get_by_id_or_raise(
        self,
        thread_id: UUID,
        include_deleted: bool = False
    ) -> Thread:
        """Get thread by ID or raise NotFoundError"""
        thread = self.get_by_id(thread_id, include_deleted)
        if not thread:
            raise NotFoundError(
                message="Thread not found",
                details={"thread_id": str(thread_id)}
            )
        return thread

    def list_threads(
        self,
        limit: int = 50,
        cursor: Optional[datetime] = None,
        include_deleted: bool = False
    ) -> List[Thread]:
        """List threads with pagination"""
        query = self.db.query(Thread)

        if not include_deleted:
            query = query.filter(Thread.deleted_at.is_(None))

        if cursor:
            query = query.filter(Thread.updated_at < cursor)

        query = query.order_by(desc(Thread.updated_at))
        query = query.limit(limit)

        return query.all()

    def soft_delete(self, thread_id: UUID) -> Thread:
        """Soft delete a thread"""
        thread = self.get_by_id_or_raise(thread_id)
        thread.deleted_at = datetime.utcnow()
        self.db.flush()
        return thread

    def hard_delete(self, thread_id: UUID) -> None:
        """Hard delete a thread (cascade deletes messages)"""
        thread = self.get_by_id_or_raise(thread_id, include_deleted=True)
        self.db.delete(thread)
        self.db.flush()

    def update_timestamp(self, thread_id: UUID) -> Thread:
        """Update thread's updated_at timestamp"""
        thread = self.get_by_id_or_raise(thread_id)
        thread.updated_at = datetime.utcnow()
        self.db.flush()
        return thread


class MessageRepository:
    """Repository for Message operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        thread_id: UUID,
        role: MessageRole,
        content: str,
        agent_name: Optional[str] = None,
        tool_calls: Optional[dict] = None,
        usage: Optional[dict] = None
    ) -> Message:
        """Create a new message"""
        message = Message(
            thread_id=thread_id,
            role=role,
            content=content,
            agent_name=agent_name,
            tool_calls=tool_calls,
            usage=usage
        )
        self.db.add(message)
        self.db.flush()
        return message

    def list_by_thread(
        self,
        thread_id: UUID,
        limit: Optional[int] = None,
        before_id: Optional[int] = None
    ) -> List[Message]:
        """List messages for a thread"""
        query = self.db.query(Message).filter(Message.thread_id == thread_id)

        if before_id:
            query = query.filter(Message.id < before_id)

        query = query.order_by(Message.created_at)

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_by_id(self, message_id: int) -> Optional[Message]:
        """Get message by ID"""
        return self.db.query(Message).filter(Message.id == message_id).first()
