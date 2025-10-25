/**
 * Scope API Functions
 */

import { apiClient } from './client'
import type {
  ScopeListResponse,
  ScopeResponse,
  ScopeCreate,
  ScopeUpdate,
  ScopeListParams,
} from './types'

// ============================================================================
// Scope API
// ============================================================================

export const scopesApi = {
  /**
   * List all scopes with optional filters and pagination
   */
  async list(params?: ScopeListParams): Promise<ScopeListResponse> {
    return apiClient.get<ScopeListResponse>('/v1/scopes', { params })
  },

  /**
   * Get a specific scope by ID
   */
  async get(scopeId: string): Promise<ScopeResponse> {
    return apiClient.get<ScopeResponse>(`/v1/scopes/${scopeId}`)
  },

  /**
   * Create a new scope
   */
  async create(data: ScopeCreate): Promise<ScopeResponse> {
    return apiClient.post<ScopeResponse>('/v1/scopes', data)
  },

  /**
   * Update an existing scope
   */
  async update(scopeId: string, data: ScopeUpdate): Promise<ScopeResponse> {
    return apiClient.patch<ScopeResponse>(`/v1/scopes/${scopeId}`, data)
  },

  /**
   * Delete a scope permanently
   * @param scopeId - The scope ID
   */
  async delete(scopeId: string): Promise<void> {
    return apiClient.delete(`/v1/scopes/${scopeId}`)
  },
}

export default scopesApi
