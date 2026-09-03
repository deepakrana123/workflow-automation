"""add workflow_chains table

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-08-26

Stores detected and accepted connections between workflows in a workspace.
A chain means: when workflow A reaches a terminal step, workflow B is
dispatched (either unconditionally or under a condition).

Chain lifecycle:
  suggested → auto-detected, awaits review
  accepted  → user confirmed; on_*_dispatch written into source step config
  rejected  → user dismissed
  auto      → system-applied for high-confidence name_match chains
"""

import sqlalchemy as sa
from alembic import op

revision = "d3e4f5a6b7c8"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow_chains",
        sa.Column("id",                 sa.Integer(),     primary_key=True),
        sa.Column("workspace_id",       sa.Integer(),     sa.ForeignKey("workspaces.id"),  nullable=False),
        sa.Column("source_workflow_id", sa.Integer(),     sa.ForeignKey("workflows.id"),   nullable=False),
        sa.Column("source_step_id",     sa.String(),      nullable=False),
        sa.Column("source_action",      sa.String(),      nullable=False),
        sa.Column("target_workflow_id", sa.Integer(),     sa.ForeignKey("workflows.id"),   nullable=False),
        sa.Column("target_trigger",     sa.String(),      nullable=False),
        sa.Column("match_type",         sa.Enum("name_match", "fts_match", "rule_mention",
                                                name="chainmatchtype"), nullable=False),
        sa.Column("confidence",         sa.Float(),       nullable=False, server_default="1.0"),
        sa.Column("status",             sa.Enum("suggested", "accepted", "rejected", "auto",
                                                name="chainstatus"),
                                        nullable=False, server_default="suggested"),
        sa.Column("note",               sa.Text(),        nullable=True),
        sa.Column("detected_at",        sa.DateTime(timezone=True),
                                        server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at",         sa.DateTime(timezone=True),
                                        server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_workflow_chains_workspace_id",       "workflow_chains", ["workspace_id"])
    op.create_index("ix_workflow_chains_source_workflow_id", "workflow_chains", ["source_workflow_id"])
    op.create_index("ix_workflow_chains_target_workflow_id", "workflow_chains", ["target_workflow_id"])


def downgrade() -> None:
    op.drop_index("ix_workflow_chains_target_workflow_id", table_name="workflow_chains")
    op.drop_index("ix_workflow_chains_source_workflow_id", table_name="workflow_chains")
    op.drop_index("ix_workflow_chains_workspace_id",       table_name="workflow_chains")
    op.drop_table("workflow_chains")
    op.execute("DROP TYPE IF EXISTS chainmatchtype")
    op.execute("DROP TYPE IF EXISTS chainstatus")
