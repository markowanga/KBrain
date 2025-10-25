"""KBrain Backend API - Main application entry point."""

import os
from contextlib import asynccontextmanager
from typing import Optional, AsyncIterator, Any, Dict

from fastapi import FastAPI, HTTPException, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
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
app.include_router(
    documents.router, prefix="/api"
)  # Documents have full paths with /api/v1
app.include_router(tags.router, prefix="/api/v1")  # Tags routes
app.include_router(tags.documents_router, prefix="/api")  # Document tags routes
app.include_router(statistics.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api")  # Health endpoints under /api


# if __name__ == "__main__":
#     uvicorn.run(
#         app,
#         host=settings.host,
#         port=settings.port,
#         log_level=settings.log_level.lower(),
#     )
