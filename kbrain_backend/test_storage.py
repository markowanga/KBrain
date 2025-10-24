"""
Test script for file storage implementations.
Run with: python test_storage.py
"""

import asyncio
from pathlib import Path
from storage import LocalFileStorage


async def test_local_storage():
    """Test local file storage."""
    print("\n=== Testing LocalFileStorage ===")

    # Initialize storage
    storage = LocalFileStorage(root_path="test_storage_data")
    print(f"Initialized storage at: {storage.root_path}")

    # Test 1: Save and read file
    print("\n--- Test 1: Save and read file ---")
    test_content = b"Hello, KBrain!"
    success = await storage.save_file("test.txt", test_content)
    print(f"Save file: {success}")

    content = await storage.read_file("test.txt")
    print(f"Read content: {content.decode('utf-8')}")
    assert content == test_content, "Content mismatch!"

    # Test 2: Check if file exists
    print("\n--- Test 2: Check file existence ---")
    exists = await storage.exists("test.txt")
    print(f"File exists: {exists}")
    assert exists, "File should exist!"

    not_exists = await storage.exists("nonexistent.txt")
    print(f"Nonexistent file: {not_exists}")
    assert not not_exists, "File should not exist!"

    # Test 3: Save file in subdirectory
    print("\n--- Test 3: Save file in subdirectory ---")
    success = await storage.save_file("docs/readme.md", b"# KBrain\n\nDocumentation")
    print(f"Save in subdirectory: {success}")

    content = await storage.read_file("docs/readme.md")
    print(f"Read from subdirectory: {content.decode('utf-8')[:20]}...")

    # Test 4: List directory
    print("\n--- Test 4: List directory ---")
    files = await storage.list_directory()
    print(f"Files in root: {files}")

    files_in_docs = await storage.list_directory("docs")
    print(f"Files in docs/: {files_in_docs}")

    # Test 5: List directory recursively
    print("\n--- Test 5: List directory recursively ---")
    await storage.save_file("docs/api/endpoints.md", b"# API Endpoints")
    await storage.save_file("docs/guides/getting-started.md", b"# Getting Started")

    all_files = await storage.list_directory(recursive=True)
    print(f"All files (recursive): {all_files}")

    # Test 6: Get file size
    print("\n--- Test 6: Get file size ---")
    size = await storage.get_file_size("test.txt")
    print(f"File size: {size} bytes")
    assert size == len(test_content), "Size mismatch!"

    # Test 7: Create directory
    print("\n--- Test 7: Create directory ---")
    success = await storage.create_directory("new_dir")
    print(f"Create directory: {success}")

    exists = await storage.exists("new_dir")
    print(f"Directory exists: {exists}")

    # Test 8: Copy file
    print("\n--- Test 8: Copy file ---")
    success = await storage.copy_file("test.txt", "test_copy.txt")
    print(f"Copy file: {success}")

    content = await storage.read_file("test_copy.txt")
    print(f"Copied content: {content.decode('utf-8')}")
    assert content == test_content, "Copied content mismatch!"

    # Test 9: Move file
    print("\n--- Test 9: Move file ---")
    success = await storage.move_file("test_copy.txt", "moved.txt")
    print(f"Move file: {success}")

    exists_old = await storage.exists("test_copy.txt")
    exists_new = await storage.exists("moved.txt")
    print(f"Old location exists: {exists_old}, New location exists: {exists_new}")
    assert not exists_old and exists_new, "Move failed!"

    # Test 10: Delete file
    print("\n--- Test 10: Delete file ---")
    success = await storage.delete_file("moved.txt")
    print(f"Delete file: {success}")

    exists = await storage.exists("moved.txt")
    print(f"File exists after delete: {exists}")
    assert not exists, "File should be deleted!"

    # Test 11: Overwrite protection
    print("\n--- Test 11: Overwrite protection ---")
    success = await storage.save_file("protected.txt", b"Original", overwrite=False)
    print(f"Save new file: {success}")

    success = await storage.save_file("protected.txt", b"Modified", overwrite=False)
    print(f"Attempt overwrite (should fail): {success}")
    assert not success, "Should not overwrite!"

    content = await storage.read_file("protected.txt")
    print(f"Content unchanged: {content.decode('utf-8')}")
    assert content == b"Original", "Content should be unchanged!"

    # Test 12: Path traversal protection
    print("\n--- Test 12: Path traversal protection ---")
    try:
        await storage.save_file("../outside.txt", b"Bad")
        print("ERROR: Path traversal not prevented!")
    except ValueError as e:
        print(f"Path traversal prevented: {e}")

    # Test 13: Delete directory
    print("\n--- Test 13: Delete directory ---")
    success = await storage.delete_directory("docs", recursive=True)
    print(f"Delete directory: {success}")

    # Cleanup
    print("\n--- Cleanup ---")
    await storage.delete_directory("", recursive=True)
    print("Test cleanup completed")

    print("\n✓ All LocalFileStorage tests passed!")


async def test_path_handling():
    """Test path handling edge cases."""
    print("\n=== Testing Path Handling ===")

    storage = LocalFileStorage(root_path="test_path_data")

    # Test different path formats
    print("\n--- Test path formats ---")
    paths = [
        "simple.txt",
        "dir/file.txt",
        "deep/nested/path/file.txt",
        Path("pathlib.txt"),
        Path("dir") / "pathlib.txt"
    ]

    for path in paths:
        await storage.save_file(path, b"test")
        exists = await storage.exists(path)
        print(f"  {path}: {exists}")
        assert exists, f"Path {path} failed!"

    # List all
    all_files = await storage.list_directory(recursive=True)
    print(f"\nAll files created: {all_files}")

    # Cleanup
    await storage.delete_directory("", recursive=True)

    print("\n✓ Path handling tests passed!")


async def test_binary_and_text():
    """Test binary and text file handling."""
    print("\n=== Testing Binary and Text Files ===")

    storage = LocalFileStorage(root_path="test_binary_data")

    # Text file
    print("\n--- Text file ---")
    text = "Hello, 世界! 🌍"
    await storage.save_file("text.txt", text.encode('utf-8'))
    content = await storage.read_file("text.txt")
    print(f"Text content: {content.decode('utf-8')}")
    assert content.decode('utf-8') == text

    # Binary file
    print("\n--- Binary file ---")
    binary = bytes([0, 1, 2, 255, 254, 253])
    await storage.save_file("binary.bin", binary)
    content = await storage.read_file("binary.bin")
    print(f"Binary content: {content.hex()}")
    assert content == binary

    # Cleanup
    await storage.delete_directory("", recursive=True)

    print("\n✓ Binary and text tests passed!")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("KBrain File Storage Test Suite")
    print("=" * 60)

    await test_local_storage()
    await test_path_handling()
    await test_binary_and_text()

    print("\n" + "=" * 60)
    print("All tests completed successfully! ✓")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
