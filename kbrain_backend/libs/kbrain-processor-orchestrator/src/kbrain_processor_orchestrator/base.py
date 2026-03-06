"""Abstract base class for document processors."""

from abc import ABC, abstractmethod

from kbrain_processor_orchestrator.models import (
    DocumentInfo,
    ProcessingResult,
    QueueMessage,
)


class BaseProcessor(ABC):
    """
    Abstract base class for document processors.

    Implement this interface to create custom document processors
    that can be registered with the orchestrator.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the processor name.

        This should be a unique identifier for the processor.
        """
        pass

    @property
    def enabled(self) -> bool:
        """
        Check if the processor is enabled.

        Override this to add conditional logic for enabling/disabling
        the processor based on configuration or runtime conditions.

        Returns:
            True if processor is enabled, False otherwise
        """
        return True

    async def can_process(self, document: DocumentInfo) -> bool:
        """
        Check if this processor can handle the given document.

        Override this to add filtering logic based on:
        - File extension
        - MIME type
        - Document tags
        - Scope configuration
        - etc.

        Args:
            document: Document information

        Returns:
            True if processor can handle this document, False otherwise
        """
        return True

    @abstractmethod
    async def process(self, document: DocumentInfo) -> ProcessingResult:
        """
        Process the document.

        This is the main processing method that must be implemented.
        It receives full document information including:
        - Scope details
        - Tags
        - Storage path
        - Download URL
        - Metadata

        Args:
            document: Complete document information

        Returns:
            ProcessingResult with success status and optional metadata

        Raises:
            Exception: Any exception will be caught and logged by orchestrator
        """
        pass

    async def on_success(
            self, document: DocumentInfo, result: ProcessingResult
    ) -> None:
        """
        Hook called after successful processing.

        Override this to implement post-processing actions like:
        - Sending notifications
        - Updating external systems
        - Cleanup operations

        Args:
            document: Document that was processed
            result: Processing result
        """
        pass

    async def on_failure(
            self, document: DocumentInfo, error: Exception, attempt: int
    ) -> None:
        """
        Hook called after processing failure.

        Override this to implement error handling like:
        - Error logging
        - Alerting
        - Cleanup operations

        Args:
            document: Document that failed processing
            error: Exception that occurred
            attempt: Current attempt number
        """
        pass

    def can_handle_delete(self, message: QueueMessage) -> bool:
        """
        Check if this processor should handle deletion for the given message.

        Override this to filter based on file extension or other criteria.
        Default implementation returns True if file_extension matches
        processor's SUPPORTED_EXTENSIONS (if defined).

        Args:
            message: Queue message with delete info

        Returns:
            True if processor should handle this deletion
        """
        supported = getattr(self, "SUPPORTED_EXTENSIONS", None)
        if supported and message.file_extension:
            return message.file_extension.lower() in supported
        return False

    async def on_delete(self, message: QueueMessage) -> ProcessingResult:
        """
        Handle document deletion cleanup.

        Override this to implement cleanup logic when a document is deleted:
        - Remove embeddings from vector store
        - Delete cached data
        - Clean up external resources

        Args:
            message: Queue message containing document_id, storage_path, etc.

        Returns:
            ProcessingResult indicating success/failure of cleanup
        """
        # Default: no cleanup needed
        return ProcessingResult(
            success=True,
            metadata={"action": "delete", "cleanup": "none"},
        )


class ExampleProcessor(BaseProcessor):
    """
    Example processor implementation.

    This is a simple example showing how to implement a processor.
    """

    @property
    def name(self) -> str:
        """Return processor name."""
        return "example_processor"

    async def can_process(self, document: DocumentInfo) -> bool:
        """Only process PDF files."""
        return document.file_extension.lower() == "pdf"

    async def process(self, document: DocumentInfo) -> ProcessingResult:
        """
        Example processing logic.

        In a real implementation, you would:
        1. Download the file using document.download_url or storage path
        2. Process the file content
        3. Store results somewhere
        4. Return processing result with metadata
        """
        # Simulate processing
        return ProcessingResult(
            success=True,
            metadata={
                "processed_by": self.name,
                "file_size": document.file_size,
                "file_name": document.original_name,
            },
            duration_seconds=0.5,
        )
