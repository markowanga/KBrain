"""Scope database model."""
from datetime import datetime
from typing import List
from uuid import uuid4

from sqlalchemy import Boolean, String, Text, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kbrain_backend.database.connection import Base


class Scope(Base):
    """Scope model for organizing documents."""

    __tablename__ = "scopes"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    allowed_extensions: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(50), default="local")
    storage_config: Mapped[dict] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="scope", cascade="all, delete-orphan"
    )
    tags: Mapped[List["Tag"]] = relationship(
        "Tag", back_populates="scope", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Scope(id={self.id}, name={self.name})>"
