"""merge workflow and observability heads

Revision ID: f432bf45f607
Revises: b8d4e5f6a7c9, f7a8b9c0d1e2
Create Date: 2026-08-16 09:45:31.733473

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f432bf45f607'
down_revision: Union[str, Sequence[str], None] = ('b8d4e5f6a7c9', 'f7a8b9c0d1e2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
