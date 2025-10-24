/**
 * React Hook for Document Management
 */

import { useState, useCallback } from 'react'
import { documentsApi } from '../api'
import type {
  DocumentListResponse,
  DocumentDetailResponse,
  DocumentUploadResponse,
  DocumentStatusUpdate,
  DocumentListParams,
} from '../api/types'
import { ApiClientError } from '../api/client'

// ============================================================================
// Types
// ============================================================================

interface UseDocumentsState {
  documents: DocumentListResponse | null
  selectedDocument: DocumentDetailResponse | null
  loading: boolean
  error: string | null
  uploadProgress: number | null
}

interface UseDocumentsReturn extends UseDocumentsState {
  // List operations
  fetchDocuments: (scopeId: string, params?: DocumentListParams) => Promise<void>

  // Single document operations
  fetchDocument: (documentId: string) => Promise<void>
  uploadDocument: (scopeId: string, file: File) => Promise<DocumentUploadResponse | null>
  deleteDocument: (documentId: string, deleteStorage?: boolean) => Promise<boolean>
  updateDocumentStatus: (documentId: string, data: DocumentStatusUpdate) => Promise<boolean>
  updateDocumentMetadata: (documentId: string, metadata: Record<string, any>) => Promise<boolean>
  downloadDocument: (documentId: string, filename?: string) => Promise<void>

  // State management
  clearError: () => void
  clearSelectedDocument: () => void
}

// ============================================================================
// Hook
// ============================================================================

export function useDocuments(): UseDocumentsReturn {
  const [state, setState] = useState<UseDocumentsState>({
    documents: null,
    selectedDocument: null,
    loading: false,
    error: null,
    uploadProgress: null,
  })

  // Helper to update state
  const updateState = useCallback((updates: Partial<UseDocumentsState>) => {
    setState(prev => ({ ...prev, ...updates }))
  }, [])

  // Fetch documents list
  const fetchDocuments = useCallback(async (
    scopeId: string,
    params?: DocumentListParams
  ) => {
    try {
      updateState({ loading: true, error: null })
      const data = await documentsApi.list(scopeId, params)
      updateState({ documents: data, loading: false })
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można pobrać listy dokumentów'
      updateState({ error: errorMessage, loading: false })
    }
  }, [updateState])

  // Fetch single document
  const fetchDocument = useCallback(async (documentId: string) => {
    try {
      updateState({ loading: true, error: null })
      const data = await documentsApi.get(documentId)
      updateState({ selectedDocument: data, loading: false })
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można pobrać dokumentu'
      updateState({ error: errorMessage, loading: false })
    }
  }, [updateState])

  // Upload document
  const uploadDocument = useCallback(async (
    scopeId: string,
    file: File
  ): Promise<DocumentUploadResponse | null> => {
    try {
      updateState({ loading: true, error: null, uploadProgress: 0 })
      const document = await documentsApi.upload(scopeId, file)
      updateState({ loading: false, uploadProgress: null })

      // Refresh documents list
      await fetchDocuments(scopeId)

      return document
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można przesłać dokumentu'
      updateState({ error: errorMessage, loading: false, uploadProgress: null })
      return null
    }
  }, [updateState, fetchDocuments])

  // Delete document
  const deleteDocument = useCallback(async (
    documentId: string,
    deleteStorage = true
  ): Promise<boolean> => {
    try {
      updateState({ loading: true, error: null })
      await documentsApi.delete(documentId, deleteStorage)
      updateState({ loading: false })
      return true
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można usunąć dokumentu'
      updateState({ error: errorMessage, loading: false })
      return false
    }
  }, [updateState])

  // Update document status
  const updateDocumentStatus = useCallback(async (
    documentId: string,
    data: DocumentStatusUpdate
  ): Promise<boolean> => {
    try {
      updateState({ loading: true, error: null })
      await documentsApi.updateStatus(documentId, data)
      updateState({ loading: false })

      // Refresh document details if we have one selected
      if (state.selectedDocument?.id === documentId) {
        await fetchDocument(documentId)
      }

      return true
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można zaktualizować statusu dokumentu'
      updateState({ error: errorMessage, loading: false })
      return false
    }
  }, [updateState, fetchDocument, state.selectedDocument])

  // Update document metadata
  const updateDocumentMetadata = useCallback(async (
    documentId: string,
    metadata: Record<string, any>
  ): Promise<boolean> => {
    try {
      updateState({ loading: true, error: null })
      await documentsApi.updateMetadata(documentId, metadata)
      updateState({ loading: false })

      // Refresh document details if we have one selected
      if (state.selectedDocument?.id === documentId) {
        await fetchDocument(documentId)
      }

      return true
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można zaktualizować metadanych dokumentu'
      updateState({ error: errorMessage, loading: false })
      return false
    }
  }, [updateState, fetchDocument, state.selectedDocument])

  // Download document
  const downloadDocument = useCallback(async (
    documentId: string,
    filename?: string
  ): Promise<void> => {
    try {
      updateState({ loading: true, error: null })
      const blob = await documentsApi.download(documentId)

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename || 'document'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      updateState({ loading: false })
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można pobrać dokumentu'
      updateState({ error: errorMessage, loading: false })
    }
  }, [updateState])

  // Clear error
  const clearError = useCallback(() => {
    updateState({ error: null })
  }, [updateState])

  // Clear selected document
  const clearSelectedDocument = useCallback(() => {
    updateState({ selectedDocument: null })
  }, [updateState])

  return {
    ...state,
    fetchDocuments,
    fetchDocument,
    uploadDocument,
    deleteDocument,
    updateDocumentStatus,
    updateDocumentMetadata,
    downloadDocument,
    clearError,
    clearSelectedDocument,
  }
}

export default useDocuments
