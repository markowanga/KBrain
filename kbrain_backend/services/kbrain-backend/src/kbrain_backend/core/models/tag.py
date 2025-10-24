"""Tag database model."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import String, Text, ForeignKey, JSON, Table, Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kbrain_backend.core.models.document import Document
from kbrain_backend.core.models.scope import Scope
from kbrain_backend.database.connection import Base


# Association table for many-to-many relationship between documents and tags
document_tags = Table(
    "document_tags",
    Base.metadata,
    Column(
        "document_id",
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", TIMESTAMP(timezone=True), default=datetime.utcnow),
)


class Tag(Base):
    """Tag model for categorizing and processing documents."""

    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    scope_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scopes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(
        String(7), nullable=True
    )  # Hex color code
    meta: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # Processing instructions
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    scope: Mapped[Scope] = relationship("Scope", back_populates="tags")
    documents: Mapped[List[Document]] = relationship(
        "Document", secondary=document_tags, back_populates="tags"
    )

    # Unique constraint: tag name must be unique within a scope
    __table_args__ = (UniqueConstraint("scope_id", "name", name="uq_scope_tag_name"),)

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name={self.name}, scope_id={self.scope_id})>"
