"""add_embedding_metadata_columns

Revision ID: h2i3j4k5l6m7
Revises: g1h2i3j4k5l6
Create Date: 2026-11-18

Add embedding provenance metadata to track which model generated each
embedding and when. This enables detection of stale embeddings after
model version changes.

New nullable columns on three tables:
  - action_definitions
  - trigger_definitions
  - workflow_business_rule

Columns:
  - embedding_model_name VARCHAR(255) NULL
    Example: "BAAI/bge-small-en-v1.5"
  - embedding_model_version VARCHAR(64) NULL
    Example: "v1.5" or "2026-11-18"
  - embedding_generated_at TIMESTAMP NULL
    Example: 2026-11-18 09:30:00+00:00

All columns are nullable for backward compatibility.
Existing rows will have NULL metadata and remain valid.
New embeddings populate metadata during backfill.

Stale-embedding detection queries:
  SELECT COUNT(*) FROM action_definitions
  WHERE embedding IS NOT NULL
    AND (embedding_model_name != 'BAAI/bge-small-en-v1.5'
         OR embedding_model_name IS NULL);

Migration is reversible: downgrade removes all columns.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "h2i3j4k5l6m7"
down_revision: Union[str, Sequence[str], None] = "g1h2i3j4k5l6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add embedding metadata columns to all three embedding tables."""
    
    # action_definitions: track which model generated embeddings
    op.add_column(
        "action_definitions",
        sa.Column("embedding_model_name", sa.String(255), nullable=True),
    )
    op.add_column(
        "action_definitions",
        sa.Column("embedding_model_version", sa.String(64), nullable=True),
    )
    op.add_column(
        "action_definitions",
        sa.Column("embedding_generated_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # trigger_definitions: track which model generated embeddings
    op.add_column(
        "trigger_definitions",
        sa.Column("embedding_model_name", sa.String(255), nullable=True),
    )
    op.add_column(
        "trigger_definitions",
        sa.Column("embedding_model_version", sa.String(64), nullable=True),
    )
    op.add_column(
        "trigger_definitions",
        sa.Column("embedding_generated_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # workflow_business_rule: track which model generated embeddings
    op.add_column(
        "workflow_business_rule",
        sa.Column("embedding_model_name", sa.String(255), nullable=True),
    )
    op.add_column(
        "workflow_business_rule",
        sa.Column("embedding_model_version", sa.String(64), nullable=True),
    )
    op.add_column(
        "workflow_business_rule",
        sa.Column("embedding_generated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Remove embedding metadata columns from all three tables."""
    
    # workflow_business_rule
    op.drop_column("workflow_business_rule", "embedding_generated_at")
    op.drop_column("workflow_business_rule", "embedding_model_version")
    op.drop_column("workflow_business_rule", "embedding_model_name")
    
    # trigger_definitions
    op.drop_column("trigger_definitions", "embedding_generated_at")
    op.drop_column("trigger_definitions", "embedding_model_version")
    op.drop_column("trigger_definitions", "embedding_model_name")
    
    # action_definitions
    op.drop_column("action_definitions", "embedding_generated_at")
    op.drop_column("action_definitions", "embedding_model_version")
    op.drop_column("action_definitions", "embedding_model_name")
