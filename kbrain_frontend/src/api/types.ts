/**
 * API Type Definitions for KBrain
 *
 * These types match the backend Pydantic schemas
 */

// ============================================================================
// Common Types
// ============================================================================

export interface PaginationResponse {
  page: number
  per_page: number
  total_pages: number
  total_items: number
  has_next: boolean
  has_prev: boolean
}

export interface ApiError {
  error: {
    code: string
    message: string
    details?: Array<{
      field?: string
      message: string
    }>
  }
}

// ============================================================================
// Scope Types
// ============================================================================

export interface Scope {
  id: string
  name: string
  description: string | null
  allowed_extensions: string[]
  storage_backend: string
  storage_config: Record<string, any> | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ScopeStatistics {
  document_count: number
  total_size: number
  status_breakdown: {
    added: number
    processing: number
    processed: number
    failed: number
  }
}

export interface ScopeResponse extends Scope {
  statistics?: ScopeStatistics
}

export interface ScopeListItem extends Scope {
  document_count: number
  total_size: number
}

export interface ScopeListResponse {
  scopes: ScopeListItem[]
  pagination: PaginationResponse
}

export interface ScopeCreate {
  name: string
  description?: string | null
  allowed_extensions: string[]
  storage_backend?: string
  storage_config?: Record<string, any> | null
}

export interface ScopeUpdate {
  name?: string
  description?: string | null
  allowed_extensions?: string[]
  is_active?: boolean
}

// ============================================================================
// Document Types
// ============================================================================

export type DocumentStatus = 'added' | 'processing' | 'processed' | 'failed'

export interface Document {
  id: string
  scope_id: string
  filename: string
  original_name: string
  file_size: number
  mime_type: string | null
  file_extension: string
  storage_backend: string
  status: DocumentStatus
  upload_date: string
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface DocumentDetailResponse extends Document {
  scope_name: string | null
  storage_path: string
  checksum_md5: string | null
  checksum_sha256: string | null
  processing_started: string | null
  processed_at: string | null
  retry_count: number
  metadata: Record<string, any> | null
}

export interface DocumentResponse extends Document {
  metadata?: Record<string, any> | null
}

export interface DocumentListResponse {
  documents: DocumentResponse[]
  pagination: PaginationResponse
}

export interface DocumentUploadResponse extends Document {
  metadata: Record<string, any> | null
}

export interface DocumentStatusUpdate {
  status: DocumentStatus
  metadata?: Record<string, any>
}

export interface DocumentMetadataUpdate {
  metadata: Record<string, any>
}

export interface DownloadUrlResponse {
  download_url: string
  expires_at: string | null
  filename: string
  file_size: number
}

// ============================================================================
// Statistics Types
// ============================================================================

export interface GlobalStatistics {
  total_scopes: number
  active_scopes: number
  total_documents: number
  total_size: number
  documents_by_status: {
    added: number
    processing: number
    processed: number
    failed: number
  }
  documents_by_extension: Record<string, number>
  storage_backends: Record<string, {
    document_count: number
    total_size: number
  }>
}

// ============================================================================
// Query Parameters
// ============================================================================

export interface ScopeListParams {
  page?: number
  per_page?: number
  is_active?: boolean
  sort?: 'name' | 'created_at'
  order?: 'asc' | 'desc'
}

export interface DocumentListParams {
  page?: number
  per_page?: number
  status?: DocumentStatus
  extension?: string
  sort?: 'upload_date' | 'file_size' | 'original_name'
  order?: 'asc' | 'desc'
  search?: string
}
