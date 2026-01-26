# KBrain Processor Orchestrator

Document processing orchestrator with RabbitMQ worker and pluggable processors.

## Features

- **RabbitMQ Integration**: Lightweight queue messages (only document_id + scope_id)
- **Pluggable Processors**: Easy-to-implement base class for custom processors
- **Async Processing**: Fully asynchronous with aio-pika
- **Retry Logic**: Built-in retry mechanism
- **Processing Hooks**: Success/failure callbacks
- **Statistics**: Track processed documents and failures

## Architecture

### Components

1. **BaseProcessor**: Abstract class for implementing processors
2. **ProcessingOrchestrator**: Manages processor registration and execution
3. **ProcessingWorker**: RabbitMQ consumer that processes documents
4. **QueuePublisher**: Publishes lightweight messages to RabbitMQ

### Message Flow

```
Upload Document
    |
    v
POST /api/v1/processing/queue/{document_id}
    |
    v
Publish to RabbitMQ (document_id + scope_id)
    |
    v
Worker consumes message
    |
    v
Fetch full document from API
    |
    v
Process through orchestrator
    |
    v
Update document status
```

## Usage

### Create Custom Processor

```python
from kbrain_processor_orchestrator import BaseProcessor, DocumentInfo, ProcessingResult

class PDFProcessor(BaseProcessor):
    @property
    def name(self) -> str:
        return "pdf_processor"

    async def can_process(self, document: DocumentInfo) -> bool:
        return document.file_extension.lower() == "pdf"

    async def process(self, document: DocumentInfo) -> ProcessingResult:
        # Download from document.download_url
        # Process document
        # Return result

        return ProcessingResult(
            success=True,
            metadata={"extracted": True}
        )
```

### Register Processor

In `main.py`:

```python
orchestrator = ProcessingOrchestrator(max_retries=3)
orchestrator.register_processor(PDFProcessor())
```

## API Endpoints

### Queue Document for Processing

```bash
# Queue by document ID
POST /api/v1/processing/queue/{document_id}

# Queue with explicit scope
POST /api/v1/processing/queue
{
  "document_id": "uuid",
  "scope_id": "uuid"
}
```

### Get Statistics

```bash
GET /api/v1/processing/stats
```

### Control Worker

```bash
POST /api/v1/processing/worker/start
POST /api/v1/processing/worker/stop
```

## Configuration

```bash
# Enable/disable processing
PROCESSING_ENABLED=true

# RabbitMQ connection
RABBITMQ_URL=amqp://guest:guest@localhost/
RABBITMQ_QUEUE_NAME=document_processing
RABBITMQ_PREFETCH_COUNT=10

# Processing
PROCESSING_MAX_RETRIES=3
PROCESSING_API_TOKEN=optional-token
```

## Development

### Install Dependencies

```bash
uv sync
```

### Run with Docker Compose

RabbitMQ can be added to docker-compose.yml:

```yaml
rabbitmq:
  image: rabbitmq:3-management
  ports:
    - "5672:5672"
    - "15672:15672"
  environment:
    RABBITMQ_DEFAULT_USER: guest
    RABBITMQ_DEFAULT_PASS: guest
```

## License

MIT
