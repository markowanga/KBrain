"""Text processor for TXT files."""

import os

import httpx
from loguru import logger

from kbrain_processor_orchestrator.base import BaseProcessor
from kbrain_processor_orchestrator.models import (
    DocumentInfo,
    ProcessingResult,
    QueueMessage,
)
from kbrain_processor_orchestrator.ragflow_client import RAGFlowClient


class TextProcessor(BaseProcessor):
    """
    Processor for plain text files (TXT).

    Sends text files directly to RAGFlow for indexing.
    No LLM processing needed - just read and send.
    """

    SUPPORTED_EXTENSIONS = {"txt"}

    def __init__(
        self,
        # RAGFlow settings
        ragflow_url: str | None = None,
        ragflow_api_key: str | None = None,
        ragflow_dataset_id: str | None = None,
        ragflow_wait_for_parsing: bool = True,
        ragflow_max_wait: float = 300.0,
    ) -> None:
        """
        Initialize the text processor.

        Args:
            ragflow_url: RAGFlow API URL (defaults to RAGFLOW_URL env var)
            ragflow_api_key: RAGFlow API key (defaults to RAGFLOW_API_KEY env var)
            ragflow_dataset_id: RAGFlow dataset ID (defaults to RAGFLOW_DATASET_ID env var)
            ragflow_wait_for_parsing: Whether to wait for RAGFlow parsing
            ragflow_max_wait: Maximum wait time for RAGFlow parsing
        """
        # RAGFlow configuration
        self.ragflow_url = ragflow_url or os.getenv("RAGFLOW_URL")
        self.ragflow_api_key = ragflow_api_key or os.getenv("RAGFLOW_API_KEY")
        self.ragflow_dataset_id = ragflow_dataset_id or os.getenv("RAGFLOW_DATASET_ID")
        self.ragflow_wait_for_parsing = ragflow_wait_for_parsing
        self.ragflow_max_wait = ragflow_max_wait

        # Initialize RAGFlow client if configured
        self._ragflow_client: RAGFlowClient | None = None
        if self.ragflow_url and self.ragflow_api_key:
            self._ragflow_client = RAGFlowClient(
                base_url=self.ragflow_url,
                api_key=self.ragflow_api_key,
            )
            logger.info("RAGFlow client initialized for text processor")

    @property
    def name(self) -> str:
        """Return processor name."""
        return "text_processor"

    async def can_process(self, document: DocumentInfo) -> bool:
        """Check if document is a supported text format."""
        return document.file_extension.lower() in self.SUPPORTED_EXTENSIONS

    async def process(self, document: DocumentInfo) -> ProcessingResult:
        """
        Process a text file.

        Args:
            document: Document information with download URL

        Returns:
            ProcessingResult with text content and RAGFlow info
        """
        logger.info(f"Processing text file: {document.original_name}")

        try:
            # Download text content
            text_bytes = await self._download_file(document.download_url)

            if not text_bytes:
                return ProcessingResult(
                    success=False,
                    error_message="Failed to download text file",
                )

            # Decode text (try UTF-8, fallback to latin-1)
            try:
                text_content = text_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text_content = text_bytes.decode("latin-1")

            result_metadata: dict[str, object] = {
                "processor": self.name,
                "file_type": "txt",
                "file_size": len(text_bytes),
                "char_count": len(text_content),
                "line_count": text_content.count("\n") + 1,
                "word_count": len(text_content.split()),
                "text_content": text_content,
            }

            logger.info(f"Successfully read text file: {document.original_name}")

            # Send to RAGFlow if configured
            if self._ragflow_client and self.ragflow_dataset_id:
                ragflow_result = await self._send_to_ragflow(
                    document.original_name,
                    text_content,
                )
                result_metadata["ragflow"] = ragflow_result

            return ProcessingResult(
                success=True,
                metadata=result_metadata,
            )

        except Exception as e:
            logger.error(f"Error processing text file {document.original_name}: {e}")
            return ProcessingResult(
                success=False,
                error_message=str(e),
            )

    async def _send_to_ragflow(
        self,
        original_filename: str,
        text_content: str,
    ) -> dict[str, object]:
        """
        Send text content to RAGFlow.

        Args:
            original_filename: Original filename
            text_content: Text content

        Returns:
            RAGFlow result dict
        """
        if not self._ragflow_client or not self.ragflow_dataset_id:
            return {"error": "RAGFlow not configured"}

        logger.info(f"Sending {original_filename} to RAGFlow...")

        # For TXT files, send as-is (not converting to .md)
        result = await self._ragflow_client.upload_and_parse(
            dataset_id=self.ragflow_dataset_id,
            filename=original_filename,
            content=text_content,
            content_type="text/plain",
            wait_for_completion=self.ragflow_wait_for_parsing,
            max_wait=self.ragflow_max_wait,
        )

        if result.get("success"):
            logger.info(
                f"RAGFlow indexing complete: {result.get('chunk_count', 0)} chunks"
            )
        else:
            logger.warning(f"RAGFlow indexing issue: {result.get('error', 'unknown')}")

        return result

    async def _download_file(self, url: str | None) -> bytes | None:
        """
        Download file from URL.

        Args:
            url: Download URL

        Returns:
            File bytes or None if failed
        """
        if not url:
            return None

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"Failed to download file from {url}: {e}")
            return None

    async def on_delete(self, message: QueueMessage) -> ProcessingResult:
        """
        Handle text file deletion cleanup.

        Args:
            message: Queue message with document_id, storage_path, etc.

        Returns:
            ProcessingResult indicating cleanup success/failure
        """
        logger.info(
            f"Cleanup for deleted text file {message.document_id} "
            f"(file: {message.original_name or 'unknown'})"
        )

        cleanup_results: dict[str, object] = {
            "action": "delete",
            "document_id": str(message.document_id),
            "file_extension": message.file_extension,
        }

        # Delete from RAGFlow if configured and we have the RAGFlow document ID
        if (
            self._ragflow_client
            and self.ragflow_dataset_id
            and message.ragflow_document_id
        ):
            logger.info(
                f"Deleting text file {message.ragflow_document_id} from RAGFlow..."
            )
            deleted = await self._ragflow_client.delete_document(
                dataset_id=self.ragflow_dataset_id,
                document_id=message.ragflow_document_id,
            )
            cleanup_results["ragflow_deleted"] = deleted
            cleanup_results["ragflow_document_id"] = message.ragflow_document_id

            if deleted:
                logger.info(
                    f"Successfully deleted text file {message.ragflow_document_id} "
                    f"from RAGFlow"
                )
            else:
                logger.warning(
                    f"Failed to delete text file {message.ragflow_document_id} "
                    f"from RAGFlow"
                )
        elif self._ragflow_client and self.ragflow_dataset_id:
            logger.warning(
                f"No RAGFlow document ID provided for text file {message.document_id}, "
                f"cannot delete from RAGFlow"
            )
            cleanup_results["ragflow_deleted"] = False
            cleanup_results["ragflow_error"] = "No RAGFlow document ID provided"

        return ProcessingResult(
            success=True,
            metadata=cleanup_results,
        )
