"""Document API routes."""

import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from kbrain_backend.api.schemas import (
    DocumentResponse,
    DocumentListResponse,
    DocumentUploadResponse,
    DocumentDetailResponse,
    DocumentStatusUpdate,
    DocumentMetadataUpdate,
    DownloadUrlResponse,
    PaginationResponse,
)
from kbrain_backend.core.models.scope import Scope
from kbrain_backend.core.models.document import Document
from kbrain_backend.database.connection import get_db
from kbrain_backend.config.settings import settings

# We'll use the storage from main.py, for now we'll import it
# In a real implementation, this should be dependency-injected
from kbrain_storage import BaseFileStorage

router = APIRouter(tags=["documents"])


# Placeholder for storage - will be injected
_storage: Optional[BaseFileStorage] = None


def set_storage(storage: BaseFileStorage) -> None:
    """Set the storage backend."""
    global _storage
    _storage = storage


def get_storage() -> BaseFileStorage:
    """Get the storage backend."""
    if _storage is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Storage backend not initialized",
        )
    return _storage


@router.get("/v1/scopes/{scope_id}/documents", response_model=DocumentListResponse)
async def list_documents(
    scope_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    status_filter: Optional[str] = Query(None, alias="status"),
    extension: Optional[str] = Query(None),
    sort: str = Query("upload_date", pattern="^(upload_date|file_size|original_name)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """List documents in a scope."""
    # Verify scope exists
    scope_query = select(Scope).where(Scope.id == scope_id)
    scope = await db.scalar(scope_query)
    if not scope:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Scope not found"}},
        )

    # Build query
    query = select(Document).options(selectinload(Document.tags)).where(Document.scope_id == scope_id)

    # Apply filters
    if status_filter:
        query = query.where(Document.status == status_filter)
    if extension:
        query = query.where(Document.file_extension == extension)
    if search:
        query = query.where(Document.original_name.ilike(f"%{search}%"))

    # Count total items
    count_query = select(func.count()).select_from(query.subquery())
    total_items = await db.scalar(count_query)

    # Apply sorting
    sort_column = getattr(Document, sort)
    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)

    # Execute query
    result = await db.execute(query)
    documents = result.scalars().all()

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

    document_responses = [DocumentResponse.model_validate(doc) for doc in documents]

    return DocumentListResponse(documents=document_responses, pagination=pagination)


@router.get("/v1/documents/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> DocumentDetailResponse:
    """Get details of a specific document."""
    query = select(Document).options(selectinload(Document.tags)).where(Document.id == document_id)
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Document not found"}},
        )

    # Get scope name
    scope_query = select(Scope).where(Scope.id == document.scope_id)
    scope = await db.scalar(scope_query)

    response = DocumentDetailResponse(
        id=cast(UUID, document.id),
        scope_id=cast(UUID, document.scope_id),
        scope_name=scope.name if scope else None,
        filename=document.filename,
        original_name=document.original_name,
        file_size=document.file_size,
        mime_type=document.mime_type,
        file_extension=document.file_extension,
        storage_path=document.storage_path,
        storage_backend=document.storage_backend,
        checksum_md5=document.checksum_md5,
        checksum_sha256=document.checksum_sha256,
        status=document.status,
        upload_date=document.upload_date,
        processing_started=document.processing_started,
        processed_at=document.processed_at,
        retry_count=document.retry_count,
        error_message=document.error_message,
        metadata=document.doc_metadata,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )

    return response


@router.post(
    "/v1/scopes/{scope_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    scope_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    storage: BaseFileStorage = Depends(get_storage),
) -> DocumentUploadResponse:
    """Upload a new document to a scope."""
    # Verify scope exists and is active
    scope_query = select(Scope).where(Scope.id == scope_id, Scope.is_active)
    scope = await db.scalar(scope_query)

    if not scope:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {"code": "NOT_FOUND", "message": "Scope not found or inactive"}
            },
        )

    # Get file extension
    file_ext = Path(file.filename).suffix.lstrip(".").lower() if file.filename else ""

    # Validate file extension
    if file_ext not in scope.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid file extension",
                    "details": [
                        {
                            "field": "file",
                            "message": f"File extension '{file_ext}' not allowed in this scope. Allowed: {', '.join(scope.allowed_extensions)}",
                        }
                    ],
                }
            },
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Check file size
    if file_size > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": f"File size exceeds maximum allowed size of {settings.max_file_size} bytes",
                }
            },
        )

    # Generate unique filename
    unique_filename = (
        f"{datetime.now().strftime('%Y-%m-%d')}_{uuid4().hex[:12]}.{file_ext}"
    )

    # Generate storage path (scope-based)
    storage_path = f"scopes/{scope.name}/{datetime.now().year}/{datetime.now().month:02d}/{unique_filename}"

    # Calculate checksums
    md5_hash = hashlib.md5(content).hexdigest()
    sha256_hash = hashlib.sha256(content).hexdigest()

    # Get MIME type
    mime_type, _ = mimetypes.guess_type(file.filename or "")

    # Save file to storage
    try:
        success = await storage.save_file(storage_path, content)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "STORAGE_ERROR",
                        "message": "Failed to save file to storage",
                    }
                },
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "STORAGE_ERROR", "message": str(e)}},
        )

    # Create document record
    document = Document(
        scope_id=scope_id,
        filename=unique_filename,
        original_name=file.filename,
        file_size=file_size,
        mime_type=mime_type,
        file_extension=file_ext,
        storage_path=storage_path,
        storage_backend=scope.storage_backend,
        checksum_md5=md5_hash,
        checksum_sha256=sha256_hash,
        status="added",
        upload_date=datetime.utcnow(),
    )

    db.add(document)
    await db.commit()
    await db.refresh(document, attribute_names=["tags"])

    return DocumentUploadResponse(
        id=cast(UUID, document.id),
        scope_id=cast(UUID, document.scope_id),
        filename=document.filename,
        original_name=document.original_name,
        file_size=document.file_size,
        mime_type=document.mime_type,
        file_extension=document.file_extension,
        storage_backend=document.storage_backend,
        status=document.status,
        upload_date=document.upload_date,
        metadata=document.doc_metadata,
        tags=[],
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.get("/v1/documents/{document_id}/download", response_model=DownloadUrlResponse)
async def get_download_url(
    document_id: UUID,
    expiration: int = Query(3600, ge=1, le=86400),
    db: AsyncSession = Depends(get_db),
) -> DownloadUrlResponse:
    """Get a download URL for a document."""
    query = select(Document).where(Document.id == document_id)
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Document not found"}},
        )

    # For local storage, we'll use a proxy download endpoint
    # In production, this would generate signed URLs for S3/Azure
    download_url = f"/v1/documents/{document_id}/content"

    return DownloadUrlResponse(
        download_url=download_url,
        expires_at=None,  # No expiration for local proxy
        filename=document.original_name,
        file_size=document.file_size,
    )


@router.get("/v1/documents/{document_id}/content")
async def download_document_content(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    storage: BaseFileStorage = Depends(get_storage),
) -> StreamingResponse:
    """Directly download document content (proxy download)."""
    query = select(Document).where(Document.id == document_id)
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Document not found"}},
        )

    # Read file from storage
    try:
        content = await storage.read_file(document.storage_path)
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "File not found in storage",
                    }
                },
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "STORAGE_ERROR", "message": str(e)}},
        )

    # Return file as streaming response
    return StreamingResponse(
        iter([content]),
        media_type=document.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{document.original_name}"',
            "Content-Length": str(document.file_size),
        },
    )


@router.delete("/v1/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    delete_storage: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    storage: BaseFileStorage = Depends(get_storage),
) -> None:
    """Delete a document."""
    query = select(Document).where(Document.id == document_id)
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Document not found"}},
        )

    # Delete from storage if requested
    if delete_storage:
        try:
            await storage.delete_file(document.storage_path)
        except Exception:
            # Log error but continue with database deletion
            pass

    # Delete from database
    await db.delete(document)
    await db.commit()

    return None


@router.patch("/v1/documents/{document_id}/status", response_model=DocumentResponse)
async def update_document_status(
    document_id: UUID,
    status_update: DocumentStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Update document status."""
    query = select(Document).options(selectinload(Document.tags)).where(Document.id == document_id)
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Document not found"}},
        )

    # Update status
    old_status = document.status
    document.status = status_update.status

    # Update timestamps based on status
    if status_update.status == "processing" and old_status != "processing":
        document.processing_started = datetime.utcnow()
    elif status_update.status == "processed" and old_status != "processed":
        document.processed_at = datetime.utcnow()

    # Update metadata if provided
    if status_update.metadata:
        if document.doc_metadata:
            document.doc_metadata.update(status_update.metadata)
        else:
            document.doc_metadata = status_update.metadata

    await db.commit()
    await db.refresh(document)

    return DocumentResponse.model_validate(document)


@router.patch("/v1/documents/{document_id}/metadata", response_model=DocumentResponse)
async def update_document_metadata(
    document_id: UUID,
    metadata_update: DocumentMetadataUpdate,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Update document metadata."""
    query = select(Document).options(selectinload(Document.tags)).where(Document.id == document_id)
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": "Document not found"}},
        )

    # Update metadata
    if document.doc_metadata:
        document.doc_metadata.update(metadata_update.metadata)
    else:
        document.doc_metadata = metadata_update.metadata

    await db.commit()
    await db.refresh(document)

    return DocumentResponse.model_validate(document)
