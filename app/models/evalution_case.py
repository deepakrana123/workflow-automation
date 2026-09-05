"""
app/models/retrieval_eval.py

SQLAlchemy models for the retrieval evaluation framework.

Four tables:
  evaluation_cases      — ground truth dataset (BRD action → expected catalog action)
  evaluation_runs       — one experiment = one run (records config snapshot)
  evaluation_results    — per-case result for one run (metrics + classification)
  evaluation_candidates — full top-K candidate list per result (for diagnosis)

These tables are isolated from the production retrieval pipeline.
They share ActionDefinition via FK but do not modify it.
"""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class EvaluationCase(Base):
    """One ground-truth test case: a BRD action phrase → expected catalog action."""

    __tablename__ = "evaluation_cases"

    id = Column(Integer, primary_key=True)

    # The raw BRD action phrase (e.g. "Verify Identification Credentials")
    brd_action = Column(String, nullable=False)

    # Optional longer description from the BRD
    description = Column(Text, nullable=True)

    # FK to action_definitions.id — NULL when the expected action is not in the
    # 597-action catalog (CATALOG_MISSING cases are excluded from metrics).
    expected_action_definition_id = Column(
        Integer,
        ForeignKey("action_definitions.id"),
        nullable=True,
    )

    # Denormalised name for display (avoids joins in reports)
    expected_action_name = Column(String, nullable=True)

    # Source BRD document name for traceability
    source_brd = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    expected_action = relationship("ActionDefinition", foreign_keys=[expected_action_definition_id])



