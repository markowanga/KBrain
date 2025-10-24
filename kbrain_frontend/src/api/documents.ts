/**
 * Document API Functions
 */

import { apiClient } from './client'
import type {
  DocumentListResponse,
  DocumentDetailResponse,
  DocumentUploadResponse,
  DocumentResponse,
  DocumentStatusUpdate,
  DownloadUrlResponse,
  DocumentListParams,
} from './types'

// ============================================================================
// Document API
// ============================================================================

export const documentsApi = {
  /**
   * List documents in a scope with optional filters and pagination
   */
  async list(scopeId: string, params?: DocumentListParams): Promise<DocumentListResponse> {
    return apiClient.get<DocumentListResponse>(`/v1/scopes/${scopeId}/documents`, { params })
  },

  /**
   * Get detailed information about a specific document
   */
  async get(documentId: string): Promise<DocumentDetailResponse> {
    return apiClient.get<DocumentDetailResponse>(`/v1/documents/${documentId}`)
  },

  /**
   * Upload a document to a scope
   */
  async upload(scopeId: string, file: File): Promise<DocumentUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    return apiClient.postFormData<DocumentUploadResponse>(
      `/v1/scopes/${scopeId}/documents`,
      formData
    )
  },

  /**
   * Delete a document
   * @param documentId - The document ID
   * @param deleteStorage - If true, also delete file from storage
   */
  async delete(documentId: string, deleteStorage = true): Promise<void> {
    return apiClient.delete(`/v1/documents/${documentId}`, {
      params: { delete_storage: deleteStorage },
    })
  },

  /**
   * Update document status
   */
  async updateStatus(documentId: string, data: DocumentStatusUpdate): Promise<DocumentResponse> {
    return apiClient.patch<DocumentResponse>(`/v1/documents/${documentId}/status`, data)
  },

  /**
   * Update document metadata
   */
  async updateMetadata(documentId: string, metadata: Record<string, any>): Promise<DocumentResponse> {
    return apiClient.patch<DocumentResponse>(`/v1/documents/${documentId}/metadata`, {
      metadata,
    })
  },

  /**
   * Get download URL for a document
   */
  async getDownloadUrl(documentId: string, expiration = 3600): Promise<DownloadUrlResponse> {
    return apiClient.get<DownloadUrlResponse>(`/v1/documents/${documentId}/download`, {
      params: { expiration },
    })
  },

  /**
   * Download document content directly
   */
  async download(documentId: string): Promise<Blob> {
    const response = await fetch(
      `${import.meta.env.VITE_API_URL || '/api'}/v1/documents/${documentId}/content`
    )

    if (!response.ok) {
      throw new Error('Failed to download document')
    }

    return response.blob()
  },
}

export default documentsApi
