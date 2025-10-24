# KBrain - System Architecture

## Overview

KBrain is a knowledge management system that allows users to organize and process documents within defined scopes. The system provides a flexible document upload mechanism with pluggable storage backends and automated document processing pipeline.

## System Goals

- **Scope-based Organization**: Documents are organized within scopes (knowledge domains)
- **Flexible File Types**: Each scope defines allowed file extensions
- **Multiple Storage Backends**: Support for S3, Azure Blob Storage, and SFTP
- **Processing Pipeline**: Automatic document processing with status tracking
- **No Authentication (v1)**: Initial version without user authentication

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Web UI)                        │
│  - Scope Management                                          │
│  - Document Upload                                           │
│  - Status Monitoring                                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ REST API
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    Backend API Server                        │
│  - Scope CRUD Operations                                     │
│  - Document Upload Handler                                   │
│  - Storage Abstraction Layer                                 │
│  - Processing Queue Manager                                  │
└───────┬──────────────────────────┬──────────────────────────┘
        │                          │
        │                          │
┌───────▼─────────┐      ┌─────────▼────────────────────────┐
│   Database      │      │    Storage Layer (Interface)     │
│                 │      │                                   │
│ - Scopes        │      │  ┌─────────────────────────────┐ │
│ - Documents     │      │  │  S3 Implementation          │ │
│ - Status        │      │  └─────────────────────────────┘ │
│ - Metadata      │      │  ┌─────────────────────────────┐ │
└─────────────────┘      │  │  Azure Blob Implementation  │ │
                         │  └─────────────────────────────┘ │
                         │  ┌─────────────────────────────┐ │
                         │  │  SFTP Implementation        │ │
                         │  └─────────────────────────────┘ │
                         └──────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              Document Processing Worker(s)                   │
│  - Polls processing queue                                    │
│  - Updates document status                                   │
│  - Extensible processing pipeline                            │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Frontend Application
- Single Page Application (SPA)
- Scope management interface
- Document upload with progress tracking
- Document list with status indicators
- File extension validation before upload

### 2. Backend API Server
- RESTful API endpoints
- Request validation
- Storage abstraction layer
- Database operations
- Queue management for processing

### 3. Storage Interface
- Abstract interface defining storage operations
- Multiple implementations (S3, Azure Blob, SFTP)
- Configurable per scope or globally
- Operations: upload, download, delete, check existence

### 4. Database
- Stores scope definitions
- Tracks document metadata
- Manages processing status
- Provides query capabilities

### 5. Processing Worker
- Background worker for document processing
- Status updates (Added → Processing → Processed)
- Extensible for future processing logic
- Error handling and retry mechanisms

## Data Flow

### Document Upload Flow

1. User selects scope and file(s) in UI
2. Frontend validates file extensions against scope configuration
3. File uploaded to backend API
4. Backend:
   - Validates request
   - Creates database record with status "Added"
   - Uploads file to configured storage backend
   - Queues document for processing
5. Processing worker:
   - Picks up document from queue
   - Updates status to "Processing"
   - Performs processing operations
   - Updates status to "Processed"
6. Frontend polls or receives updates on document status

### Scope Creation Flow

1. User creates new scope with:
   - Scope name
   - Description
   - Allowed file extensions (e.g., .pdf, .docx, .txt)
   - Storage configuration (optional)
2. Backend validates and creates scope in database
3. Scope becomes available for document uploads

## Key Design Decisions

### 1. Storage Abstraction
- **Decision**: Use interface/abstract class pattern for storage
- **Rationale**: Allows easy switching between storage providers, supports multiple storage backends, facilitates testing with mock implementations

### 2. Status Tracking
- **Decision**: Three-state status model (Added, Processing, Processed)
- **Rationale**: Simple enough for v1, extensible for future states (Failed, Archived, etc.)

### 3. Scope-based Organization
- **Decision**: All documents belong to a scope
- **Rationale**: Provides natural organization, allows different configurations per knowledge domain, prepares for future multi-tenant scenarios

### 4. File Extension Validation
- **Decision**: Configure allowed extensions per scope
- **Rationale**: Prevents invalid file uploads, scope-specific requirements, reduces processing errors

### 5. Asynchronous Processing
- **Decision**: Decouple upload from processing
- **Rationale**: Better user experience, scalability, allows long-running processing tasks

## Scalability Considerations

### Phase 1 (Current)
- Single backend server
- Single processing worker
- SQLite or PostgreSQL database
- Single storage backend

### Future Phases
- Multiple backend instances (load balancer)
- Multiple processing workers (queue-based distribution)
- Database clustering/replication
- Multiple storage backends per scope
- Caching layer (Redis)
- CDN for file delivery

## Security Considerations (Future)

While v1 has no authentication, the architecture should support future additions:
- User authentication and authorization
- Role-based access control (RBAC)
- Scope-level permissions
- Encrypted storage
- Audit logging

## Technology Stack (Recommendations)

See separate document: `TECH_STACK.md`

## Related Documentation

- [Database Schema](./DATABASE_SCHEMA.md)
- [Storage Interface Specification](./STORAGE_INTERFACE.md)
- [API Specification](./API_SPECIFICATION.md)
- [Project Structure](./PROJECT_STRUCTURE.md)
- [Technology Stack](./TECH_STACK.md)
