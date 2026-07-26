"""model fixes: table rename, status enum, unique constraint, timestamp columns

Revision ID: d1e2f3a4b5c6
Revises: c9f1a2b3d4e5
Create Date: 2026-07-26 00:00:00.000000

Changes:
  1. Rename workflow_trigger_mappings → workflow_trigger_mapping  (consistent singular naming)
  2. Create mappingstatus enum type
  3. Add status column to workflow_action_mapping (varchar → enum)
  4. Add status column to workflow_trigger_mapping
  5. Add UniqueConstraint on action_configurations(workflow_knowledge_id, action_definition_id, version)
  6. Add created_at / updated_at to workspace_integrations
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "fd12c88c1c06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Enum values — must match MappingStatus in workflow_action_mapping.py
_MAPPING_STATUS_VALUES = ("PENDING", "MAPPED", "UNMAPPED", "FAILED")
_ENUM_NAME = "mappingstatus"


def upgrade() -> None:
    # ── 1. Create the mappingstatus enum type ────────────────────────────────
    mapping_status = postgresql.ENUM(
        *_MAPPING_STATUS_VALUES,
        name=_ENUM_NAME,
        create_type=True,
    )
    mapping_status.create(op.get_bind(), checkfirst=True)

    # ── 2. Migrate status column on workflow_action_mapping ──────────────────
    # Old column was String; replace with the enum type.
    op.drop_column("workflow_action_mapping", "status")
    op.add_column(
        "workflow_action_mapping",
        sa.Column(
            "status",
            sa.Enum(*_MAPPING_STATUS_VALUES, name=_ENUM_NAME, create_type=False),
            nullable=False,
            server_default="PENDING",
        ),
    )

    # ── 3. Rename workflow_trigger_mappings → workflow_trigger_mapping ────────
    op.rename_table("workflow_trigger_mappings", "workflow_trigger_mapping")

    # ── 4. Add status column to workflow_trigger_mapping ─────────────────────
    op.add_column(
        "workflow_trigger_mapping",
        sa.Column(
            "status",
            sa.Enum(*_MAPPING_STATUS_VALUES, name=_ENUM_NAME, create_type=False),
            nullable=False,
            server_default="PENDING",
        ),
    )

    # ── 5. UniqueConstraint on action_configurations ─────────────────────────
    op.create_unique_constraint(
        "uq_action_configuration_workflow_action_version",
        "action_configurations",
        ["workflow_knowledge_id", "action_definition_id", "version"],
    )




def downgrade() -> None:
    
    # ── 5. Drop UniqueConstraint on action_configurations ────────────────────
    op.drop_constraint(
        "uq_action_configuration_workflow_action_version",
        "action_configurations",
        type_="unique",
    )

    # ── 4. Drop status from workflow_trigger_mapping ──────────────────────────
    op.drop_column("workflow_trigger_mapping", "status")

    # ── 3. Rename workflow_trigger_mapping → workflow_trigger_mappings ────────
    op.rename_table("workflow_trigger_mapping", "workflow_trigger_mappings")

    # ── 2. Revert status column on workflow_action_mapping to String ──────────
    op.drop_column("workflow_action_mapping", "status")
    op.add_column(
        "workflow_action_mapping",
        sa.Column(
            "status",
            sa.String(),
            nullable=False,
            server_default="PENDING",
        ),
    )

    # ── 1. Drop the mappingstatus enum type ───────────────────────────────────
    mapping_status = postgresql.ENUM(
        *_MAPPING_STATUS_VALUES,
        name=_ENUM_NAME,
        create_type=False,
    )
    mapping_status.drop(op.get_bind(), checkfirst=True)
