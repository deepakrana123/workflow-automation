"""add applicable_rules and responsible_actors to action and trigger mapping tables

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-08-26

Adds two nullable JSONB columns to both workflow_action_mapping and
workflow_trigger_mapping:

  applicable_rules     — business rules from the BRD that specifically apply
                         to this action/trigger (not all workspace rules)
  responsible_actors   — actors responsible for or involved in this action/trigger

Written at BRD ingestion time by WorkflowRepository.save() from the LLM
extraction response. No backfill — existing rows get NULL, which is correct.
Workspace-level rules remain available via WorkflowBusinessRule (unchanged).
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── workflow_action_mapping ───────────────────────────────────────────────
    op.add_column(
        "workflow_action_mapping",
        sa.Column("applicable_rules", JSONB(), nullable=True),
    )
    op.add_column(
        "workflow_action_mapping",
        sa.Column("responsible_actors", JSONB(), nullable=True),
    )

    # ── workflow_trigger_mapping ──────────────────────────────────────────────
    op.add_column(
        "workflow_trigger_mapping",
        sa.Column("applicable_rules", JSONB(), nullable=True),
    )
    op.add_column(
        "workflow_trigger_mapping",
        sa.Column("responsible_actors", JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workflow_trigger_mapping", "responsible_actors")
    op.drop_column("workflow_trigger_mapping", "applicable_rules")
    op.drop_column("workflow_action_mapping", "responsible_actors")
    op.drop_column("workflow_action_mapping", "applicable_rules")
