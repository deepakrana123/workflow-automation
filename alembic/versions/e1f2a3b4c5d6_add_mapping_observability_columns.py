"""add mapping observability columns to workflow_action_mapping

Revision ID: e1f2a3b4c5d6
Revises: d1e2f3a4b5c6
Create Date: 2026-08-10 00:00:00.000000

Adds:
  - query_text      : the combined query string used for BM25 + Postgres retrieval
  - top_candidates  : JSONB — top-K ranked candidates from the full retrieval run
                      (rrf_score, cross_encoder_score, vector_rank, bm25_rank, postgres_rank per entry)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "workflow_action_mapping",
        sa.Column("query_text", sa.Text(), nullable=True),
    )
    op.add_column(
        "workflow_action_mapping",
        sa.Column(
            "top_candidates",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("workflow_action_mapping", "top_candidates")
    op.drop_column("workflow_action_mapping", "query_text")
