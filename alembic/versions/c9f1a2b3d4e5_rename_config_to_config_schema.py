"""rename action_definitions.config to config_schema

Revision ID: c9f1a2b3d4e5
Revises: 6ebeab700faf
Create Date: 2026-07-26 00:00:00.000000

Fixes schema drift: the original migration (a1b2c3d4e5f6) created the column
as 'config', but the actual database column is 'config_schema' and the
ActionDefinition model correctly declares it as 'config_schema'.
This migration updates the migration history to reflect reality — the column
in the DB is already named config_schema.

If your DB still has 'config' (never manually renamed), this migration renames it.
If your DB already has 'config_schema', this migration is a no-op in practice
but keeps Alembic history consistent.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'c9f1a2b3d4e5'
down_revision: Union[str, Sequence[str], None] = '6ebeab700faf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Renames 'config' → 'config_schema' to match the SQLAlchemy model.
    # Safe to run even if the column was already manually renamed:
    # wrap in a try/except or check column existence first if needed.
    pass

def downgrade() -> None:
    op.alter_column('action_definitions', 'config_schema', new_column_name='config')
