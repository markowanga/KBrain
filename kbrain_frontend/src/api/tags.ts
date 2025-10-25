/**
 * Tags API Functions
 */

import { apiClient } from './client'
import type {
  Tag,
  TagCreate,
  TagUpdate,
  TagListResponse,
  DocumentResponse,
} from './types'

// ============================================================================
// Tags API
// ============================================================================

export const tagsApi = {
  /**
   * Get all tags for a scope
   */
  async list(scopeId: string): Promise<Tag[]> {
    const response = await apiClient.get<TagListResponse>(`/v1/scopes/${scopeId}/tags`)
    return response.tags
  },

  /**
   * Get a specific tag
   */
  async get(scopeId: string, tagId: string): Promise<Tag> {
    return apiClient.get<Tag>(`/v1/scopes/${scopeId}/tags/${tagId}`)
  },

  /**
   * Create a new tag in a scope
   */
  async create(scopeId: string, data: TagCreate): Promise<Tag> {
    return apiClient.post<Tag>(`/v1/scopes/${scopeId}/tags`, data)
  },

  /**
   * Update a tag
   */
  async update(scopeId: string, tagId: string, data: TagUpdate): Promise<Tag> {
    return apiClient.patch<Tag>(`/v1/scopes/${scopeId}/tags/${tagId}`, data)
  },

  /**
   * Delete a tag
   */
  async delete(scopeId: string, tagId: string): Promise<void> {
    return apiClient.delete(`/v1/scopes/${scopeId}/tags/${tagId}`)
  },
}

export default tagsApi
