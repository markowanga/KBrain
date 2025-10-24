"""
Local filesystem storage implementation.
Uses pathlib for cross-platform file operations.
"""

import asyncio
from pathlib import Path
from typing import List, Optional, Union
import aiofiles
import aiofiles.os

from .base import BaseFileStorage


class LocalFileStorage(BaseFileStorage):
    """
    Local filesystem storage implementation.
    Stores files in a local directory using pathlib.
    """

    def __init__(self, root_path: Union[str, Path] = "storage_data"):
        """
        Initialize local file storage.

        Args:
            root_path: Root directory for file storage
        """
        self.root_path = Path(root_path).resolve()
        self._lock = asyncio.Lock()

        # Create root directory if it doesn't exist
        self.root_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, path: Union[str, Path]) -> Path:
        """
        Resolve path relative to root and ensure it's within root.

        Args:
            path: Relative path

        Returns:
            Absolute path within storage root

        Raises:
            ValueError: If path tries to escape root directory
        """
        # Convert to Path and resolve
        rel_path = Path(path)

        # Prevent path traversal attacks
        if rel_path.is_absolute():
            raise ValueError("Path must be relative to storage root")

        full_path = (self.root_path / rel_path).resolve()

        # Ensure path is within root
        try:
            full_path.relative_to(self.root_path)
        except ValueError:
            raise ValueError(f"Path {path} is outside storage root")

        return full_path

    async def save_file(
        self,
        path: Union[str, Path],
        content: bytes,
        overwrite: bool = True
    ) -> bool:
        """
        Save file to local filesystem.

        Args:
            path: File path (relative to root)
            content: File content as bytes
            overwrite: Whether to overwrite existing file

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If path is invalid or outside storage root
        """
        # This will raise ValueError if path is invalid
        full_path = self._resolve_path(path)

        try:
            # Check if file exists and overwrite is False
            if not overwrite and full_path.exists():
                return False

            # Create parent directories
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file asynchronously
            async with aiofiles.open(full_path, 'wb') as f:
                await f.write(content)

            return True
        except Exception as e:
            print(f"Error saving file {path}: {e}")
            return False

    async def read_file(self, path: Union[str, Path]) -> Optional[bytes]:
        """
        Read file from local filesystem.

        Args:
            path: File path (relative to root)

        Returns:
            File content as bytes, or None if not found
        """
        try:
            full_path = self._resolve_path(path)

            if not full_path.exists() or not full_path.is_file():
                return None

            async with aiofiles.open(full_path, 'rb') as f:
                return await f.read()
        except Exception as e:
            print(f"Error reading file {path}: {e}")
            return None

    async def exists(self, path: Union[str, Path]) -> bool:
        """
        Check if file or directory exists.

        Args:
            path: File or directory path

        Returns:
            True if exists, False otherwise
        """
        try:
            full_path = self._resolve_path(path)
            return full_path.exists()
        except Exception:
            return False

    async def list_directory(
        self,
        path: Union[str, Path] = "",
        recursive: bool = False
    ) -> List[str]:
        """
        List files in directory.

        Args:
            path: Directory path (empty string for root)
            recursive: Whether to list recursively

        Returns:
            List of file paths (relative to storage root)
        """
        try:
            if path == "":
                full_path = self.root_path
            else:
                full_path = self._resolve_path(path)

            if not full_path.exists() or not full_path.is_dir():
                return []

            files = []

            if recursive:
                # Recursive listing
                for item in full_path.rglob('*'):
                    if item.is_file():
                        # Get path relative to root
                        rel_path = item.relative_to(self.root_path)
                        files.append(str(rel_path))
            else:
                # Non-recursive listing
                for item in full_path.iterdir():
                    if item.is_file():
                        # Get path relative to root
                        rel_path = item.relative_to(self.root_path)
                        files.append(str(rel_path))

            return sorted(files)
        except Exception as e:
            print(f"Error listing directory {path}: {e}")
            return []

    async def delete_file(self, path: Union[str, Path]) -> bool:
        """
        Delete file from local filesystem.

        Args:
            path: File path

        Returns:
            True if deleted, False if not found
        """
        try:
            full_path = self._resolve_path(path)

            if not full_path.exists() or not full_path.is_file():
                return False

            await aiofiles.os.remove(str(full_path))
            return True
        except Exception as e:
            print(f"Error deleting file {path}: {e}")
            return False

    async def get_file_size(self, path: Union[str, Path]) -> Optional[int]:
        """
        Get file size in bytes.

        Args:
            path: File path

        Returns:
            File size in bytes, or None if not found
        """
        try:
            full_path = self._resolve_path(path)

            if not full_path.exists() or not full_path.is_file():
                return None

            stat = await aiofiles.os.stat(str(full_path))
            return stat.st_size
        except Exception as e:
            print(f"Error getting file size {path}: {e}")
            return None

    async def create_directory(self, path: Union[str, Path]) -> bool:
        """
        Create directory in local filesystem.

        Args:
            path: Directory path

        Returns:
            True if successful
        """
        try:
            full_path = self._resolve_path(path)
            full_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory {path}: {e}")
            return False

    async def delete_directory(
        self,
        path: Union[str, Path],
        recursive: bool = False
    ) -> bool:
        """
        Delete directory from local filesystem.

        Args:
            path: Directory path
            recursive: Whether to delete recursively (with contents)

        Returns:
            True if deleted, False otherwise
        """
        try:
            full_path = self._resolve_path(path)

            if not full_path.exists() or not full_path.is_dir():
                return False

            if recursive:
                # Delete directory and all contents
                import shutil
                shutil.rmtree(full_path)
            else:
                # Delete only if empty
                full_path.rmdir()

            return True
        except Exception as e:
            print(f"Error deleting directory {path}: {e}")
            return False

    async def copy_file(
        self,
        source: Union[str, Path],
        destination: Union[str, Path]
    ) -> bool:
        """
        Copy file within storage.

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            True if successful
        """
        try:
            content = await self.read_file(source)
            if content is None:
                return False

            return await self.save_file(destination, content, overwrite=True)
        except Exception as e:
            print(f"Error copying file {source} to {destination}: {e}")
            return False

    async def move_file(
        self,
        source: Union[str, Path],
        destination: Union[str, Path]
    ) -> bool:
        """
        Move file within storage.

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            True if successful
        """
        try:
            if await self.copy_file(source, destination):
                return await self.delete_file(source)
            return False
        except Exception as e:
            print(f"Error moving file {source} to {destination}: {e}")
            return False
