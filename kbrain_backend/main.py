import os
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import uvicorn

from storage import BaseFileStorage, LocalFileStorage

# Storage configuration (can be set via environment variable)
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")  # "local", "s3", or "azure"
STORAGE_ROOT = os.getenv("STORAGE_ROOT", "storage_data")

app = FastAPI(title="KBrain API")

# Initialize storage backend
storage: BaseFileStorage

if STORAGE_BACKEND == "local":
    storage = LocalFileStorage(root_path=STORAGE_ROOT)
    print(f"Using local file storage in '{STORAGE_ROOT}' directory")
elif STORAGE_BACKEND == "s3":
    # TODO: Implement S3 initialization
    raise NotImplementedError("S3 storage not yet implemented")
elif STORAGE_BACKEND == "azure":
    # TODO: Implement Azure initialization
    raise NotImplementedError("Azure Blob storage not yet implemented")
else:
    raise ValueError(f"Unknown storage backend: {STORAGE_BACKEND}")

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API requests
class SaveFileRequest(BaseModel):
    path: str
    content: str  # Base64 encoded or plain text
    overwrite: bool = True


# Basic endpoints
@app.get("/")
async def root():
    return {"message": "Hello World from KBrain API!"}


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "kbrain-backend",
        "storage_backend": STORAGE_BACKEND,
        "storage_root": STORAGE_ROOT
    }


# File Storage API endpoints
@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    path: Optional[str] = None
):
    """
    Upload a file to storage.

    Args:
        file: The file to upload
        path: Optional custom path (defaults to original filename)
    """
    try:
        # Use provided path or original filename
        file_path = path if path else file.filename

        # Read file content
        content = await file.read()

        # Save to storage
        success = await storage.save_file(file_path, content)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to save file")

        return {
            "success": True,
            "path": file_path,
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/files/download/{path:path}")
async def download_file(path: str):
    """
    Download a file from storage.

    Args:
        path: File path in storage
    """
    content = await storage.read_file(path)

    if content is None:
        raise HTTPException(status_code=404, detail=f"File '{path}' not found")

    # Determine content type based on extension
    import mimetypes
    content_type, _ = mimetypes.guess_type(path)
    content_type = content_type or "application/octet-stream"

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={path.split('/')[-1]}"}
    )


@app.get("/api/files/read/{path:path}")
async def read_file(path: str):
    """
    Read a file from storage and return as JSON.

    Args:
        path: File path in storage
    """
    content = await storage.read_file(path)

    if content is None:
        raise HTTPException(status_code=404, detail=f"File '{path}' not found")

    # Try to decode as text
    try:
        text_content = content.decode('utf-8')
        return {
            "path": path,
            "content": text_content,
            "size": len(content),
            "type": "text"
        }
    except UnicodeDecodeError:
        # Return base64 for binary files
        import base64
        return {
            "path": path,
            "content": base64.b64encode(content).decode('ascii'),
            "size": len(content),
            "type": "binary"
        }


@app.get("/api/files/exists/{path:path}")
async def check_file_exists(path: str):
    """
    Check if a file exists.

    Args:
        path: File path in storage
    """
    exists = await storage.exists(path)
    return {"path": path, "exists": exists}


@app.get("/api/files/list")
async def list_files(
    path: str = "",
    recursive: bool = False
):
    """
    List files in directory.

    Args:
        path: Directory path (empty for root)
        recursive: Whether to list recursively
    """
    files = await storage.list_directory(path, recursive)
    return {
        "path": path,
        "files": files,
        "count": len(files)
    }


@app.delete("/api/files/delete/{path:path}")
async def delete_file(path: str):
    """
    Delete a file from storage.

    Args:
        path: File path in storage
    """
    success = await storage.delete_file(path)

    if not success:
        raise HTTPException(status_code=404, detail=f"File '{path}' not found")

    return {"path": path, "deleted": True}


@app.get("/api/files/info/{path:path}")
async def get_file_info(path: str):
    """
    Get file information.

    Args:
        path: File path in storage
    """
    exists = await storage.exists(path)

    if not exists:
        raise HTTPException(status_code=404, detail=f"File '{path}' not found")

    size = await storage.get_file_size(path)

    return {
        "path": path,
        "exists": exists,
        "size": size
    }


@app.post("/api/files/directory")
async def create_directory(path: str):
    """
    Create a directory.

    Args:
        path: Directory path
    """
    success = await storage.create_directory(path)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to create directory")

    return {"path": path, "created": True}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
