"""Data models for document processing."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProcessingStatus(str, Enum):
    """Document processing status."""

    ADDED = "added"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class QueueAction(str, Enum):
    """Action type for queue messages."""

    ADD = "add"
    DELETE = "delete"


class Tag(BaseModel):
    """Document tag information."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    name: str
    description: str | None = None
    color: str | None = None
    meta: dict[str, Any] | None = None


class Scope(BaseModel):
    """Document scope information."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    name: str
    description: str | None = None
    allowed_extensions: list[str]
    storage_backend: str | None = None
    is_active: bool = True


class DocumentInfo(BaseModel):
    """Complete document information for processing."""

    id: UUID
    scope_id: UUID
    scope: Scope
    filename: str
    original_name: str
    file_size: int
    mime_type: str | None = None
    file_extension: str
    storage_path: str
    storage_backend: str
    checksum_md5: str | None = None
    checksum_sha256: str | None = None
    status: ProcessingStatus
    upload_date: datetime
    doc_metadata: dict[str, Any] | None = Field(default=None, alias="metadata")
    tags: list[Tag] = Field(default_factory=list)
    download_url: str | None = None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class ProcessingResult(BaseModel):
    """Result of document processing."""

    success: bool
    error_message: str | None = None
    metadata: dict[str, Any] | None = None
    duration_seconds: float | None = None


class ProcessingContext(BaseModel):
    """Context information for processing."""

    document: DocumentInfo
    processor_name: str
    attempt: int = 1
    max_attempts: int = 3
    started_at: datetime = Field(default_factory=datetime.utcnow)


class QueueMessage(BaseModel):
    """Lightweight message for RabbitMQ queue - only IDs, fetch details from API."""

    document_id: UUID
    scope_id: UUID
    action: QueueAction = QueueAction.ADD
    retry_count: int = 0
    # Extra data for delete action (since document won't exist in API)
    storage_path: str | None = None
    file_extension: str | None = None
    original_name: str | None = None
    ragflow_document_id: str | None = None
