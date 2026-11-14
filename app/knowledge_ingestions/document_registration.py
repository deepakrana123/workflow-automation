"""
app/knowledge_ingestions/document_registration.py

DocumentRegistrationService — the entry point for registering a BRD or policy
PDF before extraction begins.

Responsibilities
----------------
1.  Verify that workspace belongs to tenant (tenant/workspace consistency).
2.  Validate the uploaded file (non-empty, PDF magic bytes).
3.  Compute SHA-256 content hash.
4.  Detect duplicate uploads (same bytes already registered in this workspace).
5.  Store the original file bytes via FileStorageService.
6.  Create or return the logical BRDDocument row.
7.  Create an immutable DocumentVersion row.
8.  Create an initial IngestionAttempt row (status = PENDING).
9.  Commit the database transaction.
10. Return a RegistrationResult with all created IDs.

Storage key format
------------------
    {tenant_id}/{workspace_id}/{hash_prefix}/{file_id}_{sanitised_filename}

The tenant_id prefix is the structural cross-tenant isolation guarantee.
Even if two workspaces at different banks upload identical bytes, the files
land in different directories and the DB rows are scoped to different tenants.

Atomicity guarantee (best-effort)
----------------------------------
File storage and database writes are NOT in the same transaction.

The safe ordering is:
    1. Store file (storage is durable first).
    2. Commit database rows.
    3. If commit fails → delete the stored file (cleanup), re-raise.

If the cleanup delete also fails, the stored file is an orphan.
Orphaned files do not cause correctness problems (the DB row was never
committed) but consume storage.  A future reconciliation job can detect
and remove orphans by comparing storage keys against DocumentVersion rows.

Duplicate detection
-------------------
Deduplication is scoped to the workspace (not the tenant).
Two different workspaces may legitimately store the same PDF because their
extraction context (workspace name, actors, rules) differs.

If the same bytes are uploaded to the same workspace twice:
  - The existing DocumentVersion is returned.
  - A new IngestionAttempt is created on the existing version.
  - No new file is stored (the existing storage_path is used).
  - The caller receives DuplicateDocumentResult to signal this case.

Concurrency
-----------
Two concurrent uploads of identical bytes to the same workspace will both
pass the hash check (the first INSERT hasn't committed yet).  The second
INSERT will hit the UNIQUE constraint on (workspace_id, sha256_hash) on
brd_documents.  This is caught as an IntegrityError, the transaction is
rolled back, and the service re-fetches the existing document to build a
consistent RegistrationResult.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.execution.python.base.generate_model import GeneratedFile
from app.models.brd_document import BRDDocument, DocumentType, IngestionStatus
from app.models.document_version import DocumentVersion, VersionStatus
from app.models.ingestion_attempt import IngestionAttempt, AttemptStatus
from app.models.workspace import Workspace
from app.storage.service import FileStorageService
from app.storage.exceptions import StorageError
from app.core.logger import logger


# PDF magic bytes — first 4 bytes of every valid PDF file.
_PDF_MAGIC = b"%PDF"

# Characters that are safe in a storage key filename component.
# Everything else is replaced with "_".
_SAFE_FILENAME_RE = re.compile(r"[^\w.\-]")


def _sanitise_filename(name: str) -> str:
    """Replace unsafe characters in a filename with underscores.

    Keeps alphanumerics, dots, hyphens and underscores.
    Prevents path traversal and special character injection in storage keys.
    """
    return _SAFE_FILENAME_RE.sub("_", name)[:200]  # 200-char cap for key safety


def _sha256(content: bytes) -> str:
    """Return lowercase hex SHA-256 digest of ``content``."""
    return hashlib.sha256(content).hexdigest()


def _build_storage_key(
    tenant_id: int,
    workspace_id: int,
    sha256_hash: str,
    file_id: str,
    original_filename: str,
) -> str:
    """Build the storage key for a BRD PDF.

    Format: {tenant_id}/{workspace_id}/{hash_prefix}/{file_id}_{filename}

    The tenant_id prefix provides structural cross-tenant isolation at the
    storage layer — different tenants' files land in different directories
    regardless of workspace_id or filename.

    The first 8 hex characters of the hash form a prefix directory, which
    distributes files across subdirectories to avoid large flat directories
    in filesystem-backed providers.
    """
    safe_name = _sanitise_filename(original_filename)
    return str(
        PurePosixPath(str(tenant_id))
        / str(workspace_id)
        / sha256_hash[:8]
        / f"{file_id}_{safe_name}"
    )


# ── Return types ──────────────────────────────────────────────────────────────

@dataclass
class RegistrationResult:
    """Returned by DocumentRegistrationService.register() on success.

    ``is_duplicate`` is True when the same bytes were already registered in
    this workspace.  In that case document and version are the existing rows,
    and attempt is a freshly created IngestionAttempt on the existing version.
    """

    document: BRDDocument
    version: DocumentVersion
    attempt: IngestionAttempt
    is_duplicate: bool = False


# ── Custom exceptions ─────────────────────────────────────────────────────────

class RegistrationError(Exception):
    """Base class for document registration errors."""


class InvalidFileError(RegistrationError):
    """Raised when the uploaded file fails validation."""


class WorkspaceTenantMismatchError(RegistrationError):
    """Raised when workspace.tenant_id != supplied tenant_id."""


class WorkspaceNotFoundError(RegistrationError):
    """Raised when the workspace does not exist or is inactive."""


# ── Service ───────────────────────────────────────────────────────────────────

class DocumentRegistrationService:
    """Register an uploaded BRD PDF and return the created DB records.

    Usage::

        svc = DocumentRegistrationService(db)
        result = svc.register(
            file_bytes=raw_pdf_bytes,
            original_filename="personal_loan_brd_v3.pdf",
            tenant_id=1,
            workspace_id=2,
        )
        # result.document  → BRDDocument
        # result.version   → DocumentVersion
        # result.attempt   → IngestionAttempt (PENDING)
        # result.is_duplicate → True if same bytes were already registered
    """

    def __init__(
        self,
        db: Session,
        storage: FileStorageService | None = None,
    ):
        self._db      = db
        self._storage = storage or FileStorageService()

    # ── Public API ────────────────────────────────────────────────────────────

    def register(
        self,
        *,
        file_bytes: bytes,
        original_filename: str,
        tenant_id: int,
        workspace_id: int,
        document_type: str = DocumentType.BRD,
        mime_type: str = "application/pdf",
        pipeline_config: dict | None = None,
    ) -> RegistrationResult:
        """Register a BRD PDF.

        Steps:
            1. Validate the file.
            2. Verify workspace → tenant ownership.
            3. Compute SHA-256 hash.
            4. Check for duplicate (same hash, same workspace).
            5. Store the file via FileStorageService.
            6. Persist BRDDocument + DocumentVersion + IngestionAttempt.
            7. Return RegistrationResult.

        Args:
            file_bytes:        Raw PDF bytes.
            original_filename: Filename as supplied by the uploader.
            tenant_id:         ID of the owning tenant (bank).
            workspace_id:      ID of the owning workspace.
            document_type:     "brd" or "policy".
            mime_type:         MIME type as declared by the uploader.
            pipeline_config:   Optional JSONB snapshot of extraction config.

        Returns:
            RegistrationResult with document, version, attempt and is_duplicate.

        Raises:
            InvalidFileError:            File is empty or not a valid PDF.
            WorkspaceNotFoundError:      Workspace does not exist or is inactive.
            WorkspaceTenantMismatchError: workspace.tenant_id != tenant_id.
            RegistrationError:           Any other registration failure.
        """
        # ── Step 1: validate file ─────────────────────────────────────────────
        self._validate_file(file_bytes, original_filename)

        # ── Step 2: verify workspace → tenant ownership ───────────────────────
        workspace = self._require_workspace(workspace_id, tenant_id)

        # ── Step 3: compute content hash ──────────────────────────────────────
        sha256_hash = _sha256(file_bytes)
        file_size   = len(file_bytes)

        # ── Step 4: duplicate detection ───────────────────────────────────────
        existing_doc = self._find_existing_document(workspace_id, sha256_hash)
        if existing_doc is not None:
            return self._handle_duplicate(existing_doc, pipeline_config)

        # ── Step 5: store file ────────────────────────────────────────────────
        stored = self._store_file(
            file_bytes=file_bytes,
            original_filename=original_filename,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            sha256_hash=sha256_hash,
            mime_type=mime_type,
        )

        # ── Steps 6-7: persist DB rows, clean up file on failure ──────────────
        try:
            result = self._persist(
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                original_filename=original_filename,
                sha256_hash=sha256_hash,
                mime_type=mime_type,
                file_size=file_size,
                storage_path=stored.storage_path,
                storage_file_id=stored.file_id,
                document_type=document_type,
                pipeline_config=pipeline_config,
            )
        except IntegrityError:
            # Race condition: concurrent upload of the same bytes committed first.
            # Roll back and re-fetch the winning row.
            self._db.rollback()
            self._cleanup_storage(stored.storage_path)

            existing_doc = self._find_existing_document(workspace_id, sha256_hash)
            if existing_doc is None:
                raise RegistrationError(
                    "Concurrent registration conflict — please retry."
                )
            return self._handle_duplicate(existing_doc, pipeline_config)

        except Exception as exc:
            # DB commit failed for any other reason — remove the stored file.
            self._db.rollback()
            self._cleanup_storage(stored.storage_path)
            raise RegistrationError(
                f"Database registration failed: {exc}"
            ) from exc

        logger.info(
            "document_registered",
            extra={"extra_data": {
                "document_id":  result.document.id,
                "version_id":   result.version.id,
                "attempt_id":   result.attempt.id,
                "workspace_id": workspace_id,
                "tenant_id":    tenant_id,
                "sha256":       sha256_hash,
                "filename":     original_filename,
                "size_bytes":   file_size,
            }},
        )

        return result

    def retrieve_original(self, storage_path: str) -> bytes:
        """Return the raw bytes of a previously stored PDF.

        Args:
            storage_path: The value from DocumentVersion.storage_path.

        Returns:
            Raw PDF bytes.

        Raises:
            FileNotFoundInStorageError: If the file no longer exists.
        """
        return self._storage.retrieve(storage_path)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _validate_file(self, file_bytes: bytes, filename: str) -> None:
        """Raise InvalidFileError if the file cannot be accepted."""
        if not file_bytes:
            raise InvalidFileError(f"Uploaded file '{filename}' is empty.")
        if not file_bytes.startswith(_PDF_MAGIC):
            raise InvalidFileError(
                f"'{filename}' does not appear to be a valid PDF "
                f"(magic bytes: {file_bytes[:4]!r})."
            )

    def _require_workspace(self, workspace_id: int, tenant_id: int) -> Workspace:
        """Return the workspace or raise a typed exception."""
        workspace = (
            self._db.query(Workspace)
            .filter(
                Workspace.id == workspace_id,
                Workspace.active.is_(True),
            )
            .first()
        )
        if workspace is None:
            raise WorkspaceNotFoundError(
                f"Workspace {workspace_id} not found or is inactive."
            )
        if workspace.tenant_id != tenant_id:
            raise WorkspaceTenantMismatchError(
                f"Workspace {workspace_id} belongs to tenant "
                f"{workspace.tenant_id}, not tenant {tenant_id}."
            )
        return workspace

    def _find_existing_document(
        self, workspace_id: int, sha256_hash: str
    ) -> BRDDocument | None:
        """Return an existing BRDDocument if the same bytes are already registered."""
        return (
            self._db.query(BRDDocument)
            .filter(
                BRDDocument.workspace_id == workspace_id,
                BRDDocument.sha256_hash  == sha256_hash,
            )
            .first()
        )

    def _store_file(
        self,
        *,
        file_bytes: bytes,
        original_filename: str,
        tenant_id: int,
        workspace_id: int,
        sha256_hash: str,
        mime_type: str,
    ):
        """Store file bytes via FileStorageService using a tenant-scoped key.

        The key is built manually here (instead of using FileStorageService's
        default workspace-only key) to include tenant_id as the top-level
        directory, providing structural cross-tenant isolation.
        """
        import uuid
        from app.storage.local import LocalStorageProvider

        file_id = uuid.uuid4().hex
        key = _build_storage_key(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            sha256_hash=sha256_hash,
            file_id=file_id,
            original_filename=original_filename,
        )

        generated = GeneratedFile(
            file_name=_sanitise_filename(original_filename),
            mime_type=mime_type,
            content=file_bytes,
            extension=".pdf",
            size=len(file_bytes),
        )

        # Write directly through the provider using our custom key so we
        # control the full path (including tenant prefix).
        try:
            self._storage._provider.save(key, file_bytes)
        except StorageError as exc:
            raise RegistrationError(
                f"File storage failed for '{original_filename}': {exc}"
            ) from exc

        # Return a minimal object with the fields we need.
        from app.execution.python.base.stored import StoredFile
        return StoredFile(
            file_id=file_id,
            file_name=generated.file_name,
            storage_provider=self._storage._provider.provider_name,
            storage_path=key,
            public_url=None,
            generated_file=generated,
        )

    def _cleanup_storage(self, storage_path: str) -> None:
        """Best-effort: delete a stored file after a DB failure.

        Never raises — a cleanup failure is logged as a warning.
        Orphaned files are acceptable (reconciliation job can remove them)
        but a cleanup failure must not mask the original DB error.
        """
        try:
            self._storage._provider.delete(storage_path)
            logger.info(
                "document_storage_cleaned_up",
                extra={"extra_data": {"storage_path": storage_path}},
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "document_storage_cleanup_failed",
                extra={"extra_data": {
                    "storage_path": storage_path,
                    "error": str(exc),
                }},
            )

    def _persist(
        self,
        *,
        tenant_id: int,
        workspace_id: int,
        original_filename: str,
        sha256_hash: str,
        mime_type: str,
        file_size: int,
        storage_path: str,
        storage_file_id: str,
        document_type: str,
        pipeline_config: dict | None,
    ) -> RegistrationResult:
        """Write BRDDocument + DocumentVersion + IngestionAttempt, then commit."""

        # BRDDocument — logical identity
        doc = BRDDocument(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            original_filename=original_filename,
            sha256_hash=sha256_hash,
            mime_type=mime_type,
            file_size_bytes=file_size,
            storage_path=storage_path,
            storage_file_id=storage_file_id,
            document_type=document_type,
            ingestion_status=IngestionStatus.REGISTERED.value,
            attempt_count=0,
            version=1,
        )
        self._db.add(doc)
        self._db.flush()  # assigns doc.id

        # DocumentVersion — immutable file revision
        ver = DocumentVersion(
            document_id=doc.id,
            version_number=1,
            original_filename=original_filename,
            sha256_hash=sha256_hash,
            mime_type=mime_type,
            file_size_bytes=file_size,
            storage_path=storage_path,
            storage_file_id=storage_file_id,
            pipeline_config=pipeline_config,
            status=VersionStatus.REGISTERED.value,
        )
        self._db.add(ver)
        self._db.flush()  # assigns ver.id

        # IngestionAttempt — first pipeline execution (queued)
        attempt = IngestionAttempt(
            document_version_id=ver.id,
            attempt_number=1,
            status=AttemptStatus.PENDING.value,
        )
        self._db.add(attempt)
        self._db.commit()

        # Refresh to populate server defaults (created_at, updated_at)
        self._db.refresh(doc)
        self._db.refresh(ver)
        self._db.refresh(attempt)

        return RegistrationResult(
            document=doc,
            version=ver,
            attempt=attempt,
            is_duplicate=False,
        )

    def _handle_duplicate(
        self,
        existing_doc: BRDDocument,
        pipeline_config: dict | None,
    ) -> RegistrationResult:
        """Return a RegistrationResult for an already-registered document.

        Re-uses the existing DocumentVersion.
        Creates a new IngestionAttempt so the caller can trigger re-extraction
        without overwriting the history of previous attempts.
        """
        # Find the matching version (same hash, same document)
        existing_ver = (
            self._db.query(DocumentVersion)
            .filter(
                DocumentVersion.document_id == existing_doc.id,
                DocumentVersion.sha256_hash == existing_doc.sha256_hash,
            )
            .first()
        )

        if existing_ver is None:
            # Version row missing (data inconsistency) — treat as new document
            # by raising so the caller can decide how to handle it.
            raise RegistrationError(
                f"Document {existing_doc.id} has no matching DocumentVersion. "
                "Database may be inconsistent."
            )

        # Determine next attempt number
        from sqlalchemy import func as sa_func
        max_attempt = (
            self._db.query(sa_func.max(IngestionAttempt.attempt_number))
            .filter(IngestionAttempt.document_version_id == existing_ver.id)
            .scalar()
        ) or 0

        attempt = IngestionAttempt(
            document_version_id=existing_ver.id,
            attempt_number=max_attempt + 1,
            status=AttemptStatus.PENDING.value,
            pipeline_snapshot=pipeline_config,
        )
        self._db.add(attempt)
        self._db.commit()
        self._db.refresh(attempt)

        logger.info(
            "document_duplicate_registered",
            extra={"extra_data": {
                "document_id":    existing_doc.id,
                "version_id":     existing_ver.id,
                "attempt_number": attempt.attempt_number,
                "workspace_id":   existing_doc.workspace_id,
                "sha256":         existing_doc.sha256_hash,
            }},
        )

        return RegistrationResult(
            document=existing_doc,
            version=existing_ver,
            attempt=attempt,
            is_duplicate=True,
        )
