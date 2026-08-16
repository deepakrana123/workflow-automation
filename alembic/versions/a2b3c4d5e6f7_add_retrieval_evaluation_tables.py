"""add retrieval evaluation tables

Revision ID: a2b3c4d5e6f7
Revises: f432bf45f607
Create Date: 2026-08-10 00:00:00.000000

Creates four isolated evaluation tables:
  evaluation_cases      — ground truth dataset
  evaluation_runs       — experiment config snapshots
  evaluation_results    — per-case metrics per run
  evaluation_candidates — full top-K candidate list per result
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "f432bf45f607"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evaluation_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("brd_action", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "expected_action_definition_id",
            sa.Integer(),
            sa.ForeignKey("action_definitions.id"),
            nullable=True,
        ),
        sa.Column("expected_action_name", sa.String(), nullable=True),
        sa.Column("source_brd", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_evaluation_cases_id", "evaluation_cases", ["id"])

    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("embedding_model", sa.String(), nullable=True),
        sa.Column("embedding_input_strategy", sa.String(), nullable=True),
        sa.Column("query_strategy", sa.String(), nullable=True),
        sa.Column("top_k", sa.Integer(), nullable=True),
        sa.Column("threshold", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_evaluation_runs_id", "evaluation_runs", ["id"])
    op.create_index("ix_evaluation_runs_name", "evaluation_runs", ["name"], unique=True)

    op.create_table(
        "evaluation_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("evaluation_runs.id"), nullable=False),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("evaluation_cases.id"), nullable=False),
        sa.Column("correct_rank", sa.Integer(), nullable=True),
        sa.Column("reciprocal_rank", sa.Float(), nullable=False, server_default="0"),
        sa.Column("recall_at_1", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("recall_at_3", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("recall_at_5", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("recall_at_8", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("accepted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("diagnostic_classification", sa.String(), nullable=False, server_default="UNKNOWN"),
        sa.Column("cross_encoder_score", sa.Float(), nullable=True),
        sa.Column("final_confidence", sa.Float(), nullable=True),
    )
    op.create_index("ix_evaluation_results_run_id", "evaluation_results", ["run_id"])
    op.create_index("ix_evaluation_results_case_id", "evaluation_results", ["case_id"])

    op.create_table(
        "evaluation_candidates",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("result_id", sa.Integer(), sa.ForeignKey("evaluation_results.id"), nullable=False),
        sa.Column("action_definition_id", sa.Integer(), sa.ForeignKey("action_definitions.id"), nullable=True),
        sa.Column("action_name", sa.String(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("rrf_score", sa.Float(), nullable=True),
        sa.Column("vector_rank", sa.Integer(), nullable=True),
        sa.Column("bm25_rank", sa.Integer(), nullable=True),
        sa.Column("postgres_rank", sa.Integer(), nullable=True),
        sa.Column("cross_encoder_score", sa.Float(), nullable=True),
    )
    op.create_index("ix_evaluation_candidates_result_id", "evaluation_candidates", ["result_id"])


def downgrade() -> None:
    op.drop_table("evaluation_candidates")
    op.drop_table("evaluation_results")
    op.drop_table("evaluation_runs")
    op.drop_table("evaluation_cases")
