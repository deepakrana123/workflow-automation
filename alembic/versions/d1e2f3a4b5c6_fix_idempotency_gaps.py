"""fix_idempotency_gaps

Revision ID: d1e2f3a4b5c6
Revises: c870702e93da
Create Date: 2026-11-13

What this migration does
------------------------
Closes three idempotency and concurrency safety gaps identified during
the architecture investigation:

Gap 1 — No link from WorkflowKnowledge to its source DocumentVersion.
  ADD COLUMN workflow_knowledge.document_version_id
      INTEGER REFERENCES document_versions(id) ON DELETE SET NULL

  With only brd_document_id on WorkflowKnowledge, there was no direct link
  to the specific DocumentVersion that produced a knowledge row. Provenance
  was only recoverable via the indirect chain:
      IngestionAttempt.extracted_knowledge_id → WorkflowKnowledge
  which requires T6 to have committed successfully.

Gap 2 — No DB constraint preventing duplicate WorkflowKnowledge per version.
  CREATE UNIQUE INDEX uq_workflow_knowledge_per_version
      ON workflow_knowledge (document_version_id)
      WHERE document_version_id IS NOT NULL

  Without this index, a retry always produced a second (third, Nth)
  WorkflowKnowledge row for the same DocumentVersion — duplicating entries
  in the retrieval index.  With the index, the second INSERT raises
  IntegrityError, which the service layer catches and treats as
  "ghost-knowledge recovery" (return the existing row instead).

Gap 3 — No DB constraint preventing two concurrent RUNNING attempts.
  CREATE UNIQUE INDEX uq_one_running_attempt_per_version
      ON ingestion_attempts (document_version_id)
      WHERE status = 'RUNNING'

  The application-level SELECT guard in _check_running_guard() was a
  TOCTOU race: two processes could both pass the SELECT before either
  committed the RUNNING transition.  This partial unique index turns the
  race into a hard IntegrityError on the second committer.

Both new indexes are PARTIAL (WHERE clause) so they only constrain rows
where the column is NOT NULL or status = 'RUNNING' respectively.  Existing
rows with NULL document_version_id are unaffected.

Downgrade
---------
Drops all three additions.  No data is lost — the column is nullable
and no data was stored in it before this migration ran.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "c870702e93da"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ── Gap 1: add document_version_id to workflow_knowledge ─────────────────
    op.add_column(
        "workflow_knowledge",
        sa.Column(
            "document_version_id",
            sa.Integer(),
            sa.ForeignKey("document_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_workflow_knowledge_document_version_id",
        "workflow_knowledge",
        ["document_version_id"],
        unique=False,
    )

    # ── Gap 2: partial unique index — one WorkflowKnowledge per version ───────
    # Uses raw SQL because SQLAlchemy's op.create_index does not support
    # PostgreSQL WHERE clauses via the standard API.
    op.execute(
        """
        CREATE UNIQUE INDEX uq_workflow_knowledge_per_version
        ON workflow_knowledge (document_version_id)
        WHERE document_version_id IS NOT NULL
        """
    )

    # ── Gap 3: partial unique index — one RUNNING attempt per version ─────────
    op.execute(
        """
        CREATE UNIQUE INDEX uq_one_running_attempt_per_version
        ON ingestion_attempts (document_version_id)
        WHERE status = 'RUNNING'
        """
    )


def downgrade() -> None:

    # ── Remove Gap 3 index ────────────────────────────────────────────────────
    op.execute(
        "DROP INDEX IF EXISTS uq_one_running_attempt_per_version"
    )

    # ── Remove Gap 2 index ────────────────────────────────────────────────────
    op.execute(
        "DROP INDEX IF EXISTS uq_workflow_knowledge_per_version"
    )

    # ── Remove Gap 1 column ───────────────────────────────────────────────────
    op.drop_index(
        "ix_workflow_knowledge_document_version_id",
        table_name="workflow_knowledge",
    )
    op.drop_column("workflow_knowledge", "document_version_id")
