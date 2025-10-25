"""KBrain Backend API - Main application entry point."""

import os
from contextlib import asynccontextmanager
from typing import Optional, AsyncIterator, Any, Dict

from fastapi import FastAPI, HTTPException, UploadFile, File, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from kbrain_backend.config.settings import settings
from kbrain_backend.database.connection import init_db, close_db
from kbrain_backend.api.routes import scopes, documents, statistics, health, tags
from kbrain_backend.api.routes.documents import set_storage
from kbrain_backend.utils.errors import (
    APIError,
    api_error_handler,
    validation_error_handler,
    general_exception_handler,
    database_error_handler,
)
from kbrain_backend.utils.logger import logger

# Storage backend initialization
from kbrain_storage import BaseFileStorage, LocalFileStorage

# Storage configuration
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", settings.storage_backend)
STORAGE_ROOT = os.getenv("STORAGE_ROOT", settings.storage_root)

# Initialize storage backend
storage: BaseFileStorage

if STORAGE_BACKEND == "local":
    storage = LocalFileStorage(root_path=STORAGE_ROOT)
    logger.info(f"Using local file storage in '{STORAGE_ROOT}' directory")
elif STORAGE_BACKEND == "s3":
    # TODO: Implement S3 initialization
    raise NotImplementedError("S3 storage not yet implemented")
elif STORAGE_BACKEND == "azure":
    # TODO: Implement Azure initialization
    raise NotImplementedError("Azure Blob storage not yet implemented")
else:
    raise ValueError(f"Unknown storage backend: {STORAGE_BACKEND}")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting KBrain API...")
    logger.info(f"Database URL: {settings.database_url}")
    logger.info(f"Storage Backend: {STORAGE_BACKEND}")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.exception(f"Failed to initialize database: {e}")
        raise

    # Set storage for document routes
    set_storage(storage)

    yield

    # Shutdown
    logger.info("Shutting down KBrain API...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Knowledge Management System with Flexible Document Processing",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/v1/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handlers
app.add_exception_handler(APIError, api_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(SQLAlchemyError, database_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, general_exception_handler)

# Register routers with /api prefix (required by nginx routing)
app.include_router(scopes.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api")  # Documents have full paths with /api/v1
app.include_router(tags.router, prefix="/api/v1")  # Tags routes
app.include_router(tags.documents_router, prefix="/api")  # Document tags routes
app.include_router(statistics.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api")  # Health endpoints under /api


# Root endpoint
@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Welcome to KBrain API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/api/health")
async def legacy_health() -> Dict[str, str]:
    """Legacy health check endpoint (for backward compatibility)."""
    return {
        "status": "healthy",
        "service": "kbrain-backend",
        "storage_backend": STORAGE_BACKEND,
        "storage_root": STORAGE_ROOT,
    }


# Legacy file storage endpoints (for backward compatibility)
@app.post("/api/files/upload")
async def legacy_upload_file(file: UploadFile = File(...), path: Optional[str] = None) -> Dict[str, Any]:
    """
    Legacy file upload endpoint (for backward compatibility).
    Use /v1/scopes/{scope_id}/documents for new implementations.
    """
    try:
        # Use provided path or original filename
        file_path = path if path else file.filename
        if not file_path:
            raise HTTPException(status_code=400, detail="No file path or filename provided")

        # Read file content
        content = await file.read()

        # Save to kbrain_storage
        success = await storage.save_file(file_path, content)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to save file")

        return {"success": True, "path": file_path, "size": len(content)}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in legacy file upload endpoint: {file_path}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/files/download/{path:path}")
async def legacy_download_file(path: str) -> Response:
    """
    Legacy file download endpoint (for backward compatibility).
    Use /v1/documents/{document_id}/content for new implementations.
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
        headers={"Content-Disposition": f"attachment; filename={path.split('/')[-1]}"},
    )


@app.get("/api/files/read/{path:path}")
async def read_file(path: str) -> Dict[str, Any]:
    """
    Read a file from kbrain_storage and return as JSON.

    Args:
        path: File path in kbrain_storage
    """
    content = await storage.read_file(path)

    if content is None:
        raise HTTPException(status_code=404, detail=f"File '{path}' not found")

    # Try to decode as text
    try:
        text_content = content.decode("utf-8")
        return {
            "path": path,
            "content": text_content,
            "size": len(content),
            "type": "text",
        }
    except UnicodeDecodeError:
        # Return base64 for binary files
        import base64

        return {
            "path": path,
            "content": base64.b64encode(content).decode("ascii"),
            "size": len(content),
            "type": "binary",
        }


@app.get("/api/files/exists/{path:path}")
async def check_file_exists(path: str) -> Dict[str, Any]:
    """
    Check if a file exists.

    Args:
        path: File path in kbrain_storage
    """
    exists = await storage.exists(path)
    return {"path": path, "exists": exists}


@app.get("/api/files/list")
async def legacy_list_files(path: str = "", recursive: bool = False) -> Dict[str, Any]:
    """
    Legacy file list endpoint (for backward compatibility).
    Use /v1/scopes/{scope_id}/documents for new implementations.
    """
    files = await storage.list_directory(path, recursive)
    return {"path": path, "files": files, "count": len(files)}


@app.delete("/api/files/delete/{path:path}")
async def legacy_delete_file(path: str) -> Dict[str, Any]:
    """
    Legacy file delete endpoint (for backward compatibility).
    Use /v1/documents/{document_id} for new implementations.
    """
    success = await storage.delete_file(path)

    if not success:
        raise HTTPException(status_code=404, detail=f"File '{path}' not found")

    return {"path": path, "deleted": True}


@app.get("/api/files/info/{path:path}")
async def get_file_info(path: str) -> Dict[str, Any]:
    """
    Get file information.

    Args:
        path: File path in kbrain_storage
    """
    exists = await storage.exists(path)

    if not exists:
        raise HTTPException(status_code=404, detail=f"File '{path}' not found")

    size = await storage.get_file_size(path)

    return {"path": path, "exists": exists, "size": size}


@app.post("/api/files/directory")
async def create_directory(path: str) -> Dict[str, Any]:
    """
    Create a directory.

    Args:
        path: Directory path
    """
    success = await storage.create_directory(path)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to create directory")

    return {"path": path, "created": True}


# if __name__ == "__main__":
#     uvicorn.run(
#         app,
#         host=settings.host,
#         port=settings.port,
#         log_level=settings.log_level.lower(),
#     )
