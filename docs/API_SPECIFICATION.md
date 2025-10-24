# API Specification

## Overview

KBrain provides a RESTful API for managing scopes and documents. The API follows REST principles and uses JSON for request/response payloads.

## Base URL

```
Production: https://api.kbrain.example.com/v1
Development: http://localhost:3000/v1
```

## API Versioning

API version is included in the URL path (`/v1/`). This allows for backward compatibility when introducing breaking changes.

## Content Type

All requests and responses use JSON:

```
Content-Type: application/json
```

## Authentication (Future)

Version 1 has no authentication. Future versions will use:

```
Authorization: Bearer <jwt_token>
```

## Common Response Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST (resource created) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., duplicate name) |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

## Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "allowed_extensions",
        "message": "Must be a non-empty array"
      }
    ],
    "request_id": "req_abc123"
  }
}
```

## Common Error Codes

- `VALIDATION_ERROR`: Request validation failed
- `NOT_FOUND`: Resource not found
- `DUPLICATE_RESOURCE`: Resource already exists
- `STORAGE_ERROR`: Storage backend error
- `PROCESSING_ERROR`: Document processing error
- `INTERNAL_ERROR`: Internal server error

---

# API Endpoints

## Scopes

### List Scopes

Get a list of all scopes.

```
GET /v1/scopes
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | integer | No | Page number (default: 1) |
| per_page | integer | No | Items per page (default: 20, max: 100) |
| is_active | boolean | No | Filter by active status |
| sort | string | No | Sort field (name, created_at) |
| order | string | No | Sort order (asc, desc) |

**Response: 200 OK**

```json
{
  "scopes": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "research-papers",
      "description": "Academic research papers and publications",
      "allowed_extensions": ["pdf", "docx", "txt"],
      "storage_backend": "s3",
      "is_active": true,
      "document_count": 156,
      "total_size": 2147483648,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_pages": 3,
    "total_items": 52
  }
}
```

---

### Get Scope

Get details of a specific scope.

```
GET /v1/scopes/{scope_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| scope_id | uuid | Yes | Scope ID |

**Response: 200 OK**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "research-papers",
  "description": "Academic research papers and publications",
  "allowed_extensions": ["pdf", "docx", "txt"],
  "storage_backend": "s3",
  "storage_config": {
    "bucket": "kbrain-documents",
    "region": "us-east-1",
    "path_prefix": "scopes/research/"
  },
  "is_active": true,
  "statistics": {
    "document_count": 156,
    "total_size": 2147483648,
    "status_breakdown": {
      "added": 5,
      "processing": 2,
      "processed": 145,
      "failed": 4
    }
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Response: 404 Not Found**

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Scope not found"
  }
}
```

---

### Create Scope

Create a new scope.

```
POST /v1/scopes
```

**Request Body:**

```json
{
  "name": "legal-documents",
  "description": "Legal contracts and agreements",
  "allowed_extensions": ["pdf", "docx", "doc"],
  "storage_backend": "azure_blob",
  "storage_config": {
    "container": "legal-docs",
    "account_name": "kbrainstorage",
    "path_prefix": "legal/"
  }
}
```

**Required Fields:**
- `name`: string (3-255 chars, alphanumeric + hyphens/underscores)
- `allowed_extensions`: array of strings (at least one extension)

**Optional Fields:**
- `description`: string
- `storage_backend`: string (default: from global config)
- `storage_config`: object (backend-specific configuration)

**Response: 201 Created**

```json
{
  "id": "660f9511-f3ac-52e5-b827-557766551111",
  "name": "legal-documents",
  "description": "Legal contracts and agreements",
  "allowed_extensions": ["pdf", "docx", "doc"],
  "storage_backend": "azure_blob",
  "storage_config": {
    "container": "legal-docs",
    "path_prefix": "legal/"
  },
  "is_active": true,
  "created_at": "2024-01-20T14:22:00Z",
  "updated_at": "2024-01-20T14:22:00Z"
}
```

**Response: 409 Conflict**

```json
{
  "error": {
    "code": "DUPLICATE_RESOURCE",
    "message": "Scope with name 'legal-documents' already exists"
  }
}
```

**Response: 422 Unprocessable Entity**

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "field": "allowed_extensions",
        "message": "Must contain at least one extension"
      }
    ]
  }
}
```

---

### Update Scope

Update an existing scope.

```
PATCH /v1/scopes/{scope_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| scope_id | uuid | Yes | Scope ID |

**Request Body (all fields optional):**

```json
{
  "name": "research-papers-updated",
  "description": "Updated description",
  "allowed_extensions": ["pdf", "docx", "txt", "md"],
  "is_active": true
}
```

**Response: 200 OK**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "research-papers-updated",
  "description": "Updated description",
  "allowed_extensions": ["pdf", "docx", "txt", "md"],
  "storage_backend": "s3",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T15:45:00Z"
}
```

---

### Delete Scope

Delete a scope. This is a soft delete (sets `is_active` to false).

```
DELETE /v1/scopes/{scope_id}
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| hard_delete | boolean | No | Permanently delete (default: false) |

**Response: 204 No Content**

---

## Documents

### List Documents

Get documents in a scope.

```
GET /v1/scopes/{scope_id}/documents
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| scope_id | uuid | Yes | Scope ID |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | integer | No | Page number (default: 1) |
| per_page | integer | No | Items per page (default: 50, max: 200) |
| status | string | No | Filter by status (added, processing, processed, failed) |
| extension | string | No | Filter by file extension |
| sort | string | No | Sort field (upload_date, file_size, original_name) |
| order | string | No | Sort order (asc, desc, default: desc) |
| search | string | No | Search in original_name |

**Response: 200 OK**

```json
{
  "documents": [
    {
      "id": "770fa622-g4bd-63f6-c938-668877662222",
      "scope_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "2024-01-20_abc123def456.pdf",
      "original_name": "research_paper_ml.pdf",
      "file_size": 2457600,
      "mime_type": "application/pdf",
      "file_extension": "pdf",
      "storage_backend": "s3",
      "status": "processed",
      "upload_date": "2024-01-20T10:15:30Z",
      "processing_started": "2024-01-20T10:15:45Z",
      "processed_at": "2024-01-20T10:16:22Z",
      "error_message": null,
      "metadata": {
        "pages": 24,
        "author": "John Doe"
      },
      "created_at": "2024-01-20T10:15:30Z",
      "updated_at": "2024-01-20T10:16:22Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total_pages": 4,
    "total_items": 156
  }
}
```

---

### Get Document

Get details of a specific document.

```
GET /v1/documents/{document_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| document_id | uuid | Yes | Document ID |

**Response: 200 OK**

```json
{
  "id": "770fa622-g4bd-63f6-c938-668877662222",
  "scope_id": "550e8400-e29b-41d4-a716-446655440000",
  "scope_name": "research-papers",
  "filename": "2024-01-20_abc123def456.pdf",
  "original_name": "research_paper_ml.pdf",
  "file_size": 2457600,
  "mime_type": "application/pdf",
  "file_extension": "pdf",
  "storage_path": "scopes/research/2024/01/2024-01-20_abc123def456.pdf",
  "storage_backend": "s3",
  "checksum_md5": "5d41402abc4b2a76b9719d911017c592",
  "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "status": "processed",
  "upload_date": "2024-01-20T10:15:30Z",
  "processing_started": "2024-01-20T10:15:45Z",
  "processed_at": "2024-01-20T10:16:22Z",
  "retry_count": 0,
  "error_message": null,
  "metadata": {
    "pages": 24,
    "author": "John Doe",
    "extracted_text_length": 45678
  },
  "created_at": "2024-01-20T10:15:30Z",
  "updated_at": "2024-01-20T10:16:22Z"
}
```

---

### Upload Document

Upload a new document to a scope.

```
POST /v1/scopes/{scope_id}/documents
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| scope_id | uuid | Yes | Scope ID |

**Request: multipart/form-data**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | file | Yes | The file to upload |
| metadata | json | No | Additional metadata (as JSON string) |

**Example with curl:**

```bash
curl -X POST http://localhost:3000/v1/scopes/{scope_id}/documents \
  -F "file=@/path/to/document.pdf" \
  -F 'metadata={"author":"John Doe","category":"research"}'
```

**Response: 201 Created**

```json
{
  "id": "880fb733-h5ce-74g7-d049-779988773333",
  "scope_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "2024-01-20_def789ghi012.pdf",
  "original_name": "document.pdf",
  "file_size": 1024000,
  "mime_type": "application/pdf",
  "file_extension": "pdf",
  "storage_backend": "s3",
  "status": "added",
  "upload_date": "2024-01-20T16:30:00Z",
  "metadata": {
    "author": "John Doe",
    "category": "research"
  },
  "created_at": "2024-01-20T16:30:00Z",
  "updated_at": "2024-01-20T16:30:00Z"
}
```

**Response: 400 Bad Request**

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid file extension",
    "details": [
      {
        "field": "file",
        "message": "File extension 'exe' not allowed in this scope. Allowed: pdf, docx, txt"
      }
    ]
  }
}
```

**Response: 413 Payload Too Large**

```json
{
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "File size exceeds maximum allowed size of 100MB"
  }
}
```

---

### Upload Multiple Documents

Upload multiple documents in a single request.

```
POST /v1/scopes/{scope_id}/documents/batch
```

**Request: multipart/form-data**

Multiple files with field name `files[]`:

```bash
curl -X POST http://localhost:3000/v1/scopes/{scope_id}/documents/batch \
  -F "files[]=@/path/to/doc1.pdf" \
  -F "files[]=@/path/to/doc2.pdf" \
  -F "files[]=@/path/to/doc3.pdf"
```

**Response: 207 Multi-Status**

```json
{
  "results": [
    {
      "filename": "doc1.pdf",
      "status": "success",
      "document": {
        "id": "990fc844-i6df-85h8-e15a-88aa99884444",
        "original_name": "doc1.pdf",
        "status": "added"
      }
    },
    {
      "filename": "doc2.pdf",
      "status": "success",
      "document": {
        "id": "aa0fd955-j7eg-96i9-f26b-99bb00995555",
        "original_name": "doc2.pdf",
        "status": "added"
      }
    },
    {
      "filename": "doc3.pdf",
      "status": "error",
      "error": {
        "code": "STORAGE_ERROR",
        "message": "Failed to upload to storage backend"
      }
    }
  ],
  "summary": {
    "total": 3,
    "successful": 2,
    "failed": 1
  }
}
```

---

### Download Document

Get a download URL for a document.

```
GET /v1/documents/{document_id}/download
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| document_id | uuid | Yes | Document ID |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| expiration | integer | No | URL expiration in seconds (default: 3600, max: 86400) |

**Response: 200 OK**

```json
{
  "download_url": "https://s3.amazonaws.com/bucket/file.pdf?X-Amz-Signature=...",
  "expires_at": "2024-01-20T17:30:00Z",
  "filename": "research_paper_ml.pdf",
  "file_size": 2457600
}
```

**Note:** For storage backends that don't support signed URLs (SFTP, local), the API will proxy the download:

```json
{
  "download_url": "https://api.kbrain.example.com/v1/documents/{document_id}/content",
  "expires_at": null,
  "filename": "research_paper_ml.pdf",
  "file_size": 2457600
}
```

---

### Download Document Content

Directly download document content (proxy download).

```
GET /v1/documents/{document_id}/content
```

**Response: 200 OK**

Binary file content with appropriate headers:

```
Content-Type: application/pdf
Content-Disposition: attachment; filename="research_paper_ml.pdf"
Content-Length: 2457600
```

---

### Delete Document

Delete a document.

```
DELETE /v1/documents/{document_id}
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| delete_storage | boolean | No | Also delete from storage (default: true) |

**Response: 204 No Content**

---

### Update Document Status

Manually update document status (primarily for admin/processing workers).

```
PATCH /v1/documents/{document_id}/status
```

**Request Body:**

```json
{
  "status": "processed",
  "metadata": {
    "processing_time_ms": 15000,
    "extracted_entities": 42
  }
}
```

**Response: 200 OK**

```json
{
  "id": "770fa622-g4bd-63f6-c938-668877662222",
  "status": "processed",
  "processed_at": "2024-01-20T16:45:30Z",
  "updated_at": "2024-01-20T16:45:30Z"
}
```

---

### Update Document Metadata

Update document metadata.

```
PATCH /v1/documents/{document_id}/metadata
```

**Request Body:**

```json
{
  "author": "Jane Smith",
  "tags": ["machine-learning", "research", "2024"],
  "custom_field": "custom_value"
}
```

**Response: 200 OK**

```json
{
  "id": "770fa622-g4bd-63f6-c938-668877662222",
  "metadata": {
    "author": "Jane Smith",
    "tags": ["machine-learning", "research", "2024"],
    "custom_field": "custom_value",
    "pages": 24
  },
  "updated_at": "2024-01-20T17:00:00Z"
}
```

---

## Statistics

### Get Global Statistics

Get system-wide statistics.

```
GET /v1/statistics
```

**Response: 200 OK**

```json
{
  "total_scopes": 12,
  "total_documents": 3456,
  "total_storage_size": 52428800000,
  "documents_by_status": {
    "added": 23,
    "processing": 8,
    "processed": 3401,
    "failed": 24
  },
  "documents_by_extension": {
    "pdf": 2100,
    "docx": 980,
    "txt": 376
  },
  "storage_backends": {
    "s3": 2800,
    "azure_blob": 500,
    "sftp": 156
  },
  "recent_uploads": {
    "last_hour": 45,
    "last_24_hours": 234,
    "last_7_days": 1205
  }
}
```

---

### Get Scope Statistics

Get statistics for a specific scope.

```
GET /v1/scopes/{scope_id}/statistics
```

**Response: 200 OK**

```json
{
  "scope_id": "550e8400-e29b-41d4-a716-446655440000",
  "scope_name": "research-papers",
  "total_documents": 156,
  "total_size": 2147483648,
  "documents_by_status": {
    "added": 5,
    "processing": 2,
    "processed": 145,
    "failed": 4
  },
  "documents_by_extension": {
    "pdf": 120,
    "docx": 30,
    "txt": 6
  },
  "upload_timeline": [
    {
      "date": "2024-01-20",
      "count": 12,
      "size": 125829120
    },
    {
      "date": "2024-01-19",
      "count": 8,
      "size": 83886080
    }
  ],
  "processing_performance": {
    "average_processing_time_ms": 12500,
    "success_rate": 0.974
  }
}
```

---

## Health & Status

### Health Check

Check API health status.

```
GET /health
```

**Response: 200 OK**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-20T18:00:00Z",
  "services": {
    "database": "healthy",
    "storage": "healthy",
    "queue": "healthy"
  }
}
```

**Response: 503 Service Unavailable**

```json
{
  "status": "unhealthy",
  "version": "1.0.0",
  "timestamp": "2024-01-20T18:00:00Z",
  "services": {
    "database": "healthy",
    "storage": "unhealthy",
    "queue": "healthy"
  }
}
```

---

### Version Info

Get API version information.

```
GET /version
```

**Response: 200 OK**

```json
{
  "api_version": "1.0.0",
  "build": "2024.01.20.1",
  "commit": "abc123def456",
  "timestamp": "2024-01-20T12:00:00Z"
}
```

---

## Rate Limiting

**Headers in Response:**

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705776000
```

**Rate Limit Exceeded Response:**

```
HTTP/1.1 429 Too Many Requests
Retry-After: 60

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please try again in 60 seconds."
  }
}
```

---

## Pagination

All list endpoints support pagination:

**Request:**
```
GET /v1/scopes?page=2&per_page=20
```

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "per_page": 20,
    "total_pages": 5,
    "total_items": 93,
    "has_next": true,
    "has_prev": true
  },
  "links": {
    "first": "/v1/scopes?page=1&per_page=20",
    "prev": "/v1/scopes?page=1&per_page=20",
    "next": "/v1/scopes?page=3&per_page=20",
    "last": "/v1/scopes?page=5&per_page=20"
  }
}
```

---

## WebSocket API (Future Enhancement)

Real-time updates for document processing status:

```javascript
const ws = new WebSocket('wss://api.kbrain.example.com/v1/ws');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  // {
  //   "type": "document_status_update",
  //   "document_id": "...",
  //   "status": "processed",
  //   "timestamp": "2024-01-20T18:30:00Z"
  // }
};
```

---

## OpenAPI Specification

The full API is documented using OpenAPI 3.0 specification. The OpenAPI file can be accessed at:

```
GET /v1/openapi.json
```

Interactive API documentation (Swagger UI) available at:

```
GET /docs
```
