"""add embedding column to workflow_action_mapping

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-08-26

Adds a 384-dim pgvector embedding to workflow_action_mapping.

Purpose:
  Workspace owners can manually resolve UNMAPPED BRD actions by filling in
  action_name, display_name, execution_template etc. directly on the mapping row
  — without creating a global ActionDefinition. The embedding is stored here so
  WorkspaceCatalogMatcher can include this action in vector + FTS matching during
  generation. ActionDefinition is never touched for workspace-local actions.
"""

from alembic import op

revision    = "e4f5a6b7c8d9"
down_revision = "d3e4f5a6b7c8"
branch_labels = None
depends_on  = None


def upgrade() -> None:
    # vector type is provided by the pgvector extension (already enabled)
    op.execute(
        "ALTER TABLE workflow_action_mapping "
        "ADD COLUMN IF NOT EXISTS embedding vector(384)"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE workflow_action_mapping "
        "DROP COLUMN IF EXISTS embedding"
    )
