/**
 * Statistics API Functions
 */

import { apiClient } from './client'
import type { GlobalStatistics, ScopeStatistics } from './types'

// ============================================================================
// Statistics API
// ============================================================================

export const statisticsApi = {
  /**
   * Get global statistics across all scopes
   */
  async getGlobal(): Promise<GlobalStatistics> {
    return apiClient.get<GlobalStatistics>('/v1/statistics')
  },

  /**
   * Get statistics for a specific scope
   */
  async getScope(scopeId: string): Promise<ScopeStatistics> {
    return apiClient.get<ScopeStatistics>(`/v1/statistics/scopes/${scopeId}`)
  },
}

export default statisticsApi
