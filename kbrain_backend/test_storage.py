"""
Simple test script for storage implementations.
Run with: python test_storage.py
"""

import asyncio
from storage import MemoryStorage, FileStorage


async def test_memory_storage():
    """Test in-memory storage."""
    print("\n=== Testing MemoryStorage ===")
    storage = MemoryStorage()

    # Test basic operations
    print("Setting key 'test' to 'hello'")
    await storage.set("test", "hello")

    print("Getting key 'test':", await storage.get("test"))
    print("Key exists:", await storage.exists("test"))
    print("Count:", await storage.count())

    # Test batch operations
    print("\nSetting multiple items...")
    await storage.set_many({
        "user:1": {"name": "Alice", "age": 30},
        "user:2": {"name": "Bob", "age": 25},
        "config:theme": "dark"
    })

    print("Total count:", await storage.count())
    print("Keys with 'user:' prefix:", await storage.list_keys("user:"))
    print("All keys:", await storage.list_keys())

    # Test get_all
    print("\nAll items:")
    all_items = await storage.get_all()
    for key, value in all_items.items():
        print(f"  {key}: {value}")

    # Test delete
    print("\nDeleting 'test' key")
    deleted = await storage.delete("test")
    print(f"Deleted: {deleted}")
    print("Count after delete:", await storage.count())

    # Test delete_many
    print("\nDeleting multiple keys")
    deleted_count = await storage.delete_many(["user:1", "user:2"])
    print(f"Deleted {deleted_count} keys")
    print("Final count:", await storage.count())

    # Clear all
    print("\nClearing all data")
    await storage.clear()
    print("Count after clear:", await storage.count())

    print("\n✓ MemoryStorage tests completed!")


async def test_file_storage():
    """Test file-based storage."""
    print("\n=== Testing FileStorage ===")
    storage = FileStorage(storage_dir="test_data")

    # Test basic operations
    print("Setting key 'test' to 'hello file'")
    await storage.set("test", "hello file")

    print("Getting key 'test':", await storage.get("test"))
    print("Key exists:", await storage.exists("test"))
    print("Count:", await storage.count())

    # Test batch operations
    print("\nSetting multiple items...")
    await storage.set_many({
        "user:1": {"name": "Charlie", "age": 35},
        "user:2": {"name": "Diana", "age": 28},
        "config:theme": "light",
        "config:lang": "pl"
    })

    print("Total count:", await storage.count())
    print("Keys with 'user:' prefix:", await storage.list_keys("user:"))
    print("Keys with 'config:' prefix:", await storage.list_keys("config:"))

    # Test persistence - create new instance
    print("\nTesting persistence...")
    storage2 = FileStorage(storage_dir="test_data")
    print("New instance count:", await storage2.count())
    print("Retrieved 'test' from new instance:", await storage2.get("test"))

    # Test backup
    print("\nCreating backup...")
    backup_success = await storage.backup("test_data/backup.json")
    print(f"Backup created: {backup_success}")

    # Clear and restore
    print("\nClearing storage...")
    await storage.clear()
    print("Count after clear:", await storage.count())

    print("Restoring from backup...")
    restore_success = await storage.restore("test_data/backup.json")
    print(f"Restore successful: {restore_success}")
    print("Count after restore:", await storage.count())

    # Final cleanup
    print("\nFinal cleanup...")
    await storage.clear()

    print("\n✓ FileStorage tests completed!")


async def test_polymorphism():
    """Test that both implementations work with BaseStorage interface."""
    print("\n=== Testing Polymorphism ===")

    async def test_storage_interface(storage, storage_name):
        print(f"\nTesting {storage_name}...")
        await storage.set("poly", "morphism")
        value = await storage.get("poly")
        print(f"  Retrieved value: {value}")
        await storage.clear()

    memory = MemoryStorage()
    file = FileStorage(storage_dir="test_data")

    await test_storage_interface(memory, "MemoryStorage")
    await test_storage_interface(file, "FileStorage")

    print("\n✓ Polymorphism test completed!")


async def main():
    """Run all tests."""
    print("KBrain Storage Test Suite")
    print("=" * 50)

    await test_memory_storage()
    await test_file_storage()
    await test_polymorphism()

    print("\n" + "=" * 50)
    print("All tests completed successfully! ✓")


if __name__ == "__main__":
    asyncio.run(main())
