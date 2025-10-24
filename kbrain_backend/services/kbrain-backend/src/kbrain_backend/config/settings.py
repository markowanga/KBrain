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
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
