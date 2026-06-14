"""add generation_logs table

Revision ID: a1b2c3d4e5f6
Revises: 93cb7d655ff7
Create Date: 2026-06-14 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '93cb7d655ff7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'generation_logs',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_request', sa.Text(), nullable=False),
        sa.Column('domain', sa.String(length=100), nullable=True),
        sa.Column('prompt_name', sa.String(length=100), nullable=False),
        sa.Column('prompt_version', sa.String(length=20), nullable=False),
        sa.Column('estimated_tokens', sa.Integer(), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('is_fallback', sa.Boolean(), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('failure_reason', sa.String(length=100), nullable=True),
        sa.Column('errors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_generation_logs_id', 'generation_logs', ['id'])
    op.create_index('ix_generation_logs_prompt_version', 'generation_logs', ['prompt_version'])
    op.create_index('ix_generation_logs_provider', 'generation_logs', ['provider'])
    op.create_index('ix_generation_logs_success', 'generation_logs', ['success'])
    op.create_index('ix_generation_logs_created_at', 'generation_logs', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_generation_logs_created_at', table_name='generation_logs')
    op.drop_index('ix_generation_logs_success', table_name='generation_logs')
    op.drop_index('ix_generation_logs_provider', table_name='generation_logs')
    op.drop_index('ix_generation_logs_prompt_version', table_name='generation_logs')
    op.drop_index('ix_generation_logs_id', table_name='generation_logs')
    op.drop_table('generation_logs')
