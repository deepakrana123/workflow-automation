"""
app/knowledge_ingestions/table_image_extractor.py

TableImageExtractor — renders PDF pages to PNG images and calls a
VisionProvider to extract structured content from tables and diagrams.

Responsibilities:
  - Render a specific PDF page to a PNG image using pdf2image
  - Load the appropriate prompt (table or image) based on page type
  - Call VisionProvider.extract_page(image_bytes, prompt)
  - Return the extracted text for that page

Why one page at a time (not batch):
  Gemini inline_data supports multiple parts per request, but batching
  pages into one call makes error handling harder — one bad page fails
  the whole batch. One call per page means partial failures are isolated
  and logged per page, not per document.

Why pdf2image instead of pypdf for image rendering:
  pypdf can extract embedded image objects but cannot render the full page
  as it would appear visually (including text positioning, table borders,
  vector graphics). pdf2image renders the full page via Poppler — the same
  renderer a PDF viewer uses — so tables with borders, shaded cells, and
  merged cells are all visible in the output image.

DPI=150 is the default:
  150 DPI produces ~1240x1754px for an A4 page (~500KB PNG).
  Sufficient for Gemini to read table content without exceeding inline_data
  size limits. 200+ DPI would improve OCR quality for scanned pages but
  increases payload size significantly.
"""

from __future__ import annotations

import io
from pathlib import Path

from app.core.logger import logger
from app.core.setting import POPPLER_PATH
from app.knowledge_ingestions.page_classifier import PageClassification
from app.knowledge_ingestions.providers.base import VisionProvider, VisionProviderError
from app.prompting import PromptManager, PromptContext, PromptKey


# Render DPI — balance between quality and payload size
_DEFAULT_DPI = 150

# Prompt keys for the two visual content types
_TABLE_PROMPT_PATH = "app/prompts/table_extraction.md"
_IMAGE_PROMPT_PATH = "app/prompts/image_extraction.md"


class TableImageExtractor:
    """
    Extracts business content from table and image pages via a VisionProvider.

    The provider is injected — it is never instantiated here. This keeps
    the extractor fully decoupled from any specific model.

    Usage:
        provider = get_vision_provider()   # from registry
        extractor = TableImageExtractor(provider)
        result = extractor.extract_page(pdf_path, page_classification)
    """

    def __init__(self, vision_provider: VisionProvider):
        self._provider = vision_provider
        self._table_prompt: str | None = None
        self._image_prompt: str | None = None

    def extract_page(
        self,
        pdf_path: Path,
        page: PageClassification,
        dpi: int = _DEFAULT_DPI,
    ) -> str:
        """
        Render one PDF page to PNG and extract content via VisionProvider.

        Args:
            pdf_path:   path to the source PDF
            page:       classification result for this page (carries page_number and page_type)
            dpi:        render resolution (default 150)

        Returns:
            Extracted text from the VisionProvider.
            Returns empty string on failure (logged, never raises to caller).

        Why never raises:
            A failed table extraction should not abort the entire BRD ingestion.
            The page's pypdf text (which may be garbled) is used as fallback.
            The caller (MultiModalDocumentExtractor) handles the fallback logic.
        """
        try:
            image_bytes = self._render_page(pdf_path, page.page_number, dpi)
        except Exception as exc:
            logger.warning(
                "table_image_extractor_render_failed",
                extra={"extra_data": {
                    "pdf": pdf_path.name,
                    "page": page.page_number,
                    "error": str(exc),
                }},
            )
            return ""

        prompt = self._get_prompt(page.page_type)

        try:
            result = self._provider.extract_page(image_bytes, prompt)
            logger.info(
                "table_image_extractor_success",
                extra={"extra_data": {
                    "provider":    self._provider.provider_name,
                    "pdf":         pdf_path.name,
                    "page":        page.page_number,
                    "page_type":   page.page_type,
                    "result_len":  len(result),
                }},
            )
            return result

        except VisionProviderError as exc:
            logger.warning(
                "table_image_extractor_provider_failed",
                extra={"extra_data": {
                    "provider":  self._provider.provider_name,
                    "pdf":       pdf_path.name,
                    "page":      page.page_number,
                    "retryable": exc.retryable,
                    "error":     str(exc),
                }},
            )
            return ""

    def extract_pages(
        self,
        pdf_path: Path,
        pages: list[PageClassification],
        dpi: int = _DEFAULT_DPI,
    ) -> dict[int, str]:
        """
        Extract content from multiple pages.

        Returns:
            dict mapping page_number → extracted text.
            Pages that fail are mapped to empty string.

        Note: called sequentially — the parallel orchestration happens one
        layer up in MultiModalDocumentExtractor via ThreadPoolExecutor.
        """
        results: dict[int, str] = {}
        for page in pages:
            results[page.page_number] = self.extract_page(pdf_path, page, dpi)
        return results

    # ── Private helpers ───────────────────────────────────────────────────────

    def _render_page(self, pdf_path: Path, page_number: int, dpi: int) -> bytes:
        """
        Render a single PDF page to PNG bytes using pdf2image.

        page_number is 0-indexed (matching pypdf convention).
        pdf2image uses 1-indexed first_page/last_page parameters.
        """
        from pdf2image import convert_from_path

        pages = convert_from_path(
            str(pdf_path),
            dpi=dpi,
            first_page=page_number + 1,
            last_page=page_number + 1,
            poppler_path=str(POPPLER_PATH) if POPPLER_PATH else None,
            fmt="png",
        )

        if not pages:
            raise RuntimeError(
                f"pdf2image returned no pages for page {page_number} of {pdf_path.name}"
            )

        # Convert PIL Image to PNG bytes
        buf = io.BytesIO()
        pages[0].save(buf, format="PNG")
        return buf.getvalue()

    def _get_prompt(self, page_type: str) -> str:
        """Load the appropriate extraction prompt for the page type."""
        if page_type == "table":
            if self._table_prompt is None:
                self._table_prompt = _load_prompt(_TABLE_PROMPT_PATH)
            return self._table_prompt

        # "image" or any other visual type
        if self._image_prompt is None:
            self._image_prompt = _load_prompt(_IMAGE_PROMPT_PATH)
        return self._image_prompt


def _load_prompt(path: str) -> str:
    """Load a prompt file from disk. Raises FileNotFoundError if missing."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Extraction prompt not found: {path}")
    return p.read_text(encoding="utf-8")
