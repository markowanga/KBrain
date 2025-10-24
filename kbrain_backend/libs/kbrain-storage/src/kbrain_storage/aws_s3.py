"""
AWS S3 kbrain_storage implementation.
Requires: boto3, aioboto3
"""

from pathlib import Path
from typing import List, Optional, Union

from kbrain_storage.base import BaseFileStorage


class S3FileStorage(BaseFileStorage):
    """
    AWS S3 kbrain_storage implementation.

    Configuration:
        - AWS_ACCESS_KEY_ID: AWS access key
        - AWS_SECRET_ACCESS_KEY: AWS secret key
        - AWS_REGION: AWS region (e.g., 'us-east-1')
        - S3_BUCKET_NAME: S3 bucket name

    Installation:
        pip install aioboto3

    Example:
        kbrain_storage = S3FileStorage(
            bucket_name="my-bucket",
            region="us-east-1"
        )
    """

    def __init__(self, bucket_name: str, region: str = "us-east-1", prefix: str = ""):
        """
        Initialize S3 kbrain_storage.

        Args:
            bucket_name: S3 bucket name
            region: AWS region
            prefix: Optional prefix for all keys (acts as root directory)
        """
        self.bucket_name = bucket_name
        self.region = region
        self.prefix = prefix.strip("/")

        # TODO: Initialize aioboto3 session
        # import aioboto3
        # self.session = aioboto3.Session()
        raise NotImplementedError(
            "S3FileStorage is not yet implemented. "
            "Install 'aioboto3' and implement the methods."
        )

    def _get_key(self, path: Union[str, Path]) -> str:
        """
        Convert path to S3 key with prefix.

        Args:
            path: File path

        Returns:
            Full S3 key
        """
        path_str = str(Path(path)).replace("\\", "/")
        if self.prefix:
            return f"{self.prefix}/{path_str}"
        return path_str

    async def save_file(
        self, path: Union[str, Path], content: bytes, overwrite: bool = True
    ) -> bool:
        """
        Save file to S3.

        Implementation notes:
            - Use aioboto3 client.put_object()
            - Set Content-Type based on file extension
            - Handle overwrite by checking if key exists first
        """
        raise NotImplementedError("S3FileStorage.save_file not implemented")

    async def read_file(self, path: Union[str, Path]) -> Optional[bytes]:
        """
        Read file from S3.

        Implementation notes:
            - Use aioboto3 client.get_object()
            - Stream the response body
            - Return None if key doesn't exist
        """
        raise NotImplementedError("S3FileStorage.read_file not implemented")

    async def exists(self, path: Union[str, Path]) -> bool:
        """
        Check if file exists in S3.

        Implementation notes:
            - Use aioboto3 client.head_object()
            - Catch NoSuchKey exception
        """
        raise NotImplementedError("S3FileStorage.exists not implemented")

    async def list_directory(
        self, path: Union[str, Path] = "", recursive: bool = False
    ) -> List[str]:
        """
        List files in S3 directory.

        Implementation notes:
            - Use aioboto3 client.list_objects_v2()
            - Use Prefix parameter for directory
            - Use Delimiter='/' for non-recursive listing
            - Filter out directory markers (keys ending with /)
        """
        raise NotImplementedError("S3FileStorage.list_directory not implemented")

    async def delete_file(self, path: Union[str, Path]) -> bool:
        """
        Delete file from S3.

        Implementation notes:
            - Use aioboto3 client.delete_object()
            - S3 delete always returns success even if key doesn't exist
            - Check if key existed before deletion
        """
        raise NotImplementedError("S3FileStorage.delete_file not implemented")

    async def get_file_size(self, path: Union[str, Path]) -> Optional[int]:
        """
        Get file size in S3.

        Implementation notes:
            - Use aioboto3 client.head_object()
            - Extract ContentLength from response
        """
        raise NotImplementedError("S3FileStorage.get_file_size not implemented")

    async def create_directory(self, path: Union[str, Path]) -> bool:
        """
        Create directory in S3.

        Implementation notes:
            - S3 doesn't have real directories
            - Optionally create a zero-byte object with key ending in /
            - Or just return True (directories are implicit in S3)
        """
        raise NotImplementedError("S3FileStorage.create_directory not implemented")
