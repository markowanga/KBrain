"""Tag API routes."""
from typing import List
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
    DocumentResponse,
    DocumentTagsUpdate,
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
    # Verify scope exists and is active
    scope_query = select(Scope).where(Scope.id == scope_id, Scope.is_active == True)
    scope = await db.scalar(scope_query)

    if not scope:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Scope not found or inactive"}},
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
        metadata=tag_data.metadata,
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
            and_(
                Tag.scope_id == scope_id,
                Tag.name == tag_data.name,
                Tag.id != tag_id
            )
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

    if tag_data.metadata is not None:
        tag.metadata = tag_data.metadata

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


# Document-Tag relationship endpoints

@router.post("/{tag_id}/documents/{document_id}", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def add_tag_to_document(
    scope_id: UUID,
    tag_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Add a tag to a document."""
    # Verify tag exists and belongs to the scope
    tag_query = select(Tag).where(and_(Tag.id == tag_id, Tag.scope_id == scope_id))
    tag = await db.scalar(tag_query)

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Tag not found"}},
        )

    # Verify document exists and belongs to the scope
    doc_query = select(Document).options(selectinload(Document.tags)).where(
        and_(Document.id == document_id, Document.scope_id == scope_id)
    )
    result = await db.execute(doc_query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Document not found in this scope"}},
        )

    # Check if tag is already assigned
    if tag in document.tags:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "DUPLICATE_RESOURCE", "message": "Tag already assigned to document"}},
        )

    # Add tag to document
    document.tags.append(tag)
    await db.commit()
    await db.refresh(document)

    return DocumentResponse.model_validate(document)


@router.delete("/{tag_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag_from_document(
    scope_id: UUID,
    tag_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove a tag from a document."""
    # Verify tag exists and belongs to the scope
    tag_query = select(Tag).where(and_(Tag.id == tag_id, Tag.scope_id == scope_id))
    tag = await db.scalar(tag_query)

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Tag not found"}},
        )

    # Verify document exists and belongs to the scope
    doc_query = select(Document).options(selectinload(Document.tags)).where(
        and_(Document.id == document_id, Document.scope_id == scope_id)
    )
    result = await db.execute(doc_query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Document not found in this scope"}},
        )

    # Check if tag is assigned
    if tag not in document.tags:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Tag not assigned to document"}},
        )

    # Remove tag from document
    document.tags.remove(tag)
    await db.commit()

    return None


# Endpoint to update all tags on a document at once
documents_router = APIRouter(prefix="/v1/documents", tags=["documents", "tags"])


@documents_router.put("/{document_id}/tags", response_model=DocumentResponse)
async def update_document_tags(
    document_id: UUID,
    tags_update: DocumentTagsUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update all tags assigned to a document."""
    # Get document with current tags
    doc_query = select(Document).options(selectinload(Document.tags)).where(Document.id == document_id)
    result = await db.execute(doc_query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Document not found"}},
        )

    # Verify all tags exist and belong to the same scope as the document
    if tags_update.tag_ids:
        tags_query = select(Tag).where(
            and_(Tag.id.in_(tags_update.tag_ids), Tag.scope_id == document.scope_id)
        )
        result = await db.execute(tags_query)
        tags = result.scalars().all()

        if len(tags) != len(tags_update.tag_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "One or more tags not found or do not belong to the document's scope",
                    }
                },
            )

        # Replace all tags
        document.tags = tags
    else:
        # Clear all tags
        document.tags = []

    await db.commit()
    await db.refresh(document)

    return DocumentResponse.model_validate(document)


@documents_router.get("/{document_id}/tags", response_model=TagListResponse)
async def get_document_tags(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all tags assigned to a document."""
    doc_query = select(Document).options(selectinload(Document.tags)).where(Document.id == document_id)
    result = await db.execute(doc_query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Document not found"}},
        )

    return TagListResponse(tags=[TagResponse.model_validate(tag) for tag in document.tags])
