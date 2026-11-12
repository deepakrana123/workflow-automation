"""resize_embeddings_to_384

Revision ID: a1b2c3d4e5f6
Revises: 868d6c9195f3
Create Date: 2026-10-18

Change embedding columns on action_definitions and trigger_definitions
from vector(1024) to vector(384) to match the BAAI/bge-small-en-v1.5 model.

Existing embedding values are nulled out since 1024-dim vectors are
incompatible with the new column size. Run backfill_embeddings.py after
applying this migration to regenerate them.
"""
from typing import Sequence, Union

import pgvector.sqlalchemy.vector
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "868d6c9195f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Null out existing 1024-dim embeddings first — they are incompatible.
    op.execute("UPDATE action_definitions SET embedding = NULL")
    op.execute("UPDATE trigger_definitions SET embedding = NULL")

    # Alter columns to vector(384)
    op.alter_column(
        "action_definitions",
        "embedding",
        type_=pgvector.sqlalchemy.vector.VECTOR(dim=384),
        existing_nullable=True,
        postgresql_using="NULL::vector(384)",
    )
    op.alter_column(
        "trigger_definitions",
        "embedding",
        type_=pgvector.sqlalchemy.vector.VECTOR(dim=384),
        existing_nullable=True,
        postgresql_using="NULL::vector(384)",
    )


def downgrade() -> None:
    op.execute("UPDATE action_definitions SET embedding = NULL")
    op.execute("UPDATE trigger_definitions SET embedding = NULL")

    op.alter_column(
        "action_definitions",
        "embedding",
        type_=pgvector.sqlalchemy.vector.VECTOR(dim=1024),
        existing_nullable=True,
        postgresql_using="NULL::vector(1024)",
    )
    op.alter_column(
        "trigger_definitions",
        "embedding",
        type_=pgvector.sqlalchemy.vector.VECTOR(dim=1024),
        existing_nullable=True,
        postgresql_using="NULL::vector(1024)",
    )
