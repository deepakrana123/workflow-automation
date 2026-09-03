"""
app/knowledge_ingestions/appendix_extractor.py

AppendixExtractor — sends appendix page text to a TextProvider and
returns structured extraction (roles, rules, thresholds).

Why a separate extractor and prompt for appendices (not bundled with body):
  The main extractor (WorkflowExtractor) sends the full document body to
  Gemini with a prompt focused on workflow structure — triggers, actions,
  business rules. Appendices have a different structure: they are lookup
  tables, role definitions, and supplementary constraints. Sending them
  with the main body would dilute the extraction signal and push the body
  further from the front of the context window. A dedicated call with a
  dedicated prompt produces cleaner results.

Why TextProvider (not VisionProvider) for appendices:
  pypdf successfully extracts text from most appendices — they are usually
  formatted text (approval matrices as text tables, role definitions as
  bullet lists). Only when the appendix contains embedded images would we
  need vision. That case is handled by the PageClassifier routing those
  pages to the image/table path instead. AppendixExtractor only receives
  pages classified as "appendix" with text content.
"""

from __future__ import annotations

from pathlib import Path

from app.core.logger import logger
from app.knowledge_ingestions.page_classifier import PageClassification
from app.knowledge_ingestions.providers.base import TextProvider, TextProviderError


_APPENDIX_PROMPT_PATH = "app/prompts/appendix_extraction.md"


class AppendixExtractor:
    """
    Extracts business content from appendix pages via a TextProvider.

    The provider is injected — never instantiated here.

    Usage:
        provider = get_text_provider()
        extractor = AppendixExtractor(provider)
        text = extractor.extract(appendix_pages)
    """

    def __init__(self, text_provider: TextProvider):
        self._provider = text_provider
        self._prompt: str | None = None

    def extract(self, appendix_pages: list[PageClassification]) -> str:
        """
        Combine all appendix page texts and send to TextProvider for extraction.

        All appendix pages are merged into one call rather than one call per
        page because:
          1. Appendix content is often split across multiple pages (e.g.
             Schedule 1 on page 35, Schedule 2 on page 36).
          2. One call with the full appendix produces better cross-page
             coherence (role defined on page 35 referenced in rule on page 36).
          3. Appendix text is usually compact — fits comfortably in one call.

        Args:
            appendix_pages: list of PageClassification with page_type="appendix"

        Returns:
            Extracted structured text from the TextProvider.
            Returns empty string on failure (logged, never raises).
        """
        if not appendix_pages:
            return ""

        # Combine all appendix pages in order, with clear page separators
        combined_text = _combine_appendix_text(appendix_pages)

        if not combined_text.strip():
            logger.info(
                "appendix_extractor_empty_text",
                extra={"extra_data": {
                    "page_count": len(appendix_pages),
                }},
            )
            return ""

        prompt = self._build_prompt(combined_text)

        try:
            result = self._provider.generate(prompt)
            logger.info(
                "appendix_extractor_success",
                extra={"extra_data": {
                    "provider":    self._provider.provider_name,
                    "page_count":  len(appendix_pages),
                    "input_chars": len(combined_text),
                    "result_len":  len(result),
                }},
            )
            return result

        except TextProviderError as exc:
            logger.warning(
                "appendix_extractor_provider_failed",
                extra={"extra_data": {
                    "provider":  self._provider.provider_name,
                    "retryable": exc.retryable,
                    "error":     str(exc),
                }},
            )
            return ""

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_prompt(self, appendix_text: str) -> str:
        """Combine the appendix prompt template with the extracted text."""
        if self._prompt is None:
            self._prompt = _load_prompt(_APPENDIX_PROMPT_PATH)

        return (
            self._prompt
            + "\n\n---\n\n"
            + "APPENDIX TEXT:\n\n"
            + appendix_text
        )


# ── Pure helpers ──────────────────────────────────────────────────────────────

def _combine_appendix_text(pages: list[PageClassification]) -> str:
    """
    Join appendix pages in order with clear page markers.

    Page markers help the model understand where one section ends and
    another begins — important for multi-schedule appendices.
    """
    sorted_pages = sorted(pages, key=lambda p: p.page_number)
    parts: list[str] = []
    for page in sorted_pages:
        if page.text.strip():
            parts.append(f"[Page {page.page_number + 1}]\n{page.text.strip()}")
    return "\n\n".join(parts)


def _load_prompt(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Appendix prompt not found: {path}")
    return p.read_text(encoding="utf-8")
