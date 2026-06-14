"""add generation_log table

Revision ID: 64f3b55ea484
Revises: 8a36a17fb69c
Create Date: 2026-06-14 21:35:11.954017

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64f3b55ea484'
down_revision: Union[str, Sequence[str], None] = '8a36a17fb69c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
