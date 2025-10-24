"""Rename tag metadata column to meta

Revision ID: rename_tag_metadata
Revises: add_tags_feature
Create Date: 2025-10-24 22:50:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "rename_tag_metadata"
down_revision: Union[str, Sequence[str], None] = "add_tags_feature"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename metadata column to meta in tags table."""
    op.alter_column("tags", "metadata", new_column_name="meta")


def downgrade() -> None:
    """Rename meta column back to metadata in tags table."""
    op.alter_column("tags", "meta", new_column_name="metadata")
