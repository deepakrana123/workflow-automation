"""add human_tasks table

Revision ID: e1f2a3b4c5d6
Revises: dfeffbf5ac0f
Create Date: 2026-08-07

Adds the human_tasks table backing the Human Executor (human_task steps).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "dfeffbf5ac0f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "human_tasks",
        sa.Column("id", sa.BigInteger(), primary_key=True, index=True),
        sa.Column(
            "workflow_execution_id",
            sa.BigInteger(),
            sa.ForeignKey("workflow_executions.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "step_execution_id",
            sa.BigInteger(),
            sa.ForeignKey("execution_steps.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("step_id", sa.String(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING", index=True),
        sa.Column("decision", sa.String(length=10), nullable=True),
        sa.Column("on_timeout", sa.String(length=10), nullable=True),
        sa.Column("timeout_at", sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column("resolved_by", sa.String(length=20), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("human_tasks")
