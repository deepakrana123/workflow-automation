"""add_embedding_to_workflow_business_rule

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-10-20

Add a vector(384) embedding column to workflow_business_rule.
The column is populated by scripts/backfill_embeddings.py after
this migration is applied.

The embedding is built from the concatenation of:
  rule + condition + outcome + responsible_role + threshold
using the BAAI/bge-small-en-v1.5 model (384-dimensional, L2-normalised).

An IVFFlat index is created on non-null rows so that cosine-similarity
queries over active rules stay fast as the table grows.
"""

from typing import Sequence, Union

import pgvector.sqlalchemy.vector
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the embedding column — nullable so existing rows are valid
    # immediately and the backfill script fills them in asynchronously.
    op.add_column(
        "workflow_business_rule",
        sa.Column(
            "embedding",
            pgvector.sqlalchemy.vector.VECTOR(dim=384),
            nullable=True,
        ),
    )

    # IVFFlat index for cosine-similarity search over populated rows.
    # lists=100 is a reasonable starting point; tune upward once the
    # table exceeds ~1 M rows.
    op.execute(
        """
        CREATE INDEX ix_workflow_business_rule_embedding
        ON workflow_business_rule
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        WHERE embedding IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP INDEX IF EXISTS ix_workflow_business_rule_embedding"
    )
    op.drop_column("workflow_business_rule", "embedding")
