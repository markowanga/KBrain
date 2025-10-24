/**
 * React Hook for Statistics
 */

import { useState, useCallback } from 'react'
import { statisticsApi } from '../api'
import type { GlobalStatistics, ScopeStatistics } from '../api/types'
import { ApiClientError } from '../api/client'

// ============================================================================
// Types
// ============================================================================

interface UseStatisticsState {
  globalStats: GlobalStatistics | null
  scopeStats: ScopeStatistics | null
  loading: boolean
  error: string | null
}

interface UseStatisticsReturn extends UseStatisticsState {
  fetchGlobalStatistics: () => Promise<void>
  fetchScopeStatistics: (scopeId: string) => Promise<void>
  clearError: () => void
}

// ============================================================================
// Hook
// ============================================================================

export function useStatistics(): UseStatisticsReturn {
  const [state, setState] = useState<UseStatisticsState>({
    globalStats: null,
    scopeStats: null,
    loading: false,
    error: null,
  })

  // Helper to update state
  const updateState = useCallback((updates: Partial<UseStatisticsState>) => {
    setState(prev => ({ ...prev, ...updates }))
  }, [])

  // Fetch global statistics
  const fetchGlobalStatistics = useCallback(async () => {
    try {
      updateState({ loading: true, error: null })
      const data = await statisticsApi.getGlobal()
      updateState({ globalStats: data, loading: false })
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można pobrać statystyk'
      updateState({ error: errorMessage, loading: false })
    }
  }, [updateState])

  // Fetch scope statistics
  const fetchScopeStatistics = useCallback(async (scopeId: string) => {
    try {
      updateState({ loading: true, error: null })
      const data = await statisticsApi.getScope(scopeId)
      updateState({ scopeStats: data, loading: false })
    } catch (err) {
      const errorMessage = err instanceof ApiClientError
        ? err.message
        : 'Nie można pobrać statystyk scope\'a'
      updateState({ error: errorMessage, loading: false })
    }
  }, [updateState])

  // Clear error
  const clearError = useCallback(() => {
    updateState({ error: null })
  }, [updateState])

  return {
    ...state,
    fetchGlobalStatistics,
    fetchScopeStatistics,
    clearError,
  }
}

export default useStatistics
