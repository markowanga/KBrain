"""Document processors for different file types."""

from kbrain_processor_orchestrator.processors.document_processor import (
    DocumentProcessor,
)
from kbrain_processor_orchestrator.processors.image_processor import ImageProcessor
from kbrain_processor_orchestrator.processors.text_processor import TextProcessor
from kbrain_processor_orchestrator.processors.xlsx_medication_processor import (
    XlsxMedicationProcessor,
)

__all__ = [
    "ImageProcessor",
    "TextProcessor",
    "DocumentProcessor",
    "XlsxMedicationProcessor",
]