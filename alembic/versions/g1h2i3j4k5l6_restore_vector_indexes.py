"""restore_vector_indexes

Revision ID: g1h2i3j4k5l6
Revises: f51580e76d10
Create Date: 2026-11-18

Restore pgvector IVFFlat indexes on embedding columns that were
inadvertently dropped in migration 99e9cf39be25.

This migration creates indexes on:
  - action_definitions.embedding (Vector(384))
  - trigger_definitions.embedding (Vector(384))
  - workflow_business_rule.embedding (Vector(384))

All three tables use cosine distance for vector similarity queries.
Each index uses:
  - Type: IVFFlat (efficient for update-heavy workloads)
  - Operator: vector_cosine_ops (L2-normalized cosine similarity)
  - Parameter: lists=100 (tunable; increase as table grows beyond 1M rows)
  - Partial filter: WHERE embedding IS NOT NULL (reduce index size)

The indexes are created CONCURRENTLY where possible to minimize
impact on production queries. Downgrade removes all indexes.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers
revision: str = "g1h2i3j4k5l6"
down_revision: Union[str, Sequence[str], None] = "f51580e76d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create IVFFlat indexes on all three embedding columns.
    
    Note: We create indexes without CONCURRENTLY since migrations run in
    transaction mode. The non-concurrent creation is acceptable for a one-time
    backfill operation. For production use cases where you need concurrent index
    creation (no table locks), run these CREATE INDEX CONCURRENTLY statements
    manually outside of Alembic.
    """
    
    # Index on action_definitions.embedding
    # Used by: SemanticRepository.search_actions(), WorkflowRepository.search_actions_by_embedding()
    op.execute(
        """
        CREATE INDEX ix_action_definitions_embedding
        ON action_definitions
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        WHERE embedding IS NOT NULL
        """
    )
    
    # Index on trigger_definitions.embedding
    # Used by: SemanticRepository.search_triggers(), WorkflowRepository.search_triggers_by_embedding()
    op.execute(
        """
        CREATE INDEX ix_trigger_definitions_embedding
        ON trigger_definitions
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        WHERE embedding IS NOT NULL
        """
    )
    
    # Index on workflow_business_rule.embedding
    # Previously created in migration b2c3d4e5f6a7 then dropped in 99e9cf39be25
    # Used by: RuleRepository.search_by_embedding()
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
    """Remove the three IVFFlat indexes."""
    
    op.execute("DROP INDEX IF EXISTS ix_workflow_business_rule_embedding")
    op.execute("DROP INDEX IF EXISTS ix_trigger_definitions_embedding")
    op.execute("DROP INDEX IF EXISTS ix_action_definitions_embedding")
