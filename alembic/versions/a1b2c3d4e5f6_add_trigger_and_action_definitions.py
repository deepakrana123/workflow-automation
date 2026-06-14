"""add trigger and action definitions

Revision ID: a1b2c3d4e5f6
Revises: 93cb7d655ff7
Create Date: 2026-06-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '93cb7d655ff7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'trigger_definitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('workflow_type', sa.String(), nullable=False),
        sa.Column('aliases', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index(
        op.f('ix_trigger_definitions_id'),
        'trigger_definitions', ['id'], unique=False,
    )
    op.create_index(
        op.f('ix_trigger_definitions_name'),
        'trigger_definitions', ['name'], unique=True,
    )
    op.create_index(
        op.f('ix_trigger_definitions_workflow_type'),
        'trigger_definitions', ['workflow_type'], unique=False,
    )
    op.create_index(
        op.f('ix_trigger_definitions_active'),
        'trigger_definitions', ['active'], unique=False,
    )

    op.create_table(
        'action_definitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('workflow_type', sa.String(), nullable=False),
        sa.Column('aliases', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index(
        op.f('ix_action_definitions_id'),
        'action_definitions', ['id'], unique=False,
    )
    op.create_index(
        op.f('ix_action_definitions_name'),
        'action_definitions', ['name'], unique=True,
    )
    op.create_index(
        op.f('ix_action_definitions_workflow_type'),
        'action_definitions', ['workflow_type'], unique=False,
    )
    op.create_index(
        op.f('ix_action_definitions_active'),
        'action_definitions', ['active'], unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_action_definitions_active'), table_name='action_definitions')
    op.drop_index(op.f('ix_action_definitions_workflow_type'), table_name='action_definitions')
    op.drop_index(op.f('ix_action_definitions_name'), table_name='action_definitions')
    op.drop_index(op.f('ix_action_definitions_id'), table_name='action_definitions')
    op.drop_table('action_definitions')

    op.drop_index(op.f('ix_trigger_definitions_active'), table_name='trigger_definitions')
    op.drop_index(op.f('ix_trigger_definitions_workflow_type'), table_name='trigger_definitions')
    op.drop_index(op.f('ix_trigger_definitions_name'), table_name='trigger_definitions')
    op.drop_index(op.f('ix_trigger_definitions_id'), table_name='trigger_definitions')
    op.drop_table('trigger_definitions')
