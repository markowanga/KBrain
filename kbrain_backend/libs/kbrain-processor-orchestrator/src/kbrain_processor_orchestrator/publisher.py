"""RabbitMQ message publisher for queueing documents."""

from uuid import UUID

from aio_pika import DeliveryMode, Message, connect_robust
from aio_pika.abc import AbstractChannel, AbstractConnection
from loguru import logger

from kbrain_processor_orchestrator.models import QueueAction, QueueMessage


class QueuePublisher:
    """
    RabbitMQ publisher for sending document processing messages.

    Publishes lightweight messages (just document_id and scope_id) to the queue.
    Worker will fetch full details from API.
    """

    def __init__(self, rabbitmq_url: str, queue_name: str) -> None:
        """
        Initialize the publisher.

        Args:
            rabbitmq_url: RabbitMQ connection URL
            queue_name: Name of the queue to publish to
        """
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self._connection: AbstractConnection | None = None
        self._channel: AbstractChannel | None = None

    async def connect(self) -> None:
        """Establish connection to RabbitMQ."""
        if self._connection and not self._connection.is_closed:
            return

        logger.info(f"Connecting to RabbitMQ: {self.rabbitmq_url}")
        self._connection = await connect_robust(self.rabbitmq_url)
        self._channel = await self._connection.channel()

        # Declare queue (idempotent)
        await self._channel.declare_queue(self.queue_name, durable=True)
        logger.info(f"Connected to RabbitMQ - queue: {self.queue_name}")

    async def disconnect(self) -> None:
        """Close connection to RabbitMQ."""
        if self._channel:
            await self._channel.close()

        if self._connection:
            await self._connection.close()

        logger.info("Disconnected from RabbitMQ")

    async def publish_document(
        self,
        document_id: UUID | str,
        scope_id: UUID | str,
        retry_count: int = 0,
    ) -> None:
        """
        Publish a document for processing (ADD action).

        Args:
            document_id: Document ID to process
            scope_id: Scope ID
            retry_count: Current retry count (default: 0)
        """
        queue_msg = QueueMessage(
            document_id=UUID(str(document_id)),
            scope_id=UUID(str(scope_id)),
            action=QueueAction.ADD,
            retry_count=retry_count,
        )
        await self._publish(queue_msg)
        logger.info(f"Published ADD for document {document_id}")

    async def publish_delete(
        self,
        document_id: UUID | str,
        scope_id: UUID | str,
        storage_path: str | None = None,
        file_extension: str | None = None,
        original_name: str | None = None,
        ragflow_document_id: str | None = None,
    ) -> None:
        """
        Publish a document deletion message.

        Args:
            document_id: Document ID being deleted
            scope_id: Scope ID
            storage_path: Storage path of the document (for cleanup)
            file_extension: File extension (to route to correct processor)
            original_name: Original filename (for logging)
            ragflow_document_id: RAGFlow document ID (for cleanup from RAGFlow)
        """
        queue_msg = QueueMessage(
            document_id=UUID(str(document_id)),
            scope_id=UUID(str(scope_id)),
            action=QueueAction.DELETE,
            storage_path=storage_path,
            file_extension=file_extension,
            original_name=original_name,
            ragflow_document_id=ragflow_document_id,
        )
        await self._publish(queue_msg)
        logger.info(f"Published DELETE for document {document_id}")

    async def _publish(self, queue_msg: QueueMessage) -> None:
        """
        Publish a message to the queue.

        Args:
            queue_msg: Message to publish
        """
        await self.connect()

        # Serialize to JSON
        body = queue_msg.model_dump_json()

        # Create RabbitMQ message
        message = Message(
            body=body.encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type="application/json",
        )

        # Publish to queue
        if self._channel:
            await self._channel.default_exchange.publish(
                message, routing_key=self.queue_name
            )
