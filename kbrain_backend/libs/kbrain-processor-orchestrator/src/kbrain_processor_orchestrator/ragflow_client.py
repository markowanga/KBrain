"""RAGFlow API client for document management."""

import asyncio
from enum import Enum
from typing import Any

import httpx
from loguru import logger
from pydantic import BaseModel


class RAGFlowDocumentStatus(str, Enum):
    """RAGFlow document processing status."""

    UNSTART = "UNSTART"  # 0
    RUNNING = "RUNNING"  # 1
    CANCEL = "CANCEL"  # 2
    DONE = "DONE"  # 3
    FAIL = "FAIL"  # 4


class RAGFlowDocument(BaseModel):
    """RAGFlow document response model."""

    id: str
    name: str
    dataset_id: str | None = None
    knowledgebase_id: str | None = None
    run: str
    chunk_count: int = 0
    size: int = 0
    progress: float = 0.0
    progress_msg: str = ""


class RAGFlowClient:
    """
    Client for RAGFlow API.

    Handles document upload, parsing, and status monitoring.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 120,
    ) -> None:
        """
        Initialize RAGFlow client.

        Args:
            base_url: RAGFlow API base URL (e.g., http://localhost:9380)
            api_key: RAGFlow API key
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self, content_type: str | None = None) -> dict[str, str]:
        """Get request headers."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    async def upload_document(
        self,
        dataset_id: str,
        filename: str,
        content: bytes,
        content_type: str = "text/plain",
    ) -> RAGFlowDocument | None:
        """
        Upload a document to RAGFlow dataset.

        Args:
            dataset_id: Target dataset ID
            filename: Name for the uploaded file
            content: File content as bytes
            content_type: MIME type of the content

        Returns:
            RAGFlowDocument if successful, None otherwise
        """
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/documents"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {"file": (filename, content, content_type)}

                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files=files,
                )

                data = response.json()

                if data.get("code") != 0:
                    logger.error(f"RAGFlow upload failed: {data.get('message')}")
                    return None

                # Response contains list of uploaded documents
                docs = data.get("data", [])
                if docs:
                    return RAGFlowDocument(**docs[0])

                return None

        except Exception as e:
            logger.error(f"Error uploading to RAGFlow: {e}")
            return None

    async def upload_markdown(
        self,
        dataset_id: str,
        original_filename: str,
        markdown_content: str,
    ) -> RAGFlowDocument | None:
        """
        Upload markdown content to RAGFlow.

        Converts the original filename to .md extension.

        Args:
            dataset_id: Target dataset ID
            original_filename: Original filename (will be converted to .md)
            markdown_content: Markdown text content

        Returns:
            RAGFlowDocument if successful, None otherwise
        """
        # Convert filename to .md
        base_name = original_filename.rsplit(".", 1)[0]
        md_filename = f"{base_name}.md"

        return await self.upload_document(
            dataset_id=dataset_id,
            filename=md_filename,
            content=markdown_content.encode("utf-8"),
            content_type="text/markdown",
        )

    async def parse_documents(
        self,
        dataset_id: str,
        document_ids: list[str],
    ) -> bool:
        """
        Start parsing documents in RAGFlow.

        Args:
            dataset_id: Dataset ID
            document_ids: List of document IDs to parse

        Returns:
            True if parsing started successfully
        """
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/chunks"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers=self._headers("application/json"),
                    json={"document_ids": document_ids},
                )

                data = response.json()

                if data.get("code") != 0:
                    logger.error(f"RAGFlow parse failed: {data.get('message')}")
                    return False

                logger.info(f"Started parsing {len(document_ids)} documents in RAGFlow")
                return True

        except Exception as e:
            logger.error(f"Error starting RAGFlow parse: {e}")
            return False

    async def get_document_status(
        self,
        dataset_id: str,
        document_id: str,
    ) -> RAGFlowDocument | None:
        """
        Get document status from RAGFlow.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID

        Returns:
            RAGFlowDocument with current status
        """
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/documents"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers=self._headers(),
                    params={"id": document_id},
                )

                data = response.json()

                if data.get("code") != 0:
                    logger.error(f"RAGFlow status check failed: {data.get('message')}")
                    return None

                docs = data.get("data", {}).get("docs", [])
                if docs:
                    return RAGFlowDocument(**docs[0])

                return None

        except Exception as e:
            logger.error(f"Error checking RAGFlow status: {e}")
            return None

    async def list_documents(
        self,
        dataset_id: str,
        page: int = 1,
        page_size: int = 100,
        order_by: str = "create_time",
        descend: bool = True,
    ) -> list[RAGFlowDocument]:
        """
        List all documents in a RAGFlow dataset.

        Args:
            dataset_id: Dataset ID
            page: Page number (1-indexed)
            page_size: Number of documents per page
            order_by: Field to order by
            descend: Whether to sort descending

        Returns:
            List of RAGFlowDocument objects
        """
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/documents"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers=self._headers(),
                    params={
                        "page": page,
                        "page_size": page_size,
                        "orderby": order_by,
                        "desc": str(descend).lower(),
                    },
                )

                data = response.json()

                if data.get("code") != 0:
                    logger.error(f"RAGFlow list documents failed: {data.get('message')}")
                    return []

                docs = data.get("data", {}).get("docs", [])
                return [RAGFlowDocument(**doc) for doc in docs]

        except Exception as e:
            logger.error(f"Error listing RAGFlow documents: {e}")
            return []

    async def list_all_documents(
        self,
        dataset_id: str,
        page_size: int = 100,
    ) -> list[RAGFlowDocument]:
        """
        List ALL documents in a RAGFlow dataset (handles pagination).

        Args:
            dataset_id: Dataset ID
            page_size: Number of documents per page

        Returns:
            List of all RAGFlowDocument objects
        """
        all_docs: list[RAGFlowDocument] = []
        page = 1

        while True:
            docs = await self.list_documents(
                dataset_id=dataset_id,
                page=page,
                page_size=page_size,
            )

            if not docs:
                break

            all_docs.extend(docs)

            if len(docs) < page_size:
                break

            page += 1

        logger.info(f"Listed {len(all_docs)} documents from RAGFlow dataset {dataset_id}")
        return all_docs

    async def wait_for_parsing(
        self,
        dataset_id: str,
        document_id: str,
        poll_interval: float = 2.0,
        max_wait: float = 300.0,
    ) -> RAGFlowDocumentStatus:
        """
        Wait for document parsing to complete.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID to monitor
            poll_interval: Seconds between status checks
            max_wait: Maximum seconds to wait

        Returns:
            Final document status
        """
        elapsed = 0.0

        while elapsed < max_wait:
            doc = await self.get_document_status(dataset_id, document_id)

            if not doc:
                logger.warning(f"Could not get status for document {document_id}")
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                continue

            status = RAGFlowDocumentStatus(doc.run)

            if status == RAGFlowDocumentStatus.DONE:
                logger.info(
                    f"RAGFlow parsing complete for {document_id}: "
                    f"{doc.chunk_count} chunks"
                )
                return status

            if status == RAGFlowDocumentStatus.FAIL:
                logger.error(
                    f"RAGFlow parsing failed for {document_id}: {doc.progress_msg}"
                )
                return status

            if status == RAGFlowDocumentStatus.CANCEL:
                logger.warning(f"RAGFlow parsing cancelled for {document_id}")
                return status

            # Still running or not started
            logger.debug(
                f"RAGFlow parsing {document_id}: {status.value} "
                f"({doc.progress:.1%}) - {doc.progress_msg}"
            )

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        logger.warning(f"Timeout waiting for RAGFlow parsing of {document_id}")
        return RAGFlowDocumentStatus.RUNNING

    async def delete_document(
        self,
        dataset_id: str,
        document_id: str,
    ) -> bool:
        """
        Delete a document from RAGFlow.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID to delete

        Returns:
            True if deleted successfully
        """
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/documents"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    "DELETE",
                    url,
                    headers=self._headers("application/json"),
                    json={"ids": [document_id]},
                )

                data = response.json()

                if data.get("code") != 0:
                    logger.error(f"RAGFlow delete failed: {data.get('message')}")
                    return False

                logger.info(f"Deleted document {document_id} from RAGFlow")
                return True

        except Exception as e:
            logger.error(f"Error deleting from RAGFlow: {e}")
            return False

    async def download_document(
        self,
        dataset_id: str,
        document_id: str,
    ) -> bytes | None:
        """
        Download document content from RAGFlow.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID to download

        Returns:
            File content as bytes, or None if failed
        """
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/documents/{document_id}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._headers())

                if response.status_code != 200:
                    logger.error(
                        f"RAGFlow download failed for {document_id}: "
                        f"HTTP {response.status_code}"
                    )
                    return None

                # Check if response is JSON error
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    data = response.json()
                    if data.get("code") != 0:
                        logger.error(f"RAGFlow download failed: {data.get('message')}")
                        return None

                return response.content

        except Exception as e:
            logger.error(f"Error downloading from RAGFlow: {e}")
            return None

    async def upload_and_parse(
        self,
        dataset_id: str,
        filename: str,
        content: bytes | str,
        content_type: str = "text/markdown",
        wait_for_completion: bool = True,
        max_wait: float = 300.0,
    ) -> dict[str, Any]:
        """
        Upload document and start parsing, optionally waiting for completion.

        Args:
            dataset_id: Target dataset ID
            filename: Filename for the document
            content: File content (bytes or string)
            content_type: MIME type
            wait_for_completion: Whether to wait for parsing to complete
            max_wait: Maximum wait time in seconds

        Returns:
            Result dict with document_id, status, chunk_count
        """
        # Convert string to bytes if needed
        if isinstance(content, str):
            content = content.encode("utf-8")

        # Upload document
        doc = await self.upload_document(
            dataset_id=dataset_id,
            filename=filename,
            content=content,
            content_type=content_type,
        )

        if not doc:
            return {
                "success": False,
                "error": "Failed to upload document to RAGFlow",
            }

        logger.info(f"Uploaded {filename} to RAGFlow as {doc.id}")

        # Start parsing
        parse_started = await self.parse_documents(
            dataset_id=dataset_id,
            document_ids=[doc.id],
        )

        if not parse_started:
            return {
                "success": False,
                "document_id": doc.id,
                "error": "Failed to start parsing",
            }

        if not wait_for_completion:
            return {
                "success": True,
                "document_id": doc.id,
                "ragflow_document_id": doc.id,
                "status": RAGFlowDocumentStatus.RUNNING.value,
            }

        # Wait for parsing to complete
        final_status = await self.wait_for_parsing(
            dataset_id=dataset_id,
            document_id=doc.id,
            max_wait=max_wait,
        )

        # Get final document info
        final_doc = await self.get_document_status(dataset_id, doc.id)

        return {
            "success": final_status == RAGFlowDocumentStatus.DONE,
            "document_id": doc.id,
            "ragflow_document_id": doc.id,
            "status": final_status.value,
            "chunk_count": final_doc.chunk_count if final_doc else 0,
            "progress_msg": final_doc.progress_msg if final_doc else "",
        }
