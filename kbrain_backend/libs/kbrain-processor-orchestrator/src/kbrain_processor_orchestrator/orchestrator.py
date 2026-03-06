"""Document processing orchestrator."""

import asyncio
from datetime import datetime
from typing import Any

from loguru import logger

from kbrain_processor_orchestrator.base import BaseProcessor
from kbrain_processor_orchestrator.models import (
    DocumentInfo,
    ProcessingResult,
    QueueMessage,
)


class ProcessingOrchestrator:
    """
    Orchestrates document processing through multiple processors.

    This class manages:
    - Processor registration
    - Document processing pipeline
    - Error handling and retries
    - Processing hooks
    """

    def __init__(self, max_retries: int = 3) -> None:
        """
        Initialize the orchestrator.

        Args:
            max_retries: Maximum number of retry attempts for failed processing
        """
        self._processors: list[BaseProcessor] = []
        self.max_retries = max_retries

    def register_processor(self, processor: BaseProcessor) -> None:
        """
        Register a processor with the orchestrator.

        Args:
            processor: Processor instance to register
        """
        if not processor.enabled:
            logger.info(
                f"Processor {processor.name} is disabled, skipping registration"
            )
            return

        self._processors.append(processor)
        logger.info(f"Registered processor: {processor.name}")

    def get_processors(self) -> list[BaseProcessor]:
        """
        Get all registered processors.

        Returns:
            List of registered processors
        """
        return self._processors.copy()

    async def process_document(
        self, document: DocumentInfo, attempt: int = 1
    ) -> dict[str, ProcessingResult]:
        """
        Process a document through all applicable processors.

        Args:
            document: Document to process
            attempt: Current attempt number (for retries)

        Returns:
            Dictionary mapping processor names to their results
        """
        if not self._processors:
            logger.warning("No processors registered")
            return {}

        logger.info(
            f"Processing document {document.id} ({document.original_name}) "
            f"- attempt {attempt}/{self.max_retries}"
        )

        results: dict[str, ProcessingResult] = {}

        # Get applicable processors
        applicable_processors = await self._get_applicable_processors(document)

        if not applicable_processors:
            logger.info(f"No applicable processors for document {document.id}")
            return results

        # Process through each applicable processor
        for processor in applicable_processors:
            result = await self._process_with_processor(processor, document, attempt)
            results[processor.name] = result

        return results

    async def _get_applicable_processors(
        self, document: DocumentInfo
    ) -> list[BaseProcessor]:
        """
        Get processors that can handle the document.

        Args:
            document: Document to check

        Returns:
            List of applicable processors
        """
        applicable: list[BaseProcessor] = []

        for processor in self._processors:
            try:
                if await processor.can_process(document):
                    applicable.append(processor)
            except Exception as e:
                logger.error(
                    f"Error checking if processor {processor.name} can process "
                    f"document {document.id}: {e}"
                )

        logger.info(
            f"Found {len(applicable)} applicable processor(s) for document {document.id}: "
            f"{[p.name for p in applicable]}"
        )

        return applicable

    async def _process_with_processor(
        self, processor: BaseProcessor, document: DocumentInfo, attempt: int
    ) -> ProcessingResult:
        """
        Process document with a specific processor.

        Args:
            processor: Processor to use
            document: Document to process
            attempt: Current attempt number

        Returns:
            Processing result
        """
        # context = ProcessingContext(
        #     document=document,
        #     processor_name=processor.name,
        #     attempt=attempt,
        #     max_attempts=self.max_retries,
        # )

        start_time = datetime.utcnow()

        try:
            logger.info(f"Processing document {document.id} with {processor.name}")

            result = await processor.process(document)

            # Calculate duration
            duration = (datetime.utcnow() - start_time).total_seconds()
            result.duration_seconds = duration

            logger.info(
                f"Successfully processed document {document.id} with {processor.name} "
                f"in {duration:.2f}s"
            )

            # Call success hook
            try:
                await processor.on_success(document, result)
            except Exception as e:
                logger.error(f"Error in on_success hook for {processor.name}: {e}")

            return result

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()

            logger.error(
                f"Error processing document {document.id} with {processor.name}: {e}",
                exc_info=True,
            )

            # Call failure hook
            try:
                await processor.on_failure(document, e, attempt)
            except Exception as hook_error:
                logger.error(
                    f"Error in on_failure hook for {processor.name}: {hook_error}"
                )

            return ProcessingResult(
                success=False,
                error_message=str(e),
                duration_seconds=duration,
            )

    async def process_document_with_retry(
        self, document: DocumentInfo
    ) -> dict[str, ProcessingResult]:
        """
        Process document with automatic retry on failure.

        Args:
            document: Document to process

        Returns:
            Dictionary mapping processor names to their results
        """
        for attempt in range(1, self.max_retries + 1):
            results = await self.process_document(document, attempt)

            # Check if all processors succeeded
            all_success = all(r.success for r in results.values())

            if all_success or attempt == self.max_retries:
                return results

            # Wait before retry (exponential backoff)
            wait_time = 2**attempt
            logger.info(
                f"Retrying document {document.id} in {wait_time}s "
                f"(attempt {attempt + 1}/{self.max_retries})"
            )
            await asyncio.sleep(wait_time)

        return results

    async def delete_document(
        self, message: QueueMessage
    ) -> dict[str, ProcessingResult]:
        """
        Handle document deletion through applicable processors.

        Args:
            message: Queue message with deletion info

        Returns:
            Dictionary mapping processor names to their cleanup results
        """
        if not self._processors:
            logger.warning("No processors registered")
            return {}

        logger.info(
            f"Handling deletion for document {message.document_id} "
            f"(file: {message.original_name or 'unknown'})"
        )

        results: dict[str, ProcessingResult] = {}

        # Get processors that can handle this deletion
        applicable_processors = self._get_delete_processors(message)

        if not applicable_processors:
            logger.info(f"No processors to handle deletion for {message.document_id}")
            return results

        # Run cleanup on each applicable processor
        for processor in applicable_processors:
            result = await self._delete_with_processor(processor, message)
            results[processor.name] = result

        return results

    def _get_delete_processors(self, message: QueueMessage) -> list[BaseProcessor]:
        """
        Get processors that should handle deletion for the message.

        Args:
            message: Queue message with deletion info

        Returns:
            List of processors that can handle the deletion
        """
        applicable: list[BaseProcessor] = []

        for processor in self._processors:
            try:
                if processor.can_handle_delete(message):
                    applicable.append(processor)
            except Exception as e:
                logger.error(
                    f"Error checking if processor {processor.name} can handle delete: {e}"
                )

        logger.info(
            f"Found {len(applicable)} processor(s) for deletion of {message.document_id}: "
            f"{[p.name for p in applicable]}"
        )

        return applicable

    async def _delete_with_processor(
        self, processor: BaseProcessor, message: QueueMessage
    ) -> ProcessingResult:
        """
        Handle deletion with a specific processor.

        Args:
            processor: Processor to use
            message: Queue message with deletion info

        Returns:
            Processing result
        """
        start_time = datetime.utcnow()

        try:
            logger.info(
                f"Running deletion cleanup for {message.document_id} "
                f"with {processor.name}"
            )

            result = await processor.on_delete(message)

            duration = (datetime.utcnow() - start_time).total_seconds()
            result.duration_seconds = duration

            logger.info(
                f"Deletion cleanup for {message.document_id} with {processor.name} "
                f"completed in {duration:.2f}s"
            )

            return result

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()

            logger.error(
                f"Error during deletion cleanup for {message.document_id} "
                f"with {processor.name}: {e}",
                exc_info=True,
            )

            return ProcessingResult(
                success=False,
                error_message=str(e),
                duration_seconds=duration,
            )

    def get_processor_stats(self) -> dict[str, Any]:
        """
        Get statistics about registered processors.

        Returns:
            Dictionary with processor statistics
        """
        return {
            "total_processors": len(self._processors),
            "enabled_processors": len([p for p in self._processors if p.enabled]),
            "processors": [
                {
                    "name": p.name,
                    "enabled": p.enabled,
                    "class": p.__class__.__name__,
                }
                for p in self._processors
            ],
        }
