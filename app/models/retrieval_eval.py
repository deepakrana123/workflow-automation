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
    results = relationship("EvaluationResult", back_populates="case", cascade="all, delete-orphan")


class EvaluationRun(Base):
    """One evaluation experiment — records the config so runs are reproducible."""

    __tablename__ = "evaluation_runs"

    id = Column(Integer, primary_key=True)

    # Human-readable name for this run (e.g. "baseline-name-only", "v2-with-description")
    name = Column(String, nullable=False, unique=True)

    # Snapshot of config used for this run
    embedding_model = Column(String, nullable=True)          # e.g. "BAAI/bge-small-en-v1.5"
    embedding_input_strategy = Column(String, nullable=True)  # e.g. "name_only", "name_description"
    query_strategy = Column(String, nullable=True)            # e.g. "name_only", "name_description"
    top_k = Column(Integer, nullable=True)                    # candidates retrieved before rerank
    threshold = Column(Float, nullable=True)                  # acceptance confidence threshold

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    results = relationship("EvaluationResult", back_populates="run", cascade="all, delete-orphan")


class EvaluationResult(Base):
    """Per-case result for one evaluation run."""

    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True)

    run_id = Column(Integer, ForeignKey("evaluation_runs.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("evaluation_cases.id"), nullable=False)

    # Rank of the expected action in the retrieved candidates (1-based). NULL = not retrieved.
    correct_rank = Column(Integer, nullable=True)

    # 1/correct_rank if retrieved, else 0
    reciprocal_rank = Column(Float, nullable=False, default=0.0)

    # Recall@K: 1 if expected action is in top-K, else 0
    recall_at_1 = Column(Boolean, nullable=False, default=False)
    recall_at_3 = Column(Boolean, nullable=False, default=False)
    recall_at_5 = Column(Boolean, nullable=False, default=False)
    recall_at_8 = Column(Boolean, nullable=False, default=False)

    # Whether the decision engine accepted a candidate
    accepted = Column(Boolean, nullable=False, default=False)

    # Failure classification
    # ACCEPTED | RETRIEVAL_MISS | TOP_K_RETRIEVED_BUT_REJECTED |
    # RANKING_FAILURE | THRESHOLD_FAILURE | CATALOG_MISSING | UNKNOWN
    diagnostic_classification = Column(String, nullable=False, default="UNKNOWN")

    # Scores from the accepted/top candidate
    cross_encoder_score = Column(Float, nullable=True)
    final_confidence = Column(Float, nullable=True)

    # Relationships
    run = relationship("EvaluationRun", back_populates="results")
    case = relationship("EvaluationCase", back_populates="results")
    candidates = relationship(
        "EvaluationCandidate", back_populates="result", cascade="all, delete-orphan"
    )


class EvaluationCandidate(Base):
    """Full ranked candidate list for one evaluation result."""

    __tablename__ = "evaluation_candidates"

    id = Column(BigInteger, primary_key=True)

    result_id = Column(Integer, ForeignKey("evaluation_results.id"), nullable=False)
    action_definition_id = Column(Integer, ForeignKey("action_definitions.id"), nullable=True)
    action_name = Column(String, nullable=False)

    rank = Column(Integer, nullable=False)          # 1-based position in final ranked list
    rrf_score = Column(Float, nullable=True)
    vector_rank = Column(Integer, nullable=True)
    bm25_rank = Column(Integer, nullable=True)
    postgres_rank = Column(Integer, nullable=True)
    cross_encoder_score = Column(Float, nullable=True)

    result = relationship("EvaluationResult", back_populates="candidates")
    action = relationship("ActionDefinition", foreign_keys=[action_definition_id])
