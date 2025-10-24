/**
 * React Hook for Scope Management
 */

import { useState, useCallback } from 'react'
import { scopesApi } from '../api'
import type {
  ScopeListResponse,
  ScopeResponse,
  ScopeCreate,
  ScopeUpdate,
  ScopeListParams,
} from '../api/types'
import { ApiClientError } from '../api/client'

// ============================================================================
// Types
// ============================================================================

interface UseScopesState {
  scopes: ScopeListResponse | null
  selectedScope: ScopeResponse | null
  loading: boolean
  error: string | null
}

interface UseScopesReturn extends UseScopesState {
  // List operations
  fetchScopes: (params?: ScopeListParams) => Promise<void>

  // Single scope operations
  fetchScope: (scopeId: string) => Promise<void>
  createScope: (data: ScopeCreate) => Promise<ScopeResponse | null>
  updateScope: (scopeId: string, data: ScopeUpdate) => Promise<ScopeResponse | null>
  deleteScope: (scopeId: string, hardDelete?: boolean) => Promise<boolean>

  // State management
  clearError: () => void
  clearSelectedScope: () => void
}

// ============================================================================
// Hook
// ============================================================================

export function useScopes(): UseScopesReturn {
  const [state, setState] = useState<UseScopesState>({
    scopes: null,
    selectedScope: null,
    loading: false,
    error: null,
  })

  // Helper to update state
  const updateState = useCallback((updates: Partial<UseScopesState>) => {
    setState(prev => ({ ...prev, ...updates }))
  }, [])

  // Fetch scopes list
  const fetchScopes = useCallback(async (params?: ScopeListParams) => {
    try {
      updateState({ loading: true, error: null })
      const data = await scopesApi.list(params)
      updateState({ scopes: data, loading: false })
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można pobrać listy scope\'ów'
      updateState({ error: errorMessage, loading: false })
    }
  }, [updateState])

  // Fetch single scope
  const fetchScope = useCallback(async (scopeId: string) => {
    try {
      updateState({ loading: true, error: null })
      const data = await scopesApi.get(scopeId)
      updateState({ selectedScope: data, loading: false })
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można pobrać scope\'a'
      updateState({ error: errorMessage, loading: false })
    }
  }, [updateState])

  // Create scope
  const createScope = useCallback(async (data: ScopeCreate): Promise<ScopeResponse | null> => {
    try {
      updateState({ loading: true, error: null })
      const scope = await scopesApi.create(data)
      updateState({ loading: false })

      // Refresh scopes list
      await fetchScopes()

      return scope
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można utworzyć scope\'a'
      updateState({ error: errorMessage, loading: false })
      return null
    }
  }, [updateState, fetchScopes])

  // Update scope
  const updateScope = useCallback(async (
    scopeId: string,
    data: ScopeUpdate
  ): Promise<ScopeResponse | null> => {
    try {
      updateState({ loading: true, error: null })
      const scope = await scopesApi.update(scopeId, data)
      updateState({ loading: false })

      // Refresh scopes list
      await fetchScopes()

      return scope
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można zaktualizować scope\'a'
      updateState({ error: errorMessage, loading: false })
      return null
    }
  }, [updateState, fetchScopes])

  // Delete scope
  const deleteScope = useCallback(async (
    scopeId: string,
    hardDelete = false
  ): Promise<boolean> => {
    try {
      updateState({ loading: true, error: null })
      await scopesApi.delete(scopeId, hardDelete)
      updateState({ loading: false })

      // Refresh scopes list
      await fetchScopes()

      return true
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można usunąć scope\'a'
      updateState({ error: errorMessage, loading: false })
      return false
    }
  }, [updateState, fetchScopes])

  // Clear error
  const clearError = useCallback(() => {
    updateState({ error: null })
  }, [updateState])

  // Clear selected scope
  const clearSelectedScope = useCallback(() => {
    updateState({ selectedScope: null })
  }, [updateState])

  return {
    ...state,
    fetchScopes,
    fetchScope,
    createScope,
    updateScope,
    deleteScope,
    clearError,
    clearSelectedScope,
  }
}

export default useScopes
