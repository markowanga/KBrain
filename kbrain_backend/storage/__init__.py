"""
File storage module for KBrain backend.
Provides unified interface for different storage backends: Local, AWS S3, Azure Blob.
"""

from .base import BaseFileStorage
from .local import LocalFileStorage

__all__ = ["BaseFileStorage", "LocalFileStorage"]
