"""
app/models/brd_document.py

BRDDocument — the persistent identity record for every BRD or policy PDF
registered into FlowOS.

Design decisions
----------------
1.  Document identity is independent of extraction.
    A document exists the moment it is registered.  Extraction attempts are
    tracked separately on this same row (via `ingestion_status`).  This means
    a failed extraction does not destroy the document record, and a retry is a
    state transition — not a new row.

2.  Content hash is the deduplication key within a workspace.
    `sha256_hash` is computed from the raw PDF bytes before storage.
    If the same bytes are uploaded again the caller gets back the existing
    document ID.  A new filename with different bytes is a new document.
    An updated BRD (same filename, different bytes) produces a new version
    row that links back to the original via `previous_version_id`.

3.  Storage reference, not PDF binary.
    `storage_path` holds the key understood by `FileStorageService`.  The
    actual bytes live in the configured `StorageProvider` (local filesystem
    today, object storage later).  The database never holds binary content.

4.  Tenant/workspace consistency is enforced at the application layer.
    The model carries both `tenant_id` and `workspace_id`.  The service layer
    must verify that `workspace.tenant_id == brd_document.tenant_id` before
    inserting.  A `CheckConstraint` cannot cross tables in PostgreSQL without
    a trigger, so this is an explicit application-level invariant documented
    here and enforced in the ingestion service (Step 2 of the phase plan).

5.  Lifecycle status uses an explicit Python enum.
    This keeps the allowed values in one place and makes transitions
    type-safe.  The DB column is a plain VARCHAR with a CHECK constraint so
    Alembic does not need to manage a PostgreSQL enum type.

6.  `document_type` is a plain string.
    Current values: "brd", "policy".  New types can be added without a
    migration by updating the application-layer validation.

Relationships
-------------
    Tenant (1) ──< BRDDocument (N)   via tenant_id
    Workspace (1) ──< BRDDocument (N) via workspace_id
    BRDDocument (1) ──< BRDDocument (N) via previous_version_id  (version chain)

The `WorkflowKnowledge` model will be linked to `BRDDocument` in a later step
via a nullable `brd_document_id` FK (Step 3 of the phase plan).  That FK is not
added here so this step remains a pure additive change.
"""

import enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class DocumentType:
    """Allowed values for BRDDocument.document_type.

    Kept as plain class constants (not an enum) so new types can be added
    without a schema migration — only application-layer validation changes.
    """

    BRD    = "brd"     # Bank Requirements Document
    POLICY = "policy"  # Standalone policy document


class IngestionStatus(str, enum.Enum):
    """Lifecycle states for a BRD document.

    Transitions:
        REGISTERED   → PROCESSING  (ingestion job picks it up)
        PROCESSING   → COMPLETED   (extraction + mapping finished cleanly)
        PROCESSING   → FAILED      (unrecoverable error during extraction)
        FAILED       → RETRY_PENDING (operator schedules a retry)
        RETRY_PENDING → PROCESSING  (retry job picks it up)

    A COMPLETED document may transition back to RETRY_PENDING only if an
    operator explicitly requests re-extraction (e.g. after a prompt update).
    Re-extraction must not silently overwrite the existing WorkflowKnowledge
    rows — the service layer is responsible for versioning that content.
    """

    REGISTERED    = "REGISTERED"
    PROCESSING    = "PROCESSING"
    COMPLETED     = "COMPLETED"
    FAILED        = "FAILED"
    RETRY_PENDING = "RETRY_PENDING"


# Allowed status values as a tuple for the CHECK constraint
_VALID_STATUSES = tuple(s.value for s in IngestionStatus)


class BRDDocument(Base):
    """Persistent identity record for a registered BRD or policy PDF.

    One row per unique document version inside a workspace.  The same PDF
    bytes uploaded twice map to the same row (idempotent via sha256_hash +
    workspace_id uniqueness).  An updated BRD (different bytes) creates a
    new row with `previous_version_id` pointing at the row it supersedes.
    """

    __tablename__ = "brd_documents"

    __table_args__ = (
        # Within one workspace, the same content cannot be registered twice.
        # Different workspaces (even within the same tenant) may store the
        # same PDF independently because their extraction contexts differ.
        UniqueConstraint(
            "workspace_id",
            "sha256_hash",
            name="uq_brd_document_workspace_hash",
        ),
        # Status must be one of the declared lifecycle values.
        CheckConstraint(
            f"ingestion_status IN {_VALID_STATUSES}",
            name="ck_brd_document_ingestion_status",
        ),
        # document_type must be a known value.
        CheckConstraint(
            "document_type IN ('brd', 'policy')",
            name="ck_brd_document_type",
        ),
    )

    # ── Primary key ───────────────────────────────────────────────────────────
    id = Column(Integer, primary_key=True)

    # ── Tenant ownership ─────────────────────────────────────────────────────
    # Denormalised from workspace for efficient tenant-scoped queries and to
    # make cross-table isolation checks straightforward.
    # Invariant (enforced by service): tenant_id == workspace.tenant_id.
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Workspace ownership ───────────────────────────────────────────────────
    workspace_id = Column(
        Integer,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Document identity ─────────────────────────────────────────────────────

    # Original filename as supplied by the uploader.
    # Not unique — the same filename can appear in different document versions.
    # Do NOT use this as an identity key; use sha256_hash + workspace_id.
    original_filename = Column(String(512), nullable=False)

    # SHA-256 hex digest of the raw PDF bytes, computed before storage.
    # This is the deduplication key within a workspace.
    # Length 64 = 256 bits expressed as lowercase hex characters.
    sha256_hash = Column(String(64), nullable=False, index=True)

    # MIME type as declared by the uploader.  Used for display only —
    # magic-byte validation is the responsibility of the upload route.
    mime_type = Column(String(128), nullable=False, default="application/pdf")

    # Size of the original file in bytes.
    file_size_bytes = Column(Integer, nullable=True)

    # Number of pages detected during classification.
    # NULL until classification succeeds.
    page_count = Column(Integer, nullable=True)

    # ── Storage reference ─────────────────────────────────────────────────────
    # Key understood by FileStorageService / StorageProvider.
    # Format (current): "{workspace_id}/{file_id}_{original_filename}"
    # NULL until the file has been written to storage.
    storage_path = Column(String(1024), nullable=True)

    # Opaque identifier returned by FileStorageService.store().
    # Useful for retrieval without reconstructing the storage_path.
    storage_file_id = Column(String(255), nullable=True)

    # ── Classification ────────────────────────────────────────────────────────
    # "brd" or "policy" — see DocumentType constants above.
    document_type = Column(String(32), nullable=False, default=DocumentType.BRD)

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    ingestion_status = Column(
        String(32),
        nullable=False,
        default=IngestionStatus.REGISTERED.value,
        index=True,
    )

    # Human-readable reason for the last failure.  NULL when status is not FAILED.
    failure_reason = Column(Text, nullable=True)

    # How many extraction attempts have been made (including the current one).
    # Incremented each time status moves to PROCESSING.
    attempt_count = Column(Integer, nullable=False, default=0)

    # ── Versioning ────────────────────────────────────────────────────────────
    # Monotonically increasing integer within a document's version chain.
    # First registration is version 1.  A re-upload with different bytes
    # creates a new row with version = previous.version + 1.
    version = Column(Integer, nullable=False, default=1)

    # FK to the row this document supersedes.  NULL for version 1.
    # Follows the same workspace — cross-workspace version chains are not
    # allowed.
    previous_version_id = Column(
        Integer,
        ForeignKey("brd_documents.id", ondelete="SET NULL"),
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

    # Parent tenant — read-only navigation.
    tenant = relationship("Tenant", foreign_keys=[tenant_id])

    # Parent workspace — read-only navigation.
    workspace = relationship("Workspace", foreign_keys=[workspace_id])

    # Previous version in the chain (many-to-one, self-referential).
    previous_version = relationship(
        "BRDDocument",
        foreign_keys=[previous_version_id],
        remote_side="BRDDocument.id",
        back_populates="newer_versions",
    )

    # All newer versions that supersede this document (one-to-many).
    newer_versions = relationship(
        "BRDDocument",
        foreign_keys=[previous_version_id],
        back_populates="previous_version",
    )

    # All DocumentVersion rows for this logical document.
    # Ordered by version_number ascending in queries.
    # back_populates matches DocumentVersion.document.
    versions = relationship(
        "DocumentVersion",
        back_populates="document",
        order_by="DocumentVersion.version_number",
        cascade="all, delete-orphan",
    )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def is_terminal(self) -> bool:
        """Return True if the document is in a terminal lifecycle state.

        Terminal states: COMPLETED, FAILED.
        Non-terminal states: REGISTERED, PROCESSING, RETRY_PENDING.
        """
        return self.ingestion_status in (
            IngestionStatus.COMPLETED.value,
            IngestionStatus.FAILED.value,
        )

    def can_retry(self) -> bool:
        """Return True if an operator may schedule a retry for this document."""
        return self.ingestion_status in (
            IngestionStatus.FAILED.value,
            IngestionStatus.RETRY_PENDING.value,
        )

    def __repr__(self) -> str:
        return (
            f"<BRDDocument id={self.id} "
            f"tenant_id={self.tenant_id} "
            f"workspace_id={self.workspace_id} "
            f"filename={self.original_filename!r} "
            f"version={self.version} "
            f"status={self.ingestion_status!r}>"
        )
