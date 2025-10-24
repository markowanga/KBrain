# Storage Interface Specification

## Overview

The Storage Interface provides an abstraction layer for document storage, allowing KBrain to support multiple storage backends (AWS S3, Azure Blob Storage, SFTP) through a unified API. This design pattern enables easy switching between storage providers and simplifies testing.

## Design Pattern

**Strategy Pattern**: Each storage backend implements the same interface, allowing runtime selection of storage provider.

## Core Interface Definition

### IStorageProvider Interface

```
Interface: IStorageProvider

Methods:
  - upload(file_path: string, destination_path: string, metadata?: object): Promise<UploadResult>
  - download(storage_path: string, local_path: string): Promise<DownloadResult>
  - delete(storage_path: string): Promise<DeleteResult>
  - exists(storage_path: string): Promise<boolean>
  - get_metadata(storage_path: string): Promise<FileMetadata>
  - list_files(prefix: string, options?: ListOptions): Promise<FileList>
  - get_signed_url(storage_path: string, expiration_seconds: number): Promise<string>
  - copy(source_path: string, destination_path: string): Promise<CopyResult>
  - move(source_path: string, destination_path: string): Promise<MoveResult>
```

## Data Types

### UploadResult

```typescript
interface UploadResult {
  success: boolean;
  storage_path: string;
  size: number;
  checksum_md5?: string;
  checksum_sha256?: string;
  etag?: string;
  error?: string;
  metadata?: {
    backend_specific: any;
  };
}
```

### DownloadResult

```typescript
interface DownloadResult {
  success: boolean;
  local_path: string;
  size: number;
  checksum_md5?: string;
  error?: string;
}
```

### DeleteResult

```typescript
interface DeleteResult {
  success: boolean;
  deleted_path: string;
  error?: string;
}
```

### FileMetadata

```typescript
interface FileMetadata {
  path: string;
  size: number;
  created_at: Date;
  modified_at: Date;
  content_type?: string;
  checksum_md5?: string;
  checksum_sha256?: string;
  custom_metadata?: Record<string, string>;
}
```

### FileList

```typescript
interface FileList {
  files: FileInfo[];
  directories: string[];
  has_more: boolean;
  next_token?: string;
}

interface FileInfo {
  path: string;
  size: number;
  modified_at: Date;
  is_directory: boolean;
}
```

### ListOptions

```typescript
interface ListOptions {
  max_results?: number;
  continuation_token?: string;
  recursive?: boolean;
}
```

### CopyResult / MoveResult

```typescript
interface CopyResult {
  success: boolean;
  source_path: string;
  destination_path: string;
  error?: string;
}

interface MoveResult {
  success: boolean;
  source_path: string;
  destination_path: string;
  error?: string;
}
```

## Storage Provider Implementations

### 1. S3StorageProvider

AWS S3 implementation of the storage interface.

#### Configuration

```typescript
interface S3Configuration {
  type: 's3';
  region: string;
  bucket: string;
  access_key_id?: string;  // Optional, can use IAM role
  secret_access_key?: string;  // Optional, can use IAM role
  endpoint?: string;  // For S3-compatible services (MinIO, DigitalOcean Spaces)
  path_prefix?: string;  // Base path within bucket
  server_side_encryption?: 'AES256' | 'aws:kms';
  kms_key_id?: string;  // If using KMS encryption
  storage_class?: 'STANDARD' | 'INTELLIGENT_TIERING' | 'GLACIER';
}
```

#### Implementation Notes

- Use AWS SDK for JavaScript/Python/etc.
- Support multipart uploads for large files (> 5MB)
- Implement retry logic with exponential backoff
- Use presigned URLs for direct browser uploads (future)
- Support S3 event notifications for processing triggers

#### Example Path Structure

```
s3://bucket-name/
  └── scopes/
      └── research/
          ├── 2024/
          │   ├── 01/
          │   │   ├── abc123-document.pdf
          │   │   └── def456-paper.docx
          │   └── 02/
          └── 2025/
```

### 2. AzureBlobStorageProvider

Azure Blob Storage implementation.

#### Configuration

```typescript
interface AzureBlobConfiguration {
  type: 'azure_blob';
  account_name: string;
  account_key?: string;  // Optional, can use managed identity
  connection_string?: string;  // Alternative to account_name + key
  container: string;
  path_prefix?: string;
  sas_token?: string;  // For limited access
  endpoint?: string;  // Custom endpoint
  tier?: 'Hot' | 'Cool' | 'Archive';
}
```

#### Implementation Notes

- Use Azure Storage SDK
- Support block blob uploads
- Implement lease mechanism for concurrent access control
- Support Azure CDN integration
- Handle blob snapshots for versioning (future)

#### Example Path Structure

```
https://account.blob.core.windows.net/container/
  └── kbrain/
      └── scopes/
          └── legal/
              ├── contracts/
              │   ├── contract-001.pdf
              │   └── contract-002.pdf
              └── agreements/
```

### 3. SFTPStorageProvider

SFTP (SSH File Transfer Protocol) implementation.

#### Configuration

```typescript
interface SFTPConfiguration {
  type: 'sftp';
  host: string;
  port: number;
  username: string;
  password?: string;  // Password authentication
  private_key?: string;  // SSH key authentication (preferred)
  private_key_path?: string;  // Path to SSH key file
  passphrase?: string;  // If private key is encrypted
  base_path: string;  // Base directory on SFTP server
  connection_timeout?: number;  // Seconds
  keepalive_interval?: number;  // Seconds
}
```

#### Implementation Notes

- Use SSH2/SFTP library (e.g., ssh2-sftp-client for Node.js)
- Implement connection pooling for performance
- Handle connection timeouts and retries
- Ensure proper file permissions on upload
- No native signed URL support (would require proxy implementation)

#### Example Path Structure

```
/remote/kbrain/
  └── documents/
      └── scope-research/
          ├── pdfs/
          │   ├── research-001.pdf
          │   └── research-002.pdf
          └── texts/
              └── notes.txt
```

### 4. LocalStorageProvider

Local filesystem implementation (for development/testing).

#### Configuration

```typescript
interface LocalStorageConfiguration {
  type: 'local';
  base_path: string;  // Absolute path to kbrain_storage directory
  create_directories?: boolean;  // Auto-create directories
}
```

#### Implementation Notes

- Simple filesystem operations
- Useful for development and testing
- NOT recommended for production
- Can be used as fallback

#### Example Path Structure

```
/var/kbrain/storage/
  └── scopes/
      └── test-scope/
          ├── documents/
          │   └── test-file.pdf
          └── temp/
```

## Storage Factory Pattern

### StorageFactory

Responsible for creating appropriate storage provider instances.

```typescript
class StorageFactory {
  static create(config: StorageConfiguration): IStorageProvider {
    switch (config.type) {
      case 's3':
        return new S3StorageProvider(config as S3Configuration);
      case 'azure_blob':
        return new AzureBlobStorageProvider(config as AzureBlobConfiguration);
      case 'sftp':
        return new SFTPStorageProvider(config as SFTPConfiguration);
      case 'local':
        return new LocalStorageProvider(config as LocalStorageConfiguration);
      default:
        throw new Error(`Unknown storage type: ${config.type}`);
    }
  }
}
```

## Error Handling

### Common Error Types

```typescript
enum StorageErrorType {
  NOT_FOUND = 'NOT_FOUND',
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  CONNECTION_ERROR = 'CONNECTION_ERROR',
  TIMEOUT = 'TIMEOUT',
  QUOTA_EXCEEDED = 'QUOTA_EXCEEDED',
  INVALID_PATH = 'INVALID_PATH',
  CHECKSUM_MISMATCH = 'CHECKSUM_MISMATCH',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR'
}

class StorageError extends Error {
  type: StorageErrorType;
  original_error?: Error;
  details?: any;

  constructor(type: StorageErrorType, message: string, original?: Error) {
    super(message);
    this.type = type;
    this.original_error = original;
  }
}
```

### Retry Strategy

Implement exponential backoff for transient errors:

```
Retry Conditions:
  - Connection timeouts
  - Network errors
  - Rate limiting (429, 503)
  - Temporary server errors (500, 502, 503, 504)

Retry Strategy:
  - Max retries: 3
  - Initial delay: 1 second
  - Backoff multiplier: 2
  - Max delay: 30 seconds
  - Add jitter to prevent thundering herd

Non-Retryable Errors:
  - File not found (404)
  - Permission denied (403)
  - Invalid credentials (401)
  - Invalid path/parameters (400)
```

## Performance Considerations

### Multipart Upload

For large files (> 100MB), use multipart/chunked uploads:

**S3**: Use multipart upload API (5MB chunks)
**Azure Blob**: Use block upload API
**SFTP**: Stream in chunks to avoid memory issues

### Connection Pooling

**S3/Azure**: HTTP connection pooling handled by SDKs
**SFTP**: Implement connection pool (max 5-10 connections per provider)

### Streaming

Prefer streaming for downloads to reduce memory usage:

```typescript
interface IStorageProvider {
  download_stream(storage_path: string): Promise<ReadableStream>;
  upload_stream(stream: ReadableStream, destination_path: string): Promise<UploadResult>;
}
```

## Security Considerations

### Credentials Management

- **Never** hardcode credentials in source code
- Use environment variables or secret management service
- Prefer IAM roles (AWS) or Managed Identities (Azure) when possible
- Rotate credentials regularly
- Use least privilege principle

### Encryption

**At Rest:**
- S3: Server-side encryption (SSE-S3 or SSE-KMS)
- Azure: Storage Service Encryption (SSE)
- SFTP: Depends on server configuration

**In Transit:**
- All connections use TLS/SSL
- SFTP uses SSH encryption

### Access Control

- Use bucket policies (S3) or container ACLs (Azure)
- Implement path validation to prevent directory traversal
- Validate file types and sizes before upload
- Sanitize filenames

## Testing Strategy

### Unit Tests

Mock storage providers for testing business logic:

```typescript
class MockStorageProvider implements IStorageProvider {
  private files: Map<string, Buffer> = new Map();

  async upload(file_path: string, destination_path: string): Promise<UploadResult> {
    // In-memory implementation
  }

  async download(storage_path: string, local_path: string): Promise<DownloadResult> {
    // In-memory implementation
  }

  // ... other methods
}
```

### Integration Tests

Test against real storage backends:
- Use test buckets/containers/directories
- Clean up after tests
- Test error scenarios (network issues, permission errors)
- Test large file handling

### Test Matrix

```
Provider | Upload | Download | Delete | List | Metadata | Signed URL
---------|--------|----------|--------|------|----------|------------
S3       |   ✓    |    ✓     |   ✓    |  ✓   |    ✓     |     ✓
Azure    |   ✓    |    ✓     |   ✓    |  ✓   |    ✓     |     ✓
SFTP     |   ✓    |    ✓     |   ✓    |  ✓   |    ✓     |     ✗
Local    |   ✓    |    ✓     |   ✓    |  ✓   |    ✓     |     ✗
```

## Configuration Examples

### Environment Variables

```bash
# S3 Configuration
STORAGE_TYPE=s3
S3_REGION=us-east-1
S3_BUCKET=kbrain-documents
S3_PATH_PREFIX=production/
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# Azure Blob Configuration
STORAGE_TYPE=azure_blob
AZURE_STORAGE_ACCOUNT=kbrainstorage
AZURE_STORAGE_CONTAINER=documents
AZURE_STORAGE_KEY=...

# SFTP Configuration
STORAGE_TYPE=sftp
SFTP_HOST=sftp.example.com
SFTP_PORT=22
SFTP_USERNAME=kbrain
SFTP_PRIVATE_KEY_PATH=/keys/kbrain_rsa
SFTP_BASE_PATH=/data/kbrain/
```

### JSON Configuration (in database)

```json
{
  "type": "s3",
  "region": "eu-west-1",
  "bucket": "kbrain-eu-documents",
  "path_prefix": "scopes/research/",
  "storage_class": "INTELLIGENT_TIERING",
  "server_side_encryption": "aws:kms",
  "kms_key_id": "arn:aws:kms:eu-west-1:123456789:key/abc-123"
}
```

## Migration Between Storage Providers

### Migration Strategy

1. **Dual Write**: Write to both old and new storage
2. **Background Migration**: Copy existing files to new storage
3. **Read Fallback**: Try new storage first, fallback to old
4. **Verification**: Verify checksums after migration
5. **Cutover**: Switch to new storage exclusively
6. **Cleanup**: Remove old storage data after verification period

### Migration Tool Pseudocode

```
function migrate_storage(old_provider, new_provider, scope_id):
  documents = get_documents_by_scope(scope_id)

  for document in documents:
    if not new_provider.exists(document.storage_path):
      temp_file = old_provider.download(document.storage_path)
      result = new_provider.upload(temp_file, document.storage_path)

      if result.checksum_md5 == document.checksum_md5:
        update_document_storage_backend(document.id, new_provider.type)
        log_success(document.id)
      else:
        log_error(document.id, "Checksum mismatch")
```

## Monitoring and Metrics

### Key Metrics to Track

- Upload/download success rate
- Average upload/download time
- Storage space used per scope
- API call counts (to track costs)
- Error rates by type
- Connection pool utilization (SFTP)

### Logging

Log all storage operations with:
- Timestamp
- Operation type
- Storage path
- File size
- Duration
- Success/failure
- Error details

## Future Enhancements

1. **CDN Integration**: Serve files through CloudFront/Azure CDN
2. **Caching Layer**: Cache frequently accessed files in Redis
3. **Versioning**: Support file versions in storage
4. **Compression**: Automatic compression for certain file types
5. **Deduplication**: Detect and prevent duplicate file uploads
6. **Lifecycle Policies**: Automatic archival/deletion based on rules
7. **Multi-region**: Replicate files across regions for redundancy
8. **Encryption at Application Level**: Encrypt files before storage upload
