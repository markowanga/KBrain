"""Document processing routes."""

import hashlib
import mimetypes
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kbrain_backend.config.settings import settings
from kbrain_backend.core.models.document import Document
from kbrain_backend.core.models.scope import Scope
from kbrain_backend.database.connection import get_db
from kbrain_backend.utils.logger import logger
from kbrain_processor_orchestrator import RAGFlowClient

# Router for processing endpoints
router = APIRouter(prefix="/v1/processing", tags=["processing"])

# Global orchestrator, worker and publisher instances (will be set from main.py)
_orchestrator: Any = None
_worker: Any = None
_publisher: Any = None


def set_orchestrator_worker_publisher(
    orchestrator: Any, worker: Any, publisher: Any
) -> None:
    """
    Set global orchestrator, worker and publisher instances.

    Args:
        orchestrator: ProcessingOrchestrator instance
        worker: ProcessingWorker instance
        publisher: QueuePublisher instance
    """
    global _orchestrator, _worker, _publisher
    _orchestrator = orchestrator
    _worker = worker
    _publisher = publisher


def get_orchestrator() -> Any:
    """Get the global orchestrator instance."""
    if _orchestrator is None:
        raise HTTPException(
            status_code=503, detail="Processing orchestrator not initialized"
        )
    return _orchestrator


def get_worker() -> Any:
    """Get the global worker instance."""
    if _worker is None:
        raise HTTPException(status_code=503, detail="Processing worker not initialized")
    return _worker


def get_publisher() -> Any:
    """Get the global publisher instance."""
    if _publisher is None:
        raise HTTPException(status_code=503, detail="Queue publisher not initialized")
    return _publisher


class QueueDocumentRequest(BaseModel):
    """Request to queue a document for processing."""

    document_id: UUID
    scope_id: UUID


class QueueDocumentResponse(BaseModel):
    """Response for queued document."""

    message: str
    document_id: UUID
    scope_id: UUID


class ProcessingStatsResponse(BaseModel):
    """Response with processing statistics."""

    worker_stats: dict[str, Any]
    orchestrator_stats: dict[str, Any]


@router.post("/queue", status_code=202)
async def queue_document_for_processing(
    request: QueueDocumentRequest,
    db: AsyncSession = Depends(get_db),
) -> QueueDocumentResponse:
    """
    Queue a document for processing.

    Publishes a lightweight message (document_id + scope_id) to RabbitMQ.
    The worker will fetch full details from the API and process the document.

    Args:
        request: Document IDs to queue
        db: Database session

    Returns:
        Acknowledgment response
    """
    # Validate document exists
    query = select(Document).where(Document.id == request.document_id)
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Verify scope matches
    if document.scope_id != request.scope_id:
        raise HTTPException(
            status_code=400,
            detail=f"Document {request.document_id} does not belong to scope {request.scope_id}",
        )

    # Publish to RabbitMQ
    publisher = get_publisher()
    await publisher.publish_document(
        document_id=request.document_id,
        scope_id=request.scope_id,
    )

    logger.info(f"Queued document {request.document_id} for processing")

    return QueueDocumentResponse(
        message="Document queued for processing",
        document_id=request.document_id,
        scope_id=request.scope_id,
    )


@router.post("/queue/{document_id}", status_code=202)
async def queue_document_by_id(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> QueueDocumentResponse:
    """
    Queue a document for processing by document ID only.

    Convenience endpoint that fetches scope_id from the document.

    Args:
        document_id: Document ID to queue
        db: Database session

    Returns:
        Acknowledgment response
    """
    # Get document
    query = select(Document).where(Document.id == document_id)
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Publish to RabbitMQ
    publisher = get_publisher()
    await publisher.publish_document(
        document_id=document_id,
        scope_id=UUID(str(document.scope_id)),
    )

    logger.info(f"Queued document {document_id} for processing")

    return QueueDocumentResponse(
        message="Document queued for processing",
        document_id=document_id,
        scope_id=UUID(str(document.scope_id)),
    )


@router.get("/stats", response_model=ProcessingStatsResponse)
async def get_processing_stats() -> ProcessingStatsResponse:
    """
    Get processing statistics.

    Returns worker and orchestrator statistics including:
    - Number of documents processed
    - Processing failures
    - Registered processors
    - Worker uptime

    Returns:
        Processing statistics
    """
    if not settings.processing_enabled:
        raise HTTPException(status_code=503, detail="Processing is disabled")

    worker = get_worker()
    orchestrator = get_orchestrator()

    return ProcessingStatsResponse(
        worker_stats=worker.get_stats(),
        orchestrator_stats=orchestrator.get_processor_stats(),
    )


@router.post("/worker/start", status_code=200)
async def start_worker() -> dict[str, str]:
    """
    Start the processing worker.

    This endpoint starts the RabbitMQ consumer worker.
    Usually the worker starts automatically on application startup.

    Returns:
        Status message
    """
    if not settings.processing_enabled:
        raise HTTPException(status_code=503, detail="Processing is disabled")

    worker = get_worker()

    if worker.is_running:
        return {
            "status": "already_running",
            "message": "Worker is already running",
        }

    await worker.start()
    return {"status": "started", "message": "Worker started successfully"}


@router.post("/worker/stop", status_code=200)
async def stop_worker() -> dict[str, str]:
    """
    Stop the processing worker.

    This endpoint stops the RabbitMQ consumer worker gracefully.

    Returns:
        Status message
    """
    if not settings.processing_enabled:
        raise HTTPException(status_code=503, detail="Processing is disabled")

    worker = get_worker()

    if not worker.is_running:
        return {"status": "not_running", "message": "Worker is not running"}

    await worker.stop()
    return {"status": "stopped", "message": "Worker stopped successfully"}


class RAGFlowDocumentInfo(BaseModel):
    """RAGFlow document info."""

    id: str
    name: str
    status: str
    chunk_count: int
    size: int


class SyncFromRAGFlowResponse(BaseModel):
    """Response for RAGFlow sync operation."""

    total_in_ragflow: int
    already_synced: int
    newly_imported: int
    failed: int
    documents: list[RAGFlowDocumentInfo]


@router.get("/ragflow/documents", response_model=list[RAGFlowDocumentInfo])
async def list_ragflow_documents() -> list[RAGFlowDocumentInfo]:
    """
    List all documents in the configured RAGFlow dataset.

    Returns:
        List of documents from RAGFlow
    """
    if not settings.ragflow_url or not settings.ragflow_api_key:
        raise HTTPException(
            status_code=503,
            detail="RAGFlow is not configured (missing RAGFLOW_URL or RAGFLOW_API_KEY)",
        )

    if not settings.ragflow_dataset_id:
        raise HTTPException(
            status_code=503,
            detail="RAGFlow dataset ID is not configured (missing RAGFLOW_DATASET_ID)",
        )

    client = RAGFlowClient(
        base_url=settings.ragflow_url,
        api_key=settings.ragflow_api_key,
    )

    docs = await client.list_all_documents(dataset_id=settings.ragflow_dataset_id)

    return [
        RAGFlowDocumentInfo(
            id=doc.id,
            name=doc.name,
            status=doc.run,
            chunk_count=doc.chunk_count,
            size=doc.size,
        )
        for doc in docs
    ]


@router.post("/ragflow/sync/{scope_id}", response_model=SyncFromRAGFlowResponse)
async def sync_from_ragflow(
    scope_id: UUID,
    db: AsyncSession = Depends(get_db),
    dry_run: bool = Query(False, description="If true, only report what would be synced"),
) -> SyncFromRAGFlowResponse:
    """
    Sync documents from RAGFlow dataset to KBrain.

    Fetches all documents from the configured RAGFlow dataset and imports
    them into the specified scope. Documents that already exist (matched by
    ragflow_document_id) are skipped.

    Args:
        scope_id: Scope to import documents into
        db: Database session
        dry_run: If true, only report what would be synced without making changes

    Returns:
        Sync results including counts and document list
    """
    # Validate RAGFlow configuration
    if not settings.ragflow_url or not settings.ragflow_api_key:
        raise HTTPException(
            status_code=503,
            detail="RAGFlow is not configured (missing RAGFLOW_URL or RAGFLOW_API_KEY)",
        )

    if not settings.ragflow_dataset_id:
        raise HTTPException(
            status_code=503,
            detail="RAGFlow dataset ID is not configured (missing RAGFLOW_DATASET_ID)",
        )

    # Validate scope exists
    scope_query = select(Scope).where(Scope.id == scope_id)
    scope_result = await db.execute(scope_query)
    scope = scope_result.scalar_one_or_none()

    if not scope:
        raise HTTPException(status_code=404, detail="Scope not found")

    # Get RAGFlow documents
    client = RAGFlowClient(
        base_url=settings.ragflow_url,
        api_key=settings.ragflow_api_key,
    )

    ragflow_docs = await client.list_all_documents(dataset_id=settings.ragflow_dataset_id)
    logger.info(f"Found {len(ragflow_docs)} documents in RAGFlow dataset")

    # Get existing documents with ragflow_document_id
    existing_query = select(Document).where(Document.scope_id == scope_id)
    existing_result = await db.execute(existing_query)
    existing_docs = existing_result.scalars().all()

    # Build set of existing ragflow_document_ids
    existing_ragflow_ids: set[str] = set()
    for doc in existing_docs:
        if doc.processing_result:
            for processor_result in doc.processing_result.values():
                if isinstance(processor_result, dict):
                    ragflow_data = processor_result.get("ragflow", {})
                    if isinstance(ragflow_data, dict):
                        ragflow_id = ragflow_data.get("ragflow_document_id")
                        if ragflow_id:
                            existing_ragflow_ids.add(ragflow_id)

    # Process RAGFlow documents
    already_synced = 0
    newly_imported = 0
    failed = 0
    imported_docs: list[RAGFlowDocumentInfo] = []

    for ragflow_doc in ragflow_docs:
        doc_info = RAGFlowDocumentInfo(
            id=ragflow_doc.id,
            name=ragflow_doc.name,
            status=ragflow_doc.run,
            chunk_count=ragflow_doc.chunk_count,
            size=ragflow_doc.size,
        )

        # Check if already synced
        if ragflow_doc.id in existing_ragflow_ids:
            already_synced += 1
            continue

        if dry_run:
            newly_imported += 1
            imported_docs.append(doc_info)
            continue

        # Download file from RAGFlow and store locally
        try:
            # Download file content
            file_bytes = await client.download_document(
                dataset_id=settings.ragflow_dataset_id,
                document_id=ragflow_doc.id,
            )

            if not file_bytes:
                logger.error(f"Failed to download {ragflow_doc.name} from RAGFlow")
                failed += 1
                continue

            # Extract file extension from name
            name_parts = ragflow_doc.name.rsplit(".", 1)
            file_ext = name_parts[1].lower() if len(name_parts) > 1 else ""

            # Generate unique filename and storage path
            unique_filename = (
                f"{datetime.now().strftime('%Y-%m-%d')}_{uuid4().hex[:12]}.{file_ext}"
            )
            storage_path = (
                f"scopes/{scope.name}/{datetime.now().year}/"
                f"{datetime.now().month:02d}/{unique_filename}"
            )

            # Save to local storage (lazy import to avoid circular dependency)
            from kbrain_backend.api.routes.documents import get_storage
            storage = get_storage()
            success = await storage.save_file(storage_path, file_bytes)
            if not success:
                logger.error(f"Failed to save {ragflow_doc.name} to storage")
                failed += 1
                continue

            # Calculate checksums
            md5_hash = hashlib.md5(file_bytes).hexdigest()
            sha256_hash = hashlib.sha256(file_bytes).hexdigest()

            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(ragflow_doc.name)

            # Create document record
            new_doc = Document(
                scope_id=scope_id,
                filename=unique_filename,
                original_name=ragflow_doc.name,
                file_size=len(file_bytes),
                mime_type=mime_type,
                file_extension=file_ext,
                storage_path=storage_path,
                storage_backend="local",
                checksum_md5=md5_hash,
                checksum_sha256=sha256_hash,
                status="processed",
                upload_date=datetime.utcnow(),
                processing_result={
                    "ragflow_import": {
                        "ragflow": {
                            "ragflow_document_id": ragflow_doc.id,
                            "status": ragflow_doc.run,
                            "chunk_count": ragflow_doc.chunk_count,
                        },
                        "imported_at": datetime.utcnow().isoformat(),
                        "source": "ragflow_sync",
                    }
                },
            )

            db.add(new_doc)
            newly_imported += 1
            imported_docs.append(doc_info)

            logger.info(
                f"Imported document from RAGFlow: {ragflow_doc.name} -> {storage_path}"
            )

        except Exception as e:
            logger.error(f"Failed to import document {ragflow_doc.name}: {e}")
            failed += 1

    if not dry_run:
        await db.commit()

    return SyncFromRAGFlowResponse(
        total_in_ragflow=len(ragflow_docs),
        already_synced=already_synced,
        newly_imported=newly_imported,
        failed=failed,
        documents=imported_docs,
    )
