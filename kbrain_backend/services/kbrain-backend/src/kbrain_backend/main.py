"""KBrain Backend API - Main application entry point."""

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from kbrain_backend.config.settings import settings
from kbrain_backend.database.connection import init_db, close_db
from kbrain_backend.api.routes import (
    scopes,
    documents,
    statistics,
    health,
    tags,
    processing,
)
from kbrain_backend.api.routes.documents import set_storage
from kbrain_backend.api.routes.processing import set_orchestrator_worker_publisher
from kbrain_backend.utils.errors import (
    APIError,
    api_error_handler,
    validation_error_handler,
    general_exception_handler,
    database_error_handler,
)
from kbrain_backend.utils.logger import logger
from kbrain_processor_orchestrator.orchestrator import ProcessingOrchestrator
from kbrain_processor_orchestrator.publisher import QueuePublisher
from kbrain_processor_orchestrator.worker import ProcessingWorker
from kbrain_processor_orchestrator.processors import (
    DocumentProcessor,
    ImageProcessor,
    TextProcessor,
    XlsxMedicationProcessor,
)

# Storage backend initialization
from kbrain_storage import BaseFileStorage, LocalFileStorage

# Processing orchestrator

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

    # Initialize processing orchestrator, worker and publisher
    orchestrator = None
    worker = None
    publisher = None

    if settings.processing_enabled:
        try:
            logger.info("Initializing document processing orchestrator...")

            # Create orchestrator
            orchestrator = ProcessingOrchestrator(
                max_retries=settings.processing_max_retries
            )

            # Register document processors with settings
            orchestrator.register_processor(
                DocumentProcessor(
                    openai_api_key=settings.openai_api_key,
                    openai_base_url=settings.openai_base_url,
                    model=settings.openai_model,
                    ragflow_url=settings.ragflow_url,
                    ragflow_api_key=settings.ragflow_api_key,
                    ragflow_dataset_id=settings.ragflow_dataset_id,
                    ragflow_wait_for_parsing=settings.ragflow_wait_for_parsing,
                    ragflow_max_wait=settings.ragflow_max_wait,
                )
            )
            orchestrator.register_processor(
                ImageProcessor(
                    openai_api_key=settings.openai_api_key,
                    openai_base_url=settings.openai_base_url,
                    model=settings.openai_model,
                    ragflow_url=settings.ragflow_url,
                    ragflow_api_key=settings.ragflow_api_key,
                    ragflow_dataset_id=settings.ragflow_dataset_id,
                    ragflow_wait_for_parsing=settings.ragflow_wait_for_parsing,
                    ragflow_max_wait=settings.ragflow_max_wait,
                )
            )
            orchestrator.register_processor(
                TextProcessor(
                    ragflow_url=settings.ragflow_url,
                    ragflow_api_key=settings.ragflow_api_key,
                    ragflow_dataset_id=settings.ragflow_dataset_id,
                    ragflow_wait_for_parsing=settings.ragflow_wait_for_parsing,
                    ragflow_max_wait=settings.ragflow_max_wait,
                )
            )
            orchestrator.register_processor(
                XlsxMedicationProcessor(
                    service_url=settings.xlsx_medication_service_url,
                )
            )

            # Create publisher
            publisher = QueuePublisher(
                rabbitmq_url=settings.rabbitmq_url,
                queue_name=settings.rabbitmq_queue_name,
            )
            await publisher.connect()
            logger.info("RabbitMQ publisher connected")

            # Create worker
            api_base_url = f"http://{settings.host}:{settings.port}/api"
            worker = ProcessingWorker(
                orchestrator=orchestrator,
                rabbitmq_url=settings.rabbitmq_url,
                queue_name=settings.rabbitmq_queue_name,
                api_base_url=api_base_url,
                prefetch_count=settings.rabbitmq_prefetch_count,
                api_token=settings.processing_api_token,
            )

            # Set orchestrator, worker and publisher for routes
            set_orchestrator_worker_publisher(orchestrator, worker, publisher)

            # Start worker
            await worker.start()
            logger.info("RabbitMQ consumer worker started successfully")

        except Exception as e:
            logger.exception(f"Failed to initialize processing: {e}")
            # Don't fail app startup if processing fails
            logger.warning("Continuing without document processing enabled")

    yield

    # Shutdown
    logger.info("Shutting down KBrain API...")

    # Stop processing worker
    if worker and worker.is_running:
        logger.info("Stopping RabbitMQ consumer worker...")
        await worker.stop()
        logger.info("RabbitMQ consumer worker stopped")

    # Disconnect publisher
    if publisher:
        logger.info("Disconnecting RabbitMQ publisher...")
        await publisher.disconnect()
        logger.info("RabbitMQ publisher disconnected")

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
    allow_origins=["*"],
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
app.include_router(processing.router, prefix="/api")  # Processing endpoints

# if __name__ == "__main__":
#     uvicorn.run(
#         app,
#         host=settings.host,
#         port=settings.port,
#         log_level=settings.log_level.lower(),
#     )
