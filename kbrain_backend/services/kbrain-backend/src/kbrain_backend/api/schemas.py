"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Common Schemas
# ============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=200, description="Items per page")


class PaginationResponse(BaseModel):
    """Pagination response metadata."""
    page: int
    per_page: int
    total_pages: int
    total_items: int
    has_next: bool = False
    has_prev: bool = False


class ErrorDetail(BaseModel):
    """Error detail for validation errors."""
    field: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: Dict[str, Any]


# ============================================================================
# Scope Schemas
# ============================================================================

class ScopeBase(BaseModel):
    """Base scope schema."""
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    allowed_extensions: List[str] = Field(..., min_items=1)
    storage_backend: Optional[str] = Field(None, max_length=50)
    storage_config: Optional[Dict[str, Any]] = None


class ScopeCreate(ScopeBase):
    """Schema for creating a scope."""
    pass


class ScopeUpdate(BaseModel):
    """Schema for updating a scope."""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    allowed_extensions: Optional[List[str]] = Field(None, min_items=1)
    is_active: Optional[bool] = None


class ScopeStatistics(BaseModel):
    """Scope statistics."""
    document_count: int = 0
    total_size: int = 0
    status_breakdown: Optional[Dict[str, int]] = None


class ScopeResponse(ScopeBase):
    """Schema for scope response."""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    statistics: Optional[ScopeStatistics] = None

    model_config = ConfigDict(from_attributes=True)


class ScopeListItem(BaseModel):
    """Schema for scope list item (simplified)."""
    id: UUID
    name: str
    description: Optional[str]
    allowed_extensions: List[str]
    storage_backend: str
    is_active: bool
    document_count: int = 0
    total_size: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScopeListResponse(BaseModel):
    """Schema for scope list response."""
    scopes: List[ScopeListItem]
    pagination: PaginationResponse


# ============================================================================
# Document Schemas
# ============================================================================

class DocumentBase(BaseModel):
    """Base document schema."""
    filename: str
    original_name: str
    file_size: int
    mime_type: Optional[str] = None
    file_extension: str
    storage_path: str
    storage_backend: str


class DocumentCreate(BaseModel):
    """Schema for creating a document (used internally)."""
    scope_id: UUID
    filename: str
    original_name: str
    file_size: int
    mime_type: Optional[str] = None
    file_extension: str
    storage_path: str
    storage_backend: str
    checksum_md5: Optional[str] = None
    checksum_sha256: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    id: UUID
    scope_id: UUID
    status: str
    upload_date: datetime
    processing_started: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(None, validation_alias='doc_metadata')
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DocumentDetailResponse(DocumentResponse):
    """Schema for detailed document response."""
    scope_name: Optional[str] = None
    checksum_md5: Optional[str] = None
    checksum_sha256: Optional[str] = None
    retry_count: int = 0


class DocumentListResponse(BaseModel):
    """Schema for document list response."""
    documents: List[DocumentResponse]
    pagination: PaginationResponse


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""
    id: UUID
    scope_id: UUID
    filename: str
    original_name: str
    file_size: int
    mime_type: Optional[str]
    file_extension: str
    storage_backend: str
    status: str
    upload_date: datetime
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class DocumentStatusUpdate(BaseModel):
    """Schema for updating document status."""
    status: str = Field(..., pattern="^(added|processing|processed|failed)$")
    metadata: Optional[Dict[str, Any]] = None


class DocumentMetadataUpdate(BaseModel):
    """Schema for updating document metadata."""
    metadata: Dict[str, Any]


class DownloadUrlResponse(BaseModel):
    """Schema for download URL response."""
    download_url: str
    expires_at: Optional[datetime] = None
    filename: str
    file_size: int


class BatchUploadResult(BaseModel):
    """Schema for individual batch upload result."""
    filename: str
    status: str  # "success" or "error"
    document: Optional[DocumentUploadResponse] = None
    error: Optional[Dict[str, str]] = None


class BatchUploadResponse(BaseModel):
    """Schema for batch upload response."""
    results: List[BatchUploadResult]
    summary: Dict[str, int]


# ============================================================================
# Statistics Schemas
# ============================================================================

class GlobalStatistics(BaseModel):
    """Schema for global statistics."""
    total_scopes: int
    total_documents: int
    total_storage_size: int
    documents_by_status: Dict[str, int]
    documents_by_extension: Dict[str, int]
    storage_backends: Dict[str, int]
    recent_uploads: Dict[str, int]


class ScopeStatisticsDetail(BaseModel):
    """Schema for detailed scope statistics."""
    scope_id: UUID
    scope_name: str
    total_documents: int
    total_size: int
    documents_by_status: Dict[str, int]
    documents_by_extension: Dict[str, int]
    upload_timeline: Optional[List[Dict[str, Any]]] = None
    processing_performance: Optional[Dict[str, Any]] = None


# ============================================================================
# Health Check Schemas
# ============================================================================

class ServiceStatus(BaseModel):
    """Service status."""
    database: str
    storage: str
    queue: str = "healthy"


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime
    services: ServiceStatus


class VersionResponse(BaseModel):
    """Version info response."""
    api_version: str
    build: str
    commit: str
    timestamp: datetime
