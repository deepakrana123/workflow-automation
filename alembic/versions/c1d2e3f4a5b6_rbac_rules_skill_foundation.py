"""rbac, rules, skill foundation

Adds workspace hierarchy, structured business rules, role assignments,
human task role fields, audit log extensions, and skill file columns.

All changes are backward-compatible:
  - existing workspaces become level='branch', parent_id=NULL
  - existing audit_logs rows get NULL for new columns
  - existing human_tasks rows get NULL for new JSONB columns
  - Workflow.skill_file_id/path start NULL

Revision ID: c1d2e3f4a5b6
Revises: a2b3c4d5e6f7
Create Date: 2026-08-19
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Workspace hierarchy ────────────────────────────────────────────────
    # Add level + parent_id to workspaces.
    # Existing rows backfilled to level='branch', parent_id=NULL (safe default).
    op.add_column(
        "workspaces",
        sa.Column("level", sa.String(20), nullable=True),
    )
    op.add_column(
        "workspaces",
        sa.Column("parent_id", sa.Integer(), nullable=True),
    )
    # Backfill existing workspaces as branch level
    op.execute("UPDATE workspaces SET level = 'branch' WHERE level IS NULL")
    # Make level non-nullable after backfill
    op.alter_column("workspaces", "level", nullable=False)
    # FK for parent_id (self-referential, nullable — global nodes have NULL)
    op.create_foreign_key(
        "fk_workspaces_parent_id",
        "workspaces",
        "workspaces",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_workspaces_level", "workspaces", ["level"])
    op.create_index("ix_workspaces_parent_id", "workspaces", ["parent_id"])

    # ── 2. Structured business rule definitions ───────────────────────────────
    op.create_table(
        "business_rule_definitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "scope_workspace_id",
            sa.Integer(),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_workflow_knowledge_id",
            sa.Integer(),
            sa.ForeignKey("workflow_knowledge.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # The WorkflowContext key this rule reads (e.g. "loan_amount")
        sa.Column("field", sa.String(255), nullable=True),
        # Operator — one of: ==, !=, >, >=, <, <=, in, not_in
        sa.Column("op", sa.String(20), nullable=True),
        # Threshold value — numeric, string, or list
        sa.Column("value", postgresql.JSONB(), nullable=True),
        # Original BRD sentence — used in skill.md
        sa.Column("description", sa.Text(), nullable=False),
        # Roles extracted from the actor in the same BRD sentence
        sa.Column("allowed_roles", postgresql.JSONB(), nullable=True),
        # If True, lower-level workspaces cannot narrow this rule further
        sa.Column("locked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_brd_scope_workspace_id",
        "business_rule_definitions",
        ["scope_workspace_id"],
    )
    op.create_index(
        "ix_brd_field_active",
        "business_rule_definitions",
        ["field", "active"],
    )

    # ── 3. Role assignments ───────────────────────────────────────────────────
    op.create_table(
        "role_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        # NULL until HR/admin maps a real user to this role shape
        sa.Column("user_id", sa.String(255), nullable=True),
        # One of: global_admin, region_manager, zone_manager, branch_manager,
        #         branch_officer, auditor, read_only
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column(
            "workspace_id",
            sa.Integer(),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Which structured rule caused this role shape to be extracted
        sa.Column(
            "source_rule_id",
            sa.Integer(),
            sa.ForeignKey("business_rule_definitions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_ra_user_id", "role_assignments", ["user_id"])
    op.create_index("ix_ra_workspace_id", "role_assignments", ["workspace_id"])
    op.create_index("ix_ra_role", "role_assignments", ["role"])
    # Unique: one role per user per workspace
    op.create_unique_constraint(
        "uq_role_assignment_user_workspace",
        "role_assignments",
        ["user_id", "workspace_id"],
    )

    # ── 4. HumanTask role + escalation fields ─────────────────────────────────
    op.add_column(
        "human_tasks",
        sa.Column("allowed_roles", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "human_tasks",
        sa.Column("escalation_policy", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "human_tasks",
        sa.Column(
            "escalation_level",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    # ── 5. AuditLog — user_id + workspace_id ─────────────────────────────────
    op.add_column(
        "audit_logs",
        sa.Column("user_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "audit_logs",
        sa.Column(
            "workspace_id",
            sa.Integer(),
            sa.ForeignKey("workspaces.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_workspace_id", "audit_logs", ["workspace_id"])

    # ── 6. Workflow — skill file reference ───────────────────────────────────
    op.add_column(
        "workflows",
        sa.Column("skill_file_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "workflows",
        sa.Column("skill_file_path", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    # Workflow skill file
    op.drop_column("workflows", "skill_file_path")
    op.drop_column("workflows", "skill_file_id")

    # AuditLog extensions
    op.drop_index("ix_audit_logs_workspace_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_column("audit_logs", "workspace_id")
    op.drop_column("audit_logs", "user_id")

    # HumanTask role fields
    op.drop_column("human_tasks", "escalation_level")
    op.drop_column("human_tasks", "escalation_policy")
    op.drop_column("human_tasks", "allowed_roles")

    # Role assignments
    op.drop_constraint("uq_role_assignment_user_workspace", "role_assignments", type_="unique")
    op.drop_index("ix_ra_role", table_name="role_assignments")
    op.drop_index("ix_ra_workspace_id", table_name="role_assignments")
    op.drop_index("ix_ra_user_id", table_name="role_assignments")
    op.drop_table("role_assignments")

    # Business rule definitions
    op.drop_index("ix_brd_field_active", table_name="business_rule_definitions")
    op.drop_index("ix_brd_scope_workspace_id", table_name="business_rule_definitions")
    op.drop_table("business_rule_definitions")

    # Workspace hierarchy
    op.drop_index("ix_workspaces_parent_id", table_name="workspaces")
    op.drop_index("ix_workspaces_level", table_name="workspaces")
    op.drop_constraint("fk_workspaces_parent_id", "workspaces", type_="foreignkey")
    op.drop_column("workspaces", "parent_id")
    op.drop_column("workspaces", "level")
