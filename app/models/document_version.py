"""
app/models/document_version.py

DocumentVersion — an immutable record of one uploaded revision of a BRDDocument.

Design decisions
----------------
1.  Immutability.
    Once a DocumentVersion row is created its content-identity columns
    (sha256_hash, storage_path, storage_file_id, file_size_bytes, mime_type,
    original_filename) are never updated.  If the same bytes are re-uploaded,
    the service layer returns the existing version.  If different bytes are
    uploaded for the same logical document, a new version row is created.

2.  Version number is owned here, not on BRDDocument.
    BRDDocument is the logical identity ("HDFC Personal Loan BRD").
    DocumentVersion is a concrete file revision of that document.
    version_number is unique within a document (enforced by composite
    unique constraint).  The service layer assigns it as MAX(version_number)+1.

3.  Content hash deduplication is scoped to the document.
    The same PDF bytes uploaded to two different BRDDocument records (e.g.
    the same policy attached to two different workspaces) results in two
    independent DocumentVersion rows.  This is intentional — tenant isolation
    takes precedence over storage deduplication.

4.  Status lives here, not on BRDDocument.
    BRDDocument currently carries its own ingestion_status and attempt_count
    as a convenience summary.  Those fields will be deprecated once the
    pipeline is fully migrated to DocumentVersion + IngestionAttempt.
    For now they coexist.  The authoritative lifecycle state is on
    DocumentVersion; BRDDocument.ingestion_status is a denormalised mirror
    maintained by the service layer.

5.  pipeline_config captures the extraction parameters at registration time.
    This is a JSONB snapshot of whatever configuration drove the extraction
    (prompt version, model, provider preferences, etc.).  Stored on the
    version so that a later retry can determine whether a re-run is needed
    (e.g. after a prompt upgrade).

Relationships
-------------
    BRDDocument (1) ──< DocumentVersion (N)   via document_id
    DocumentVersion (1) ──< IngestionAttempt (N)   (defined in ingestion_attempt.py)

Status lifecycle
----------------
    REGISTERED    — version created, not yet picked up for extraction
    PROCESSING    — extraction pipeline is currently running
    COMPLETED     — extraction succeeded; WorkflowKnowledge rows exist
    FAILED        — all attempts exhausted without success
    RETRY_PENDING — operator scheduled a new attempt after FAILED

Transitions:
    REGISTERED    → PROCESSING      (pipeline picks it up)
    PROCESSING    → COMPLETED       (clean extraction)
    PROCESSING    → FAILED          (unrecoverable error)
    FAILED        → RETRY_PENDING   (operator schedules retry)
    RETRY_PENDING → PROCESSING      (retry job picks it up)
    COMPLETED     → RETRY_PENDING   (operator requests re-extraction)
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


class VersionStatus(str, enum.Enum):
    """Lifecycle states for a DocumentVersion.

    Distinct from IngestionAttempt status (which tracks a single pipeline run).
    A version transitions through these states as attempts are made against it.
    """

    REGISTERED    = "REGISTERED"
    PROCESSING    = "PROCESSING"
    COMPLETED     = "COMPLETED"
    FAILED        = "FAILED"
    RETRY_PENDING = "RETRY_PENDING"


_VALID_VERSION_STATUSES = tuple(s.value for s in VersionStatus)


class DocumentVersion(Base):
    """Immutable record of one uploaded revision of a BRDDocument.

    One row per distinct file (sha256_hash) per BRDDocument.
    Uploading the same bytes again returns the existing row.
    Uploading different bytes creates a new row with a higher version_number.
    """

    __tablename__ = "document_versions"

    __table_args__ = (
        # Version numbers must be unique within a document.
        UniqueConstraint(
            "document_id",
            "version_number",
            name="uq_document_version_number",
        ),
        # Same content uploaded twice to the same logical document
        # returns the existing version rather than creating a duplicate.
        UniqueConstraint(
            "document_id",
            "sha256_hash",
            name="uq_document_version_hash",
        ),
        # Status must be one of the declared lifecycle values.
        CheckConstraint(
            f"status IN {_VALID_VERSION_STATUSES}",
            name="ck_document_version_status",
        ),
    )

    # ── Primary key ───────────────────────────────────────────────────────────
    id = Column(Integer, primary_key=True)

    # ── Parent document ───────────────────────────────────────────────────────
    document_id = Column(
        Integer,
        ForeignKey("brd_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Version identity ──────────────────────────────────────────────────────
    # Monotonically increasing integer within a document.
    # Assigned by the service as MAX(version_number) + 1.
    # First upload is version 1.
    version_number = Column(Integer, nullable=False)

    # ── File identity ─────────────────────────────────────────────────────────
    # Original filename as supplied by the uploader.
    # Stored here because different versions may have different filenames
    # (e.g. "personal_loan_brd_v2.pdf").
    original_filename = Column(String(512), nullable=False)

    # SHA-256 hex digest of the raw PDF bytes, computed before storage.
    # Deduplication key within this document (uq_document_version_hash).
    sha256_hash = Column(String(64), nullable=False, index=True)

    # MIME type as declared by the uploader.
    mime_type = Column(String(128), nullable=False, default="application/pdf")

    # Size of the uploaded file in bytes.
    file_size_bytes = Column(Integer, nullable=True)

    # Number of pages detected during page classification.
    # NULL until the classifier runs.
    page_count = Column(Integer, nullable=True)

    # ── Storage reference ─────────────────────────────────────────────────────
    # Key understood by FileStorageService.retrieve(storage_path).
    # Format: "{workspace_id}/{file_id}_{original_filename}"
    # NULL until the file has been written to storage.
    storage_path = Column(String(1024), nullable=True)

    # Opaque identifier returned by FileStorageService.store().
    storage_file_id = Column(String(255), nullable=True)

    # ── Extraction configuration snapshot ─────────────────────────────────────
    # JSONB snapshot of pipeline configuration at registration time.
    # Example: {"prompt_version": "v3", "model": "gemini-1.5-pro",
    #           "vision_provider": "gemini", "text_provider": "openai"}
    # Used by retry logic to determine whether re-extraction is needed after
    # a configuration change (e.g. prompt upgrade).
    # NULL for versions registered before this field was introduced.
    pipeline_config = Column(JSONB, nullable=True)

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    status = Column(
        String(32),
        nullable=False,
        default=VersionStatus.REGISTERED.value,
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

    # Parent logical document.
    document = relationship(
        "BRDDocument",
        back_populates="versions",
    )

    # All extraction attempts made against this version.
    # Ordered by attempt_number ascending in queries.
    attempts = relationship(
        "IngestionAttempt",
        back_populates="version",
        order_by="IngestionAttempt.attempt_number",
        cascade="all, delete-orphan",
    )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def latest_attempt(self):
        """Return the most recent IngestionAttempt, or None."""
        if not self.attempts:
            return None
        return max(self.attempts, key=lambda a: a.attempt_number)

    def is_terminal(self) -> bool:
        """Return True if this version is in a terminal state (COMPLETED or FAILED)."""
        return self.status in (
            VersionStatus.COMPLETED.value,
            VersionStatus.FAILED.value,
        )

    def can_retry(self) -> bool:
        """Return True if the operator may schedule a new extraction attempt."""
        return self.status in (
            VersionStatus.FAILED.value,
            VersionStatus.RETRY_PENDING.value,
        )

    def __repr__(self) -> str:
        return (
            f"<DocumentVersion id={self.id} "
            f"document_id={self.document_id} "
            f"v{self.version_number} "
            f"status={self.status!r}>"
        )
