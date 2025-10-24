/**
 * React Hook for Tag Management
 */

import { useState, useCallback } from 'react'
import { tagsApi } from '../api'
import type { Tag, TagCreate, TagUpdate } from '../api/types'
import { ApiClientError } from '../api/client'

// ============================================================================
// Types
// ============================================================================

interface UseTagsState {
  tags: Tag[] | null
  selectedTag: Tag | null
  loading: boolean
  error: string | null
}

interface UseTagsReturn extends UseTagsState {
  // List operations
  fetchTags: (scopeId: string) => Promise<void>

  // Single tag operations
  fetchTag: (scopeId: string, tagId: string) => Promise<void>
  createTag: (scopeId: string, data: TagCreate) => Promise<Tag | null>
  updateTag: (scopeId: string, tagId: string, data: TagUpdate) => Promise<Tag | null>
  deleteTag: (scopeId: string, tagId: string) => Promise<boolean>

  // Document-tag operations
  addTagToDocument: (scopeId: string, tagId: string, documentId: string) => Promise<boolean>
  removeTagFromDocument: (scopeId: string, tagId: string, documentId: string) => Promise<boolean>

  // State management
  clearError: () => void
  clearSelectedTag: () => void
}

// ============================================================================
// Hook
// ============================================================================

export function useTags(): UseTagsReturn {
  const [state, setState] = useState<UseTagsState>({
    tags: null,
    selectedTag: null,
    loading: false,
    error: null,
  })

  // Helper to update state
  const updateState = useCallback((updates: Partial<UseTagsState>) => {
    setState(prev => ({ ...prev, ...updates }))
  }, [])

  // Fetch tags list for a scope
  const fetchTags = useCallback(async (scopeId: string) => {
    try {
      updateState({ loading: true, error: null })
      const data = await tagsApi.list(scopeId)
      updateState({ tags: data, loading: false })
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można pobrać listy tagów'
      updateState({ error: errorMessage, loading: false })
    }
  }, [updateState])

  // Fetch single tag
  const fetchTag = useCallback(async (scopeId: string, tagId: string) => {
    try {
      updateState({ loading: true, error: null })
      const data = await tagsApi.get(scopeId, tagId)
      updateState({ selectedTag: data, loading: false })
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można pobrać tagu'
      updateState({ error: errorMessage, loading: false })
    }
  }, [updateState])

  // Create tag
  const createTag = useCallback(async (
    scopeId: string,
    data: TagCreate
  ): Promise<Tag | null> => {
    try {
      updateState({ loading: true, error: null })
      const tag = await tagsApi.create(scopeId, data)
      updateState({ loading: false })

      // Refresh tags list
      await fetchTags(scopeId)

      return tag
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można utworzyć tagu'
      updateState({ error: errorMessage, loading: false })
      return null
    }
  }, [updateState, fetchTags])

  // Update tag
  const updateTag = useCallback(async (
    scopeId: string,
    tagId: string,
    data: TagUpdate
  ): Promise<Tag | null> => {
    try {
      updateState({ loading: true, error: null })
      const tag = await tagsApi.update(scopeId, tagId, data)
      updateState({ loading: false })

      // Refresh tags list
      await fetchTags(scopeId)

      return tag
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można zaktualizować tagu'
      updateState({ error: errorMessage, loading: false })
      return null
    }
  }, [updateState, fetchTags])

  // Delete tag
  const deleteTag = useCallback(async (
    scopeId: string,
    tagId: string
  ): Promise<boolean> => {
    try {
      updateState({ loading: true, error: null })
      await tagsApi.delete(scopeId, tagId)
      updateState({ loading: false })

      // Refresh tags list
      await fetchTags(scopeId)

      return true
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można usunąć tagu'
      updateState({ error: errorMessage, loading: false })
      return false
    }
  }, [updateState, fetchTags])

  // Add tag to document
  const addTagToDocument = useCallback(async (
    scopeId: string,
    tagId: string,
    documentId: string
  ): Promise<boolean> => {
    try {
      updateState({ loading: true, error: null })
      await tagsApi.addToDocument(scopeId, tagId, documentId)
      updateState({ loading: false })
      return true
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można dodać tagu do dokumentu'
      updateState({ error: errorMessage, loading: false })
      return false
    }
  }, [updateState])

  // Remove tag from document
  const removeTagFromDocument = useCallback(async (
    scopeId: string,
    tagId: string,
    documentId: string
  ): Promise<boolean> => {
    try {
      updateState({ loading: true, error: null })
      await tagsApi.removeFromDocument(scopeId, tagId, documentId)
      updateState({ loading: false })
      return true
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można usunąć tagu z dokumentu'
      updateState({ error: errorMessage, loading: false })
      return false
    }
  }, [updateState])

  // Clear error
  const clearError = useCallback(() => {
    updateState({ error: null })
  }, [updateState])

  // Clear selected tag
  const clearSelectedTag = useCallback(() => {
    updateState({ selectedTag: null })
  }, [updateState])

  return {
    ...state,
    fetchTags,
    fetchTag,
    createTag,
    updateTag,
    deleteTag,
    addTagToDocument,
    removeTagFromDocument,
    clearError,
    clearSelectedTag,
  }
}

export default useTags
