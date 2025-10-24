"""Scope API routes."""

from typing import Optional, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from kbrain_backend.api.schemas import (
    ScopeCreate,
    ScopeUpdate,
    ScopeResponse,
    ScopeListResponse,
    ScopeListItem,
    PaginationResponse,
    ScopeStatistics,
)
from kbrain_backend.core.models.scope import Scope
from kbrain_backend.core.models.document import Document
from kbrain_backend.database.connection import get_db

router = APIRouter(prefix="/scopes", tags=["scopes"])


@router.get("", response_model=ScopeListResponse)
async def list_scopes(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    sort: str = Query("created_at", pattern="^(name|created_at)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
) -> ScopeListResponse:
    """List all scopes with pagination."""
    # Build query
    query = select(Scope)

    # Filter by active status
    if is_active is not None:
        query = query.where(Scope.is_active == is_active)

    # Count total items
    count_query = select(func.count()).select_from(query.subquery())
    total_items = await db.scalar(count_query)

    # Apply sorting
    sort_column = getattr(Scope, sort)
    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)

    # Execute query
    result = await db.execute(query)
    scopes = result.scalars().all()

    # Get document counts and sizes for each scope
    scope_items = []
    for scope in scopes:
        doc_count_query = (
            select(func.count())
            .select_from(Document)
            .where(Document.scope_id == scope.id)
        )
        doc_count = await db.scalar(doc_count_query) or 0

        total_size_query = select(func.sum(Document.file_size)).where(
            Document.scope_id == scope.id
        )
        total_size = await db.scalar(total_size_query) or 0

        scope_item = ScopeListItem(
            id=cast(UUID, scope.id),
            name=scope.name,
            description=scope.description,
            allowed_extensions=scope.allowed_extensions,
            storage_backend=scope.storage_backend,
            is_active=scope.is_active,
            document_count=doc_count,
            total_size=total_size,
            created_at=scope.created_at,
            updated_at=scope.updated_at,
        )
        scope_items.append(scope_item)

    # Pagination metadata
    total_items_count = total_items or 0
    total_pages = (total_items_count + per_page - 1) // per_page if total_items_count else 0
    pagination = PaginationResponse(
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        total_items=total_items_count,
        has_next=page < total_pages,
        has_prev=page > 1,
    )

    return ScopeListResponse(scopes=scope_items, pagination=pagination)


@router.get("/{scope_id}", response_model=ScopeResponse)
async def get_scope(
    scope_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ScopeResponse:
    """Get a specific scope by ID."""
    query = select(Scope).where(Scope.id == scope_id)
    result = await db.execute(query)
    scope = result.scalar_one_or_none()

    if not scope:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Scope not found"}},
        )

    # Get statistics
    doc_count_query = (
        select(func.count()).select_from(Document).where(Document.scope_id == scope.id)
    )
    doc_count = await db.scalar(doc_count_query) or 0

    total_size_query = select(func.sum(Document.file_size)).where(
        Document.scope_id == scope.id
    )
    total_size = await db.scalar(total_size_query) or 0

    # Status breakdown
    status_breakdown = {}
    for doc_status in ["added", "processing", "processed", "failed"]:
        count_query = (
            select(func.count())
            .select_from(Document)
            .where(Document.scope_id == scope.id, Document.status == doc_status)
        )
        count = await db.scalar(count_query) or 0
        status_breakdown[doc_status] = count

    statistics = ScopeStatistics(
        document_count=doc_count,
        total_size=total_size,
        status_breakdown=status_breakdown,
    )

    response = ScopeResponse(
        id=cast(UUID, scope.id),
        name=scope.name,
        description=scope.description,
        allowed_extensions=scope.allowed_extensions,
        storage_backend=scope.storage_backend,
        storage_config=scope.storage_config,
        is_active=scope.is_active,
        created_at=scope.created_at,
        updated_at=scope.updated_at,
        statistics=statistics,
    )

    return response


@router.post("", response_model=ScopeResponse, status_code=status.HTTP_201_CREATED)
async def create_scope(
    scope_data: ScopeCreate,
    db: AsyncSession = Depends(get_db),
) -> ScopeResponse:
    """Create a new scope."""
    # Check if scope with same name exists
    existing_query = select(Scope).where(Scope.name == scope_data.name)
    existing = await db.scalar(existing_query)

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "DUPLICATE_RESOURCE",
                    "message": f"Scope with name '{scope_data.name}' already exists",
                }
            },
        )

    # Create new scope
    scope = Scope(
        name=scope_data.name,
        description=scope_data.description,
        allowed_extensions=scope_data.allowed_extensions,
        storage_backend=scope_data.storage_backend or "local",
        storage_config=scope_data.storage_config,
        is_active=True,
    )

    db.add(scope)
    await db.commit()
    await db.refresh(scope)

    return ScopeResponse(
        id=cast(UUID, scope.id),
        name=scope.name,
        description=scope.description,
        allowed_extensions=scope.allowed_extensions,
        storage_backend=scope.storage_backend,
        storage_config=scope.storage_config,
        is_active=scope.is_active,
        created_at=scope.created_at,
        updated_at=scope.updated_at,
    )


@router.patch("/{scope_id}", response_model=ScopeResponse)
async def update_scope(
    scope_id: UUID,
    scope_data: ScopeUpdate,
    db: AsyncSession = Depends(get_db),
) -> ScopeResponse:
    """Update an existing scope."""
    query = select(Scope).where(Scope.id == scope_id)
    result = await db.execute(query)
    scope = result.scalar_one_or_none()

    if not scope:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Scope not found"}},
        )

    # Update fields
    if scope_data.name is not None:
        # Check for duplicate name
        existing_query = select(Scope).where(
            Scope.name == scope_data.name, Scope.id != scope_id
        )
        existing = await db.scalar(existing_query)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "DUPLICATE_RESOURCE",
                        "message": f"Scope with name '{scope_data.name}' already exists",
                    }
                },
            )
        scope.name = scope_data.name

    if scope_data.description is not None:
        scope.description = scope_data.description

    if scope_data.allowed_extensions is not None:
        scope.allowed_extensions = scope_data.allowed_extensions

    if scope_data.is_active is not None:
        scope.is_active = scope_data.is_active

    await db.commit()
    await db.refresh(scope)

    return ScopeResponse(
        id=cast(UUID, scope.id),
        name=scope.name,
        description=scope.description,
        allowed_extensions=scope.allowed_extensions,
        storage_backend=scope.storage_backend,
        storage_config=scope.storage_config,
        is_active=scope.is_active,
        created_at=scope.created_at,
        updated_at=scope.updated_at,
    )


@router.delete("/{scope_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scope(
    scope_id: UUID,
    hard_delete: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a scope (soft delete by default, hard delete if specified)."""
    query = select(Scope).where(Scope.id == scope_id)
    result = await db.execute(query)
    scope = result.scalar_one_or_none()

    if not scope:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Scope not found"}},
        )

    if hard_delete:
        # Hard delete - remove from database
        await db.delete(scope)
    else:
        # Soft delete - set is_active to False
        scope.is_active = False

    await db.commit()
    return None
