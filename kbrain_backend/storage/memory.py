"""
In-memory storage implementation.
Fast, volatile storage using dictionary in RAM.
"""

import asyncio
from typing import Any, Dict, List, Optional
from .base import BaseStorage


class MemoryStorage(BaseStorage):
    """
    In-memory storage implementation using a dictionary.
    All data is stored in RAM and will be lost on restart.
    Thread-safe with async locks.
    """

    def __init__(self):
        """Initialize the in-memory storage."""
        self._storage: Dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value by key from memory.

        Args:
            key: The key to retrieve

        Returns:
            The stored value or None if not found
        """
        async with self._lock:
            return self._storage.get(key)

    async def set(self, key: str, value: Any) -> bool:
        """
        Store a value with a key in memory.

        Args:
            key: The key to store under
            value: The value to store

        Returns:
            True if successful
        """
        async with self._lock:
            self._storage[key] = value
            return True

    async def delete(self, key: str) -> bool:
        """
        Delete a value by key from memory.

        Args:
            key: The key to delete

        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            if key in self._storage:
                del self._storage[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in memory.

        Args:
            key: The key to check

        Returns:
            True if exists, False otherwise
        """
        async with self._lock:
            return key in self._storage

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """
        List all keys in memory, optionally filtered by prefix.

        Args:
            prefix: Optional prefix to filter keys

        Returns:
            List of matching keys
        """
        async with self._lock:
            if prefix is None:
                return list(self._storage.keys())
            return [key for key in self._storage.keys() if key.startswith(prefix)]

    async def clear(self) -> bool:
        """
        Clear all data from memory.

        Returns:
            True if successful
        """
        async with self._lock:
            self._storage.clear()
            return True

    async def get_all(self) -> Dict[str, Any]:
        """
        Get all key-value pairs from memory.

        Returns:
            Dictionary of all stored data
        """
        async with self._lock:
            return dict(self._storage)

    async def set_many(self, items: Dict[str, Any]) -> bool:
        """
        Store multiple key-value pairs at once in memory.

        Args:
            items: Dictionary of key-value pairs to store

        Returns:
            True if successful
        """
        async with self._lock:
            self._storage.update(items)
            return True

    async def delete_many(self, keys: List[str]) -> int:
        """
        Delete multiple keys at once from memory.

        Args:
            keys: List of keys to delete

        Returns:
            Number of keys actually deleted
        """
        async with self._lock:
            deleted_count = 0
            for key in keys:
                if key in self._storage:
                    del self._storage[key]
                    deleted_count += 1
            return deleted_count

    async def count(self) -> int:
        """
        Count total number of items in memory.

        Returns:
            Number of items in storage
        """
        async with self._lock:
            return len(self._storage)
