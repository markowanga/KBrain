/**
 * Utility functions for formatting data
 */

/**
 * Format bytes to human-readable string
 */
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

/**
 * Get Tailwind CSS classes for document status badge
 */
export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    added: 'bg-blue-100 text-blue-800',
    processing: 'bg-yellow-100 text-yellow-800',
    processed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  }

  return colors[status] || 'bg-gray-100 text-gray-800'
}

/**
 * Format date to locale string
 */
export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('pl-PL', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * Format date to short locale string
 */
export function formatDateShort(date: string | Date): string {
  return new Date(date).toLocaleDateString('pl-PL')
}
