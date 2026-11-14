"""add_tenants_and_restructure_workspaces

Revision ID: c1f2a3b4d5e6
Revises: 99e9cf39be25
Create Date: 2026-11-13

What this migration does
------------------------
1.  CREATE TABLE tenants
2.  INSERT one bootstrap development tenant (id=1)
3.  ADD workspaces.tenant_id (nullable first)
4.  UPDATE all existing workspaces → tenant_id = 1  (no meaningful data to preserve)
5.  SET tenant_id NOT NULL
6.  DROP old UNIQUE(name) on workspaces
7.  CREATE UNIQUE(tenant_id, name)  → allows different banks to share workspace names
8.  DROP self-referential FK  workspaces.parent_id → workspaces.id
9.  DROP workspaces.parent_id
10. DROP workspaces.level
11. DROP workspaces.organization_name

Downgrade
---------
Steps 8-11 are destructive (column data is permanently gone).
A full downgrade restores the schema shape but cannot recover the
dropped column values.  Take a table dump before running upgrade if
the data matters.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c1f2a3b4d5e6"
down_revision: Union[str, Sequence[str], None] = "99e9cf39be25"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ── Step 1: create tenants table ─────────────────────────────────────────
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_tenant_name"),
        sa.UniqueConstraint("slug", name="uq_tenant_slug"),
    )
    op.create_index("ix_tenant_name", "tenants", ["name"], unique=True)
    op.create_index("ix_tenant_slug", "tenants", ["slug"], unique=True)

    # ── Step 2: bootstrap development tenant ─────────────────────────────────
    op.execute(
        """
        INSERT INTO tenants (id, name, slug, display_name, active, created_at, updated_at)
        VALUES (1, 'bootstrap_dev', 'bootstrap-dev',
                'Bootstrap Development Tenant', true, now(), now())
        """
    )

    # ── Step 3: add tenant_id as nullable ────────────────────────────────────
    op.add_column(
        "workspaces",
        sa.Column(
            "tenant_id",
            sa.Integer(),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index("ix_workspaces_tenant_id", "workspaces", ["tenant_id"])

    # ── Step 4: backfill all existing workspaces to bootstrap tenant ─────────
    op.execute("UPDATE workspaces SET tenant_id = 1")

    # ── Step 5: enforce NOT NULL ──────────────────────────────────────────────
    op.alter_column("workspaces", "tenant_id", nullable=False)

    # ── Step 6: drop old global UNIQUE(name) ─────────────────────────────────
    # PostgreSQL auto-names this workspaces_name_key when no name is given.
    op.drop_constraint("workspaces_name_key", "workspaces", type_="unique")

    # ── Step 7: add composite unique (tenant_id, name) ───────────────────────
    op.create_unique_constraint(
        "uq_workspace_tenant_name", "workspaces", ["tenant_id", "name"]
    )

    # ── Step 8: drop self-referential FK on parent_id ────────────────────────
    # Constraint name is workspaces_parent_id_fkey (PostgreSQL default).
    op.drop_constraint("workspaces_parent_id_fkey", "workspaces", type_="foreignkey")

    # ── Steps 9-11: drop hierarchy columns ───────────────────────────────────
    op.drop_column("workspaces", "parent_id")
    op.drop_column("workspaces", "level")
    op.drop_column("workspaces", "organization_name")


def downgrade() -> None:

    # ── Restore hierarchy columns (data is gone — defaults used) ─────────────
    op.add_column(
        "workspaces",
        sa.Column(
            "organization_name",
            sa.String(),
            nullable=True,
        ),
    )
    op.add_column(
        "workspaces",
        sa.Column(
            "level",
            sa.String(length=20),
            nullable=False,
            server_default="branch",   # satisfy NOT NULL for existing rows
        ),
    )
    op.add_column(
        "workspaces",
        sa.Column(
            "parent_id",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "workspaces_parent_id_fkey",
        "workspaces",
        "workspaces",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── Restore old unique constraint ─────────────────────────────────────────
    op.drop_constraint("uq_workspace_tenant_name", "workspaces", type_="unique")
    op.create_unique_constraint("workspaces_name_key", "workspaces", ["name"])

    # ── Remove tenant_id ──────────────────────────────────────────────────────
    op.drop_index("ix_workspaces_tenant_id", table_name="workspaces")
    op.drop_column("workspaces", "tenant_id")

    # ── Remove tenants table ──────────────────────────────────────────────────
    op.drop_index("ix_tenant_slug", table_name="tenants")
    op.drop_index("ix_tenant_name", table_name="tenants")
    op.drop_table("tenants")
