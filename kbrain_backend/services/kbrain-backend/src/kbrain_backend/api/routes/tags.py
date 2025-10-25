"""Tag API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from kbrain_backend.api.schemas import (
    TagCreate,
    TagUpdate,
    TagResponse,
    TagListResponse,
)
from kbrain_backend.core.models.scope import Scope
from kbrain_backend.core.models.tag import Tag
from kbrain_backend.core.models.document import Document
from kbrain_backend.database.connection import get_db

router = APIRouter(prefix="/scopes/{scope_id}/tags", tags=["tags"])


@router.get("", response_model=TagListResponse)
async def list_tags(
    scope_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all tags for a specific scope."""
    # Verify scope exists
    scope_query = select(Scope).where(Scope.id == scope_id)
    scope = await db.scalar(scope_query)

    if not scope:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Scope not found"}},
        )

    # Get all tags for this scope
    query = select(Tag).where(Tag.scope_id == scope_id).order_by(Tag.name)
    result = await db.execute(query)
    tags = result.scalars().all()

    return TagListResponse(tags=[TagResponse.model_validate(tag) for tag in tags])


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    scope_id: UUID,
    tag_data: TagCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new tag in a scope."""
    # Verify scope exists
    scope_query = select(Scope).where(Scope.id == scope_id)
    scope = await db.scalar(scope_query)

    if not scope:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Scope not found"}},
        )

    # Check if tag with same name exists in this scope
    existing_query = select(Tag).where(
        and_(Tag.scope_id == scope_id, Tag.name == tag_data.name)
    )
    existing = await db.scalar(existing_query)

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "DUPLICATE_RESOURCE",
                    "message": f"Tag with name '{tag_data.name}' already exists in this scope",
                }
            },
        )

    # Create new tag
    tag = Tag(
        scope_id=scope_id,
        name=tag_data.name,
        description=tag_data.description,
        color=tag_data.color,
        meta=tag_data.meta,
    )

    db.add(tag)
    await db.commit()
    await db.refresh(tag)

    return TagResponse.model_validate(tag)


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    scope_id: UUID,
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific tag by ID."""
    query = select(Tag).where(and_(Tag.id == tag_id, Tag.scope_id == scope_id))
    result = await db.execute(query)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Tag not found"}},
        )

    return TagResponse.model_validate(tag)


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
    scope_id: UUID,
    tag_id: UUID,
    tag_data: TagUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing tag."""
    query = select(Tag).where(and_(Tag.id == tag_id, Tag.scope_id == scope_id))
    result = await db.execute(query)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Tag not found"}},
        )

    # Update fields
    if tag_data.name is not None:
        # Check for duplicate name
        existing_query = select(Tag).where(
            and_(Tag.scope_id == scope_id, Tag.name == tag_data.name, Tag.id != tag_id)
        )
        existing = await db.scalar(existing_query)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "DUPLICATE_RESOURCE",
                        "message": f"Tag with name '{tag_data.name}' already exists in this scope",
                    }
                },
            )
        tag.name = tag_data.name

    if tag_data.description is not None:
        tag.description = tag_data.description

    if tag_data.color is not None:
        tag.color = tag_data.color

    if tag_data.meta is not None:
        tag.meta = tag_data.meta

    await db.commit()
    await db.refresh(tag)

    return TagResponse.model_validate(tag)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    scope_id: UUID,
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a tag."""
    query = select(Tag).where(and_(Tag.id == tag_id, Tag.scope_id == scope_id))
    result = await db.execute(query)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Tag not found"}},
        )

    await db.delete(tag)
    await db.commit()

    return None


# Read-only endpoint for document tags (tags can only be set during upload)
documents_router = APIRouter(prefix="/v1/documents", tags=["documents", "tags"])


@documents_router.get("/{document_id}/tags", response_model=TagListResponse)
async def get_document_tags(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all tags assigned to a document."""
    doc_query = (
        select(Document)
        .options(selectinload(Document.tags))
        .where(Document.id == document_id)
    )
    result = await db.execute(doc_query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Document not found"}},
        )

    return TagListResponse(
        tags=[TagResponse.model_validate(tag) for tag in document.tags]
    )
