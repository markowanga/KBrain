"""Image processor for PNG and JPG files using OpenAI Vision API."""

import base64
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


class ImageProcessor(BaseProcessor):
    """
    Processor for image files (PNG, JPG, JPEG) using OpenAI Vision API.

    Uses GPT-4o vision capabilities for OCR and image description,
    then sends the extracted markdown to RAGFlow for indexing.
    """

    SUPPORTED_EXTENSIONS = {"png", "jpg", "jpeg"}

    MIME_TYPES = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
    }

    def __init__(
        self,
        openai_api_key: str | None = None,
        openai_base_url: str = "https://api.openai.com/v1/chat/completions",
        model: str = "gpt-5.2-2025-12-11",
        prompt: str = (
            "Analyze this image. First, extract any text visible in the image (OCR). "
            "Then, describe what you see in the image. "
            "Format your response as:\n\n"
            "## Extracted Text\n[OCR text here, or 'No text found' if none]\n\n"
            "## Image Description\n[Description here]"
        ),
        timeout: int = 60,
        # RAGFlow settings
        ragflow_url: str | None = None,
        ragflow_api_key: str | None = None,
        ragflow_dataset_id: str | None = None,
        ragflow_wait_for_parsing: bool = True,
        ragflow_max_wait: float = 300.0,
    ) -> None:
        """
        Initialize the image processor.

        Args:
            openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            openai_base_url: OpenAI API base URL
            model: Model to use for vision processing
            prompt: Prompt for the vision model
            timeout: Request timeout in seconds
            ragflow_url: RAGFlow API URL (defaults to RAGFLOW_URL env var)
            ragflow_api_key: RAGFlow API key (defaults to RAGFLOW_API_KEY env var)
            ragflow_dataset_id: RAGFlow dataset ID (defaults to RAGFLOW_DATASET_ID env var)
            ragflow_wait_for_parsing: Whether to wait for RAGFlow parsing
            ragflow_max_wait: Maximum wait time for RAGFlow parsing
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.openai_base_url = openai_base_url
        self.model = model
        self.prompt = prompt
        self.timeout = timeout

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
            logger.info("RAGFlow client initialized for image processor")

        if not self.openai_api_key:
            logger.warning(
                "No OpenAI API key provided. Set OPENAI_API_KEY env var or pass openai_api_key."
            )

    @property
    def name(self) -> str:
        """Return processor name."""
        return "image_processor"

    async def can_process(self, document: DocumentInfo) -> bool:
        """Check if document is a supported image format."""
        return document.file_extension.lower() in self.SUPPORTED_EXTENSIONS

    async def process(self, document: DocumentInfo) -> ProcessingResult:
        """
        Process an image file using OpenAI Vision API.

        Args:
            document: Document information with download URL

        Returns:
            ProcessingResult with OCR text, description and RAGFlow info
        """
        logger.info(f"Processing image with OpenAI Vision: {document.original_name}")

        if not self.openai_api_key:
            return ProcessingResult(
                success=False,
                error_message="OpenAI API key not configured",
            )

        try:
            # Download image content
            image_bytes = await self._download_file(document.download_url)

            if not image_bytes:
                return ProcessingResult(
                    success=False,
                    error_message="Failed to download image file",
                )

            # Get MIME type
            extension = document.file_extension.lower()
            mime_type = self.MIME_TYPES.get(extension, "image/jpeg")

            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            image_url = f"data:{mime_type};base64,{image_base64}"

            # Call OpenAI Vision API
            text_content = await self._call_vision_api(image_url)

            result_metadata: dict[str, object] = {
                "processor": self.name,
                "file_type": extension,
                "file_size": len(image_bytes),
                "char_count": len(text_content),
                "word_count": len(text_content.split()),
                "model": self.model,
                "text_content": text_content,
            }

            logger.info(f"Successfully processed image: {document.original_name}")

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
            logger.error(f"Error processing image {document.original_name}: {e}")
            return ProcessingResult(
                success=False,
                error_message=str(e),
            )

    async def _send_to_ragflow(
        self,
        original_filename: str,
        markdown_content: str,
    ) -> dict[str, object]:
        """
        Send extracted markdown to RAGFlow.

        Args:
            original_filename: Original filename
            markdown_content: Extracted markdown text

        Returns:
            RAGFlow result dict
        """
        if not self._ragflow_client or not self.ragflow_dataset_id:
            return {"error": "RAGFlow not configured"}

        logger.info(f"Sending {original_filename} to RAGFlow...")

        result = await self._ragflow_client.upload_and_parse(
            dataset_id=self.ragflow_dataset_id,
            filename=f"{original_filename.rsplit('.', 1)[0]}.md",
            content=markdown_content,
            content_type="text/markdown",
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

    async def _call_vision_api(self, image_url: str) -> str:
        """
        Call OpenAI Vision API with the image.

        Args:
            image_url: Base64 data URL of the image

        Returns:
            Model response text
        """
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self.prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                                "detail": "high",
                            },
                        },
                    ],
                }
            ],
            "max_tokens": 4096,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.openai_base_url,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()

            data = response.json()
            content: str = data["choices"][0]["message"]["content"]
            return content

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
        Handle image deletion cleanup.

        Args:
            message: Queue message with document_id, storage_path, etc.

        Returns:
            ProcessingResult indicating cleanup success/failure
        """
        logger.info(
            f"Cleanup for deleted image {message.document_id} "
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
                f"Deleting image {message.ragflow_document_id} from RAGFlow..."
            )
            deleted = await self._ragflow_client.delete_document(
                dataset_id=self.ragflow_dataset_id,
                document_id=message.ragflow_document_id,
            )
            cleanup_results["ragflow_deleted"] = deleted
            cleanup_results["ragflow_document_id"] = message.ragflow_document_id

            if deleted:
                logger.info(
                    f"Successfully deleted image {message.ragflow_document_id} "
                    f"from RAGFlow"
                )
            else:
                logger.warning(
                    f"Failed to delete image {message.ragflow_document_id} "
                    f"from RAGFlow"
                )
        elif self._ragflow_client and self.ragflow_dataset_id:
            logger.warning(
                f"No RAGFlow document ID provided for image {message.document_id}, "
                f"cannot delete from RAGFlow"
            )
            cleanup_results["ragflow_deleted"] = False
            cleanup_results["ragflow_error"] = "No RAGFlow document ID provided"

        return ProcessingResult(
            success=True,
            metadata=cleanup_results,
        )
