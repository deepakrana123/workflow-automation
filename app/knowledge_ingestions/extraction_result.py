"""
app/knowledge_ingestions/extraction_result.py

Normalized output contract for the PDF extraction pipeline.

Why this module exists
----------------------
The existing MultiModalDocumentExtractor returns a single merged string.
That string carries no page numbers, no per-page classification, no
provider attribution, and no record of partial failures.  Downstream
components (WorkflowExtractor, provenance tracking, IngestionAttempt
diagnostics) need all of those things.

This module defines the structured replacement:

    PageExtractionOutput   — result for one page of a PDF
    DocumentExtractionResult — result for an entire document, with ownership

Design rules
------------
1.  Every page must have a record — including pages that failed or were empty.
    "No record" means "silently lost", which the spec explicitly prohibits.

2.  Status vocabulary is minimal and explicit.
    SUCCESS, EMPTY, FAILED, SKIPPED covers all real cases without
    inventing categories that do not map to distinct handling logic.

3.  Ownership context (tenant_id, workspace_id, document_id,
    document_version_id, ingestion_attempt_id) is carried on the document
    result, not on every page.  Pages are always read through their parent
    document and do not need redundant copies.

4.  This module has zero runtime dependencies beyond the standard library
    and dataclasses.  It must remain importable with no DB session, no
    network, no model loaded.

5.  The `source_metadata` dict on PageExtractionOutput is intentionally
    untyped — it holds provider-specific diagnostics (latency_ms, model,
    prompt_tokens, etc.) that differ per provider without polluting the
    core schema.

Relationship to existing types
-------------------------------
TableImageExtractor already defines PageExtractionResult (in
table_image_extractor.py) with status vocabulary SUCCESS/EMPTY/
PROVIDER_FAILED/RATE_LIMITED.  PageExtractionOutput defined here is a
*higher-level* record that:

  - covers ALL page types (not just visual pages)
  - maps provider statuses to the unified PageStatus enum
  - adds page classification type, extracted tables, and image descriptions
  - carries the page number in a document-level position (1-indexed for humans)

The pipeline translates TableImageExtractor.PageExtractionResult →
PageExtractionOutput when processing visual pages.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone


# ── Page status ───────────────────────────────────────────────────────────────

class PageStatus(str, enum.Enum):
    """Outcome of extracting a single page.

    SUCCESS      — text was extracted without error.
    EMPTY        — the provider ran successfully but found no content.
                   (Blank pages, separator pages, fully redacted pages.)
    FAILED       — extraction failed for this page; fallback text may or
                   may not be present.
    SKIPPED      — the page was deliberately not sent to any extractor
                   (e.g. a cover page or pure whitespace page detected
                   during classification before any provider is called).
    """

    SUCCESS = "SUCCESS"
    EMPTY   = "EMPTY"
    FAILED  = "FAILED"
    SKIPPED = "SKIPPED"


# ── Page classification types ─────────────────────────────────────────────────

class PageType(str, enum.Enum):
    """Classification of a PDF page, as determined by PageClassifier.

    Mirrors PageClassifier's string labels but as an enum so callers
    get IDE completion and exhaustiveness checks.

    TEXT      — narrative paragraphs, standard body content.
    TABLE     — data grid, approval matrix, threshold table.
    IMAGE     — diagram, flowchart, scanned image page.
    APPENDIX  — supplementary section (Appendix, Annex, Schedule, Exhibit…).
    UNKNOWN   — classification failed or was not attempted.
    """

    TEXT     = "text"
    TABLE    = "table"
    IMAGE    = "image"
    APPENDIX = "appendix"
    UNKNOWN  = "unknown"


# ── Provider used ─────────────────────────────────────────────────────────────

class ExtractionProvider(str, enum.Enum):
    """Which extractor component produced the text for this page.

    PYPDF      — native PDF text via pypdf (DocumentExtractor / body thread).
    OCR        — pytesseract fallback (OCRExtractor).
    VISION     — VisionProvider (Gemini, OpenRouter, etc.) via
                 TableImageExtractor.
    TEXT_LLM   — TextProvider via AppendixExtractor.
    NONE       — no provider ran (SKIPPED or early failure before extraction).
    """

    PYPDF    = "pypdf"
    OCR      = "ocr"
    VISION   = "vision"
    TEXT_LLM = "text_llm"
    NONE     = "none"


# ── Per-page result ───────────────────────────────────────────────────────────

@dataclass
class PageExtractionOutput:
    """Extraction result for a single PDF page.

    Fields
    ------
    page_number         1-indexed human page number.  The existing pipeline
                        uses 0-indexed page_number internally (pypdf convention)
                        so the pipeline converts: human_page = internal + 1.

    page_type           Classification from PageClassifier.

    status              Outcome of the extraction attempt.

    provider            Which extractor component ran.

    text                Extracted text.  Empty string when status is EMPTY,
                        FAILED or SKIPPED.  May contain partial text when
                        status is FAILED and a fallback produced degraded output.

    tables              Structured table rows, if the provider extracted them.
                        Each entry is a list of cell strings representing one row.
                        Empty list when no tables were detected or the provider
                        does not return structured tables.

    image_descriptions  Descriptions of diagrams, charts, or images on this
                        page, as returned by the VisionProvider.
                        Empty list for text/appendix pages.

    warnings            Non-fatal issues encountered during extraction.
                        Examples: "pypdf returned empty text, OCR fallback used",
                        "vision provider rate-limited, raw text used".

    error_message       The last error message when status is FAILED.
                        None when status is SUCCESS, EMPTY or SKIPPED.

    source_metadata     Provider-specific diagnostics.
                        Examples: {"latency_ms": 1240, "model": "gemini-1.5-pro",
                                   "attempts": 2, "vision_provider": "gemini"}.
                        May be empty dict.  Never contains PII or file bytes.
    """

    page_number: int
    page_type: PageType
    status: PageStatus
    provider: ExtractionProvider
    text: str = ""
    tables: list[list[str]] = field(default_factory=list)
    image_descriptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error_message: str | None = None
    source_metadata: dict = field(default_factory=dict)

    # ── Convenience properties ─────────────────────────────────────────────────

    @property
    def succeeded(self) -> bool:
        """True when the page was extracted without error."""
        return self.status == PageStatus.SUCCESS

    @property
    def has_content(self) -> bool:
        """True when any text, table or image description is available."""
        return bool(self.text or self.tables or self.image_descriptions)

    @property
    def needs_review(self) -> bool:
        """True when the page has warnings or a degraded extraction."""
        return bool(self.warnings) or self.status == PageStatus.FAILED

    def __repr__(self) -> str:
        return (
            f"<PageExtractionOutput p={self.page_number} "
            f"type={self.page_type.value} "
            f"status={self.status.value} "
            f"provider={self.provider.value} "
            f"chars={len(self.text)}>"
        )


# ── Document-level ownership context ─────────────────────────────────────────

@dataclass
class ExtractionOwnership:
    """Ownership context carried through the entire extraction run.

    All IDs are the integer PKs from the database.  None means 'not yet
    assigned' (e.g. ingestion_attempt_id is set after the attempt row is
    created, but ownership is established from the DocumentVersion).

    tenant_id and workspace_id are denormalised from the DocumentVersion's
    parent chain so the extraction pipeline never needs to do extra DB
    lookups.  The service layer must validate these before starting extraction.
    """

    tenant_id:            int
    workspace_id:         int
    document_id:          int
    document_version_id:  int
    ingestion_attempt_id: int | None = None


# ── Document-level result ─────────────────────────────────────────────────────

@dataclass
class DocumentExtractionResult:
    """Complete extraction result for one DocumentVersion.

    This is the output of PdfExtractionPipeline.extract() and the input
    to the downstream WorkflowExtractor.

    Fields
    ------
    ownership           Tenant/workspace/document/version/attempt identifiers.

    pages               One PageExtractionOutput per page of the PDF, in
                        document order (sorted by page_number ascending).
                        Every page has a record — no silent drops.

    total_pages         Total number of pages in the PDF.

    extracted_at        UTC timestamp when extraction completed.

    extractor_version   Version tag of the extraction pipeline that produced
                        this result.  Used by retry logic to decide whether
                        re-extraction is needed after a pipeline upgrade.

    overall_status      Aggregate outcome:
                          SUCCESS      — all pages extracted without error.
                          PARTIAL      — some pages failed, others succeeded.
                          FAILED       — no pages produced usable content.
                          EMPTY        — PDF had no extractable content at all.

    warnings            Document-level warnings (e.g. "password-protected PDF,
                        decryption skipped", "large PDF — 120 pages processed").

    error_message       Set when overall_status is FAILED.  Describes the
                        document-level failure (e.g. "PdfReader raised
                        PdfReadError: EOF marker not found").
    """

    ownership: ExtractionOwnership
    pages: list[PageExtractionOutput]
    total_pages: int
    extracted_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    extractor_version: str = "1.0.0"
    overall_status: str = "SUCCESS"   # SUCCESS | PARTIAL | FAILED | EMPTY
    warnings: list[str] = field(default_factory=list)
    error_message: str | None = None

    # ── Computed properties ────────────────────────────────────────────────────

    @property
    def succeeded_pages(self) -> list[PageExtractionOutput]:
        """Pages that were extracted successfully."""
        return [p for p in self.pages if p.status == PageStatus.SUCCESS]

    @property
    def failed_pages(self) -> list[PageExtractionOutput]:
        """Pages that failed extraction."""
        return [p for p in self.pages if p.status == PageStatus.FAILED]

    @property
    def has_usable_content(self) -> bool:
        """True when at least one page has extractable content."""
        return any(p.has_content for p in self.pages)

    @property
    def full_text(self) -> str:
        """Concatenate all page texts in document order.

        This is the string equivalent of the current MultiModalDocumentExtractor
        output — a single merged string — preserved so the existing WorkflowExtractor
        can be called without modification until it is updated to consume per-page
        results directly.

        Pages are separated by double newlines.  Each page's text is prefixed with
        a lightweight page marker so provenance can be recovered from the string
        if needed.
        """
        parts: list[str] = []
        for p in sorted(self.pages, key=lambda x: x.page_number):
            if p.text.strip():
                parts.append(f"[Page {p.page_number}]\n{p.text.strip()}")
        return "\n\n".join(parts)

    def page(self, page_number: int) -> PageExtractionOutput | None:
        """Return the PageExtractionOutput for a 1-indexed page number, or None."""
        for p in self.pages:
            if p.page_number == page_number:
                return p
        return None

    def __repr__(self) -> str:
        return (
            f"<DocumentExtractionResult "
            f"doc_id={self.ownership.document_id} "
            f"version_id={self.ownership.document_version_id} "
            f"pages={self.total_pages} "
            f"status={self.overall_status} "
            f"succeeded={len(self.succeeded_pages)} "
            f"failed={len(self.failed_pages)}>"
        )


# ── Helpers for the pipeline ──────────────────────────────────────────────────

def compute_overall_status(pages: list[PageExtractionOutput]) -> str:
    """Derive the document-level overall_status from page results.

    Rules:
      EMPTY   — no pages at all, or all pages are SKIPPED/EMPTY with no content.
      FAILED  — no page produced usable content (all FAILED or SKIPPED).
      PARTIAL — at least one page failed but at least one succeeded.
      SUCCESS — all pages are SUCCESS (or EMPTY/SKIPPED, which are non-errors).
    """
    if not pages:
        return "EMPTY"

    succeeded = sum(1 for p in pages if p.status == PageStatus.SUCCESS)
    failed    = sum(1 for p in pages if p.status == PageStatus.FAILED)
    has_any_content = any(p.has_content for p in pages)

    if not has_any_content:
        return "EMPTY"

    if failed == 0:
        return "SUCCESS"

    if succeeded > 0:
        return "PARTIAL"

    return "FAILED"


def make_failed_document(
    ownership: ExtractionOwnership,
    error_message: str,
    total_pages: int = 0,
) -> DocumentExtractionResult:
    """Build a DocumentExtractionResult for a document that could not be opened.

    Used when the PDF is corrupt, password-protected, or causes a fatal error
    before any page can be classified.  Returns a result with no page records
    and overall_status = FAILED so the pipeline always returns a typed result
    rather than raising.
    """
    return DocumentExtractionResult(
        ownership=ownership,
        pages=[],
        total_pages=total_pages,
        overall_status="FAILED",
        error_message=error_message,
    )
