"""merge heads

Revision ID: 8a36a17fb69c
Revises: 23a7ad18f738, a1b2c3d4e5f6, add_distributed_tracing
Create Date: 2026-06-14 21:20:47.235287

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a36a17fb69c'
down_revision: Union[str, Sequence[str], None] = ('23a7ad18f738', 'a1b2c3d4e5f6', 'add_distributed_tracing')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
