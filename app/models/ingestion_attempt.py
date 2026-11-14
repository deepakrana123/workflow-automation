"""
app/models/ingestion_attempt.py

IngestionAttempt — one execution of the extraction pipeline against a
specific DocumentVersion.

Design decisions
----------------
1.  One row per execution, never updated in place.
    When a retry is triggered, a NEW IngestionAttempt row is created.
    The previous attempt remains unchanged — it is a permanent audit record.
    Status transitions (PENDING → RUNNING → COMPLETED/FAILED) happen on the
    current attempt row via UPDATE, but older attempt rows are never touched.

2.  attempt_number is unique within a version.
    Assigned by the service as MAX(attempt_number) + 1.
    First attempt is attempt_number = 1.

3.  Concurrency guard via active attempt uniqueness.
    A partial unique index (enforced by the application and documented here)
    prevents two attempts from being in RUNNING state simultaneously for the
    same version.  PostgreSQL partial unique indexes cannot be expressed in
    SQLAlchemy's __table_args__ without raw DDL, so this is enforced by the
    service layer with a SELECT-then-INSERT under a transaction.  The index
    DDL is included in the Alembic migration (Step 3 of the migration plan).

4.  error_code and error_message are separate.
    error_code is a machine-readable short string (e.g. "EXTRACTION_FAILED",
    "LLM_TIMEOUT", "EMPTY_DOCUMENT") used for metrics and retry decisions.
    error_message is the full human-readable detail (e.g. exception text).

5.  extracted_knowledge_id links forward to the WorkflowKnowledge row
    created by a successful attempt.
    This is a nullable FK — NULL while the attempt is running or failed.
    When the attempt COMPLETES it is set to the WorkflowKnowledge.id that
    was produced.  This completes the provenance chain:
        IngestionAttempt → WorkflowKnowledge → (actions, rules, actors)
    The WorkflowKnowledge model is NOT modified in this step — the FK is
    declared here as a soft reference (no back_populates on WorkflowKnowledge
    yet) so this remains a pure additive change.

6.  pipeline_snapshot records what actually ran.
    Distinct from DocumentVersion.pipeline_config (what was requested).
    This JSONB records the actual providers, model versions and prompt
    hashes used, enabling exact reproduction of a past extraction run.

Status lifecycle
----------------
    PENDING   — created, waiting for a worker to pick it up
    RUNNING   — worker has started; started_at is set
    COMPLETED — extraction finished without error; completed_at is set
    FAILED    — extraction encountered an unrecoverable error; completed_at
                and error_code / error_message are set

Ownership chain (read-only navigation)
---------------------------------------
    IngestionAttempt.version  → DocumentVersion
    DocumentVersion.document  → BRDDocument
    BRDDocument.workspace     → Workspace
    Workspace.tenant           → Tenant

This chain provides full tenant-isolation traceability from any attempt row
without joining through additional tables.
"""

import enum

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class AttemptStatus(str, enum.Enum):
    """Lifecycle states for a single IngestionAttempt.

    Distinct from VersionStatus (which aggregates across all attempts).
    """

    PENDING   = "PENDING"
    RUNNING   = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED    = "FAILED"


_VALID_ATTEMPT_STATUSES = tuple(s.value for s in AttemptStatus)


# Machine-readable error codes for failed attempts.
# Used for metrics, alerting and retry-decision logic.
class AttemptErrorCode:
    EMPTY_DOCUMENT       = "EMPTY_DOCUMENT"        # PDF extracted no text
    EXTRACTION_FAILED    = "EXTRACTION_FAILED"      # MultiModalDocumentExtractor raised
    LLM_TIMEOUT          = "LLM_TIMEOUT"            # All LLM providers timed out
    LLM_PARSE_ERROR      = "LLM_PARSE_ERROR"        # WorkflowExtraction validation failed
    NO_ACTIONS_EXTRACTED = "NO_ACTIONS_EXTRACTED"   # LLM returned 0 action_references
    STORAGE_FAILED       = "STORAGE_FAILED"         # FileStorageService.store() failed
    MAPPING_FAILED       = "MAPPING_FAILED"         # EmbeddingMapper raised
    UNKNOWN              = "UNKNOWN"                # Unclassified exception


class IngestionAttempt(Base):
    """One execution of the extraction pipeline against a DocumentVersion.

    Created when processing starts (or is queued).  Never mutated after
    reaching COMPLETED or FAILED — retries produce a new row.
    """

    __tablename__ = "ingestion_attempts"

    __table_args__ = (
        # Attempt numbers must be unique within a version.
        UniqueConstraint(
            "document_version_id",
            "attempt_number",
            name="uq_ingestion_attempt_version_number",
        ),
        # Status must be one of the declared lifecycle values.
        CheckConstraint(
            f"status IN {_VALID_ATTEMPT_STATUSES}",
            name="ck_ingestion_attempt_status",
        ),
    )

    # ── Primary key ───────────────────────────────────────────────────────────
    id = Column(Integer, primary_key=True)

    # ── Parent version ────────────────────────────────────────────────────────
    document_version_id = Column(
        Integer,
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Attempt identity ──────────────────────────────────────────────────────
    # Monotonically increasing integer within a version.
    # Assigned by the service as MAX(attempt_number) + 1.
    attempt_number = Column(Integer, nullable=False)

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    status = Column(
        String(32),
        nullable=False,
        default=AttemptStatus.PENDING.value,
        index=True,
    )

    # ── Timing ────────────────────────────────────────────────────────────────
    # Set when the worker transitions from PENDING → RUNNING.
    started_at = Column(DateTime(timezone=True), nullable=True)

    # Set when the worker transitions to COMPLETED or FAILED.
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # ── Failure details ───────────────────────────────────────────────────────
    # Short machine-readable code — see AttemptErrorCode constants above.
    # NULL when status is not FAILED.
    error_code = Column(String(64), nullable=True, index=True)

    # Full human-readable error detail (exception message, traceback summary).
    # NULL when status is not FAILED.
    error_message = Column(Text, nullable=True)

    # ── Pipeline provenance ───────────────────────────────────────────────────
    # Snapshot of the actual pipeline configuration used in this run.
    # Example: {"prompt_version": "v3", "prompt_hash": "abc123",
    #           "model": "gemini-1.5-pro", "vision_provider": "gemini",
    #           "text_provider": "openai", "extractor_version": "2.1.0"}
    # NULL for attempts created before this field was introduced.
    pipeline_snapshot = Column(JSONB, nullable=True)

    # ── Forward link to extraction output ─────────────────────────────────────
    # Set to the WorkflowKnowledge.id produced by a COMPLETED attempt.
    # NULL while PENDING / RUNNING, and for FAILED attempts.
    # This soft FK completes the provenance chain:
    #   IngestionAttempt → WorkflowKnowledge → (actions, rules, actors)
    # No back_populates on WorkflowKnowledge until Step 3 of the phase plan.
    extracted_knowledge_id = Column(
        Integer,
        ForeignKey("workflow_knowledge.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────

    # Parent version.
    version = relationship(
        "DocumentVersion",
        back_populates="attempts",
    )

    # The WorkflowKnowledge produced by this attempt (NULL until COMPLETED).
    # Read-only navigation — no cascade, no back_populates on WorkflowKnowledge yet.
    extracted_knowledge = relationship(
        "WorkflowKnowledge",
        foreign_keys=[extracted_knowledge_id],
    )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def duration_seconds(self) -> float | None:
        """Return wall-clock duration of this attempt in seconds, or None."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def is_active(self) -> bool:
        """Return True if this attempt is currently in a non-terminal state."""
        return self.status in (
            AttemptStatus.PENDING.value,
            AttemptStatus.RUNNING.value,
        )

    def __repr__(self) -> str:
        return (
            f"<IngestionAttempt id={self.id} "
            f"version_id={self.document_version_id} "
            f"attempt={self.attempt_number} "
            f"status={self.status!r}>"
        )
