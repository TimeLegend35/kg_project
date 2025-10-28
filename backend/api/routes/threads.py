"""Thread management routes"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session

from ..schemas.schemas import (
    ThreadCreate,
    ThreadResponse,
    ThreadListResponse
)
from ..store.database import get_db
from ..store.repository import ThreadRepository

router = APIRouter(prefix="/threads", tags=["threads"])


@router.post("", response_model=ThreadResponse, status_code=201)
async def create_thread(
    thread_data: ThreadCreate,
    db: Session = Depends(get_db)
):
    """Create a new conversation thread"""
    repo = ThreadRepository(db)
    thread = repo.create(
        title=thread_data.title,
        thread_metadata=thread_data.thread_metadata
    )
    db.commit()
    return thread


@router.get("/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific thread"""
    repo = ThreadRepository(db)
    thread = repo.get_by_id_or_raise(thread_id)
    return thread


@router.get("", response_model=ThreadListResponse)
async def list_threads(
    limit: int = Query(default=50, ge=1, le=100),
    cursor: Optional[datetime] = Query(default=None),
    db: Session = Depends(get_db)
):
    """List threads with pagination"""
    repo = ThreadRepository(db)
    threads = repo.list_threads(limit=limit, cursor=cursor)

    # Get next cursor if there are more results
    next_cursor = None
    if threads and len(threads) == limit:
        next_cursor = threads[-1].updated_at

    return ThreadListResponse(
        threads=threads,
        cursor=next_cursor
    )


@router.delete("/{thread_id}", status_code=204)
async def delete_thread(
    thread_id: UUID,
    hard: bool = Query(default=False, description="Hard delete (permanent)"),
    db: Session = Depends(get_db)
):
    """Delete a thread (soft or hard delete)"""
    repo = ThreadRepository(db)

    if hard:
        repo.hard_delete(thread_id)
    else:
        repo.soft_delete(thread_id)

    db.commit()
    return None
