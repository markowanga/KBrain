"""
File-based storage implementation.
Persistent storage using JSON files on disk.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiofiles
from .base import BaseStorage


class FileStorage(BaseStorage):
    """
    File-based storage implementation using JSON files.
    Data is persisted to disk and survives restarts.
    Thread-safe with async locks and async file I/O.
    """

    def __init__(self, storage_dir: str = "data"):
        """
        Initialize the file-based storage.

        Args:
            storage_dir: Directory path where storage files will be kept
        """
        self.storage_dir = Path(storage_dir)
        self.storage_file = self.storage_dir / "storage.json"
        self._lock = asyncio.Lock()
        self._cache: Optional[Dict[str, Any]] = None

        # Ensure storage directory exists
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def _load_data(self) -> Dict[str, Any]:
        """
        Load data from disk into cache.

        Returns:
            Dictionary of all stored data
        """
        if not self.storage_file.exists():
            return {}

        try:
            async with aiofiles.open(self.storage_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content) if content else {}
        except (json.JSONDecodeError, IOError):
            return {}

    async def _save_data(self, data: Dict[str, Any]) -> bool:
        """
        Save data from cache to disk.

        Args:
            data: Dictionary to save

        Returns:
            True if successful
        """
        try:
            async with aiofiles.open(self.storage_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
            return True
        except IOError:
            return False

    async def _ensure_loaded(self):
        """Ensure data is loaded into cache."""
        if self._cache is None:
            self._cache = await self._load_data()

    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value by key from disk.

        Args:
            key: The key to retrieve

        Returns:
            The stored value or None if not found
        """
        async with self._lock:
            await self._ensure_loaded()
            return self._cache.get(key)

    async def set(self, key: str, value: Any) -> bool:
        """
        Store a value with a key on disk.

        Args:
            key: The key to store under
            value: The value to store (must be JSON serializable)

        Returns:
            True if successful, False otherwise
        """
        async with self._lock:
            await self._ensure_loaded()
            self._cache[key] = value
            return await self._save_data(self._cache)

    async def delete(self, key: str) -> bool:
        """
        Delete a value by key from disk.

        Args:
            key: The key to delete

        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            await self._ensure_loaded()
            if key in self._cache:
                del self._cache[key]
                await self._save_data(self._cache)
                return True
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists on disk.

        Args:
            key: The key to check

        Returns:
            True if exists, False otherwise
        """
        async with self._lock:
            await self._ensure_loaded()
            return key in self._cache

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """
        List all keys from disk, optionally filtered by prefix.

        Args:
            prefix: Optional prefix to filter keys

        Returns:
            List of matching keys
        """
        async with self._lock:
            await self._ensure_loaded()
            if prefix is None:
                return list(self._cache.keys())
            return [key for key in self._cache.keys() if key.startswith(prefix)]

    async def clear(self) -> bool:
        """
        Clear all data from disk.

        Returns:
            True if successful
        """
        async with self._lock:
            self._cache = {}
            return await self._save_data(self._cache)

    async def get_all(self) -> Dict[str, Any]:
        """
        Get all key-value pairs from disk.

        Returns:
            Dictionary of all stored data
        """
        async with self._lock:
            await self._ensure_loaded()
            return dict(self._cache)

    async def set_many(self, items: Dict[str, Any]) -> bool:
        """
        Store multiple key-value pairs at once on disk.

        Args:
            items: Dictionary of key-value pairs to store

        Returns:
            True if successful
        """
        async with self._lock:
            await self._ensure_loaded()
            self._cache.update(items)
            return await self._save_data(self._cache)

    async def delete_many(self, keys: List[str]) -> int:
        """
        Delete multiple keys at once from disk.

        Args:
            keys: List of keys to delete

        Returns:
            Number of keys actually deleted
        """
        async with self._lock:
            await self._ensure_loaded()
            deleted_count = 0
            for key in keys:
                if key in self._cache:
                    del self._cache[key]
                    deleted_count += 1
            if deleted_count > 0:
                await self._save_data(self._cache)
            return deleted_count

    async def count(self) -> int:
        """
        Count total number of items on disk.

        Returns:
            Number of items in storage
        """
        async with self._lock:
            await self._ensure_loaded()
            return len(self._cache)

    async def backup(self, backup_path: Optional[str] = None) -> bool:
        """
        Create a backup of the storage file.

        Args:
            backup_path: Optional path for backup file

        Returns:
            True if successful
        """
        async with self._lock:
            await self._ensure_loaded()
            if backup_path is None:
                backup_path = f"{self.storage_file}.backup"

            try:
                async with aiofiles.open(backup_path, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(self._cache, indent=2, ensure_ascii=False))
                return True
            except IOError:
                return False

    async def restore(self, backup_path: str) -> bool:
        """
        Restore storage from a backup file.

        Args:
            backup_path: Path to backup file

        Returns:
            True if successful
        """
        async with self._lock:
            try:
                async with aiofiles.open(backup_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    self._cache = json.loads(content)
                return await self._save_data(self._cache)
            except (json.JSONDecodeError, IOError):
                return False
