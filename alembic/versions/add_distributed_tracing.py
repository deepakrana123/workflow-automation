"""add distributed tracing — trace_id, span_id, trace_events table

Revision ID: add_distributed_tracing
Revises: 93cb7d655ff7
Create Date: 2026-06-01

Changes:
    workflow_executions  — add trace_id, correlation_id
    execution_steps      — add span_id, parent_span_id
    trace_events         — new table (append-only event log)

Migration is safe for existing data:
    - All new columns are nullable
    - Existing rows backfilled with generated placeholder values
    - No destructive changes
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "add_distributed_tracing"
down_revision: Union[str, Sequence[str], None] = "93cb7d655ff7"
branch_labels = None
depends_on = None


def upgrade() -> None:

    # ── workflow_executions: add trace_id + correlation_id ────────────────────

    op.add_column(
        "workflow_executions",
        sa.Column("trace_id", sa.String(100), nullable=True),
    )
    op.add_column(
        "workflow_executions",
        sa.Column("correlation_id", sa.String(100), nullable=True),
    )

    # Backfill existing rows — use id-based placeholder so each row is unique
    op.execute(
        """
        UPDATE workflow_executions
        SET
            trace_id       = 'wf_legacy_' || id::text,
            correlation_id = 'wf_legacy_' || id::text
        WHERE trace_id IS NULL
        """
    )

    # Add indexes after backfill
    op.create_index(
        "ix_workflow_executions_trace_id",
        "workflow_executions",
        ["trace_id"],
    )
    op.create_index(
        "ix_workflow_executions_correlation_id",
        "workflow_executions",
        ["correlation_id"],
    )

    # ── execution_steps: add span_id + parent_span_id ────────────────────────

    op.add_column(
        "execution_steps",
        sa.Column("span_id", sa.String(100), nullable=True),
    )
    op.add_column(
        "execution_steps",
        sa.Column("parent_span_id", sa.String(100), nullable=True),
    )

    # Backfill existing rows
    op.execute(
        """
        UPDATE execution_steps
        SET span_id = 'sp_legacy_' || id::text
        WHERE span_id IS NULL
        """
    )

    op.create_index(
        "ix_execution_steps_span_id",
        "execution_steps",
        ["span_id"],
    )

    # ── trace_events: new append-only event log table ────────────────────────

    op.create_table(
        "trace_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("trace_id", sa.String(100), nullable=False),
        sa.Column("span_id", sa.String(100), nullable=True),
        sa.Column("parent_span_id", sa.String(100), nullable=True),
        sa.Column(
            "workflow_execution_id",
            sa.BigInteger(),
            sa.ForeignKey("workflow_executions.id"),
            nullable=False,
        ),
        sa.Column(
            "execution_step_id",
            sa.BigInteger(),
            sa.ForeignKey("execution_steps.id"),
            nullable=True,
        ),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_source", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_index("ix_trace_events_trace_id", "trace_events", ["trace_id"])
    op.create_index("ix_trace_events_span_id", "trace_events", ["span_id"])
    op.create_index(
        "ix_trace_events_workflow_execution_id",
        "trace_events",
        ["workflow_execution_id"],
    )
    op.create_index("ix_trace_events_event_type", "trace_events", ["event_type"])
    op.create_index("ix_trace_events_created_at", "trace_events", ["created_at"])


def downgrade() -> None:

    # Drop trace_events table
    op.drop_index("ix_trace_events_created_at", table_name="trace_events")
    op.drop_index("ix_trace_events_event_type", table_name="trace_events")
    op.drop_index("ix_trace_events_workflow_execution_id", table_name="trace_events")
    op.drop_index("ix_trace_events_span_id", table_name="trace_events")
    op.drop_index("ix_trace_events_trace_id", table_name="trace_events")
    op.drop_table("trace_events")

    # Drop execution_steps tracing columns
    op.drop_index("ix_execution_steps_span_id", table_name="execution_steps")
    op.drop_column("execution_steps", "parent_span_id")
    op.drop_column("execution_steps", "span_id")

    # Drop workflow_executions tracing columns
    op.drop_index("ix_workflow_executions_correlation_id", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_trace_id", table_name="workflow_executions")
    op.drop_column("workflow_executions", "correlation_id")
    op.drop_column("workflow_executions", "trace_id")
