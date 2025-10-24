"""
Abstract base class for storage implementations.
All methods are asynchronous for consistent API.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseStorage(ABC):
    """
    Abstract base class for storage backends.
    Provides a consistent async interface for different storage implementations.
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value by key.

        Args:
            key: The key to retrieve

        Returns:
            The stored value or None if not found
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any) -> bool:
        """
        Store a value with a key.

        Args:
            key: The key to store under
            value: The value to store

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a value by key.

        Args:
            key: The key to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists.

        Args:
            key: The key to check

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """
        List all keys, optionally filtered by prefix.

        Args:
            prefix: Optional prefix to filter keys

        Returns:
            List of matching keys
        """
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """
        Clear all stored data.

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def get_all(self) -> Dict[str, Any]:
        """
        Get all key-value pairs.

        Returns:
            Dictionary of all stored data
        """
        pass

    @abstractmethod
    async def set_many(self, items: Dict[str, Any]) -> bool:
        """
        Store multiple key-value pairs at once.

        Args:
            items: Dictionary of key-value pairs to store

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def delete_many(self, keys: List[str]) -> int:
        """
        Delete multiple keys at once.

        Args:
            keys: List of keys to delete

        Returns:
            Number of keys actually deleted
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """
        Count total number of stored items.

        Returns:
            Number of items in storage
        """
        pass
