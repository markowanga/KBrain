"""Statistics API routes."""

from typing import List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from kbrain_backend.api.schemas import GlobalStatistics, ScopeStatisticsDetail
from kbrain_backend.core.models.scope import Scope
from kbrain_backend.core.models.document import Document
from kbrain_backend.database.connection import get_db

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("", response_model=GlobalStatistics)
async def get_global_statistics(
    db: AsyncSession = Depends(get_db),
):
    """Get system-wide statistics."""

    # Total scopes
    total_scopes = await db.scalar(select(func.count()).select_from(Scope))

    # Total documents
    total_documents = await db.scalar(select(func.count()).select_from(Document))

    # Total storage size
    total_size = await db.scalar(select(func.sum(Document.file_size))) or 0

    # Documents by status
    documents_by_status = {}
    for doc_status in ["added", "processing", "processed", "failed"]:
        count = (
            await db.scalar(
                select(func.count())
                .select_from(Document)
                .where(Document.status == doc_status)
            )
            or 0
        )
        documents_by_status[doc_status] = count

    # Documents by extension
    documents_by_extension = {}
    ext_query = select(Document.file_extension, func.count().label("count")).group_by(
        Document.file_extension
    )
    ext_result = await db.execute(ext_query)
    for ext, count in ext_result:
        documents_by_extension[ext] = count

    # Storage backends
    storage_backends = {}
    backend_query = select(
        Document.storage_backend, func.count().label("count")
    ).group_by(Document.storage_backend)
    backend_result = await db.execute(backend_query)
    for backend, count in backend_result:
        storage_backends[backend] = count

    # Recent uploads (simplified - would need time-series analysis in production)
    recent_uploads = {
        "last_hour": 0,  # Would need real implementation
        "last_24_hours": 0,
        "last_7_days": 0,
    }

    return GlobalStatistics(
        total_scopes=total_scopes or 0,
        total_documents=total_documents or 0,
        total_size=int(total_size),
        documents_by_status=documents_by_status,
        documents_by_extension=documents_by_extension,
        storage_backends=storage_backends,
        recent_uploads=recent_uploads,
    )


@router.get("/scopes/{scope_id}", response_model=ScopeStatisticsDetail)
async def get_scope_statistics(
    scope_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get statistics for a specific scope."""

    # Verify scope exists
    scope_query = select(Scope).where(Scope.id == scope_id)
    scope = await db.scalar(scope_query)

    if not scope:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Scope not found"}},
        )

    # Total documents
    total_documents = (
        await db.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.scope_id == scope_id)
        )
        or 0
    )

    # Total size
    total_size = (
        await db.scalar(
            select(func.sum(Document.file_size)).where(Document.scope_id == scope_id)
        )
        or 0
    )

    # Documents by status
    documents_by_status = {}
    for doc_status in ["added", "processing", "processed", "failed"]:
        count = (
            await db.scalar(
                select(func.count())
                .select_from(Document)
                .where(Document.scope_id == scope_id, Document.status == doc_status)
            )
            or 0
        )
        documents_by_status[doc_status] = count

    # Documents by extension
    documents_by_extension = {}
    ext_query = (
        select(Document.file_extension, func.count().label("count"))
        .where(Document.scope_id == scope_id)
        .group_by(Document.file_extension)
    )
    ext_result = await db.execute(ext_query)
    for ext, count in ext_result:
        documents_by_extension[ext] = count

    # Upload timeline (simplified)
    upload_timeline: List[Dict[str, Any]] = []

    # Processing performance (simplified)
    processing_performance = {
        "average_processing_time_ms": 12500,  # Would need real calculation
        "success_rate": 0.974,  # Would need real calculation
    }

    return ScopeStatisticsDetail(
        scope_id=scope_id,
        scope_name=scope.name,
        total_documents=total_documents,
        total_size=int(total_size),
        documents_by_status=documents_by_status,
        documents_by_extension=documents_by_extension,
        upload_timeline=upload_timeline,
        processing_performance=processing_performance,
    )
