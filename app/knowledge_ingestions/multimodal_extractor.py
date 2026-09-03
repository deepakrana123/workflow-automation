"""
app/knowledge_ingestions/multimodal_extractor.py

MultiModalDocumentExtractor — orchestrates parallel extraction across all
page types and merges results into one enriched document text string.

Replaces DocumentExtractor as the entry point for BRD text extraction.
The output is a single string that WorkflowExtractor feeds to the main
extraction prompt — the interface to WorkflowExtractor is unchanged.

Architecture:
  PageClassifier classifies each page (local, no LLM, fast).
  Then three parallel paths run concurrently:

    Thread A — Text pages:
      pypdf.extract_text() — already done during classification, zero extra cost.

    Thread B — Table + Image pages:
      TableImageExtractor renders each page to PNG and calls VisionProvider.
      Pages within this thread are processed sequentially (one call per page)
      to avoid overwhelming the API with parallel vision calls.

    Thread C — Appendix pages:
      AppendixExtractor combines all appendix text and makes one TextProvider call.

  All three threads run in a ThreadPoolExecutor. The merge step waits for all
  three, then assembles the results in document order.

Merge strategy:
  The merged output is structured so the main WorkflowExtractor (extractor.md)
  receives:
    [BODY TEXT]          — text from all text pages, in page order
    [TABLE EXTRACTIONS]  — structured content from each table/image page
    [APPENDIX]           — structured content from appendix pages

  This structure tells the LLM that TABLE EXTRACTIONS and APPENDIX contain
  additional business rules that supplement the main body — not a different
  document.

Fallback:
  If VisionProvider fails for a page, the raw (possibly garbled) pypdf text
  for that page is used. If AppendixExtractor fails entirely, the raw appendix
  text from pypdf is used. The pipeline never produces empty output as long
  as the PDF has at least some extractable text.
"""

from __future__ import annotations

import concurrent.futures
from pathlib import Path

from app.core.logger import logger
from app.knowledge_ingestions.extractor import DocumentExtractor
from app.knowledge_ingestions.page_classifier import (
    PageClassifier,
    DocumentClassification,
    PageClassification,
)
from app.knowledge_ingestions.table_image_extractor import TableImageExtractor
from app.knowledge_ingestions.appendix_extractor import AppendixExtractor
from app.knowledge_ingestions.providers.base import VisionProvider, TextProvider
from app.knowledge_ingestions.providers.registry import (
    get_vision_provider,
    get_text_provider,
)
from app.knowledge_ingestions.exceptions import DocumentExtractionError


class MultiModalDocumentExtractor:
    """
    Extracts text from a PDF using the appropriate extractor per page type.

    Provider instances are injected at construction time (or resolved from
    the registry if not provided). This supports testing with mock providers
    and allows different models per page type without changing any caller.

    Usage (default — providers from env):
        extractor = MultiModalDocumentExtractor()
        text = extractor.extract(Path("policy.pdf"))

    Usage (custom providers for testing):
        extractor = MultiModalDocumentExtractor(
            vision_provider=MockVisionProvider(),
            text_provider=MockTextProvider(),
        )
    """

    def __init__(
        self,
        vision_provider: VisionProvider | None = None,
        text_provider:   TextProvider   | None = None,
        classifier:      PageClassifier | None = None,
    ):
        # Resolve providers from registry if not injected.
        # Done at construction time so the registry is called once per
        # extractor instance, not once per page.
        self._vision_provider = vision_provider or get_vision_provider()
        self._text_provider   = text_provider   or get_text_provider()
        self._classifier      = classifier      or PageClassifier()

        self._table_image_extractor = TableImageExtractor(self._vision_provider)
        self._appendix_extractor    = AppendixExtractor(self._text_provider)

        # Fallback for plain text extraction (used when multimodal is unavailable)
        self._plain_extractor = DocumentExtractor()

    def extract(self, file_path: Path) -> str:
        """
        Extract all text from a PDF using multimodal extraction where needed.

        Returns a single merged string ready to be passed to WorkflowExtractor.
        Never raises DocumentExtractionError from a single failed page —
        only raises if the entire document is unreadable.

        Args:
            file_path: path to the PDF file

        Returns:
            Merged document text with structured extractions from tables,
            images, and appendices.
        """
        if not file_path.exists():
            raise DocumentExtractionError(f"File not found: {file_path}")

        # ── Step 1: Classify all pages (local, fast, no LLM) ─────────────────
        try:
            doc = self._classifier.classify(file_path)
        except Exception as exc:
            logger.warning(
                "multimodal_extractor_classification_failed",
                extra={"extra_data": {
                    "pdf":   file_path.name,
                    "error": str(exc),
                }},
            )
            # Classification failed — fall back to the original plain text extractor
            logger.info(
                "multimodal_extractor_fallback_plain",
                extra={"extra_data": {"pdf": file_path.name}},
            )
            return self._plain_extractor.extract(file_path)

        logger.info(
            "multimodal_extractor_classification_done",
            extra={"extra_data": {
                "pdf":         file_path.name,
                "total_pages": doc.total_pages,
                "text_pages":  len(doc.text_pages),
                "table_pages": len(doc.table_pages),
                "image_pages": len(doc.image_pages),
                "appendix_pages": len(doc.appendix_pages),
            }},
        )

        # If the document is entirely plain text pages, skip the multimodal
        # overhead and use the plain extractor directly — no parallel threads,
        # no API calls, just pypdf.
        if not doc.has_rich_content() and not doc.appendix_pages:
            logger.info(
                "multimodal_extractor_plain_text_only",
                extra={"extra_data": {"pdf": file_path.name}},
            )
            return self._plain_extractor.extract(file_path)

        # ── Step 2: Run three extraction paths in parallel ────────────────────
        text_result:    str = ""
        visual_result:  dict[int, str] = {}
        appendix_result: str = ""

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            # Thread A — body text (already extracted during classification)
            future_text = pool.submit(
                self._extract_body_text, doc
            )

            # Thread B — table + image pages via VisionProvider
            all_visual_pages = doc.table_pages + doc.image_pages
            future_visual = pool.submit(
                self._table_image_extractor.extract_pages,
                file_path,
                all_visual_pages,
            )

            # Thread C — appendix pages via TextProvider
            future_appendix = pool.submit(
                self._appendix_extractor.extract,
                doc.appendix_pages,
            )

            # Collect — exceptions from threads are surfaced here
            try:
                text_result = future_text.result()
            except Exception as exc:
                logger.warning(
                    "multimodal_extractor_body_text_failed",
                    extra={"extra_data": {"pdf": file_path.name, "error": str(exc)}},
                )

            try:
                visual_result = future_visual.result()
            except Exception as exc:
                logger.warning(
                    "multimodal_extractor_visual_failed",
                    extra={"extra_data": {"pdf": file_path.name, "error": str(exc)}},
                )
                # Fallback: use pypdf text for visual pages
                visual_result = {
                    p.page_number: p.text
                    for p in all_visual_pages
                }

            try:
                appendix_result = future_appendix.result()
            except Exception as exc:
                logger.warning(
                    "multimodal_extractor_appendix_failed",
                    extra={"extra_data": {"pdf": file_path.name, "error": str(exc)}},
                )
                # Fallback: use raw pypdf text for appendix pages
                appendix_result = _combine_raw_text(doc.appendix_pages)

        # ── Step 3: Merge all results in structured order ─────────────────────
        merged = _merge_results(
            doc=doc,
            body_text=text_result,
            visual_results=visual_result,
            appendix_text=appendix_result,
        )

        if not merged.strip():
            raise DocumentExtractionError(
                f"No extractable content found in {file_path.name}"
            )

        logger.info(
            "multimodal_extractor_complete",
            extra={"extra_data": {
                "pdf":          file_path.name,
                "output_chars": len(merged),
            }},
        )
        return merged

    # ── Private helpers ───────────────────────────────────────────────────────

    def _extract_body_text(self, doc: DocumentClassification) -> str:
        """
        Assemble body text from text pages.
        Text was already extracted during classification — zero extra cost.
        """
        sorted_pages = sorted(doc.text_pages, key=lambda p: p.page_number)
        return "\n".join(p.text for p in sorted_pages if p.text.strip())


# ── Pure merge helpers ────────────────────────────────────────────────────────

def _merge_results(
    doc: DocumentClassification,
    body_text: str,
    visual_results: dict[int, str],
    appendix_text: str,
) -> str:
    """
    Assemble the final merged document text.

    Structure:
      [BODY]
        <text page content in page order>

      [TABLE AND DIAGRAM EXTRACTIONS]
        Page N:
          <vision provider output for that page>

      [APPENDIX]
        <appendix provider output>

    The section headers tell the LLM that TABLE AND DIAGRAM EXTRACTIONS
    contains supplementary structured data extracted from visual content,
    and that APPENDIX contains supplementary rules and roles — both should
    be used alongside the BODY when extracting workflow knowledge.
    """
    sections: list[str] = []

    # Body text
    if body_text.strip():
        sections.append("=== DOCUMENT BODY ===\n\n" + body_text.strip())

    # Visual extractions (tables and diagrams)
    all_visual = sorted(
        doc.table_pages + doc.image_pages,
        key=lambda p: p.page_number,
    )
    if all_visual:
        visual_parts: list[str] = []
        for page in all_visual:
            extracted = visual_results.get(page.page_number, "").strip()
            if not extracted:
                # Fallback to raw text if vision failed
                extracted = page.text.strip() or "(no content extracted)"
            label = "TABLE" if page.page_type == "table" else "DIAGRAM"
            visual_parts.append(
                f"[Page {page.page_number + 1} — {label}]\n{extracted}"
            )
        if visual_parts:
            sections.append(
                "=== TABLE AND DIAGRAM EXTRACTIONS ===\n\n"
                + "\n\n".join(visual_parts)
            )

    # Appendix
    if appendix_text.strip():
        sections.append("=== APPENDIX ===\n\n" + appendix_text.strip())
    elif doc.appendix_pages:
        # Fallback to raw text
        raw = _combine_raw_text(doc.appendix_pages)
        if raw.strip():
            sections.append("=== APPENDIX ===\n\n" + raw.strip())

    return "\n\n".join(sections)


def _combine_raw_text(pages: list[PageClassification]) -> str:
    """Join raw pypdf text from a list of pages in page order."""
    sorted_pages = sorted(pages, key=lambda p: p.page_number)
    return "\n".join(p.text for p in sorted_pages if p.text.strip())
