/**
 * Base API Client for KBrain
 *
 * Provides centralized HTTP request handling with error management,
 * loading states, and type safety.
 */

import type { ApiError } from './types'

// ============================================================================
// Configuration
// ============================================================================

// API base URL - /api prefix required by nginx routing
// Backend receives full paths with /api prefix (e.g., /api/v1/scopes)
// Vite proxy and Nginx both preserve /api prefix
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

// ============================================================================
// Types
// ============================================================================

interface RequestOptions extends RequestInit {
  params?: Record<string, any>
}

export class ApiClientError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public code?: string,
    public details?: Array<{ field?: string; message: string }>
  ) {
    super(message)
    this.name = 'ApiClientError'
  }
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Build URL with query parameters
 */
function buildUrl(endpoint: string, params?: Record<string, any>): string {
  // Build base URL - handle both absolute and relative paths
  let urlString = API_BASE_URL + endpoint

  // Add query parameters if present
  if (params) {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value))
      }
    })
    const queryString = searchParams.toString()
    if (queryString) {
      urlString += `?${queryString}`
    }
  }

  return urlString
}

/**
 * Parse error response
 */
async function parseError(response: Response): Promise<never> {
  let errorData: ApiError | null = null

  try {
    errorData = await response.json()
  } catch {
    // If JSON parsing fails, use status text
  }

  if (errorData?.error) {
    throw new ApiClientError(
      errorData.error.message,
      response.status,
      errorData.error.code,
      errorData.error.details
    )
  }

  throw new ApiClientError(
    response.statusText || 'Request failed',
    response.status
  )
}

/**
 * Handle API response
 */
async function handleResponse<T>(response: Response): Promise<T> {
  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T
  }

  if (!response.ok) {
    await parseError(response)
  }

  try {
    return await response.json()
  } catch (error) {
    throw new ApiClientError(
      'Failed to parse response',
      response.status
    )
  }
}

// ============================================================================
// API Client
// ============================================================================

export const apiClient = {
  /**
   * GET request
   */
  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    const url = buildUrl(endpoint, options?.params)

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    })

    return handleResponse<T>(response)
  },

  /**
   * POST request
   */
  async post<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    const url = buildUrl(endpoint, options?.params)

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    })

    return handleResponse<T>(response)
  },

  /**
   * POST request with FormData (for file uploads)
   */
  async postFormData<T>(endpoint: string, formData: FormData, options?: RequestOptions): Promise<T> {
    const url = buildUrl(endpoint, options?.params)

    const response = await fetch(url, {
      method: 'POST',
      // Don't set Content-Type for FormData - browser will set it with boundary
      body: formData,
      ...options,
    })

    return handleResponse<T>(response)
  },

  /**
   * PATCH request
   */
  async patch<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    const url = buildUrl(endpoint, options?.params)

    const response = await fetch(url, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    })

    return handleResponse<T>(response)
  },

  /**
   * DELETE request
   */
  async delete<T = void>(endpoint: string, options?: RequestOptions): Promise<T> {
    const url = buildUrl(endpoint, options?.params)

    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    })

    return handleResponse<T>(response)
  },
}

export default apiClient
