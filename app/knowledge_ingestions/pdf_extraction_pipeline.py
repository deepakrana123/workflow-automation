"""
app/knowledge_ingestions/pdf_extraction_pipeline.py

PdfExtractionPipeline — retrieves a stored PDF and runs the full multimodal
extraction pipeline, returning a structured DocumentExtractionResult.

Responsibilities
----------------
1.  Retrieve the original PDF bytes from FileStorageService using the
    storage_path recorded on the DocumentVersion.  Never accepts an
    arbitrary filesystem path from a client.

2.  Validate that the DocumentVersion belongs to the specified document
    and tenant (ownership check).

3.  Write the bytes to a managed temporary file, run extraction, and
    guarantee temp-file cleanup in a finally block regardless of outcome.

4.  Call the existing MultiModalDocumentExtractor, which runs the full
    PageClassifier → three-thread pipeline (body text, visual, appendix).
    This component is reused unchanged.

5.  Translate the existing internal types into the structured
    DocumentExtractionResult / PageExtractionOutput schema so downstream
    components (WorkflowExtractor, provenance tracking, IngestionAttempt
    diagnostics) have full per-page detail.

6.  Always return a DocumentExtractionResult — never raises to the caller.
    Failures are encoded as overall_status=FAILED and in error_message.

Design constraints
------------------
- Atomic wrt temp files: the temp file is deleted in a finally block even
  if extraction raises or the process is interrupted.

- DB and storage are not modified here.  The pipeline is a pure-function
  computation layer.  The caller (IngestionOrchestrator, Step 5) updates
  DocumentVersion.status and IngestionAttempt based on the result.

- The existing MultiModalDocumentExtractor.extract() returns a merged
  string.  We call it and also run the PageClassifier separately to build
  per-page records.  Running PageClassifier twice is cheap (local, no LLM,
  no I/O beyond reading the PDF) and avoids changing MultiModalDocumentExtractor.

- If PageClassifier raises we fall back to a single synthetic page record
  that wraps the full merged string.  The downstream WorkflowExtractor still
  receives a valid full_text from result.full_text — backward compatible.

Ownership validation
--------------------
The pipeline validates:
    version.document_id      == document.id
    document.workspace_id    == ownership.workspace_id
    document.tenant_id       == ownership.tenant_id

This prevents an attacker who obtains a valid version_id from accessing a
version that belongs to a different tenant's document.

Backward compatibility
----------------------
result.full_text produces the same merged string the existing WorkflowExtractor
already consumes.  No change to WorkflowExtractor is needed in this step.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.knowledge_ingestions.exceptions import DocumentExtractionError
from app.knowledge_ingestions.extraction_result import (
    DocumentExtractionResult,
    ExtractionOwnership,
    ExtractionProvider,
    PageExtractionOutput,
    PageStatus,
    PageType,
    compute_overall_status,
    make_failed_document,
)
from app.knowledge_ingestions.multimodal_extractor import MultiModalDocumentExtractor
from app.knowledge_ingestions.page_classifier import (
    DocumentClassification,
    PageClassifier,
    PageClassification,
)
from app.knowledge_ingestions.table_image_extractor import (
    ExtractionStatus as VisionStatus,
    PageExtractionResult,
)
from app.models.brd_document import BRDDocument
from app.models.document_version import DocumentVersion
from app.storage.exceptions import FileNotFoundInStorageError, StorageError
from app.storage.service import FileStorageService

# Bump this when the extraction logic changes in a way that warrants
# re-extracting previously completed versions.
_EXTRACTOR_VERSION = "1.0.0"

# Map PageClassifier string labels → PageType enum
_PAGE_TYPE_MAP: dict[str, PageType] = {
    "text":     PageType.TEXT,
    "table":    PageType.TABLE,
    "image":    PageType.IMAGE,
    "appendix": PageType.APPENDIX,
}


class PdfExtractionPipeline:
    """Run the full multimodal extraction pipeline for a DocumentVersion.

    Usage::

        pipeline = PdfExtractionPipeline(db)
        result = pipeline.extract(
            version=doc_version_row,
            ownership=ExtractionOwnership(
                tenant_id=1, workspace_id=2,
                document_id=3, document_version_id=4,
                ingestion_attempt_id=5,
            ),
        )
        # result.full_text   → merged string for WorkflowExtractor
        # result.pages       → per-page details for provenance tracking
        # result.overall_status → "SUCCESS" | "PARTIAL" | "FAILED" | "EMPTY"
    """

    def __init__(
        self,
        db: Session,
        storage: FileStorageService | None = None,
        extractor: MultiModalDocumentExtractor | None = None,
        classifier: PageClassifier | None = None,
    ):
        self._db        = db
        self._storage   = storage   or FileStorageService()
        self._extractor = extractor or MultiModalDocumentExtractor()
        self._classifier = classifier or PageClassifier()

    # ── Public API ────────────────────────────────────────────────────────────

    def extract(
        self,
        version: DocumentVersion,
        ownership: ExtractionOwnership,
    ) -> DocumentExtractionResult:
        """Extract text from the PDF stored at version.storage_path.

        Always returns a DocumentExtractionResult.  Never raises.

        Args:
            version:   The DocumentVersion ORM row.  Must already be loaded;
                       this method does not query the database.
            ownership: Caller-supplied context used for validation and
                       carried through to the result.

        Returns:
            DocumentExtractionResult with per-page detail and overall status.
        """
        # ── Ownership validation ──────────────────────────────────────────────
        validation_error = self._validate_ownership(version, ownership)
        if validation_error:
            logger.error(
                "pdf_pipeline_ownership_mismatch",
                extra={"extra_data": {
                    "version_id": version.id,
                    "ownership":  ownership,
                    "reason":     validation_error,
                }},
            )
            return make_failed_document(
                ownership=ownership,
                error_message=f"Ownership validation failed: {validation_error}",
            )

        storage_path = version.storage_path
        if not storage_path:
            return make_failed_document(
                ownership=ownership,
                error_message="DocumentVersion.storage_path is not set.",
            )

        # ── Retrieve PDF bytes ────────────────────────────────────────────────
        try:
            pdf_bytes = self._storage.retrieve(storage_path)
        except FileNotFoundInStorageError:
            return make_failed_document(
                ownership=ownership,
                error_message=f"PDF not found in storage: {storage_path}",
            )
        except StorageError as exc:
            return make_failed_document(
                ownership=ownership,
                error_message=f"Storage retrieval failed: {exc}",
            )

        # ── Run extraction inside a managed temp file ─────────────────────────
        return self._extract_from_bytes(
            pdf_bytes=pdf_bytes,
            original_filename=version.original_filename or "document.pdf",
            ownership=ownership,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _validate_ownership(
        self,
        version: DocumentVersion,
        ownership: ExtractionOwnership,
    ) -> str | None:
        """Return an error string if ownership is invalid, or None if OK."""
        if version.document_id != ownership.document_id:
            return (
                f"version.document_id={version.document_id} does not match "
                f"ownership.document_id={ownership.document_id}"
            )

        # Load the parent BRDDocument to verify workspace/tenant
        doc = (
            self._db.query(BRDDocument)
            .filter(BRDDocument.id == version.document_id)
            .first()
        )
        if doc is None:
            return f"BRDDocument {version.document_id} not found"

        if doc.workspace_id != ownership.workspace_id:
            return (
                f"document.workspace_id={doc.workspace_id} does not match "
                f"ownership.workspace_id={ownership.workspace_id}"
            )

        if doc.tenant_id != ownership.tenant_id:
            return (
                f"document.tenant_id={doc.tenant_id} does not match "
                f"ownership.tenant_id={ownership.tenant_id}"
            )

        return None

    def _extract_from_bytes(
        self,
        *,
        pdf_bytes: bytes,
        original_filename: str,
        ownership: ExtractionOwnership,
    ) -> DocumentExtractionResult:
        """Write bytes to a temp file, extract, clean up, return result."""

        tmp_path: Path | None = None

        try:
            # Write to a temp file — the existing extractors accept Path objects
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".pdf", prefix="mflows_extract_"
            ) as tmp:
                tmp.write(pdf_bytes)
                tmp_path = Path(tmp.name)

            return self._run_extraction(
                tmp_path=tmp_path,
                original_filename=original_filename,
                ownership=ownership,
            )

        except Exception as exc:
            # Unexpected error outside the extraction itself (e.g. tempfile OS
            # failure).  Log and return a typed failure result.
            logger.error(
                "pdf_pipeline_unexpected_error",
                extra={"extra_data": {
                    "filename": original_filename,
                    "error":    str(exc)[:400],
                }},
            )
            return make_failed_document(
                ownership=ownership,
                error_message=f"Unexpected pipeline error: {exc}",
            )

        finally:
            # Temp file is always deleted, even on exception.
            if tmp_path and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError as cleanup_exc:
                    logger.warning(
                        "pdf_pipeline_temp_cleanup_failed",
                        extra={"extra_data": {
                            "path":  str(tmp_path),
                            "error": str(cleanup_exc),
                        }},
                    )

    def _run_extraction(
        self,
        *,
        tmp_path: Path,
        original_filename: str,
        ownership: ExtractionOwnership,
    ) -> DocumentExtractionResult:
        """Run PageClassifier + MultiModalDocumentExtractor and translate output.

        Calls extract_structured() to get the merged string AND the structured
        intermediate results (DocumentClassification + per-page visual results)
        in a single pass.  No string parsing is used.
        """

        # ── Step 1: Page classification (cheap, local, no LLM) ───────────────
        # extract_structured() runs classification internally, but we also call
        # it here to get total_pages for the result.  Classification is fast
        # (pure pypdf, no rendering) so the second call is acceptable.
        # If this call fails we fall back gracefully.
        total_pages = 0
        pre_classification_warnings: list[str] = []
        try:
            pre_doc = self._classifier.classify(tmp_path)
            total_pages = pre_doc.total_pages
        except Exception as exc:
            pre_classification_warnings.append(
                f"PageClassifier failed (total_pages unknown): {exc}"
            )
            logger.warning(
                "pdf_pipeline_pre_classification_failed",
                extra={"extra_data": {
                    "filename": original_filename,
                    "error":    str(exc)[:300],
                }},
            )

        # ── Step 2: Full multimodal extraction (structured) ───────────────────
        merged_text:        str                              = ""
        doc_classification: DocumentClassification | None   = None
        visual_results:     dict[int, PageExtractionResult] = {}
        extraction_error:   str | None                      = None

        try:
            merged_text, doc_classification, visual_results = \
                self._extractor.extract_structured(tmp_path)
        except DocumentExtractionError as exc:
            extraction_error = str(exc)
            logger.warning(
                "pdf_pipeline_extraction_failed",
                extra={"extra_data": {
                    "filename": original_filename,
                    "error":    extraction_error[:400],
                }},
            )
        except Exception as exc:
            extraction_error = f"Unexpected extraction error: {exc}"
            logger.error(
                "pdf_pipeline_extraction_unexpected",
                extra={"extra_data": {
                    "filename": original_filename,
                    "error":    str(exc)[:400],
                }},
            )

        # ── Step 3: Build per-page records from structured data ───────────────
        pages: list[PageExtractionOutput] = []

        if doc_classification is not None:
            pages = self._build_page_records(
                doc=doc_classification,
                visual_results=visual_results,
                extraction_failed=(extraction_error is not None),
            )
        elif merged_text:
            # Classification was not available (plain-text fast path) but we
            # have text — synthesize one record so full_text still works.
            pages = [
                PageExtractionOutput(
                    page_number=1,
                    page_type=PageType.UNKNOWN,
                    status=PageStatus.SUCCESS,
                    provider=ExtractionProvider.PYPDF,
                    text=merged_text,
                    warnings=pre_classification_warnings,
                )
            ]

        # ── Step 4: Compute overall status ────────────────────────────────────
        if extraction_error and not merged_text:
            return DocumentExtractionResult(
                ownership=ownership,
                pages=pages,
                total_pages=total_pages,
                overall_status="FAILED",
                error_message=extraction_error,
                warnings=pre_classification_warnings,
                extractor_version=_EXTRACTOR_VERSION,
            )

        overall_status = compute_overall_status(pages)
        warnings = list(pre_classification_warnings)
        if extraction_error:
            warnings.append(f"Extraction partially failed: {extraction_error}")

        result = DocumentExtractionResult(
            ownership=ownership,
            pages=pages,
            total_pages=total_pages,
            overall_status=overall_status,
            warnings=warnings,
            extractor_version=_EXTRACTOR_VERSION,
        )

        logger.info(
            "pdf_pipeline_complete",
            extra={"extra_data": {
                "filename":       original_filename,
                "total_pages":    total_pages,
                "succeeded":      len(result.succeeded_pages),
                "failed":         len(result.failed_pages),
                "overall_status": overall_status,
                "chars":          len(merged_text),
            }},
        )

        return result

    def _build_page_records(
        self,
        *,
        doc: DocumentClassification,
        visual_results: dict[int, PageExtractionResult],
        extraction_failed: bool,
    ) -> list[PageExtractionOutput]:
        """Build one PageExtractionOutput per classified page.

        Uses structured data directly — no string parsing.

        Text/appendix pages:  text from PageClassification.text (pypdf, in memory).
        Visual pages:         status + text from PageExtractionResult in visual_results.
        """
        pages: list[PageExtractionOutput] = []
        all_pages = doc.all_pages()   # sorted by page_number, 0-indexed

        for pc in all_pages:
            human_page = pc.page_number + 1    # 1-indexed
            page_type  = _PAGE_TYPE_MAP.get(pc.page_type, PageType.UNKNOWN)

            if extraction_failed:
                pages.append(PageExtractionOutput(
                    page_number=human_page,
                    page_type=page_type,
                    status=PageStatus.FAILED,
                    provider=ExtractionProvider.NONE,
                    text="",
                    warnings=["Extraction pipeline failed for this document."],
                ))
                continue

            if page_type == PageType.TEXT:
                text   = (pc.text or "").strip()
                status = PageStatus.SUCCESS if text else PageStatus.EMPTY
                pages.append(PageExtractionOutput(
                    page_number=human_page,
                    page_type=page_type,
                    status=status,
                    provider=ExtractionProvider.PYPDF,
                    text=text,
                ))

            elif page_type == PageType.APPENDIX:
                # Appendix pages were sent to TextProvider as a batch.  The
                # per-page text from pypdf is the most reliable per-page source
                # here because the LLM batch collapses them into one string.
                text   = (pc.text or "").strip()
                status = PageStatus.SUCCESS if text else PageStatus.EMPTY
                pages.append(PageExtractionOutput(
                    page_number=human_page,
                    page_type=page_type,
                    status=status,
                    provider=ExtractionProvider.TEXT_LLM,
                    text=text,
                ))

            elif page_type in (PageType.TABLE, PageType.IMAGE):
                # Visual pages: use the structured VisionProvider result.
                vr = visual_results.get(pc.page_number)   # 0-indexed key

                if vr is None:
                    # Visual thread never produced a result for this page.
                    fallback_text = (pc.text or "").strip()
                    pages.append(PageExtractionOutput(
                        page_number=human_page,
                        page_type=page_type,
                        status=PageStatus.FAILED,
                        provider=ExtractionProvider.VISION,
                        text=fallback_text,
                        warnings=["No visual extraction result for this page."],
                    ))
                    continue

                # Map VisionStatus → PageStatus
                if vr.status == VisionStatus.SUCCESS:
                    pg_status = PageStatus.SUCCESS
                    warnings: list[str] = []
                elif vr.status == VisionStatus.EMPTY:
                    pg_status = PageStatus.EMPTY
                    warnings = []
                elif vr.status == VisionStatus.RATE_LIMITED:
                    pg_status = PageStatus.FAILED
                    warnings = ["Vision provider was rate-limited."]
                else:  # PROVIDER_FAILED
                    pg_status = PageStatus.FAILED
                    warnings = [
                        f"Vision provider failed"
                        + (f": {vr.error_type}" if vr.error_type else "")
                        + ". Raw pypdf text used as fallback."
                    ]

                # For failed visual pages, fall back to raw pypdf text.
                text = vr.text or ""
                if not text and pg_status == PageStatus.FAILED:
                    text = (pc.text or "").strip()

                pages.append(PageExtractionOutput(
                    page_number=human_page,
                    page_type=page_type,
                    status=pg_status,
                    provider=ExtractionProvider.VISION,
                    text=text,
                    warnings=warnings,
                    source_metadata={
                        "vision_provider": vr.provider,
                        "attempts":        vr.attempts,
                        "latency_ms":      vr.latency_ms,
                        "error_type":      vr.error_type,
                    },
                ))

            else:
                pages.append(PageExtractionOutput(
                    page_number=human_page,
                    page_type=PageType.UNKNOWN,
                    status=PageStatus.SKIPPED,
                    provider=ExtractionProvider.NONE,
                    warnings=[f"Unknown page type: {pc.page_type!r}"],
                ))

        return sorted(pages, key=lambda p: p.page_number)


