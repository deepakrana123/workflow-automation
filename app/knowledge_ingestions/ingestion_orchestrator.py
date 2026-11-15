"""
app/knowledge_ingestions/ingestion_orchestrator.py

IngestionOrchestrator — coordinates the full BRD ingestion pipeline.

Responsibility
--------------
This service is the single entry point that ties together:

    1. DocumentRegistrationService   — register PDF, store file, create attempt
    2. PdfExtractionPipeline         — retrieve stored PDF, run multimodal extraction
    3. KnowledgeIngestionService     — LLM workflow extraction, persist knowledge

It owns all IngestionAttempt and DocumentVersion lifecycle transitions that
none of the three subordinate services implement.

What the orchestrator does NOT own
-----------------------------------
- File validation and storage          → DocumentRegistrationService
- PDF page classification/extraction   → PdfExtractionPipeline
- LLM workflow/rule/actor extraction   → KnowledgeIngestionService
- Embedding and catalog mapping        → KnowledgeIngestionService / EmbeddingMapper

Transaction boundaries
----------------------
The key constraint is: never hold an open DB transaction during an LLM call
or PDF extraction (which may take 30–120 seconds per document).

    T1  DocumentRegistrationService.register()
            INSERT brd_documents, document_versions, ingestion_attempts(PENDING)
            COMMIT — owned by DocumentRegistrationService

    T2  Orchestrator: PENDING → RUNNING
            UPDATE ingestion_attempts, document_versions, brd_documents
            COMMIT — short write-only, closed immediately

        ← PDF extraction runs here (no transaction held) →

    T3  On extraction failure:
            UPDATE ingestion_attempts (FAILED), document_versions (FAILED),
                   brd_documents (FAILED)
            COMMIT

        ← LLM workflow extraction runs here (no transaction held) →

    T4  On LLM/persist failure:
            UPDATE ingestion_attempts (FAILED), document_versions (FAILED),
                   brd_documents (FAILED)
            COMMIT

    T5  On success (committed by KnowledgeIngestionService internally):
            WorkflowKnowledge + all child rows
            COMMIT — owned by KnowledgeIngestionService

    T6  Post-success lifecycle update:
            UPDATE ingestion_attempts (COMPLETED + extracted_knowledge_id),
                   document_versions (COMPLETED), brd_documents (COMPLETED)
            COMMIT

Duplicate-document handling
----------------------------
If DocumentRegistrationService.register() returns is_duplicate=True, the
existing WorkflowKnowledge is NOT overwritten.  The orchestrator checks
whether the existing attempt's extracted_knowledge_id is already set (meaning
successful prior extraction) and returns early if so.  Only when the prior
attempt FAILED does it proceed with re-extraction.

Concurrent-processing guard
----------------------------
Before transitioning to RUNNING the orchestrator checks whether any attempt
on the same DocumentVersion is currently RUNNING.  If one is found, it
returns an OrchestrationResult with overall_status="SKIPPED" and does not
start a second run.  This is a best-effort application-level guard — it does
not replace a true distributed lock.

Partial extraction
-------------------
overall_status="PARTIAL" from PdfExtractionPipeline means some pages were
lost but usable content exists.  The orchestrator proceeds to
KnowledgeIngestionService but records a warning in OrchestrationResult and
does NOT set IngestionAttempt.status to COMPLETED silently.  It uses
AttemptStatus.COMPLETED with a pipeline_snapshot that records the partial
result so operators can inspect it.

Tenant isolation
----------------
Ownership is validated at every stage:
  - DocumentRegistrationService validates workspace → tenant at registration.
  - PdfExtractionPipeline validates document → workspace → tenant at extraction.
  - KnowledgeIngestionService scopes all mapping queries to workspace_id.
The orchestrator builds ExtractionOwnership from the RegistrationResult rows,
never from raw caller input, so the validated tenant/workspace identity
propagates to every stage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.knowledge_ingestions.document_registration import (
    DocumentRegistrationService,
    InvalidFileError,
    RegistrationError,
    RegistrationResult,
    WorkspaceNotFoundError,
    WorkspaceTenantMismatchError,
)
from app.knowledge_ingestions.exceptions import (
    RepositoryError,
    WorkflowExtractionError,
)
from app.knowledge_ingestions.extraction_result import (
    DocumentExtractionResult,
    ExtractionOwnership,
)
from app.knowledge_ingestions.pdf_extraction_pipeline import PdfExtractionPipeline
from app.knowledge_ingestions.service import KnowledgeIngestionService
from app.models.brd_document import BRDDocument, IngestionStatus
from app.models.document_version import DocumentVersion, VersionStatus
from app.models.ingestion_attempt import AttemptStatus, IngestionAttempt
from app.storage.service import FileStorageService


# ── Result contract ───────────────────────────────────────────────────────────

@dataclass
class OrchestrationResult:
    """Returned by IngestionOrchestrator.run() regardless of success or failure.

    Fields
    ------
    document_id           BRDDocument.id
    document_version_id   DocumentVersion.id
    ingestion_attempt_id  IngestionAttempt.id
    knowledge_id          WorkflowKnowledge.id — None when ingestion failed
    overall_status        "COMPLETED" | "PARTIAL" | "FAILED" | "SKIPPED"
    is_duplicate          True when the same PDF bytes were already registered
    warnings              Non-fatal issues (e.g. partial page extraction)
    error_message         Set when overall_status is FAILED
    rules_created         Count of structured BusinessRuleDefinition rows created
    rules_skipped         Count of raw rules already extracted (idempotent re-run)
    rules_error_message   Set when rule extraction failed but knowledge persisted
    """

    document_id:          int
    document_version_id:  int
    ingestion_attempt_id: int
    knowledge_id:         int | None   = None
    overall_status:       str          = "FAILED"
    is_duplicate:         bool         = False
    warnings:             list[str]    = field(default_factory=list)
    error_message:        str | None   = None
    rules_created:        int          = 0
    rules_skipped:        int          = 0
    rules_error_message:  str | None   = None


# ── Custom exceptions ─────────────────────────────────────────────────────────

class OrchestrationError(Exception):
    """Raised for unrecoverable orchestration failures that the caller must handle."""


# ── Orchestrator ──────────────────────────────────────────────────────────────

class IngestionOrchestrator:
    """Coordinate document registration, PDF extraction, and knowledge ingestion.

    Usage::

        orchestrator = IngestionOrchestrator(db)
        result = orchestrator.run(
            file_bytes=raw_pdf_bytes,
            original_filename="personal_loan_brd.pdf",
            tenant_id=1,
            workspace_id=2,
        )
        if result.overall_status == "COMPLETED":
            print(f"Knowledge ID: {result.knowledge_id}")
    """

    def __init__(
        self,
        db: Session,
        storage: FileStorageService | None = None,
        extraction_pipeline: PdfExtractionPipeline | None = None,
        ingestion_service: KnowledgeIngestionService | None = None,
        rule_extraction_service = None,
    ):
        self._db = db
        self._storage = storage or FileStorageService()
        self._registration_svc = DocumentRegistrationService(
            db=db, storage=self._storage
        )
        self._extraction_pipeline = extraction_pipeline or PdfExtractionPipeline(
            db=db, storage=self._storage
        )
        self._ingestion_svc = ingestion_service or KnowledgeIngestionService(db=db)
        
        # Rule extraction service — constructed on demand if not injected
        if rule_extraction_service is None:
            from app.rbac.rule_extractor import RuleExtractionService
            rule_extraction_service = RuleExtractionService()
        self._rule_extraction_svc = rule_extraction_service

    # ── Public API ────────────────────────────────────────────────────────────

    def run(
        self,
        *,
        file_bytes: bytes,
        original_filename: str,
        tenant_id: int,
        workspace_id: int,
        document_type: str = "brd",
        mime_type: str = "application/pdf",
    ) -> OrchestrationResult:
        """Register, extract and ingest a BRD PDF.

        Always returns an OrchestrationResult — never raises for domain
        failures (validation errors, extraction failures, LLM errors).
        Only raises OrchestrationError for unrecoverable internal failures
        that the caller must handle (e.g. missing DB rows).

        Args:
            file_bytes:        Raw PDF bytes.
            original_filename: Filename as supplied by the uploader.
            tenant_id:         Owning tenant (bank) ID.
            workspace_id:      Owning workspace ID.
            document_type:     "brd" or "policy".
            mime_type:         MIME type as declared by the uploader.

        Returns:
            OrchestrationResult with status and all created IDs.
        """

        # ── Stage 1: register document (T1) ──────────────────────────────────
        try:
            reg = self._registration_svc.register(
                file_bytes=file_bytes,
                original_filename=original_filename,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                document_type=document_type,
                mime_type=mime_type,
            )
        except (InvalidFileError, WorkspaceNotFoundError,
                WorkspaceTenantMismatchError) as exc:
            # Caller-correctable domain errors — not a system failure.
            logger.warning(
                "orchestrator_registration_rejected",
                extra={"extra_data": {
                    "tenant_id":    tenant_id,
                    "workspace_id": workspace_id,
                    "filename":     original_filename,
                    "reason":       str(exc),
                }},
            )
            # No DB rows were created — return a typed failure with no IDs.
            return OrchestrationResult(
                document_id=0,
                document_version_id=0,
                ingestion_attempt_id=0,
                overall_status="FAILED",
                error_message=str(exc),
            )
        except RegistrationError as exc:
            logger.error(
                "orchestrator_registration_failed",
                extra={"extra_data": {
                    "tenant_id":    tenant_id,
                    "workspace_id": workspace_id,
                    "filename":     original_filename,
                    "error":        str(exc),
                }},
            )
            return OrchestrationResult(
                document_id=0,
                document_version_id=0,
                ingestion_attempt_id=0,
                overall_status="FAILED",
                error_message=f"Registration failed: {exc}",
            )

        # ── Duplicate: re-extraction only if prior attempt failed ─────────────
        if reg.is_duplicate:
            return self._handle_duplicate(reg)

        # ── Stage 2: transition PENDING → RUNNING (T2) ───────────────────────
        already_running = self._check_running_guard(reg.version.id, reg.attempt.id)
        if already_running:
            return OrchestrationResult(
                document_id=reg.document.id,
                document_version_id=reg.version.id,
                ingestion_attempt_id=reg.attempt.id,
                overall_status="SKIPPED",
                is_duplicate=False,
                warnings=["Another attempt is already RUNNING for this version."],
            )

        try:
            self._transition_to_running(reg.document, reg.version, reg.attempt)
        except Exception:
            return OrchestrationResult(
                document_id=reg.document.id,
                document_version_id=reg.version.id,
                ingestion_attempt_id=reg.attempt.id,
                overall_status="SKIPPED",
                is_duplicate=False,
                warnings=["Concurrent attempt detected — RUNNING transition blocked."],
            )

        # ── Stage 3: PDF extraction (no transaction held) ─────────────────────
        ownership = ExtractionOwnership(
            tenant_id=reg.document.tenant_id,
            workspace_id=reg.document.workspace_id,
            document_id=reg.document.id,
            document_version_id=reg.version.id,
            ingestion_attempt_id=reg.attempt.id,
        )

        extraction: DocumentExtractionResult = self._extraction_pipeline.extract(
            version=reg.version,
            ownership=ownership,
        )

        if extraction.overall_status in ("FAILED", "EMPTY"):
            error_msg = extraction.error_message or (
                f"PDF extraction produced no usable content "
                f"(status={extraction.overall_status})."
            )
            self._transition_to_failed(
                document=reg.document,
                version=reg.version,
                attempt=reg.attempt,
                error_code="EXTRACTION_FAILED",
                error_message=error_msg,
                pipeline_snapshot={"extraction_status": extraction.overall_status,
                                   "total_pages": extraction.total_pages},
            )
            return OrchestrationResult(
                document_id=reg.document.id,
                document_version_id=reg.version.id,
                ingestion_attempt_id=reg.attempt.id,
                overall_status="FAILED",
                error_message=error_msg,
            )

        warnings: list[str] = list(extraction.warnings)
        if extraction.overall_status == "PARTIAL":
            warnings.append(
                f"Partial extraction: {len(extraction.succeeded_pages)} pages "
                f"succeeded, {len(extraction.failed_pages)} failed."
            )

        # ── Stage 4: knowledge ingestion (no transaction held during LLM) ─────
        full_text = extraction.full_text
        if not full_text.strip():
            self._transition_to_failed(
                document=reg.document,
                version=reg.version,
                attempt=reg.attempt,
                error_code="EMPTY_DOCUMENT",
                error_message="Extraction produced no text content.",
                pipeline_snapshot={"extraction_status": extraction.overall_status},
            )
            return OrchestrationResult(
                document_id=reg.document.id,
                document_version_id=reg.version.id,
                ingestion_attempt_id=reg.attempt.id,
                overall_status="FAILED",
                error_message="Extraction produced no text content.",
            )

        try:
            knowledge = self._ingestion_svc.ingest_from_text(
                document_text=full_text,
                workspace_id=reg.document.workspace_id,
                source_document=original_filename,
                brd_document_id=reg.document.id,
                document_version_id=reg.version.id,
                ingestion_attempt=reg.attempt,
            )
        except WorkflowExtractionError as exc:
            error_msg = str(exc)
            error_code = (
                "NO_ACTIONS_EXTRACTED"
                if "No actions" in error_msg
                else "LLM_PARSE_ERROR"
            )
            self._transition_to_failed(
                document=reg.document,
                version=reg.version,
                attempt=reg.attempt,
                error_code=error_code,
                error_message=error_msg,
                pipeline_snapshot={"extraction_status": extraction.overall_status,
                                   "total_pages": extraction.total_pages},
            )
            return OrchestrationResult(
                document_id=reg.document.id,
                document_version_id=reg.version.id,
                ingestion_attempt_id=reg.attempt.id,
                overall_status="FAILED",
                error_message=error_msg,
            )
        except RepositoryError as exc:
            self._transition_to_failed(
                document=reg.document,
                version=reg.version,
                attempt=reg.attempt,
                error_code="MAPPING_FAILED",
                error_message=str(exc),
                pipeline_snapshot={"extraction_status": extraction.overall_status},
            )
            return OrchestrationResult(
                document_id=reg.document.id,
                document_version_id=reg.version.id,
                ingestion_attempt_id=reg.attempt.id,
                overall_status="FAILED",
                error_message=str(exc),
            )
        except Exception as exc:
            self._transition_to_failed(
                document=reg.document,
                version=reg.version,
                attempt=reg.attempt,
                error_code="UNKNOWN",
                error_message=f"Unexpected ingestion error: {exc}",
                pipeline_snapshot=None,
            )
            return OrchestrationResult(
                document_id=reg.document.id,
                document_version_id=reg.version.id,
                ingestion_attempt_id=reg.attempt.id,
                overall_status="FAILED",
                error_message=f"Unexpected ingestion error: {exc}",
            )

        # ── Stage 5: structured rule extraction ──────────────────────────────
        # At this point knowledge is persisted and committed. Extract raw rules
        # into structured BusinessRuleDefinition rows.
        rule_extraction_result = self._extract_structured_rules(
            knowledge_id=knowledge.id,
            document_id=reg.document.id,
        )

        # ── Stage 6: transition → COMPLETED (T6) ─────────────────────────────
        overall = "PARTIAL" if extraction.overall_status == "PARTIAL" else "COMPLETED"
        self._transition_to_completed(
            document=reg.document,
            version=reg.version,
            attempt=reg.attempt,
            knowledge_id=knowledge.id,
            pipeline_snapshot={
                "extraction_status":  extraction.overall_status,
                "total_pages":        extraction.total_pages,
                "succeeded_pages":    len(extraction.succeeded_pages),
                "failed_pages":       len(extraction.failed_pages),
                "extractor_version":  extraction.extractor_version,
            },
        )

        logger.info(
            "orchestration_completed",
            extra={"extra_data": {
                "document_id":   reg.document.id,
                "version_id":    reg.version.id,
                "attempt_id":    reg.attempt.id,
                "knowledge_id":  knowledge.id,
                "tenant_id":     tenant_id,
                "workspace_id":  workspace_id,
                "overall_status": overall,
                "pages":         extraction.total_pages,
                "rules_created": rule_extraction_result["rules_created"],
                "rules_skipped": rule_extraction_result["rules_skipped"],
            }},
        )

        return OrchestrationResult(
            document_id=reg.document.id,
            document_version_id=reg.version.id,
            ingestion_attempt_id=reg.attempt.id,
            knowledge_id=knowledge.id,
            overall_status=overall,
            is_duplicate=False,
            warnings=warnings,
            rules_created=rule_extraction_result["rules_created"],
            rules_skipped=rule_extraction_result["rules_skipped"],
            rules_error_message=rule_extraction_result.get("error_message"),
        )

    # ── Private: duplicate handling ───────────────────────────────────────────

    def _handle_duplicate(self, reg: RegistrationResult) -> OrchestrationResult:
        """Handle a duplicate upload.

        If the most recent prior attempt already COMPLETED, return early —
        do not re-extract and do not create duplicate knowledge rows.
        If the prior attempt FAILED or is PENDING/RUNNING (stale), proceed
        with re-extraction on the new attempt created by the registration
        service.
        """
        prior_completed = (
            self._db.query(IngestionAttempt)
            .filter(
                IngestionAttempt.document_version_id == reg.version.id,
                IngestionAttempt.status == AttemptStatus.COMPLETED.value,
                IngestionAttempt.extracted_knowledge_id.isnot(None),
            )
            .order_by(IngestionAttempt.attempt_number.desc())
            .first()
        )

        if prior_completed is not None:
            logger.info(
                "orchestrator_duplicate_already_complete",
                extra={"extra_data": {
                    "document_id": reg.document.id,
                    "version_id":  reg.version.id,
                    "knowledge_id": prior_completed.extracted_knowledge_id,
                }},
            )
            return OrchestrationResult(
                document_id=reg.document.id,
                document_version_id=reg.version.id,
                ingestion_attempt_id=reg.attempt.id,
                knowledge_id=prior_completed.extracted_knowledge_id,
                overall_status="COMPLETED",
                is_duplicate=True,
                warnings=["Duplicate upload — existing successful extraction returned."],
            )

        # Prior attempt failed or is stale — fall through to re-extraction.
        # The new attempt (reg.attempt) is PENDING; run the full pipeline on it.
        logger.info(
            "orchestrator_duplicate_re_extracting",
            extra={"extra_data": {
                "document_id":    reg.document.id,
                "version_id":     reg.version.id,
                "new_attempt_id": reg.attempt.id,
            }},
        )

        # Delegate to the main pipeline by calling run() recursively is not
        # safe (re-registers the file).  Instead re-use the extraction +
        # ingestion stages directly on the existing version.
        return self._run_extraction_and_ingestion(
            document=reg.document,
            version=reg.version,
            attempt=reg.attempt,
            original_filename=reg.document.original_filename,
            is_duplicate=True,
        )

    def _run_extraction_and_ingestion(
        self,
        *,
        document: BRDDocument,
        version: DocumentVersion,
        attempt: IngestionAttempt,
        original_filename: str,
        is_duplicate: bool,
    ) -> OrchestrationResult:
        """Run stages 2–5 (RUNNING transition, extraction, ingestion, COMPLETED)
        on an already-registered document/version/attempt triple.

        Used by both the main path and the duplicate re-extraction path so the
        logic lives in exactly one place.
        """
        # ── Concurrent guard ──────────────────────────────────────────────────
        already_running = self._check_running_guard(version.id, attempt.id)
        if already_running:
            return OrchestrationResult(
                document_id=document.id,
                document_version_id=version.id,
                ingestion_attempt_id=attempt.id,
                overall_status="SKIPPED",
                is_duplicate=is_duplicate,
                warnings=["Another attempt is already RUNNING for this version."],
            )

        try:
            self._transition_to_running(document, version, attempt)
        except Exception:
            return OrchestrationResult(
                document_id=document.id,
                document_version_id=version.id,
                ingestion_attempt_id=attempt.id,
                overall_status="SKIPPED",
                is_duplicate=is_duplicate,
                warnings=["Concurrent attempt detected — RUNNING transition blocked."],
            )

        ownership = ExtractionOwnership(
            tenant_id=document.tenant_id,
            workspace_id=document.workspace_id,
            document_id=document.id,
            document_version_id=version.id,
            ingestion_attempt_id=attempt.id,
        )

        extraction = self._extraction_pipeline.extract(
            version=version,
            ownership=ownership,
        )

        if extraction.overall_status in ("FAILED", "EMPTY"):
            error_msg = extraction.error_message or (
                f"Extraction produced no usable content "
                f"(status={extraction.overall_status})."
            )
            self._transition_to_failed(
                document=document, version=version, attempt=attempt,
                error_code="EXTRACTION_FAILED",
                error_message=error_msg,
                pipeline_snapshot={"extraction_status": extraction.overall_status},
            )
            return OrchestrationResult(
                document_id=document.id,
                document_version_id=version.id,
                ingestion_attempt_id=attempt.id,
                overall_status="FAILED",
                is_duplicate=is_duplicate,
                error_message=error_msg,
            )

        warnings: list[str] = list(extraction.warnings)
        if extraction.overall_status == "PARTIAL":
            warnings.append(
                f"Partial extraction: {len(extraction.succeeded_pages)} pages "
                f"succeeded, {len(extraction.failed_pages)} failed."
            )

        full_text = extraction.full_text
        if not full_text.strip():
            self._transition_to_failed(
                document=document, version=version, attempt=attempt,
                error_code="EMPTY_DOCUMENT",
                error_message="Extraction produced no text content.",
                pipeline_snapshot=None,
            )
            return OrchestrationResult(
                document_id=document.id,
                document_version_id=version.id,
                ingestion_attempt_id=attempt.id,
                overall_status="FAILED",
                is_duplicate=is_duplicate,
                error_message="Extraction produced no text content.",
            )

        try:
            knowledge = self._ingestion_svc.ingest_from_text(
                document_text=full_text,
                workspace_id=document.workspace_id,
                source_document=original_filename,
                brd_document_id=document.id,
                document_version_id=version.id,
                ingestion_attempt=attempt,
            )
        except (WorkflowExtractionError, RepositoryError, Exception) as exc:
            error_code = "UNKNOWN"
            if isinstance(exc, WorkflowExtractionError):
                error_code = (
                    "NO_ACTIONS_EXTRACTED"
                    if "No actions" in str(exc)
                    else "LLM_PARSE_ERROR"
                )
            elif isinstance(exc, RepositoryError):
                error_code = "MAPPING_FAILED"

            self._transition_to_failed(
                document=document, version=version, attempt=attempt,
                error_code=error_code,
                error_message=str(exc),
                pipeline_snapshot=None,
            )
            return OrchestrationResult(
                document_id=document.id,
                document_version_id=version.id,
                ingestion_attempt_id=attempt.id,
                overall_status="FAILED",
                is_duplicate=is_duplicate,
                error_message=str(exc),
            )

        # ── Rule extraction after knowledge persists ──────────────────────────
        rule_extraction_result = self._extract_structured_rules(
            knowledge_id=knowledge.id,
            document_id=document.id,
        )

        overall = "PARTIAL" if extraction.overall_status == "PARTIAL" else "COMPLETED"
        self._transition_to_completed(
            document=document, version=version, attempt=attempt,
            knowledge_id=knowledge.id,
            pipeline_snapshot={
                "extraction_status": extraction.overall_status,
                "total_pages":       extraction.total_pages,
                "succeeded_pages":   len(extraction.succeeded_pages),
                "failed_pages":      len(extraction.failed_pages),
            },
        )

        return OrchestrationResult(
            document_id=document.id,
            document_version_id=version.id,
            ingestion_attempt_id=attempt.id,
            knowledge_id=knowledge.id,
            overall_status=overall,
            is_duplicate=is_duplicate,
            warnings=warnings,
            rules_created=rule_extraction_result["rules_created"],
            rules_skipped=rule_extraction_result["rules_skipped"],
            rules_error_message=rule_extraction_result.get("error_message"),
        )

    # ── Private: lifecycle transitions ────────────────────────────────────────

    def _check_running_guard(
        self, version_id: int, current_attempt_id: int
    ) -> bool:
        """Return True if another attempt on this version is currently RUNNING.

        This is a best-effort application-level check. The DB partial unique
        index (uq_one_running_attempt_per_version) provides the hard guarantee
        and will raise IntegrityError in _transition_to_running if two processes
        race past this SELECT simultaneously.
        """
        running = (
            self._db.query(IngestionAttempt)
            .filter(
                IngestionAttempt.document_version_id == version_id,
                IngestionAttempt.status == AttemptStatus.RUNNING.value,
                IngestionAttempt.id != current_attempt_id,
            )
            .first()
        )
        return running is not None

    def _transition_to_running(
        self,
        document: BRDDocument,
        version: DocumentVersion,
        attempt: IngestionAttempt,
    ) -> None:
        """PENDING → RUNNING. Short commit — no transaction held afterward.

        If the DB partial unique index fires (two concurrent attempts racing),
        IntegrityError is raised here. The caller catches it and returns SKIPPED.
        """
        from sqlalchemy.exc import IntegrityError as _IntegrityError
        now = datetime.now(timezone.utc)
        attempt.status     = AttemptStatus.RUNNING.value
        attempt.started_at = now
        version.status     = VersionStatus.PROCESSING.value
        document.ingestion_status = IngestionStatus.PROCESSING.value
        document.attempt_count    = (document.attempt_count or 0) + 1
        try:
            self._db.commit()
        except _IntegrityError:
            self._db.rollback()
            raise  # caller (run / _run_extraction_and_ingestion) catches this
        self._db.refresh(attempt)
        self._db.refresh(version)
        self._db.refresh(document)

    def _transition_to_failed(
        self,
        *,
        document: BRDDocument,
        version: DocumentVersion,
        attempt: IngestionAttempt,
        error_code: str,
        error_message: str,
        pipeline_snapshot: dict | None,
    ) -> None:
        """RUNNING → FAILED. Records error details on the attempt row."""
        now = datetime.now(timezone.utc)
        attempt.status        = AttemptStatus.FAILED.value
        attempt.completed_at  = now
        attempt.error_code    = error_code
        attempt.error_message = error_message[:2000]   # guard against huge tracebacks
        if pipeline_snapshot is not None:
            attempt.pipeline_snapshot = pipeline_snapshot
        version.status              = VersionStatus.FAILED.value
        document.ingestion_status   = IngestionStatus.FAILED.value
        document.failure_reason     = error_message[:500]
        try:
            self._db.commit()
        except Exception as exc:
            self._db.rollback()
            logger.error(
                "orchestrator_failed_transition_commit_error",
                extra={"extra_data": {
                    "attempt_id": attempt.id,
                    "error":      str(exc),
                }},
            )

    def _transition_to_completed(
        self,
        *,
        document: BRDDocument,
        version: DocumentVersion,
        attempt: IngestionAttempt,
        knowledge_id: int,
        pipeline_snapshot: dict | None,
    ) -> None:
        """RUNNING → COMPLETED on DocumentVersion and BRDDocument.

        IngestionAttempt status and extracted_knowledge_id are already committed
        by KnowledgeIngestionService._ingest_from_extracted_text() in the merged
        T5+T6 transaction. This method only updates the version and document
        status rows — a lightweight commit.
        """
        now = datetime.now(timezone.utc)
        # Refresh attempt in case T5+T6 already committed its fields.
        try:
            self._db.refresh(attempt)
        except Exception:
            pass
        # Only write attempt fields that may not have been set yet
        # (e.g. pipeline_snapshot which the ingestion service does not set).
        if pipeline_snapshot is not None and attempt.pipeline_snapshot is None:
            attempt.pipeline_snapshot = pipeline_snapshot
        if attempt.completed_at is None:
            attempt.completed_at = now
        if attempt.extracted_knowledge_id is None:
            attempt.extracted_knowledge_id = knowledge_id

        version.status              = VersionStatus.COMPLETED.value
        document.ingestion_status   = IngestionStatus.COMPLETED.value
        document.failure_reason     = None
        try:
            self._db.commit()
        except Exception as exc:
            self._db.rollback()
            logger.error(
                "orchestrator_completed_transition_commit_error",
                extra={"extra_data": {
                    "attempt_id":   attempt.id,
                    "knowledge_id": knowledge_id,
                    "error":        str(exc),
                }},
            )


    def _extract_structured_rules(
        self,
        *,
        knowledge_id: int,
        document_id: int,
    ) -> dict:
        """Extract raw rules into structured BusinessRuleDefinition rows.

        Runs AFTER knowledge is persisted and committed, so the knowledge ID
        is stable and can be passed safely to the rule extraction service.

        Returns a dict:
            {
              "rules_created": int,
              "rules_skipped": int,
              "error_message": str | None,   (set only if extraction failed)
            }

        On exception:
        - The error is logged.
        - Persisted WorkflowKnowledge and raw rules are NOT deleted.
        - The error message is returned in the dict so the orchestrator
          can include it in OrchestrationResult as rules_error_message.
        - overall_status remains "COMPLETED" — rule extraction is post-hoc
          and does not invalidate successful knowledge extraction.
        """
        try:
            result = self._rule_extraction_svc.extract_for_knowledge(
                db=self._db,
                workflow_knowledge_id=knowledge_id,
            )
            return {
                "rules_created": result.get("rules_created", 0),
                "rules_skipped": result.get("rules_skipped", 0),
                "error_message": None,
            }
        except ValueError as exc:
            # Knowledge ID not found — should not happen in normal flow,
            # but log and return gracefully.
            error_msg = f"Knowledge not found for rule extraction: {exc}"
            logger.warning(
                "orchestrator_rule_extraction_knowledge_not_found",
                extra={"extra_data": {
                    "knowledge_id":  knowledge_id,
                    "document_id":   document_id,
                    "error":         str(exc),
                }},
            )
            return {
                "rules_created": 0,
                "rules_skipped": 0,
                "error_message": error_msg,
            }
        except Exception as exc:
            # Unexpected error — preserve knowledge, log the failure.
            error_msg = f"Structured rule extraction failed: {exc}"
            logger.error(
                "orchestrator_rule_extraction_failed",
                extra={"extra_data": {
                    "knowledge_id":  knowledge_id,
                    "document_id":   document_id,
                    "error":         str(exc),
                }},
            )
            return {
                "rules_created": 0,
                "rules_skipped": 0,
                "error_message": error_msg,
            }
