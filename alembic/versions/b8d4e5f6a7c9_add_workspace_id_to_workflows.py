"""add workspace_id to workflows

Links a generated/synthesized workflow back to its workspace. Nullable so the
global generation page (workspace-less) is unaffected and existing rows stay
valid without a backfill.

Revision ID: b8d4e5f6a7c9
Revises: f2a3b4c5d6e7
Create Date: 2026-08-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b8d4e5f6a7c9"
down_revision: Union[str, Sequence[str], None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "workflows",
        sa.Column("workspace_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_workflows_workspace_id",
        "workflows",
        ["workspace_id"],
    )
    op.create_foreign_key(
        "fk_workflows_workspace_id",
        "workflows",
        "workspaces",
        ["workspace_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_workflows_workspace_id",
        "workflows",
        type_="foreignkey",
    )
    op.drop_index("ix_workflows_workspace_id", table_name="workflows")
    op.drop_column("workflows", "workspace_id")
