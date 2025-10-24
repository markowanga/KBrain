# Database Schema

## Overview

The KBrain database stores scope definitions, document metadata, processing status, and storage configurations. The schema is designed to be extensible for future features while maintaining simplicity for v1.

## Entity Relationship Diagram

```
┌─────────────────┐         ┌──────────────────┐
│     Scopes      │         │   Documents      │
├─────────────────┤         ├──────────────────┤
│ id (PK)         │◄───────┤│ id (PK)          │
│ name            │       1:N│ scope_id (FK)    │
│ description     │         │ filename         │
│ allowed_exts    │         │ original_name    │
│ storage_config  │         │ file_size        │
│ created_at      │         │ mime_type        │
│ updated_at      │         │ storage_path     │
└─────────────────┘         │ storage_backend  │
                            │ status           │
                            │ upload_date      │
                            │ processed_at     │
                            │ error_message    │
                            │ metadata         │
                            │ created_at       │
                            │ updated_at       │
                            └──────────────────┘

┌──────────────────────────┐
│   Processing_Queue       │
├──────────────────────────┤
│ id (PK)                  │
│ document_id (FK)         │
│ priority                 │
│ retry_count              │
│ max_retries              │
│ scheduled_at             │
│ started_at               │
│ completed_at             │
│ worker_id                │
│ status                   │
│ created_at               │
└──────────────────────────┘
```

## Table Definitions

### Scopes Table

Stores knowledge scope definitions and configurations.

```sql
CREATE TABLE scopes (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(255) NOT NULL UNIQUE,
    description         TEXT,
    allowed_extensions  TEXT[] NOT NULL,  -- Array of allowed file extensions
    storage_backend     VARCHAR(50) DEFAULT 'local',  -- 's3', 'azure_blob', 'sftp', 'local'
    storage_config      JSONB,  -- Backend-specific configuration
    is_active           BOOLEAN DEFAULT true,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scopes_name ON scopes(name);
CREATE INDEX idx_scopes_is_active ON scopes(is_active);
```

**Field Descriptions:**

- `id`: Unique identifier for the scope
- `name`: Human-readable scope name (unique)
- `description`: Optional description of the scope's purpose
- `allowed_extensions`: Array of file extensions (e.g., ['pdf', 'docx', 'txt'])
- `storage_backend`: Type of storage backend to use
- `storage_config`: JSON configuration for the storage backend (credentials, bucket names, etc.)
- `is_active`: Soft delete flag
- `created_at`: Timestamp when scope was created
- `updated_at`: Timestamp of last update

**Example storage_config for different backends:**

```json
// S3
{
  "bucket": "kbrain-documents",
  "region": "us-east-1",
  "path_prefix": "scopes/research/"
}

// Azure Blob
{
  "container": "kbrain-docs",
  "path_prefix": "research/"
}

// SFTP
{
  "host": "sftp.example.com",
  "port": 22,
  "base_path": "/documents/research/",
  "username": "kbrain_user"
}
```

### Documents Table

Stores document metadata and processing status.

```sql
CREATE TABLE documents (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scope_id            UUID NOT NULL REFERENCES scopes(id) ON DELETE CASCADE,
    filename            VARCHAR(500) NOT NULL,  -- Generated unique filename
    original_name       VARCHAR(500) NOT NULL,  -- Original uploaded filename
    file_size           BIGINT NOT NULL,  -- Size in bytes
    mime_type           VARCHAR(255),
    file_extension      VARCHAR(50) NOT NULL,
    storage_path        TEXT NOT NULL,  -- Full path in storage backend
    storage_backend     VARCHAR(50) NOT NULL,  -- Inherited from scope or override
    checksum_md5        VARCHAR(32),  -- MD5 hash for integrity
    checksum_sha256     VARCHAR(64),  -- SHA-256 hash for integrity

    -- Status tracking
    status              VARCHAR(50) NOT NULL DEFAULT 'added',  -- 'added', 'processing', 'processed', 'failed'
    upload_date         TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processing_started  TIMESTAMP WITH TIME ZONE,
    processed_at        TIMESTAMP WITH TIME ZONE,

    -- Error handling
    error_message       TEXT,
    retry_count         INTEGER DEFAULT 0,

    -- Additional metadata
    metadata            JSONB,  -- Extensible metadata field

    -- Timestamps
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_scope_id ON documents(scope_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_upload_date ON documents(upload_date DESC);
CREATE INDEX idx_documents_filename ON documents(filename);
CREATE INDEX idx_documents_original_name ON documents(original_name);
```

**Field Descriptions:**

- `id`: Unique identifier for the document
- `scope_id`: Reference to the parent scope
- `filename`: Unique generated filename (e.g., UUID-based)
- `original_name`: Original filename as uploaded by user
- `file_size`: File size in bytes
- `mime_type`: MIME type of the file
- `file_extension`: File extension (for quick filtering)
- `storage_path`: Complete path in the storage backend
- `storage_backend`: Which storage backend is being used
- `checksum_md5`: MD5 hash for integrity verification
- `checksum_sha256`: SHA-256 hash for integrity verification
- `status`: Current processing status
- `upload_date`: When the file was uploaded
- `processing_started`: When processing began
- `processed_at`: When processing completed
- `error_message`: Error details if processing failed
- `retry_count`: Number of processing retries
- `metadata`: JSON field for extensible metadata (extracted text, analysis results, etc.)

**Status Values:**

- `added`: Document uploaded, waiting for processing
- `processing`: Currently being processed
- `processed`: Successfully processed
- `failed`: Processing failed

### Processing Queue Table

Manages the document processing queue (optional, can use external queue service).

```sql
CREATE TABLE processing_queue (
    id                  BIGSERIAL PRIMARY KEY,
    document_id         UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    priority            INTEGER DEFAULT 0,  -- Higher number = higher priority
    retry_count         INTEGER DEFAULT 0,
    max_retries         INTEGER DEFAULT 3,
    scheduled_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at          TIMESTAMP WITH TIME ZONE,
    completed_at        TIMESTAMP WITH TIME ZONE,
    worker_id           VARCHAR(255),  -- ID of processing worker
    status              VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    error_message       TEXT,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_queue_status ON processing_queue(status);
CREATE INDEX idx_queue_priority ON processing_queue(priority DESC, scheduled_at ASC);
CREATE INDEX idx_queue_document_id ON processing_queue(document_id);
```

**Field Descriptions:**

- `id`: Queue entry identifier
- `document_id`: Reference to document being processed
- `priority`: Processing priority (higher = sooner)
- `retry_count`: Current retry attempt
- `max_retries`: Maximum retry attempts
- `scheduled_at`: When the job was scheduled
- `started_at`: When processing started
- `completed_at`: When processing completed
- `worker_id`: Identifier of the worker processing this job
- `status`: Queue entry status
- `error_message`: Error details if failed

## Additional Tables (Future Enhancements)

### Users Table (Future)

```sql
CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email               VARCHAR(255) NOT NULL UNIQUE,
    username            VARCHAR(100) NOT NULL UNIQUE,
    password_hash       VARCHAR(255) NOT NULL,
    is_active           BOOLEAN DEFAULT true,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Scope Permissions Table (Future)

```sql
CREATE TABLE scope_permissions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scope_id            UUID NOT NULL REFERENCES scopes(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission_level    VARCHAR(50) NOT NULL,  -- 'read', 'write', 'admin'
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(scope_id, user_id)
);
```

### Audit Log Table (Future)

```sql
CREATE TABLE audit_log (
    id                  BIGSERIAL PRIMARY KEY,
    entity_type         VARCHAR(50) NOT NULL,  -- 'scope', 'document', 'user'
    entity_id           UUID NOT NULL,
    action              VARCHAR(50) NOT NULL,  -- 'create', 'update', 'delete', 'download'
    user_id             UUID REFERENCES users(id),
    changes             JSONB,  -- What changed
    ip_address          INET,
    user_agent          TEXT,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_created_at ON audit_log(created_at DESC);
```

## Database Triggers

### Update Timestamp Trigger

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_scopes_updated_at BEFORE UPDATE ON scopes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Document Status Update Trigger

```sql
CREATE OR REPLACE FUNCTION update_document_status_timestamps()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'processing' AND OLD.status != 'processing' THEN
        NEW.processing_started = CURRENT_TIMESTAMP;
    END IF;

    IF NEW.status = 'processed' AND OLD.status != 'processed' THEN
        NEW.processed_at = CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_document_status_ts BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_document_status_timestamps();
```

## Queries Examples

### Get all documents in a scope with status

```sql
SELECT
    d.id,
    d.original_name,
    d.file_size,
    d.status,
    d.upload_date,
    d.processed_at,
    s.name as scope_name
FROM documents d
JOIN scopes s ON d.scope_id = s.id
WHERE s.id = :scope_id
ORDER BY d.upload_date DESC;
```

### Get documents pending processing

```sql
SELECT
    d.id,
    d.filename,
    d.storage_path,
    d.scope_id,
    s.name as scope_name
FROM documents d
JOIN scopes s ON d.scope_id = s.id
WHERE d.status = 'added'
ORDER BY d.upload_date ASC;
```

### Get processing statistics by scope

```sql
SELECT
    s.name as scope_name,
    COUNT(*) as total_documents,
    COUNT(*) FILTER (WHERE d.status = 'added') as pending,
    COUNT(*) FILTER (WHERE d.status = 'processing') as processing,
    COUNT(*) FILTER (WHERE d.status = 'processed') as processed,
    COUNT(*) FILTER (WHERE d.status = 'failed') as failed,
    SUM(d.file_size) as total_size
FROM scopes s
LEFT JOIN documents d ON s.id = d.scope_id
GROUP BY s.id, s.name;
```

## Migration Strategy

### Initial Migration (v1.0.0)

1. Create `scopes` table
2. Create `documents` table
3. Create `processing_queue` table (optional)
4. Create indexes
5. Create triggers

### Version Control

Use migration tool (e.g., Alembic for Python, Flyway for Java, or database-specific tools) to version control schema changes.

## Backup and Maintenance

### Recommended Practices

1. **Regular Backups**: Daily full backups, hourly incremental
2. **Partition Strategy**: Partition `documents` and `audit_log` by date for better performance
3. **Archive Strategy**: Move old processed documents to archive storage after N days
4. **Index Maintenance**: Regularly analyze and rebuild indexes
5. **Vacuum**: Regular VACUUM on PostgreSQL to reclaim space

## Notes

- UUIDs used for primary keys to avoid sequential ID enumeration and support distributed systems
- JSONB fields provide flexibility for future metadata without schema changes
- Indexes optimized for common query patterns
- Timestamps include timezone information for global deployments
- Foreign keys with CASCADE delete for data integrity
- Status fields use VARCHAR for extensibility (could add more statuses later)
