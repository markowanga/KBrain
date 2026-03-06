"""KBrain Processor Orchestrator - Document processing framework."""

from kbrain_processor_orchestrator.base import BaseProcessor
from kbrain_processor_orchestrator.models import (
    DocumentInfo,
    ProcessingContext,
    ProcessingResult,
    ProcessingStatus,
    QueueAction,
    QueueMessage,
    Scope,
    Tag,
)
from kbrain_processor_orchestrator.orchestrator import ProcessingOrchestrator
from kbrain_processor_orchestrator.processors import (
    DocumentProcessor,
    ImageProcessor,
    TextProcessor,
)
from kbrain_processor_orchestrator.publisher import QueuePublisher
from kbrain_processor_orchestrator.ragflow_client import RAGFlowClient, RAGFlowDocumentStatus
from kbrain_processor_orchestrator.worker import ProcessingWorker

__all__ = [
    # Base
    "BaseProcessor",
    # Models
    "DocumentInfo",
    "ProcessingContext",
    "ProcessingResult",
    "ProcessingStatus",
    "QueueAction",
    "QueueMessage",
    "Scope",
    "Tag",
    # Orchestrator
    "ProcessingOrchestrator",
    # Worker
    "ProcessingWorker",
    # Publisher
    "QueuePublisher",
    # RAGFlow
    "RAGFlowClient",
    "RAGFlowDocumentStatus",
    # Processors
    "ImageProcessor",
    "TextProcessor",
    "DocumentProcessor",
]
