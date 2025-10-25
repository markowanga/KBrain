"""Remove is_active column from scopes table

Revision ID: 2cd7dc1e286b
Revises: rename_tag_metadata
Create Date: 2025-10-25 08:56:31.763177

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2cd7dc1e286b'
down_revision: Union[str, Sequence[str], None] = 'rename_tag_metadata'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop index first (if it exists)
    op.drop_index('ix_scopes_is_active', table_name='scopes', if_exists=True)

    # Drop is_active column from scopes table
    op.drop_column('scopes', 'is_active')


def downgrade() -> None:
    """Downgrade schema."""
    # Add is_active column back
    op.add_column('scopes',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true')
    )

    # Recreate index
    op.create_index('ix_scopes_is_active', 'scopes', ['is_active'])
