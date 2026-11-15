"""add_rule_provenance_links

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-11-13

What this migration does
------------------------
Adds two nullable FK columns that complete the rule-provenance chain,
allowing a structured BusinessRuleDefinition to be traced back to the
exact raw WorkflowBusinessRule row it was parsed from, and that raw rule
to be traced back to the BRDDocument it was extracted from.

Before this migration the provenance chain was:

    BusinessRuleDefinition.source_workflow_knowledge_id
        → workflow_knowledge  (the whole BRD ingestion, not the specific rule)
    WorkflowBusinessRule.workflow_knowledge_id
        → workflow_knowledge  (same — no link to the source document)

After this migration:

    BusinessRuleDefinition.workflow_business_rule_id
        → workflow_business_rule  (the exact raw rule row)
    WorkflowBusinessRule.source_brd_document_id
        → brd_documents  (the exact source document)

Step 1 — workflow_business_rule.source_brd_document_id
  ADD COLUMN workflow_business_rule.source_brd_document_id
      INTEGER FK → brd_documents.id  ON DELETE SET NULL  nullable
  ADD regular index ix_workflow_business_rule_source_brd_document_id

Step 2 — business_rule_definitions.workflow_business_rule_id
  ADD COLUMN business_rule_definitions.workflow_business_rule_id
      INTEGER FK → workflow_business_rule.id  ON DELETE SET NULL  nullable
  ADD regular index ix_business_rule_definitions_workflow_business_rule_id
  ADD partial unique index uq_one_definition_per_raw_rule
      ON business_rule_definitions (workflow_business_rule_id)
      WHERE workflow_business_rule_id IS NOT NULL

  The partial unique index enforces the invariant that at most one
  BusinessRuleDefinition can be derived from a given WorkflowBusinessRule.
  Using WHERE NOT NULL preserves the existing behavior for NULL values —
  multiple rows with workflow_business_rule_id = NULL are allowed (manually
  created or legacy rules), which is correct.

Backward compatibility
----------------------
Both columns are nullable.  All existing rows get NULL and remain valid.
No existing query, index, or constraint references these columns.
The runtime rule engine (RuntimeRuleEngine.evaluate) queries
BusinessRuleDefinition by scope_workspace_id only and is unaffected.
The retrieval layer (RuleRepository) queries WorkflowBusinessRule by
workflow_knowledge_id only and is unaffected.

No existing rows need backfilling in this migration.
Backfilling (setting the new columns on existing rows) is a separate
application-layer operation performed by RuleExtractionService after
this migration is applied.

Downgrade
---------
Removes in reverse dependency order:
  1. Drop unique partial index on business_rule_definitions
  2. Drop regular index on business_rule_definitions
  3. Drop column business_rule_definitions.workflow_business_rule_id
  4. Drop regular index on workflow_business_rule
  5. Drop column workflow_business_rule.source_brd_document_id

No data loss — both columns are nullable and no backfill was performed.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e2f3a4b5c6d7"
down_revision: Union[str, Sequence[str], None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ── Step 1: workflow_business_rule.source_brd_document_id ────────────────
    op.add_column(
        "workflow_business_rule",
        sa.Column(
            "source_brd_document_id",
            sa.Integer(),
            sa.ForeignKey("brd_documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_workflow_business_rule_source_brd_document_id"),
        "workflow_business_rule",
        ["source_brd_document_id"],
        unique=False,
    )

    # ── Step 2: business_rule_definitions.workflow_business_rule_id ──────────
    op.add_column(
        "business_rule_definitions",
        sa.Column(
            "workflow_business_rule_id",
            sa.Integer(),
            sa.ForeignKey("workflow_business_rule.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_business_rule_definitions_workflow_business_rule_id"),
        "business_rule_definitions",
        ["workflow_business_rule_id"],
        unique=False,
    )

    # Partial unique index: at most one BusinessRuleDefinition per raw rule.
    # WHERE clause excludes NULL so legacy/manual rows (NULL) are unaffected.
    # Raw SQL required because op.create_index does not support WHERE clauses.
    op.execute(
        """
        CREATE UNIQUE INDEX uq_one_definition_per_raw_rule
        ON business_rule_definitions (workflow_business_rule_id)
        WHERE workflow_business_rule_id IS NOT NULL
        """
    )


def downgrade() -> None:

    # ── Remove Step 2 (reverse order: index first, then column) ──────────────

    # Drop partial unique index
    op.execute(
        "DROP INDEX IF EXISTS uq_one_definition_per_raw_rule"
    )

    # Drop regular index
    op.drop_index(
        op.f("ix_business_rule_definitions_workflow_business_rule_id"),
        table_name="business_rule_definitions",
    )

    # Drop column (FK constraint is dropped automatically with the column)
    op.drop_column("business_rule_definitions", "workflow_business_rule_id")

    # ── Remove Step 1 ─────────────────────────────────────────────────────────

    # Drop regular index
    op.drop_index(
        op.f("ix_workflow_business_rule_source_brd_document_id"),
        table_name="workflow_business_rule",
    )

    # Drop column (FK constraint is dropped automatically with the column)
    op.drop_column("workflow_business_rule", "source_brd_document_id")
