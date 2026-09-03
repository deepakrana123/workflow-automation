"""add action snapshot columns to workflow_action_mapping

Revision ID: a9b8c7d6e5f4
Revises: f432bf45f607
Create Date: 2026-08-26

Copies ActionDefinition fields onto WorkflowActionMapping so that:
  - Runtime reads workspace-scoped snapshots instead of the global catalog.
  - Workspace-level overrides can be applied without touching ActionDefinition.
  - ActionDefinition remains the global catalog (untouched at runtime).

New columns (all nullable — existing rows backfilled below):
  action_name         VARCHAR  — ActionDefinition.name (Python handler key)
  display_name        VARCHAR  — ActionDefinition.display_name
  catalog_description TEXT     — ActionDefinition.description
  aliases             JSONB    — ActionDefinition.aliases
  workflow_type       VARCHAR  — ActionDefinition.workflow_type
  input_schema        JSONB    — ActionDefinition.input_schema
  output_schema       JSONB    — ActionDefinition.output_schema
  execution_template  JSONB    — ActionDefinition.execution_template
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = "a9b8c7d6e5f4"
down_revision = "f432bf45f607"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Add columns ───────────────────────────────────────────────────────────
    op.add_column(
        "workflow_action_mapping",
        sa.Column("action_name", sa.String(), nullable=True),
    )
    op.add_column(
        "workflow_action_mapping",
        sa.Column("display_name", sa.String(), nullable=True),
    )
    op.add_column(
        "workflow_action_mapping",
        sa.Column("catalog_description", sa.Text(), nullable=True),
    )
    op.add_column(
        "workflow_action_mapping",
        sa.Column("aliases", JSONB(), nullable=True),
    )
    op.add_column(
        "workflow_action_mapping",
        sa.Column("workflow_type", sa.String(), nullable=True),
    )
    op.add_column(
        "workflow_action_mapping",
        sa.Column("input_schema", JSONB(), nullable=True),
    )
    op.add_column(
        "workflow_action_mapping",
        sa.Column("output_schema", JSONB(), nullable=True),
    )
    op.add_column(
        "workflow_action_mapping",
        sa.Column("execution_template", JSONB(), nullable=True),
    )

    # ── Backfill from action_definitions for already-mapped rows ─────────────
    op.execute("""
        UPDATE workflow_action_mapping wam
        SET
            action_name         = ad.name,
            display_name        = ad.display_name,
            catalog_description = ad.description,
            aliases             = ad.aliases,
            workflow_type       = ad.workflow_type,
            input_schema        = ad.input_schema,
            output_schema       = ad.output_schema,
            execution_template  = ad.execution_template
        FROM action_definitions ad
        WHERE wam.matched_action_definition_id = ad.id
          AND wam.matched_action_definition_id IS NOT NULL
    """)


def downgrade() -> None:
    op.drop_column("workflow_action_mapping", "execution_template")
    op.drop_column("workflow_action_mapping", "output_schema")
    op.drop_column("workflow_action_mapping", "input_schema")
    op.drop_column("workflow_action_mapping", "workflow_type")
    op.drop_column("workflow_action_mapping", "aliases")
    op.drop_column("workflow_action_mapping", "catalog_description")
    op.drop_column("workflow_action_mapping", "display_name")
    op.drop_column("workflow_action_mapping", "action_name")
