"""
Abstract base class for file kbrain_storage implementations.
Supports Local filesystem, AWS S3, and Azure Blob Storage.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union


class BaseFileStorage(ABC):
    """
    Abstract base class for file kbrain_storage backends.
    Provides a consistent async interface for different kbrain_storage implementations.
    """

    @abstractmethod
    async def save_file(
        self, path: Union[str, Path], content: bytes, overwrite: bool = True
    ) -> bool:
        """
        Save file to kbrain_storage.

        Args:
            path: File path (relative to kbrain_storage root)
            content: File content as bytes
            overwrite: Whether to overwrite existing file

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def read_file(self, path: Union[str, Path]) -> Optional[bytes]:
        """
        Read file from kbrain_storage.

        Args:
            path: File path (relative to kbrain_storage root)

        Returns:
            File content as bytes, or None if not found
        """
        pass

    @abstractmethod
    async def exists(self, path: Union[str, Path]) -> bool:
        """
        Check if file or directory exists.

        Args:
            path: File or directory path

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    async def list_directory(
        self, path: Union[str, Path] = "", recursive: bool = False
    ) -> List[str]:
        """
        List files in directory.

        Args:
            path: Directory path (empty string for root)
            recursive: Whether to list recursively

        Returns:
            List of file paths (relative to kbrain_storage root)
        """
        pass

    @abstractmethod
    async def delete_file(self, path: Union[str, Path]) -> bool:
        """
        Delete file from kbrain_storage.

        Args:
            path: File path

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def get_file_size(self, path: Union[str, Path]) -> Optional[int]:
        """
        Get file size in bytes.

        Args:
            path: File path

        Returns:
            File size in bytes, or None if not found
        """
        pass

    @abstractmethod
    async def create_directory(self, path: Union[str, Path]) -> bool:
        """
        Create directory (if backend supports it).

        Args:
            path: Directory path

        Returns:
            True if successful
        """
        pass
