"""Add processing_result column to documents table

Revision ID: add_processing_result
Revises: 2cd7dc1e286b
Create Date: 2025-01-26 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision: str = "add_processing_result"
down_revision: Union[str, Sequence[str], None] = "2cd7dc1e286b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add processing_result JSON column to documents table."""
    op.add_column(
        "documents",
        sa.Column("processing_result", JSON, nullable=True),
    )


def downgrade() -> None:
    """Remove processing_result column from documents table."""
    op.drop_column("documents", "processing_result")
