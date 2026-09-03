"""add trigger snapshot columns to workflow_trigger_mapping

Revision ID: b1c2d3e4f5a6
Revises: a9b8c7d6e5f4
Create Date: 2026-08-26

Mirrors the action snapshot migration (a9b8c7d6e5f4) for the trigger side.

Copies TriggerDefinition fields onto WorkflowTriggerMapping so that:
  - Generation reads workspace-scoped trigger snapshots, never TriggerDefinition.
  - Workspace-level overrides can be applied without touching the global catalog.

New columns (all nullable — backfilled below for already-mapped rows):
  trigger_name        VARCHAR  — TriggerDefinition.name (DAG trigger key)
  display_name        VARCHAR  — TriggerDefinition.display_name
  catalog_description TEXT     — TriggerDefinition.description
  aliases             JSONB    — TriggerDefinition.aliases
  workflow_type       VARCHAR  — TriggerDefinition.workflow_type

Note: no execution_template, input_schema, output_schema —
triggers are not executed, only used to start workflows.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "b1c2d3e4f5a6"
down_revision = "a9b8c7d6e5f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workflow_trigger_mapping",
        sa.Column("trigger_name", sa.String(), nullable=True),
    )
    op.add_column(
        "workflow_trigger_mapping",
        sa.Column("display_name", sa.String(), nullable=True),
    )
    op.add_column(
        "workflow_trigger_mapping",
        sa.Column("catalog_description", sa.Text(), nullable=True),
    )
    op.add_column(
        "workflow_trigger_mapping",
        sa.Column("aliases", JSONB(), nullable=True),
    )
    op.add_column(
        "workflow_trigger_mapping",
        sa.Column("workflow_type", sa.String(), nullable=True),
    )

    # Backfill from trigger_definitions for already-mapped rows
    op.execute("""
        UPDATE workflow_trigger_mapping wtm
        SET
            trigger_name        = td.name,
            display_name        = td.display_name,
            catalog_description = td.description,
            aliases             = td.aliases,
            workflow_type       = td.workflow_type
        FROM trigger_definitions td
        WHERE wtm.matched_trigger_definition_id = td.id
          AND wtm.matched_trigger_definition_id IS NOT NULL
    """)


def downgrade() -> None:
    op.drop_column("workflow_trigger_mapping", "workflow_type")
    op.drop_column("workflow_trigger_mapping", "aliases")
    op.drop_column("workflow_trigger_mapping", "catalog_description")
    op.drop_column("workflow_trigger_mapping", "display_name")
    op.drop_column("workflow_trigger_mapping", "trigger_name")
