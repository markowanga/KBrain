/**
 * API Module Entry Point
 *
 * Exports all API functions and types
 */

export { apiClient, ApiClientError } from './client'
export { scopesApi } from './scopes'
export { documentsApi } from './documents'
export { statisticsApi } from './statistics'
export { tagsApi } from './tags'

export type * from './types'
