"""Document processor for PDF and DOCX files using Docling with OpenAI VLM."""

import os
import tempfile
from pathlib import Path

import httpx
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import VlmPipelineOptions
from docling.datamodel.pipeline_options_vlm_model import (
    ApiVlmOptions,
    ResponseFormat,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline
from loguru import logger

from kbrain_processor_orchestrator.base import BaseProcessor
from kbrain_processor_orchestrator.models import (
    DocumentInfo,
    ProcessingResult,
    QueueMessage,
)
from kbrain_processor_orchestrator.ragflow_client import RAGFlowClient


class DocumentProcessor(BaseProcessor):
    """
    Processor for document files (PDF, DOCX) using Docling with OpenAI VLM.

    Uses vision-language models to extract text and structure from documents,
    then sends the extracted markdown to RAGFlow for indexing.
    """

    SUPPORTED_EXTENSIONS = {"pdf", "docx"}

    def __init__(
        self,
        openai_api_key: str | None = None,
        openai_base_url: str = "https://api.openai.com/v1/chat/completions",
        model: str = "gpt-5.2-2025-12-11",
        prompt: str = "OCR the full page to markdown. Return only the markdown content.",
        timeout: int = 120,
        # RAGFlow settings
        ragflow_url: str | None = None,
        ragflow_api_key: str | None = None,
        ragflow_dataset_id: str | None = None,
        ragflow_wait_for_parsing: bool = True,
        ragflow_max_wait: float = 300.0,
    ) -> None:
        """
        Initialize the document processor.

        Args:
            openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            openai_base_url: OpenAI API base URL
            model: Model to use for VLM processing
            prompt: Prompt for the VLM model
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
            logger.info("RAGFlow client initialized for document processor")

        if not self.openai_api_key:
            logger.warning(
                "No OpenAI API key provided. Set OPENAI_API_KEY env var or pass openai_api_key."
            )

    @property
    def name(self) -> str:
        """Return processor name."""
        return "document_processor"

    async def can_process(self, document: DocumentInfo) -> bool:
        """Check if document is a supported document format."""
        return document.file_extension.lower() in self.SUPPORTED_EXTENSIONS

    async def process(self, document: DocumentInfo) -> ProcessingResult:
        """
        Process a document file (PDF or DOCX) using Docling with OpenAI VLM.

        Args:
            document: Document information with download URL

        Returns:
            ProcessingResult with extracted text and RAGFlow info
        """
        logger.info(f"Processing document with Docling VLM: {document.original_name}")

        if not self.openai_api_key:
            return ProcessingResult(
                success=False,
                error_message="OpenAI API key not configured",
            )

        try:
            # Download document content
            doc_bytes = await self._download_file(document.download_url)

            if not doc_bytes:
                return ProcessingResult(
                    success=False,
                    error_message="Failed to download document file",
                )

            # Save to temporary file (Docling needs file path)
            extension = document.file_extension.lower()
            with tempfile.NamedTemporaryFile(
                suffix=f".{extension}", delete=False
            ) as tmp_file:
                tmp_file.write(doc_bytes)
                tmp_path = Path(tmp_file.name)

            try:
                # Extract text using Docling VLM pipeline
                text_content = self._extract_with_docling(tmp_path, extension)

                result_metadata: dict[str, object] = {
                    "processor": self.name,
                    "file_type": extension,
                    "file_size": len(doc_bytes),
                    "char_count": len(text_content),
                    "word_count": len(text_content.split()),
                    "model": self.model,
                    "text_content": text_content,
                }

                logger.info(
                    f"Successfully extracted {len(text_content)} chars from: {document.original_name}"
                )

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

            finally:
                # Clean up temporary file
                tmp_path.unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"Error processing document {document.original_name}: {e}")
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

    def _extract_with_docling(self, file_path: Path, extension: str) -> str:
        """
        Extract text from document using Docling VLM pipeline.

        Args:
            file_path: Path to the document file
            extension: File extension (pdf, docx)

        Returns:
            Extracted text as markdown string
        """
        # Configure API-based VLM options for OpenAI
        vlm_options = ApiVlmOptions(
            url=self.openai_base_url,  # type: ignore[arg-type]
            params={"model": self.model},
            headers={"Authorization": f"Bearer {self.openai_api_key}"},
            prompt=self.prompt,
            timeout=self.timeout,
            scale=1.0,
            response_format=ResponseFormat.MARKDOWN,
        )

        # Create pipeline options
        pipeline_options = VlmPipelineOptions(
            enable_remote_services=True,
        )
        pipeline_options.vlm_options = vlm_options

        # Determine input format
        if extension == "pdf":
            input_format = InputFormat.PDF
        elif extension == "docx":
            input_format = InputFormat.DOCX
        else:
            raise ValueError(f"Unsupported extension: {extension}")

        # Initialize converter with VLM pipeline
        converter = DocumentConverter(
            format_options={
                input_format: PdfFormatOption(
                    pipeline_cls=VlmPipeline,
                    pipeline_options=pipeline_options,
                )
            }
        )

        # Convert document
        result = converter.convert(str(file_path))

        if result.status.name != "SUCCESS":
            raise RuntimeError(f"Docling conversion failed: {result.errors}")

        # Export to markdown
        markdown_content = result.document.export_to_markdown()

        return markdown_content

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
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"Failed to download file from {url}: {e}")
            return None

    async def on_delete(self, message: QueueMessage) -> ProcessingResult:
        """
        Handle document deletion cleanup.

        Removes the document from RAGFlow if it was indexed there.

        Args:
            message: Queue message with document_id, storage_path, etc.

        Returns:
            ProcessingResult indicating cleanup success/failure
        """
        logger.info(
            f"Cleanup for deleted document {message.document_id} "
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
                f"Deleting document {message.ragflow_document_id} from RAGFlow..."
            )
            deleted = await self._ragflow_client.delete_document(
                dataset_id=self.ragflow_dataset_id,
                document_id=message.ragflow_document_id,
            )
            cleanup_results["ragflow_deleted"] = deleted
            cleanup_results["ragflow_document_id"] = message.ragflow_document_id

            if deleted:
                logger.info(
                    f"Successfully deleted document {message.ragflow_document_id} "
                    f"from RAGFlow"
                )
            else:
                logger.warning(
                    f"Failed to delete document {message.ragflow_document_id} "
                    f"from RAGFlow"
                )
        elif self._ragflow_client and self.ragflow_dataset_id:
            logger.warning(
                f"No RAGFlow document ID provided for document {message.document_id}, "
                f"cannot delete from RAGFlow"
            )
            cleanup_results["ragflow_deleted"] = False
            cleanup_results["ragflow_error"] = "No RAGFlow document ID provided"

        return ProcessingResult(
            success=True,
            metadata=cleanup_results,
        )
