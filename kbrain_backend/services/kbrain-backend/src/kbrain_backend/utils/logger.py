"""Logging configuration."""
import sys
from loguru import logger
from kbrain_backend.config.settings import settings

# Remove default handler
logger.remove()

# Add custom handler with format and level
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level.upper(),
    colorize=True,
)

# Export logger for use in other modules
__all__ = ["logger"]
