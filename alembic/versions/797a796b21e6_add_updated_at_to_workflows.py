"""add updated_at to workflows

Revision ID: 797a796b21e6
Revises: 9c3491d921ce
Create Date: 2026-06-20 09:06:47.548173

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '797a796b21e6'
down_revision: Union[str, Sequence[str], None] = '9c3491d921ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "workflows",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("workflows", "updated_at")
