"""Async worker for consuming RabbitMQ messages and processing documents."""

import json
from datetime import datetime
from typing import Any

import httpx
from aio_pika import connect_robust
from aio_pika.abc import AbstractChannel, AbstractConnection, AbstractQueue
from loguru import logger

from kbrain_processor_orchestrator.models import (
    DocumentInfo,
    ProcessingStatus,
    QueueAction,
    QueueMessage,
)
from kbrain_processor_orchestrator.orchestrator import ProcessingOrchestrator


class ProcessingWorker:
    """
    RabbitMQ consumer worker that processes documents.

    The worker:
    1. Connects to RabbitMQ
    2. Consumes messages from a queue (lightweight: document_id + scope_id)
    3. Fetches document details from API
    4. Updates document status to 'processing'
    5. Processes documents through the orchestrator
    6. Updates document status to 'processed' or 'failed'
    """

    def __init__(
        self,
        orchestrator: ProcessingOrchestrator,
        rabbitmq_url: str,
        queue_name: str,
        api_base_url: str,
        prefetch_count: int = 10,
        api_token: str | None = None,
    ) -> None:
        """
        Initialize the worker.

        Args:
            orchestrator: Processing orchestrator instance
            rabbitmq_url: RabbitMQ connection URL (e.g., amqp://user:pass@localhost/)
            queue_name: Name of the queue to consume from
            api_base_url: Base URL of the KBrain API
            prefetch_count: Maximum messages to prefetch
            api_token: Optional API authentication token
        """
        self.orchestrator = orchestrator
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.api_base_url = api_base_url.rstrip("/")
        self.prefetch_count = prefetch_count
        self.api_token = api_token

        self._connection: AbstractConnection | None = None
        self._channel: AbstractChannel | None = None
        self._queue: AbstractQueue | None = None
        self._running = False
        self._consumer_tag: str | None = None

        self._stats: dict[str, int | datetime | None] = {
            "total_processed": 0,
            "total_deleted": 0,
            "total_failed": 0,
            "last_message": None,
            "started_at": None,
        }

    async def start(self) -> None:
        """Start the worker and begin consuming messages."""
        if self._running:
            logger.warning("Worker is already running")
            return

        self._running = True
        self._stats["started_at"] = datetime.utcnow()
        logger.info(f"Starting RabbitMQ worker - connecting to {self.rabbitmq_url}")

        try:
            # Connect to RabbitMQ
            self._connection = await connect_robust(self.rabbitmq_url)
            self._channel = await self._connection.channel()

            # Set prefetch count
            await self._channel.set_qos(prefetch_count=self.prefetch_count)

            # Declare queue (idempotent)
            self._queue = await self._channel.declare_queue(
                self.queue_name,
                durable=True,  # Persist queue across restarts
            )

            logger.info(
                f"Connected to RabbitMQ - consuming from queue '{self.queue_name}' "
                f"(prefetch: {self.prefetch_count})"
            )

            # Start consuming
            self._consumer_tag = await self._queue.consume(self._on_message)
            logger.info("Worker started - waiting for messages...")

        except Exception as e:
            logger.error(f"Failed to start worker: {e}", exc_info=True)
            self._running = False
            raise

    async def stop(self) -> None:
        """Stop the worker gracefully."""
        if not self._running:
            logger.warning("Worker is not running")
            return

        logger.info("Stopping RabbitMQ worker...")
        self._running = False

        try:
            # Cancel consumer
            if self._queue and self._consumer_tag:
                await self._queue.cancel(self._consumer_tag)

            # Close channel and connection
            if self._channel:
                await self._channel.close()

            if self._connection:
                await self._connection.close()

            logger.info("Worker stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping worker: {e}", exc_info=True)

    @property
    def is_running(self) -> bool:
        """Check if worker is running."""
        return self._running

    def get_stats(self) -> dict[str, Any]:
        """
        Get worker statistics.

        Returns:
            Dictionary with worker stats
        """
        uptime: float | None = None
        started_at = self._stats["started_at"]
        if started_at and isinstance(started_at, datetime):
            uptime = (datetime.utcnow() - started_at).total_seconds()

        return {
            **self._stats,
            "uptime_seconds": uptime,
            "running": self._running,
            "queue_name": self.queue_name,
            "orchestrator_stats": self.orchestrator.get_processor_stats(),
        }

    async def _on_message(self, message: Any) -> None:
        """
        Handle incoming RabbitMQ message.

        Args:
            message: RabbitMQ message
        """
        async with message.process():
            self._stats["last_message"] = datetime.utcnow()

            try:
                # Parse message
                body = message.body.decode()
                logger.debug(f"Received message: {body}")

                data = json.loads(body)
                queue_msg = QueueMessage(**data)

                logger.info(
                    f"Received {queue_msg.action.value.upper()} for document "
                    f"{queue_msg.document_id} from scope {queue_msg.scope_id}"
                )

                # Route based on action
                if queue_msg.action == QueueAction.DELETE:
                    await self._handle_delete(queue_msg)
                else:
                    await self._handle_add(queue_msg)

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in message: {e}")
                self._increment_stat("total_failed")
                # Ack message - invalid format, no point retrying

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                self._increment_stat("total_failed")
                # Message will be nacked and requeued by aio-pika
                raise

    async def _handle_add(self, queue_msg: QueueMessage) -> None:
        """
        Handle ADD action - process a new document.

        Args:
            queue_msg: Queue message with document info
        """
        # Fetch document details from API
        document = await self._fetch_document_details(str(queue_msg.document_id))

        if not document:
            logger.error(f"Document {queue_msg.document_id} not found in API")
            self._increment_stat("total_failed")
            return

        # Process document
        await self._process_document(document, queue_msg.retry_count)

    async def _handle_delete(self, queue_msg: QueueMessage) -> None:
        """
        Handle DELETE action - cleanup after document deletion.

        Args:
            queue_msg: Queue message with deletion info
        """
        logger.info(
            f"Handling deletion cleanup for document {queue_msg.document_id} "
            f"(file: {queue_msg.original_name or 'unknown'})"
        )

        try:
            # Run deletion cleanup through orchestrator
            results = await self.orchestrator.delete_document(queue_msg)

            # Check results
            if not results:
                logger.info(
                    f"No processors handled deletion for {queue_msg.document_id}"
                )
                self._increment_stat("total_deleted")
                return

            all_success = all(r.success for r in results.values())

            if all_success:
                self._increment_stat("total_deleted")
                logger.info(
                    f"Successfully cleaned up after deletion of {queue_msg.document_id}"
                )
            else:
                errors = {
                    k: v.error_message for k, v in results.items() if not v.success
                }
                self._increment_stat("total_failed")
                logger.error(
                    f"Some cleanup failed for {queue_msg.document_id}: {errors}"
                )

        except Exception as e:
            logger.error(
                f"Error during deletion cleanup for {queue_msg.document_id}: {e}",
                exc_info=True,
            )
            self._increment_stat("total_failed")

    def _increment_stat(self, stat_name: str) -> None:
        """Safely increment a stat counter."""
        value = self._stats.get(stat_name, 0)
        if isinstance(value, int):
            self._stats[stat_name] = value + 1

    async def _fetch_document_details(self, document_id: str) -> DocumentInfo | None:
        """
        Fetch document details from API.

        Args:
            document_id: Document ID

        Returns:
            DocumentInfo or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {}
                if self.api_token:
                    headers["Authorization"] = f"Bearer {self.api_token}"

                # Fetch document details
                response = await client.get(
                    f"{self.api_base_url}/v1/documents/{document_id}",
                    headers=headers,
                )

                if response.status_code == 404:
                    return None

                response.raise_for_status()
                doc_data = response.json()

                # Fetch scope details
                scope_response = await client.get(
                    f"{self.api_base_url}/v1/scopes/{doc_data['scope_id']}",
                    headers=headers,
                )
                scope_response.raise_for_status()
                scope_data = scope_response.json()

                # Add scope info and download URL
                doc_data["scope"] = scope_data
                doc_data["download_url"] = (
                    f"{self.api_base_url}/v1/documents/{document_id}/content"
                )

                return DocumentInfo(**doc_data)

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching document {document_id}: {e}")
            return None
        except Exception as e:
            logger.error("Error fetching document {}: {}", document_id, e, exc_info=True)
            return None

    async def _process_document(self, document: DocumentInfo, retry_count: int) -> None:
        """
        Process a single document.

        Args:
            document: Document to process
            retry_count: Current retry count
        """
        try:
            # Update status to 'processing'
            await self._update_document_status(
                str(document.id), ProcessingStatus.PROCESSING
            )

            # Process through orchestrator
            results = await self.orchestrator.process_document(
                document, attempt=retry_count + 1
            )

            # Check if all processors succeeded
            all_success = all(r.success for r in results.values())

            if all_success:
                # Build processing result from all processor outputs
                processing_result = {
                    processor_name: result.metadata
                    for processor_name, result in results.items()
                }

                # Update status to 'processed' with processing_result
                await self._update_document_status(
                    str(document.id),
                    ProcessingStatus.PROCESSED,
                    processing_result=processing_result,
                )
                self._increment_stat("total_processed")
                logger.info(f"Successfully processed document {document.id}")
            else:
                # Get error messages
                errors = {
                    k: v.error_message for k, v in results.items() if not v.success
                }
                error_msg = f"Processing failed: {errors}"

                # Update status to 'failed'
                await self._update_document_status(
                    str(document.id),
                    ProcessingStatus.FAILED,
                    error_message=error_msg,
                )
                self._increment_stat("total_failed")
                logger.error(f"Failed to process document {document.id}: {error_msg}")

        except Exception as e:
            logger.error(f"Error processing document {document.id}: {e}", exc_info=True)
            self._increment_stat("total_failed")

            try:
                await self._update_document_status(
                    str(document.id),
                    ProcessingStatus.FAILED,
                    error_message=str(e),
                )
            except Exception as update_error:
                logger.error(f"Failed to update document status: {update_error}")

    async def _update_document_status(
        self,
        document_id: str,
        status: ProcessingStatus,
        metadata: dict[str, Any] | None = None,
        processing_result: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> None:
        """
        Update document status via API.

        Args:
            document_id: Document ID
            status: New status
            metadata: Optional metadata to add
            processing_result: Optional processing result (extracted text, etc.)
            error_message: Optional error message
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Content-Type": "application/json"}
                if self.api_token:
                    headers["Authorization"] = f"Bearer {self.api_token}"

                payload: dict[str, Any] = {"status": status.value}

                if metadata:
                    payload["metadata"] = metadata

                if processing_result:
                    payload["processing_result"] = processing_result

                if error_message:
                    payload["error_message"] = error_message

                response = await client.patch(
                    f"{self.api_base_url}/v1/documents/{document_id}/status",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()

        except httpx.HTTPError as e:
            logger.error(f"HTTP error updating document {document_id} status: {e}")
            raise
        except Exception as e:
            logger.error(
                f"Error updating document {document_id} status: {e}",
                exc_info=True,
            )
            raise
