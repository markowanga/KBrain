# KBrain File Storage Module

Unified file storage interface for KBrain backend supporting multiple backends: Local filesystem, AWS S3, and Azure Blob Storage.

## Architecture

```
storage/
├── __init__.py         # Module exports
├── base.py             # BaseFileStorage - abstract interface
├── local.py            # LocalFileStorage - local filesystem
├── aws_s3.py          # S3FileStorage - AWS S3 (stub)
├── azure_blob.py      # AzureBlobStorage - Azure Blob (stub)
└── README.md          # This file
```

## Features

- **Unified Interface**: Single API for all storage backends
- **Async Operations**: All methods use async/await
- **Path Safety**: Protection against path traversal attacks
- **Multiple Backends**: Local, AWS S3, Azure Blob (extensible)
- **Cross-platform**: Uses pathlib for OS-independent paths

## Storage Backends

### Local File Storage

**Status**: ✅ Fully Implemented

Local filesystem storage using Python's pathlib.

```python
from storage import LocalFileStorage

storage = LocalFileStorage(root_path="storage_data")

# Save file
await storage.save_file("docs/readme.md", b"# Hello")

# Read file
content = await storage.read_file("docs/readme.md")

# Check existence
exists = await storage.exists("docs/readme.md")

# List directory
files = await storage.list_directory("docs", recursive=True)
```

**Features**:
- Thread-safe async operations
- Automatic directory creation
- Path traversal protection
- Copy/move operations
- Recursive directory operations

### AWS S3 Storage

**Status**: 🚧 Stub/Documentation Only

AWS S3 storage backend.

```python
from storage.aws_s3 import S3FileStorage

storage = S3FileStorage(
    bucket_name="my-bucket",
    region="us-east-1",
    prefix="kbrain/"  # Optional prefix
)
```

**Requirements**:
```bash
pip install aioboto3
```

**Configuration**:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

**To Implement**: See `aws_s3.py` for detailed implementation notes.

### Azure Blob Storage

**Status**: 🚧 Stub/Documentation Only

Azure Blob Storage backend.

```python
from storage.azure_blob import AzureBlobStorage

storage = AzureBlobStorage(
    container_name="my-container",
    connection_string="DefaultEndpointsProtocol=https;..."
)
```

**Requirements**:
```bash
pip install azure-kbrain_storage-blob aiohttp
```

**Configuration**:
- `AZURE_STORAGE_CONNECTION_STRING` or
- `AZURE_STORAGE_ACCOUNT_NAME` + `AZURE_STORAGE_ACCOUNT_KEY`

**To Implement**: See `azure_blob.py` for detailed implementation notes.

## API Reference

### Core Methods (All Backends)

#### save_file
```python
async def save_file(
    path: Union[str, Path],
    content: bytes,
    overwrite: bool = True
) -> bool
```
Save file to storage.

**Parameters**:
- `path`: File path relative to storage root
- `content`: File content as bytes
- `overwrite`: Whether to overwrite existing file

**Returns**: `True` if successful

#### read_file
```python
async def read_file(path: Union[str, Path]) -> Optional[bytes]
```
Read file from storage.

**Returns**: File content as bytes, or `None` if not found

#### exists
```python
async def exists(path: Union[str, Path]) -> bool
```
Check if file or directory exists.

#### list_directory
```python
async def list_directory(
    path: Union[str, Path] = "",
    recursive: bool = False
) -> List[str]
```
List files in directory.

**Parameters**:
- `path`: Directory path (empty string for root)
- `recursive`: Whether to list recursively

**Returns**: List of file paths (relative to storage root)

#### delete_file
```python
async def delete_file(path: Union[str, Path]) -> bool
```
Delete file from storage.

#### get_file_size
```python
async def get_file_size(path: Union[str, Path]) -> Optional[int]
```
Get file size in bytes.

#### create_directory
```python
async def create_directory(path: Union[str, Path]) -> bool
```
Create directory (if backend supports it).

### LocalFileStorage Additional Methods

#### copy_file
```python
async def copy_file(
    source: Union[str, Path],
    destination: Union[str, Path]
) -> bool
```
Copy file within storage.

#### move_file
```python
async def move_file(
    source: Union[str, Path],
    destination: Union[str, Path]
) -> bool
```
Move file within storage.

#### delete_directory
```python
async def delete_directory(
    path: Union[str, Path],
    recursive: bool = False
) -> bool
```
Delete directory.

## Configuration

Set storage backend via environment variables:

```bash
# Storage backend type
export STORAGE_BACKEND=local  # or "s3" or "azure"

# Local kbrain_storage root directory
export STORAGE_ROOT=storage_data

# AWS S3 configuration (if using S3)
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1
export S3_BUCKET_NAME=my-bucket

# Azure configuration (if using Azure)
export AZURE_STORAGE_CONNECTION_STRING=your_connection_string
export AZURE_CONTAINER_NAME=my-container
```

## REST API Endpoints

The backend exposes these file storage endpoints:

### Upload File
```
POST /api/files/upload
Content-Type: multipart/form-data

Parameters:
  - file: File to upload
  - path: Optional custom path
```

### Download File
```
GET /api/files/download/{path}

Returns: File content with appropriate Content-Type
```

### Read File
```
GET /api/files/read/{path}

Returns: JSON with file content (text or base64)
```

### Check File Exists
```
GET /api/files/exists/{path}

Returns: {"path": "...", "exists": true/false}
```

### List Files
```
GET /api/files/list?path=docs&recursive=true

Returns: {"path": "docs", "files": [...], "count": 5}
```

### Delete File
```
DELETE /api/files/delete/{path}

Returns: {"path": "...", "deleted": true}
```

### Get File Info
```
GET /api/files/info/{path}

Returns: {"path": "...", "exists": true, "size": 1234}
```

### Create Directory
```
POST /api/files/directory?path=new_dir

Returns: {"path": "new_dir", "created": true}
```

## Usage Examples

### Basic File Operations

```python
from storage import LocalFileStorage

# Initialize
storage = LocalFileStorage(root_path="data")

# Save a text file
await storage.save_file(
    "notes/meeting.txt",
    "Meeting notes...".encode('utf-8')
)

# Read it back
content = await storage.read_file("notes/meeting.txt")
print(content.decode('utf-8'))

# Check if exists
if await storage.exists("notes/meeting.txt"):
    print("File exists!")

# Get file info
size = await storage.get_file_size("notes/meeting.txt")
print(f"File size: {size} bytes")
```

### Directory Operations

```python
# Create directory structure
await storage.create_directory("projects/kbrain")

# Save multiple files
files = {
    "projects/kbrain/README.md": b"# KBrain",
    "projects/kbrain/setup.py": b"from setuptools import setup",
    "projects/kbrain/src/main.py": b"def main(): pass"
}

for path, content in files.items():
    await storage.save_file(path, content)

# List all files recursively
all_files = await storage.list_directory("projects", recursive=True)
print(f"Found {len(all_files)} files")

# List just one directory
kbrain_files = await storage.list_directory("projects/kbrain")
print(f"Files in kbrain: {kbrain_files}")
```

### Working with Binary Files

```python
# Save binary file
binary_data = bytes([0xFF, 0xD8, 0xFF, 0xE0])  # JPEG header
await storage.save_file("images/photo.jpg", binary_data)

# Read binary file
image_data = await storage.read_file("images/photo.jpg")
print(f"Image size: {len(image_data)} bytes")
```

### File Management

```python
# Copy file
await storage.copy_file(
    "docs/draft.md",
    "docs/final.md"
)

# Move file
await storage.move_file(
    "temp/data.json",
    "archives/data.json"
)

# Delete file
await storage.delete_file("temp/old_file.txt")

# Delete directory recursively
await storage.delete_directory("temp", recursive=True)
```

### Using Different Paths

```python
from pathlib import Path

# All these work
await storage.save_file("file.txt", b"data")
await storage.save_file("dir/file.txt", b"data")
await storage.save_file(Path("dir/file.txt"), b"data")
await storage.save_file(Path("dir") / "file.txt", b"data")
```

## Security

### Path Traversal Protection

LocalFileStorage prevents path traversal attacks:

```python
# These will raise ValueError
await storage.save_file("../outside.txt", b"data")  # ❌
await storage.save_file("/etc/passwd", b"data")      # ❌
await storage.save_file("../../etc/passwd", b"data") # ❌

# These are OK
await storage.save_file("docs/file.txt", b"data")    # ✅
await storage.save_file("a/b/c/file.txt", b"data")   # ✅
```

All paths are resolved and checked to ensure they stay within the storage root.

## Testing

Run the test suite:

```bash
cd kbrain-backend
python test_storage.py
```

Tests cover:
- Basic file operations (save, read, delete)
- Directory operations (create, list, delete)
- File management (copy, move)
- Path handling edge cases
- Binary and text files
- Security (path traversal prevention)
- Overwrite protection

## Extending with New Backends

To add a new storage backend:

1. Create a new file in `storage/` (e.g., `dropbox.py`)
2. Import `BaseFileStorage` from `base.py`
3. Implement all abstract methods
4. Add to `__init__.py` exports
5. Update `main.py` to initialize your backend

Example:

```python
from .base import BaseFileStorage

class DropboxStorage(BaseFileStorage):
    async def save_file(self, path, content, overwrite=True):
        # Implementation
        pass

    # Implement other methods...
```

## Performance Notes

### LocalFileStorage
- **Latency**: ~1-10ms per operation
- **Throughput**: High (limited by disk I/O)
- **Scalability**: Single machine
- **Best for**: Development, small deployments

### S3 / Azure (When Implemented)
- **Latency**: ~50-200ms per operation
- **Throughput**: Very high (distributed)
- **Scalability**: Unlimited
- **Best for**: Production, distributed systems

## Troubleshooting

### Permission Errors
```python
# Ensure kbrain_storage root is writable
storage = LocalFileStorage(root_path="/tmp/kbrain_storage")
```

### Path Not Found
```python
# Check if parent directory exists
await storage.create_directory("parent/child")
```

### File Too Large
```python
# For large files, consider streaming
# (feature to be added)
```

## Future Enhancements

- [ ] Implement AWS S3 backend
- [ ] Implement Azure Blob backend
- [ ] Add streaming for large files
- [ ] Add file metadata (timestamps, tags)
- [ ] Add compression support
- [ ] Add encryption support
- [ ] Add caching layer
- [ ] Add access control/permissions
- [ ] Add versioning support
- [ ] Add webhook notifications

## License

Part of the KBrain project.
