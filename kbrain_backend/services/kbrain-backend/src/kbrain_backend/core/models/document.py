"""Document database model."""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import String, Text, BigInteger, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kbrain_backend.core.models.scope import Scope
from kbrain_backend.core.models.tag import Tag
from kbrain_backend.database.connection import Base


class Document(Base):
    """Document model for uploaded files."""

    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    scope_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scopes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    original_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_extension: Mapped[str] = mapped_column(String(50), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(50), nullable=False)
    checksum_md5: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    checksum_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="added", index=True
    )
    upload_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, index=True
    )
    processing_started: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Additional metadata
    doc_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    scope: Mapped[Scope] = relationship("Scope", back_populates="documents")
    tags: Mapped[List[Tag]] = relationship(
        "Tag", secondary="document_tags", back_populates="documents"
    )

    def __repr__(self) -> str:
        return (
            f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"
        )
