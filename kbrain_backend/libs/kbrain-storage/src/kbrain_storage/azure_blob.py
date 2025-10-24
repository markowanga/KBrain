"""
Azure Blob Storage implementation.
Requires: azure-kbrain_storage-blob, aiohttp
"""

from pathlib import Path
from typing import List, Optional, Union

from kbrain_storage.base import BaseFileStorage


class AzureBlobStorage(BaseFileStorage):
    """
    Azure Blob Storage implementation.

    Configuration:
        - AZURE_STORAGE_CONNECTION_STRING: Azure connection string
        OR
        - AZURE_STORAGE_ACCOUNT_NAME: Storage account name
        - AZURE_STORAGE_ACCOUNT_KEY: Storage account key

    Installation:
        pip install azure-kbrain_storage-blob aiohttp

    Example:
        kbrain_storage = AzureBlobStorage(
            container_name="my-container",
            connection_string="DefaultEndpointsProtocol=https;..."
        )
    """

    def __init__(
        self,
        container_name: str,
        connection_string: Optional[str] = None,
        account_name: Optional[str] = None,
        account_key: Optional[str] = None,
        prefix: str = ""
    ):
        """
        Initialize Azure Blob kbrain_storage.

        Args:
            container_name: Azure container name
            connection_string: Azure connection string
            account_name: Storage account name (if not using connection_string)
            account_key: Storage account key (if not using connection_string)
            prefix: Optional prefix for all blobs (acts as root directory)
        """
        self.container_name = container_name
        self.connection_string = connection_string
        self.account_name = account_name
        self.account_key = account_key
        self.prefix = prefix.strip("/")

        # TODO: Initialize Azure BlobServiceClient
        # from azure.kbrain_storage.blob.aio import BlobServiceClient
        # if connection_string:
        #     self.client = BlobServiceClient.from_connection_string(connection_string)
        # else:
        #     self.client = BlobServiceClient(...)
        raise NotImplementedError(
            "AzureBlobStorage is not yet implemented. "
            "Install 'azure-kbrain_storage-blob' and implement the methods."
        )

    def _get_blob_name(self, path: Union[str, Path]) -> str:
        """
        Convert path to blob name with prefix.

        Args:
            path: File path

        Returns:
            Full blob name
        """
        path_str = str(Path(path)).replace("\\", "/")
        if self.prefix:
            return f"{self.prefix}/{path_str}"
        return path_str

    async def save_file(
        self,
        path: Union[str, Path],
        content: bytes,
        overwrite: bool = True
    ) -> bool:
        """
        Save file to Azure Blob Storage.

        Implementation notes:
            - Get blob client: container_client.get_blob_client(blob_name)
            - Use blob_client.upload_blob(data, overwrite=overwrite)
            - Set content_type based on file extension
        """
        raise NotImplementedError("AzureBlobStorage.save_file not implemented")

    async def read_file(self, path: Union[str, Path]) -> Optional[bytes]:
        """
        Read file from Azure Blob Storage.

        Implementation notes:
            - Get blob client
            - Use blob_client.download_blob()
            - Read with readall() or readinto()
            - Handle BlobNotFound exception
        """
        raise NotImplementedError("AzureBlobStorage.read_file not implemented")

    async def exists(self, path: Union[str, Path]) -> bool:
        """
        Check if blob exists.

        Implementation notes:
            - Get blob client
            - Use blob_client.exists()
        """
        raise NotImplementedError("AzureBlobStorage.exists not implemented")

    async def list_directory(
        self,
        path: Union[str, Path] = "",
        recursive: bool = False
    ) -> List[str]:
        """
        List blobs in directory.

        Implementation notes:
            - Use container_client.list_blobs(name_starts_with=prefix)
            - For non-recursive, filter by delimiter='/'
            - Use list_blob_names for better performance
        """
        raise NotImplementedError("AzureBlobStorage.list_directory not implemented")

    async def delete_file(self, path: Union[str, Path]) -> bool:
        """
        Delete blob from Azure.

        Implementation notes:
            - Get blob client
            - Check if exists first
            - Use blob_client.delete_blob()
        """
        raise NotImplementedError("AzureBlobStorage.delete_file not implemented")

    async def get_file_size(self, path: Union[str, Path]) -> Optional[int]:
        """
        Get blob size.

        Implementation notes:
            - Get blob client
            - Use blob_client.get_blob_properties()
            - Extract size from properties
        """
        raise NotImplementedError("AzureBlobStorage.get_file_size not implemented")

    async def create_directory(self, path: Union[str, Path]) -> bool:
        """
        Create directory in Azure Blob Storage.

        Implementation notes:
            - Azure Blob doesn't have real directories
            - Directories are implicit based on blob names with /
            - Can create a zero-byte marker blob if needed
            - Or just return True
        """
        raise NotImplementedError("AzureBlobStorage.create_directory not implemented")
