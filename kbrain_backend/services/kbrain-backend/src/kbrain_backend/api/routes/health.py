"""Health check and version API routes."""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kbrain_backend.api.schemas import HealthResponse, VersionResponse, ServiceStatus
from kbrain_backend.config.settings import settings
from kbrain_backend.database.connection import get_db
from kbrain_backend.utils.logger import logger

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db),
):
    """Check API health status."""

    # Check database
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        db_status = "unhealthy"

    # Check storage (simplified)
    storage_status = "healthy"

    # Check queue (simplified)
    queue_status = "healthy"

    overall_status = (
        "healthy"
        if all(
            [
                db_status == "healthy",
                storage_status == "healthy",
                queue_status == "healthy",
            ]
        )
        else "unhealthy"
    )

    services = ServiceStatus(
        database=db_status,
        storage=storage_status,
        queue=queue_status,
    )

    response = HealthResponse(
        status=overall_status,
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        services=services,
    )

    return response


@router.get("/version", response_model=VersionResponse)
async def version_info():
    """Get API version information."""

    return VersionResponse(
        api_version=settings.app_version,
        build="2024.10.24.1",
        commit="dev",  # Would come from git in production
        timestamp=datetime.utcnow(),
    )
