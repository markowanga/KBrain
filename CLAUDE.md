# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# KBrain Architecture Guide

This document provides a comprehensive overview of the KBrain codebase to help Claude Code instances quickly understand the architecture and make productive contributions.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Directory Structure](#directory-structure)
3. [Backend Architecture](#backend-architecture)
   - [Architecture Layers](#architecture-layers)
   - [Database Schema](#database-schema)
   - [Storage Abstraction](#storage-abstraction)
   - [API Routes and Endpoints](#api-routes-and-endpoints)
4. [Frontend Architecture](#frontend-architecture)
5. [Key Technologies & Dependencies](#key-technologies--dependencies)
6. [Entry Points and Configuration](#entry-points-and-configuration)
7. [Common Development Tasks](#common-development-tasks)
8. [Important Code Patterns](#important-code-patterns)

---

## Project Overview

**KBrain** is a knowledge management system with flexible document processing capabilities. The backend is built as a monorepo using Python's `uv` workspace manager, with:

- **FastAPI** for async REST API
- **SQLAlchemy** for ORM with async support
- **PostgreSQL** for persistent storage
- **Multiple storage backends**: Local filesystem, AWS S3, Azure Blob Storage
- **Alembic** for database migrations
- **Pydantic** for request/response validation

The system is designed to handle document uploads, organize them into scopes, tag them for processing, and track their processing status.

---

## Directory Structure

### Root Level
```
KBrain/
├── kbrain_backend/              # Backend monorepo
│   ├── libs/                    # Shared libraries
│   │   └── kbrain-storage/      # Storage abstraction library
│   ├── services/                # Microservices/applications
│   │   └── kbrain-backend/      # Main API service
│   ├── pyproject.toml           # Workspace configuration
│   └── uv.lock                  # Lockfile for reproducible builds
├── kbrain_frontend/             # React frontend (out of scope)
├── kbrain-nginx/                # Nginx reverse proxy config
├── docker-compose.yml           # Local development environment
├── README.md                    # Project overview
└── docs/                        # Documentation
```

### Backend Service Structure
```
kbrain_backend/
└── services/kbrain-backend/
    ├── src/kbrain_backend/
    │   ├── main.py                          # FastAPI app entry point
    │   ├── config/
    │   │   └── settings.py                  # Application configuration
    │   ├── api/
    │   │   ├── routes/
    │   │   │   ├── documents.py             # Document CRUD endpoints
    │   │   │   ├── scopes.py                # Scope management endpoints
    │   │   │   ├── tags.py                  # Tag management endpoints
    │   │   │   ├── statistics.py            # Analytics endpoints
    │   │   │   └── health.py                # Health check endpoints
    │   │   └── schemas.py                   # Pydantic models for validation
    │   ├── core/
    │   │   ├── models/
    │   │   │   ├── document.py              # Document SQLAlchemy model
    │   │   │   ├── scope.py                 # Scope SQLAlchemy model
    │   │   │   ├── tag.py                   # Tag SQLAlchemy model
    │   │   │   └── processing_queue.py      # Processing job model
    │   │   ├── repositories/                # Repository pattern (if used)
    │   │   └── services/                    # Business logic layer
    │   ├── database/
    │   │   └── connection.py                # SQLAlchemy engine & session config
    │   └── utils/
    │       ├── errors.py                    # Custom error classes
    │       └── logger.py                    # Logging utilities
    ├── alembic/                             # Database migrations
    │   ├── env.py                           # Migration environment
    │   ├── script.py.mako                   # Migration template
    │   └── versions/                        # Migration scripts
    │       ├── d9c4d8ddc760_initial...py    # Initial schema
    │       ├── add_tags_feature.py          # Tag feature migration
    │       └── rename_tag_metadata...py     # Metadata column rename
    ├── alembic.ini                          # Alembic config
    ├── pyproject.toml                       # Service dependencies
    ├── .env                                 # Environment variables (local)
    ├── .env.example                         # Environment template
    └── start_service.sh                     # Service startup script
```

### Storage Library Structure
```
libs/kbrain-storage/
└── src/kbrain_storage/
    ├── __init__.py                 # Exports BaseFileStorage, LocalFileStorage
    ├── base.py                     # BaseFileStorage abstract class
    ├── local.py                    # LocalFileStorage implementation
    ├── aws_s3.py                   # S3FileStorage (stub/partially implemented)
    └── azure_blob.py               # AzureFileStorage (stub/partially implemented)
```

---

## Backend Architecture

### Architecture Layers

### 1. **Presentation Layer (FastAPI Routes)**

Located in: `src/kbrain_backend/api/routes/`

All routes use async/await with dependency injection:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from kbrain_backend.database.connection import get_db

router = APIRouter(prefix="/v1/scopes", tags=["scopes"])

@router.get("", response_model=ScopeListResponse)
async def list_scopes(
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
) -> ScopeListResponse:
    """Endpoint implementation"""
```

**Key Route Groups:**
- **Scopes** (`/v1/scopes`) - Create, list, update scopes that organize documents
- **Documents** (`/v1/scopes/{scope_id}/documents`, `/v1/documents/{document_id}`) - Upload, list, download, delete documents
- **Tags** (`/v1/scopes/{scope_id}/tags`) - Create and manage document tags
- **Statistics** (`/v1/statistics`) - System-wide and scope-specific analytics
- **Health** (`/health`, `/version`) - Service health and version info

### 2. **Data Validation Layer (Pydantic)**

Located in: `src/kbrain_backend/api/schemas.py`

All request/response models inherit from Pydantic's `BaseModel`:

```python
class DocumentResponse(BaseModel):
    id: UUID
    scope_id: UUID
    filename: str
    original_name: str
    # ... more fields
    model_config = ConfigDict(from_attributes=True)  # ORM mode
```

**Key Schema Groups:**
- `Scope*` - Scope creation, updates, responses
- `Document*` - Document upload, listing, details
- `Tag*` - Tag CRUD operations
- `Error*` - Standardized error responses

### 3. **Business Logic Layer (SQLAlchemy ORM Models)**

Located in: `src/kbrain_backend/core/models/`

Models define database schema and relationships. All models inherit from `Base`:

```python
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Document(Base):
    __tablename__ = "documents"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    scope_id: Mapped[UUID] = mapped_column(ForeignKey("scopes.id"))
    # ... more columns
    
    scope: Mapped[Scope] = relationship("Scope", back_populates="documents")
    tags: Mapped[List[Tag]] = relationship("Tag", secondary="document_tags")
```

**Key Models:**
- **Scope** - Container for organizing documents; has allowed file extensions, storage backend config
- **Document** - Uploaded file metadata; tracks filename, size, checksums, processing status
- **Tag** - Labels for categorizing documents within a scope; many-to-many relationship with documents
- **ProcessingQueue** - Job queue for async document processing

### 4. **Storage Abstraction Layer**

Located in: `libs/kbrain-storage/`

All storage implementations inherit from `BaseFileStorage` abstract class:

```python
class BaseFileStorage(ABC):
    @abstractmethod
    async def save_file(self, path: str, content: bytes, overwrite: bool = True) -> bool:
        """Save file to storage backend"""
    
    @abstractmethod
    async def read_file(self, path: str) -> Optional[bytes]:
        """Read file from storage backend"""
    
    # ... other abstract methods
```

**Implementations:**
- **LocalFileStorage** - File system storage using pathlib
- **S3FileStorage** - AWS S3 (stub with TODO)
- **AzureFileStorage** - Azure Blob Storage (stub with TODO)

### 5. **Data Access Layer (Database)**

Located in: `src/kbrain_backend/database/connection.py`

Async SQLAlchemy session management:

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_min,
    max_overflow=settings.database_pool_max - settings.database_pool_min,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for route handlers"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

---

## Database Schema

### Entity Relationship Diagram (Conceptual)

```
┌─────────────┐
│   scopes    │
├─────────────┤
│ id (PK)     │
│ name        │  ◄─────┐
│ description │        │ 1:N
│ allowed_*   │        │
└─────────────┘        │
      ▲                 │
      │ 1:N             │
      │                 ▼
      │          ┌──────────────┐
      │          │  documents   │
      │          ├──────────────┤
      │          │ id (PK)      │
      │          │ scope_id (FK)│
      │          │ filename     │
      │          │ file_size    │
      │          │ status       │
      └──────────┤ storage_path │
                 │ checksums    │
                 └──────────────┘
                        ▲
                        │ M:N (via document_tags table)
                        │
                 ┌──────────────┐
                 │     tags     │
                 ├──────────────┤
                 │ id (PK)      │
                 │ scope_id (FK)│
                 │ name         │
                 │ color        │
                 └──────────────┘
```

### Tables

#### `scopes`
- Organizes documents by context/project
- Defines allowed file extensions
- Configures storage backend per scope
- Unique constraint on `name`

**Key Fields:**
- `id` (UUID, PK)
- `name` (String, unique, indexed)
- `allowed_extensions` (PostgreSQL ARRAY)
- `storage_backend` (String: "local", "s3", "azure")
- `storage_config` (JSON)
- `is_active` (Boolean, indexed)
- `created_at`, `updated_at` (TIMESTAMP with TZ)

#### `documents`
- Represents uploaded files
- Tracks metadata and processing status
- Foreign key to scopes (cascade delete)

**Key Fields:**
- `id` (UUID, PK)
- `scope_id` (UUID, FK, indexed)
- `filename` (String, indexed) - System-generated unique filename
- `original_name` (String, indexed) - Original upload filename
- `file_size` (BigInteger)
- `mime_type` (String)
- `file_extension` (String, indexed)
- `storage_path` (Text) - Path in storage backend
- `storage_backend` (String)
- `checksum_md5`, `checksum_sha256` (String)
- `status` (String, indexed: "added", "processing", "processed", "failed")
- `upload_date` (TIMESTAMP, indexed)
- `processing_started`, `processed_at` (TIMESTAMP)
- `retry_count` (Integer)
- `error_message` (Text)
- `doc_metadata` (JSON) - Custom metadata
- `created_at`, `updated_at` (TIMESTAMP)

#### `tags`
- Labels for categorizing documents within a scope
- Unique constraint: `(scope_id, name)`

**Key Fields:**
- `id` (UUID, PK)
- `scope_id` (UUID, FK, indexed)
- `name` (String, indexed)
- `description` (Text)
- `color` (String) - Hex color code
- `meta` (JSON) - Processing instructions or metadata
- `created_at`, `updated_at` (TIMESTAMP)

#### `document_tags` (Association Table)
- Many-to-many relationship between documents and tags
- Composite PK: `(document_id, tag_id)`

**Key Fields:**
- `document_id` (UUID, FK)
- `tag_id` (UUID, FK)
- `created_at` (TIMESTAMP)

#### `processing_queue`
- Async job queue for document processing
- Foreign key to documents (cascade delete)

**Key Fields:**
- `id` (BigInteger, PK, auto-increment)
- `document_id` (UUID, FK, indexed)
- `priority` (Integer, indexed)
- `retry_count`, `max_retries` (Integer)
- `scheduled_at` (TIMESTAMP, indexed)
- `started_at`, `completed_at` (TIMESTAMP)
- `worker_id` (String)
- `status` (String, indexed: "pending", "processing", "completed", "failed")
- `error_message` (Text)
- `created_at` (TIMESTAMP)

### Indexes

Strategic indexes for performance:
- `scopes(name)` - Unique, scope lookup
- `scopes(is_active)` - Filter active scopes
- `documents(scope_id)` - Find docs in scope
- `documents(status, upload_date)` - List/filter docs
- `tags(scope_id, name)` - Unique constraint enforcement
- `document_tags` - FK support
- `processing_queue(status, priority, scheduled_at)` - Job queue processing

---

## Storage Abstraction

### BaseFileStorage Interface

All storage backends implement this async interface:

```python
class BaseFileStorage(ABC):
    # Write operations
    async def save_file(path: str, content: bytes, overwrite: bool = True) -> bool
    async def create_directory(path: str) -> bool
    
    # Read operations
    async def read_file(path: str) -> Optional[bytes]
    async def exists(path: str) -> bool
    async def get_file_size(path: str) -> Optional[int]
    async def list_directory(path: str = "", recursive: bool = False) -> List[str]
    
    # Delete operations
    async def delete_file(path: str) -> bool
```

### LocalFileStorage Implementation

**Location:** `libs/kbrain-storage/src/kbrain_storage/local.py`

**Key Features:**
- Uses `pathlib.Path` for cross-platform compatibility
- Path validation to prevent directory traversal attacks
- Async I/O with `aiofiles`
- Thread-safe with `asyncio.Lock`

**Storage Path Structure:**
```
storage_data/
└── scopes/
    └── {scope_name}/
        └── {year}/
            └── {month:02d}/
                └── {timestamp}_{uuid}.{ext}
```

**Example Usage in Routes:**
```python
# In documents.py route handler
storage_path = f"scopes/{scope.name}/{datetime.now().year}/{month:02d}/{unique_filename}"
success = await storage.save_file(storage_path, content)

# Later retrieval
content = await storage.read_file(document.storage_path)
```

### Initialization in main.py

```python
import os
from kbrain_storage import LocalFileStorage

STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", settings.storage_backend)  # "local", "s3", "azure"
STORAGE_ROOT = os.getenv("STORAGE_ROOT", settings.storage_root)

if STORAGE_BACKEND == "local":
    storage = LocalFileStorage(root_path=STORAGE_ROOT)
elif STORAGE_BACKEND == "s3":
    raise NotImplementedError("S3 storage not yet implemented")
elif STORAGE_BACKEND == "azure":
    raise NotImplementedError("Azure Blob storage not yet implemented")

# Global variable accessible via get_storage() dependency
set_storage(storage)
```

---

### API Routes and Endpoints

### Scope Routes (`/v1/scopes`)

```python
# List scopes with pagination
GET /v1/scopes?page=1&per_page=20&sort=created_at&order=desc

# Get scope details
GET /v1/scopes/{scope_id}

# Create scope
POST /v1/scopes
{
    "name": "Project Alpha",
    "description": "Internal project documents",
    "allowed_extensions": ["pdf", "docx", "txt"],
    "storage_backend": "local"
}

# Update scope
PATCH /v1/scopes/{scope_id}
{
    "name": "Updated Name",
    "is_active": false
}

# Delete scope
DELETE /v1/scopes/{scope_id}
```

**Response includes statistics:**
- `document_count` - Total documents in scope
- `total_size` - Total file size in bytes
- `storage_backend` - Configured backend

### Document Routes

#### Upload/List Documents
```python
# Upload document to scope
POST /v1/scopes/{scope_id}/documents
Content-Type: multipart/form-data
[file: binary]

# List documents in scope with filtering
GET /v1/scopes/{scope_id}/documents?page=1&per_page=50&status=added&extension=pdf&sort=upload_date&order=desc&search=keyword

# Get document details
GET /v1/documents/{document_id}

# Download document
GET /v1/documents/{document_id}/content  # Streams file
GET /v1/documents/{document_id}/download # Returns download URL
```

#### Document Metadata
```python
# Update document status
PATCH /v1/documents/{document_id}/status
{
    "status": "processing",  # "added", "processing", "processed", "failed"
    "metadata": {"progress": 50}
}

# Update document metadata
PATCH /v1/documents/{document_id}/metadata
{
    "metadata": {"custom_field": "value"}
}

# Delete document
DELETE /v1/documents/{document_id}?delete_storage=true
```

**Upload Response:**
```json
{
    "id": "uuid",
    "scope_id": "uuid",
    "filename": "2024-10-24_abc123def456.pdf",
    "original_name": "my-document.pdf",
    "file_size": 1024000,
    "mime_type": "application/pdf",
    "file_extension": "pdf",
    "storage_backend": "local",
    "status": "added",
    "upload_date": "2024-10-24T12:00:00Z",
    "metadata": null,
    "tags": [],
    "created_at": "2024-10-24T12:00:00Z",
    "updated_at": "2024-10-24T12:00:00Z"
}
```

### Tag Routes (`/v1/scopes/{scope_id}/tags`)

```python
# List tags in scope
GET /v1/scopes/{scope_id}/tags

# Create tag
POST /v1/scopes/{scope_id}/tags
{
    "name": "urgent",
    "description": "Requires immediate attention",
    "color": "#FF0000",
    "meta": {"priority": "high"}
}

# Update tag
PATCH /v1/scopes/{scope_id}/tags/{tag_id}
{
    "name": "updated-name",
    "color": "#00FF00"
}

# Delete tag
DELETE /v1/scopes/{scope_id}/tags/{tag_id}

# Assign tags to document
POST /v1/documents/{document_id}/tags
{
    "tag_ids": ["tag-uuid-1", "tag-uuid-2"]
}

# Remove tag from document
DELETE /v1/documents/{document_id}/tags/{tag_id}
```

### Statistics Routes (`/v1/statistics`)

```python
# Global statistics
GET /v1/statistics
{
    "total_scopes": 5,
    "total_documents": 100,
    "total_storage_size": 5242880,
    "documents_by_status": {"added": 20, "processing": 30, "processed": 50, "failed": 0},
    "documents_by_extension": {"pdf": 60, "docx": 40},
    "storage_backends": {"local": 100},
    "recent_uploads": {"last_hour": 5, "last_24_hours": 20, "last_7_days": 80}
}

# Scope-specific statistics
GET /v1/scopes/{scope_id}/statistics
{
    "scope_id": "uuid",
    "scope_name": "Project Alpha",
    "total_documents": 30,
    "total_size": 314572800,
    "documents_by_status": {...},
    "documents_by_extension": {...}
}
```

### Health Routes

```python
# Health check with service status
GET /health
{
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2024-10-24T12:00:00Z",
    "services": {
        "database": "healthy",
        "storage": "healthy",
        "queue": "healthy"
    }
}

# Version info
GET /version
{
    "api_version": "1.0.0",
    "build": "2024.10.24.1",
    "commit": "dev",
    "timestamp": "2024-10-24T12:00:00Z"
}
```

### Legacy Endpoints (Backward Compatibility)

Located in `main.py`, these are deprecated but maintained:

```python
POST /api/files/upload
GET /api/files/download/{path}
GET /api/files/read/{path}
GET /api/files/exists/{path}
GET /api/files/list
DELETE /api/files/delete/{path}
GET /api/files/info/{path}
POST /api/files/directory
GET /api/health
```

---

## Frontend Architecture

The frontend is a React application built with TypeScript, Vite, and TailwindCSS.

### Directory Structure

```
kbrain_frontend/
├── src/
│   ├── api/                    # API client and service layer
│   │   ├── client.ts           # Base HTTP client (fetch wrapper)
│   │   ├── types.ts            # Shared TypeScript types/interfaces
│   │   ├── scopes.ts           # Scope API calls
│   │   ├── documents.ts        # Document API calls
│   │   ├── tags.ts             # Tag API calls
│   │   ├── statistics.ts       # Statistics API calls
│   │   └── index.ts            # Re-exports all API functions
│   ├── hooks/                  # Custom React hooks
│   │   ├── useScopes.ts        # Scope data fetching & mutations
│   │   ├── useDocuments.ts     # Document data fetching & mutations
│   │   ├── useTags.ts          # Tag data fetching & mutations
│   │   ├── useStatistics.ts    # Statistics data fetching
│   │   └── index.ts            # Re-exports all hooks
│   ├── utils/                  # Utility functions
│   │   └── format.ts           # Formatters (file size, dates, etc.)
│   ├── App.tsx                 # Main application component
│   ├── main.tsx                # Application entry point
│   ├── index.css               # Global styles (TailwindCSS)
│   └── vite-env.d.ts           # Vite TypeScript definitions
├── public/                     # Static assets
├── index.html                  # HTML entry point
├── vite.config.ts              # Vite build configuration
├── tailwind.config.js          # TailwindCSS configuration
├── tsconfig.json               # TypeScript configuration
├── package.json                # Dependencies and scripts
└── eslint.config.js            # ESLint configuration
```

### Technology Stack

- **React 19** - UI framework with hooks
- **TypeScript 5.9** - Type-safe JavaScript
- **Vite 7** - Fast build tool and dev server
- **TailwindCSS 3** - Utility-first CSS framework
- **ESLint 9** - Code linting

### Architecture Patterns

#### 1. API Layer (`src/api/`)

Centralized API client with typed request/response:

```typescript
// client.ts - Base HTTP client
export const apiClient = {
  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  },
  // ... post, patch, delete methods
};

// scopes.ts - Scope-specific API calls
export const scopesApi = {
  list: () => apiClient.get<ScopeListResponse>('/v1/scopes'),
  get: (id: string) => apiClient.get<ScopeResponse>(`/v1/scopes/${id}`),
  create: (data: CreateScopeRequest) => apiClient.post<ScopeResponse>('/v1/scopes', data),
  // ...
};
```

#### 2. Custom Hooks (`src/hooks/`)

Data fetching and state management with custom hooks:

```typescript
// useScopes.ts
export function useScopes() {
  const [scopes, setScopes] = useState<Scope[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    scopesApi.list()
      .then(data => setScopes(data.scopes))
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  return { scopes, loading, error };
}
```

#### 3. Type Safety (`src/api/types.ts`)

Shared TypeScript types matching backend Pydantic schemas:

```typescript
export interface Scope {
  id: string;
  name: string;
  description: string | null;
  allowed_extensions: string[];
  storage_backend: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  scope_id: string;
  filename: string;
  original_name: string;
  file_size: number;
  status: 'added' | 'processing' | 'processed' | 'failed';
  // ...
}
```

### Development Commands

```bash
# Install dependencies
npm install

# Start dev server (http://localhost:5173)
npm run dev

# Build for production
npm run build

# Lint code
npm run lint

# Preview production build
npm run preview
```

### API Client Configuration

Base API URL is configured in `src/api/client.ts`:

```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
```

Set environment variable in `.env`:
```bash
VITE_API_BASE_URL=http://localhost:8000
```

### Adding New Features

1. **Add API call** in `src/api/{feature}.ts`
2. **Create custom hook** in `src/hooks/use{Feature}.ts`
3. **Add TypeScript types** in `src/api/types.ts`
4. **Build UI component** in `src/components/` (if components directory exists)

---

## Key Technologies & Dependencies

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| **fastapi** | >=0.115.0 | Web framework with async support |
| **sqlalchemy** | >=2.0.0 | ORM for database abstraction |
| **asyncpg** | >=0.29.0 | Async PostgreSQL driver |
| **pydantic** | >=2.0.0 | Data validation and serialization |
| **pydantic-settings** | >=2.0.0 | Environment configuration management |
| **alembic** | >=1.13.0 | Database schema migrations |
| **aiofiles** | >=24.1.0 | Async file I/O |
| **loguru** | >=0.7.0 | Structured logging |
| **python-multipart** | >=0.0.6 | Multipart form handling |

### Development Dependencies

| Package | Purpose |
|---------|---------|
| **ruff** | Fast Python linter and formatter |
| **mypy** | Static type checking |
| **poethepoet** | Task runner for npm-like scripts |

### Database

- **PostgreSQL 15+** - Production database
- **asyncpg** - Async driver for PostgreSQL
- **psycopg2-binary** - Used by Alembic for migrations

---

## Entry Points and Configuration

### Main Entry Point

**File:** `services/kbrain-backend/src/kbrain_backend/main.py`

**Responsibilities:**
1. Create FastAPI application instance
2. Configure CORS middleware
3. Initialize storage backend (local/S3/Azure)
4. Register API route routers
5. Configure error handlers
6. Set up application lifespan (startup/shutdown)

**Key Code:**
```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Startup
    await init_db()
    set_storage(storage)
    yield
    # Shutdown
    await close_db()

app = FastAPI(title=settings.app_name, lifespan=lifespan)
```

### Configuration

**File:** `services/kbrain-backend/src/kbrain_backend/config/settings.py`

Uses **Pydantic Settings** to load configuration from environment variables and `.env` files:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    app_name: str = "KBrain API"
    app_version: str = "1.0.0"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "postgresql+asyncpg://..."
    database_pool_min: int = 2
    database_pool_max: int = 10
    
    # Storage
    storage_backend: str = "local"  # "local", "s3", "azure"
    storage_root: str = "storage_data"
    
    # File upload
    max_file_size: int = 104857600  # 100MB
    
    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

settings = Settings()  # Global instance
```

**Environment Variables (.env):**
```bash
# Application
APP_NAME=KBrain API
APP_VERSION=1.0.0

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://kbrain:kbrain@localhost:5432/kbrain
DATABASE_POOL_MIN=2
DATABASE_POOL_MAX=10

# Storage
STORAGE_BACKEND=local
STORAGE_ROOT=storage_data

# AWS S3 (if using S3)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET=...

# Azure Blob (if using Azure)
AZURE_STORAGE_ACCOUNT=...
AZURE_STORAGE_KEY=...
AZURE_STORAGE_CONTAINER=...

# CORS
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# Logging
LOG_LEVEL=INFO
```

### Database Initialization

**File:** `services/kbrain-backend/src/kbrain_backend/database/connection.py`

1. Creates async SQLAlchemy engine with pool configuration
2. Creates async session factory
3. Provides `get_db()` dependency for route handlers
4. Handles session lifecycle (commit/rollback/close)

**Pool Configuration:**
- `pool_size` (min connections): 2
- `max_overflow` (extra connections): 8 (pool_max - pool_min)
- `pool_pre_ping`: True (verify connections before reuse)

---

## Common Development Tasks

### Full Stack Development Setup

```bash
# 1. Backend setup
cd kbrain_backend
uv sync                                  # Install all workspace dependencies

# 2. Database setup
cd services/kbrain-backend
cp .env.example .env                     # Create environment file (edit as needed)
createdb kbrain                          # Create PostgreSQL database
alembic upgrade head                     # Run migrations

# 3. Start backend
uv run uvicorn kbrain_backend.main:app --reload --host 0.0.0.0 --port 8000

# 4. Frontend setup (in new terminal)
cd kbrain_frontend
npm install                              # Install dependencies
npm run dev                              # Start dev server on http://localhost:5173
```

### Using Docker Compose (Recommended for Development)

```bash
# Start all services (backend, frontend, database, nginx)
docker-compose up

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

### Running the Backend Only

```bash
# Navigate to backend
cd kbrain_backend

# Install dependencies
uv sync

# Run migrations
cd services/kbrain-backend
alembic upgrade head

# Start server (with reload for development)
uv run uvicorn kbrain_backend.main:app --reload

# Or use the start script
./start_service.sh
```

### Database Migrations

```bash
cd services/kbrain-backend

# Create new migration after model changes
alembic revision --autogenerate -m "Add new field to documents"

# Apply pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Check current migration status
alembic current

# View migration history
alembic history --verbose
```

### Code Quality (Backend)

```bash
# Navigate to backend directory
cd kbrain_backend

# Lint code (using ruff)
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .

# Format code (using ruff)
uv run ruff format .

# Check formatting without changes
uv run ruff format --check .

# Type checking (using mypy)
uv run mypy --strict .

# Using poe tasks (defined in pyproject.toml)
uv run poe lint          # Run linter
uv run poe lint-fix      # Run linter with auto-fix
uv run poe format        # Format code
uv run poe format-check  # Check formatting
uv run poe typecheck     # Run type checker
```

### Code Quality (Frontend)

```bash
# Navigate to frontend directory
cd kbrain_frontend

# Lint code
npm run lint

# Type checking is automatic with TypeScript compilation
npm run build
```

### Testing

Currently minimal test coverage. Create tests in the project root or services as needed.

```bash
# Run tests (example)
uv run pytest tests/
```

### Adding a New Route

1. Create handler in `src/kbrain_backend/api/routes/new_feature.py`
2. Define Pydantic schemas in `api/schemas.py`
3. Import and include router in `main.py`
4. Add database migrations if needed

Example:

```python
# routes/new_feature.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from kbrain_backend.database.connection import get_db

router = APIRouter(prefix="/v1/new-feature", tags=["new-feature"])

@router.get("")
async def list_features(db: AsyncSession = Depends(get_db)):
    """List all features"""
    # Implementation
    pass

# main.py
from kbrain_backend.api.routes import new_feature
app.include_router(new_feature.router, prefix="")
```

### Adding a New Model/Table

1. Create model in `src/kbrain_backend/core/models/new_model.py`
2. Generate migration:
   ```bash
   alembic revision --autogenerate -m "Add new_model table"
   ```
3. Review and apply migration:
   ```bash
   alembic upgrade head
   ```

---

## Important Code Patterns

### 1. Async Route Handlers

All routes must be async and use dependency injection:

```python
@router.get("/items/{item_id}")
async def get_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    storage: BaseFileStorage = Depends(get_storage),
) -> ItemResponse:
    """Route handler with database and storage dependencies"""
    # Can use await within handler
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    
    return ItemResponse.model_validate(item)
```

### 2. Database Queries

Using SQLAlchemy 2.0 async patterns:

```python
# Single record
query = select(Document).where(Document.id == doc_id)
result = await db.execute(query)
document = result.scalar_one_or_none()

# Multiple records with pagination
query = select(Document).offset((page-1)*per_page).limit(per_page)
result = await db.execute(query)
documents = result.scalars().all()

# Count
count = await db.scalar(select(func.count()).select_from(Document))

# Relationships (eager loading)
query = select(Document).options(selectinload(Document.tags))
```

### 3. Error Handling

Custom exception hierarchy with standard response format:

```python
from kbrain_backend.utils.errors import APIError, NotFoundError, ValidationError

raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail={
        "error": {
            "code": "NOT_FOUND",
            "message": "Resource not found"
        }
    }
)

# Or use custom exceptions
raise NotFoundError("Document not found")
```

All errors follow this JSON structure:

```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable message",
        "details": [
            {"field": "fieldname", "message": "error message"}
        ]
    }
}
```

### 4. File Operations

Storage-agnostic file operations via BaseFileStorage:

```python
# Save file
success = await storage.save_file(storage_path, file_content)

# Read file
content = await storage.read_file(storage_path)

# Check existence
exists = await storage.exists(storage_path)

# Delete file
deleted = await storage.delete_file(storage_path)

# List directory
files = await storage.list_directory(directory_path, recursive=True)
```

### 5. Pagination

Standard pagination pattern:

```python
page = Query(1, ge=1)
per_page = Query(50, ge=1, le=200)

# Count total
count_query = select(func.count()).select_from(Item)
total_items = await db.scalar(count_query)

# Apply pagination to query
query = query.offset((page-1)*per_page).limit(per_page)

# Create response with metadata
pagination = PaginationResponse(
    page=page,
    per_page=per_page,
    total_pages=(total_items + per_page - 1) // per_page,
    total_items=total_items,
    has_next=page < total_pages,
    has_prev=page > 1,
)

return ListResponse(items=items, pagination=pagination)
```

### 6. Timestamps and UUIDs

Consistent patterns across models:

```python
from uuid import uuid4
from datetime import datetime

class Document(Base):
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
```

### 7. Relationships

- **One-to-Many:** Scope has many Documents
- **Many-to-Many:** Documents have many Tags (via document_tags table)

```python
# In Scope model
documents: Mapped[List[Document]] = relationship(
    "Document", 
    back_populates="scope",
    cascade="all, delete-orphan"
)

# In Document model
scope: Mapped[Scope] = relationship("Scope", back_populates="documents")
tags: Mapped[List[Tag]] = relationship(
    "Tag", 
    secondary="document_tags",
    back_populates="documents"
)
```

### 8. Checksum Calculation

Documents store MD5 and SHA256 checksums:

```python
import hashlib

content = await file.read()
md5_hash = hashlib.md5(content).hexdigest()
sha256_hash = hashlib.sha256(content).hexdigest()

# Store with document
document.checksum_md5 = md5_hash
document.checksum_sha256 = sha256_hash
```

### 9. File Metadata

MIME type detection:

```python
import mimetypes

mime_type, _ = mimetypes.guess_type(filename)
mime_type = mime_type or "application/octet-stream"
```

---

## Workspace and Monorepo Structure

The project uses `uv` workspaces (defined in root `pyproject.toml`):

```toml
[tool.uv.workspace]
members = [
    "libs/kbrain-storage",
    "services/kbrain_backend",
]
```

This allows:
- Shared dependencies via workspace resolution
- Local development with `uv sync` (installs all workspace members editable)
- Independent versioning of libraries and services
- Cross-workspace imports: `from kbrain_storage import LocalFileStorage`

---

## Performance Considerations

### Connection Pooling

Database connection pool is configured with:
- Min: 2 connections
- Max: 10 connections (pool_max = pool_min + max_overflow)
- Pre-ping enabled to verify connection health

Adjust for production load:
```python
# In .env
DATABASE_POOL_MIN=5
DATABASE_POOL_MAX=20
```

### Indexes

Strategic indexes exist on:
- Foreign keys (automatic)
- Status columns (filtering)
- Upload dates (sorting)
- Scope names (lookups)

### Query Optimization

- Use `selectinload()` for eager loading relationships
- Implement pagination for large result sets
- Avoid N+1 queries with relationship loading

---

## Security Considerations

### Path Traversal Prevention

LocalFileStorage validates paths:

```python
def _resolve_path(self, path: str) -> Path:
    full_path = (self.root_path / path).resolve()
    full_path.relative_to(self.root_path)  # Raises if outside root
    return full_path
```

### File Size Limits

Upload size validation:

```python
max_file_size = 104857600  # 100MB
if file_size > settings.max_file_size:
    raise HTTPException(status_code=413, detail="File too large")
```

### Extension Validation

Per-scope allowed extensions:

```python
if file_ext not in scope.allowed_extensions:
    raise HTTPException(status_code=400, detail="Extension not allowed")
```

### CORS Configuration

Restricted to specific origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # ["http://localhost:5173", ...]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Troubleshooting

### Database Connection Issues

```bash
# Verify PostgreSQL is running
psql -U kbrain -d kbrain -h localhost

# Check migrations are applied
cd services/kbrain-backend
alembic current

# Apply missing migrations
alembic upgrade head
```

### Storage Backend Issues

Check `.env` file:
```bash
STORAGE_BACKEND=local
STORAGE_ROOT=./storage_data
```

Verify directory exists and is writable:
```bash
ls -la storage_data/
mkdir -p storage_data
chmod 755 storage_data
```

### API Not Responding

```bash
# Check if server is running
curl http://localhost:8000/health

# Check logs
docker logs kbrain-backend  # if using docker
```

### Type Checking Errors

```bash
# Run mypy to find type issues
uv run mypy --strict services/kbrain-backend

# Fix by adding type annotations or using # type: ignore
```

---

## Quick Reference

### Important Paths
- **Main app**: `/services/kbrain-backend/src/kbrain_backend/main.py`
- **Routes**: `/services/kbrain-backend/src/kbrain_backend/api/routes/`
- **Models**: `/services/kbrain-backend/src/kbrain_backend/core/models/`
- **Database**: `/services/kbrain-backend/src/kbrain_backend/database/`
- **Storage lib**: `/libs/kbrain-storage/src/kbrain_storage/`
- **Migrations**: `/services/kbrain-backend/alembic/versions/`

### Key Classes
- **BaseFileStorage** - Abstract storage interface
- **LocalFileStorage** - File system implementation
- **AsyncSession** - Database session (dependency)
- **Document, Scope, Tag** - Core ORM models
- **DocumentResponse, ScopeResponse** - Pydantic schemas

### Key Environment Variables
- `DATABASE_URL` - PostgreSQL connection
- `STORAGE_BACKEND` - "local", "s3", or "azure"
- `STORAGE_ROOT` - Local storage directory
- `MAX_FILE_SIZE` - Upload limit in bytes
- `CORS_ORIGINS` - Allowed frontend origins

### API Base URLs
- v1 API: `/v1/*` (preferred)
- Legacy: `/api/*` (deprecated)
- Health: `/health`
- Docs: `/docs` (Swagger), `/redoc` (ReDoc)

---

## Next Steps for Future Development

1. **Implement S3 Storage** - Fill in `libs/kbrain-storage/aws_s3.py`
2. **Implement Azure Storage** - Fill in `libs/kbrain-storage/azure_blob.py`
3. **Add Unit Tests** - Create comprehensive test suite
4. **Implement Processing Queue** - Async job processing with workers
5. **Add Authentication** - JWT token-based auth for routes
6. **Add Rate Limiting** - Prevent abuse of upload endpoints
7. **Implement Pagination Cache** - Optimize repeated list operations
8. **Add Full-Text Search** - For document content searching
9. **Document API** - Complete OpenAPI documentation
10. **Performance Monitoring** - Add metrics/tracing

---

**Last Updated:** 2024-10-24
**Architecture Version:** 1.0.0
**Database Schema Version:** Latest (check alembic current)

