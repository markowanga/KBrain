"""Application configuration settings."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "KBrain API"
    app_version: str = "1.0.0"
    api_v1_prefix: str = "/v1"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://kbrain:kbrain@localhost:5432/kbrain"
    database_pool_min: int = 2
    database_pool_max: int = 10

    # CORS
    cors_origins: list[str] = ["http://localhost:5174", "http://localhost:3000"]

    # Storage
    storage_backend: str = "local"  # "local", "s3", "azure"
    storage_root: str = "storage_data"

    # AWS S3
    aws_region: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    s3_bucket: Optional[str] = None

    # Azure Blob
    azure_storage_account: Optional[str] = None
    azure_storage_key: Optional[str] = None
    azure_storage_container: Optional[str] = None

    # Upload limits
    max_file_size: int = 104857600  # 100MB in bytes

    # Logging
    log_level: str = "INFO"

    # Document Processing Orchestrator
    processing_enabled: bool = True
    processing_max_retries: int = 3
    processing_api_token: Optional[str] = None

    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@localhost/"
    rabbitmq_queue_name: str = "document_processing"
    rabbitmq_prefetch_count: int = 10

    # OpenAI (for document/image processing)
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1/chat/completions"
    openai_model: str = "gpt-5.2-2025-12-11"

    # XLSX Medication Processor
    xlsx_medication_service_url: Optional[str] = None

    # RAGFlow
    ragflow_url: Optional[str] = None
    ragflow_api_key: Optional[str] = None
    ragflow_dataset_id: Optional[str] = None
    ragflow_wait_for_parsing: bool = True
    ragflow_max_wait: float = 300.0

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )


# Global settings instance
settings = Settings()
