# """
# app/knowledge_ingestions/table_image_extractor.py

# TableImageExtractor — renders PDF pages to PNG images and calls a
# VisionProvider to extract structured content from tables and diagrams.

# Responsibilities:
#   - Render a specific PDF page to a PNG image using pdf2image
#   - Load the appropriate prompt (table or image) based on page type
#   - Call VisionProvider.extract_page(image_bytes, prompt)
#   - Return the extracted text for that page

# Why one page at a time (not batch):
#   Gemini inline_data supports multiple parts per request, but batching
#   pages into one call makes error handling harder — one bad page fails
#   the whole batch. One call per page means partial failures are isolated
#   and logged per page, not per document.

# Why pdf2image instead of pypdf for image rendering:
#   pypdf can extract embedded image objects but cannot render the full page
#   as it would appear visually (including text positioning, table borders,
#   vector graphics). pdf2image renders the full page via Poppler — the same
#   renderer a PDF viewer uses — so tables with borders, shaded cells, and
#   merged cells are all visible in the output image.

# DPI=150 is the default:
#   150 DPI produces ~1240x1754px for an A4 page (~500KB PNG).
#   Sufficient for Gemini to read table content without exceeding inline_data
#   size limits. 200+ DPI would improve OCR quality for scanned pages but
#   increases payload size significantly.
# """

# from __future__ import annotations

# import io
# import time
# from pathlib import Path

# from app.core.logger import logger
# from app.core.setting import POPPLER_PATH
# from app.knowledge_ingestions.page_classifier import PageClassification
# from app.knowledge_ingestions.providers.base import VisionProvider, VisionProviderError
# from app.prompting import PromptManager, PromptContext, PromptKey


# # Render DPI — balance between quality and payload size
# _DEFAULT_DPI = 150

# # Prompt keys for the two visual content types
# _TABLE_PROMPT_PATH = "app/prompts/table_extraction.md"
# _IMAGE_PROMPT_PATH = "app/prompts/image_extraction.md"

# # Rate-limiting: pause between sequential page calls to avoid 429
# _INTER_PAGE_DELAY_SECONDS = 2.0

# # Retry on retryable errors (e.g. 429 Too Many Requests)
# _MAX_RETRIES   = 3
# _RETRY_BACKOFF = [5, 15, 30]   # seconds before each retry attempt


# class TableImageExtractor:
#     """
#     Extracts business content from table and image pages via a VisionProvider.

#     The provider is injected — it is never instantiated here. This keeps
#     the extractor fully decoupled from any specific model.

#     Usage:
#         provider = get_vision_provider()   # from registry
#         extractor = TableImageExtractor(provider)
#         result = extractor.extract_page(pdf_path, page_classification)
#     """

#     def __init__(self, vision_provider: VisionProvider):
#         self._provider = vision_provider
#         self._table_prompt: str | None = None
#         self._image_prompt: str | None = None

#     def extract_page(
#         self,
#         pdf_path: Path,
#         page: PageClassification,
#         dpi: int = _DEFAULT_DPI,
#     ) -> str:
#         """
#         Render one PDF page to PNG and extract content via VisionProvider.

#         Args:
#             pdf_path:   path to the source PDF
#             page:       classification result for this page (carries page_number and page_type)
#             dpi:        render resolution (default 150)

#         Returns:
#             Extracted text from the VisionProvider.
#             Returns empty string on failure (logged, never raises to caller).

#         Why never raises:
#             A failed table extraction should not abort the entire BRD ingestion.
#             The page's pypdf text (which may be garbled) is used as fallback.
#             The caller (MultiModalDocumentExtractor) handles the fallback logic.
#         """
#         try:
#             image_bytes = self._render_page(pdf_path, page.page_number, dpi)
#         except Exception as exc:
#             logger.warning(
#                 "table_image_extractor_render_failed",
#                 extra={"extra_data": {
#                     "pdf": pdf_path.name,
#                     "page": page.page_number,
#                     "error": str(exc),
#                 }},
#             )
#             return ""

#         prompt = self._get_prompt(page.page_type)

#         for attempt in range(_MAX_RETRIES):
#             try:
#                 result = self._provider.extract_page(image_bytes, prompt)
#                 logger.info(
#                     "table_image_extractor_success",
#                     extra={"extra_data": {
#                         "provider":    self._provider.provider_name,
#                         "pdf":         pdf_path.name,
#                         "page":        page.page_number,
#                         "page_type":   page.page_type,
#                         "result_len":  len(result),
#                         "attempt":     attempt + 1,
#                     }},
#                 )
#                 return result

#             except VisionProviderError as exc:
#                 if exc.retryable and attempt < _MAX_RETRIES - 1:
#                     wait = _RETRY_BACKOFF[attempt]
#                     logger.warning(
#                         "table_image_extractor_retrying",
#                         extra={"extra_data": {
#                             "provider":  self._provider.provider_name,
#                             "pdf":       pdf_path.name,
#                             "page":      page.page_number,
#                             "attempt":   attempt + 1,
#                             "wait_s":    wait,
#                             "error":     str(exc),
#                         }},
#                     )
#                     time.sleep(wait)
#                     continue

#                 logger.warning(
#                     "table_image_extractor_provider_failed",
#                     extra={"extra_data": {
#                         "provider":  self._provider.provider_name,
#                         "pdf":       pdf_path.name,
#                         "page":      page.page_number,
#                         "retryable": exc.retryable,
#                         "attempts":  attempt + 1,
#                         "error":     str(exc),
#                     }},
#                 )
#                 return ""

#         return ""  # exhausted retries

#     def extract_pages(
#         self,
#         pdf_path: Path,
#         pages: list[PageClassification],
#         dpi: int = _DEFAULT_DPI,
#     ) -> dict[int, str]:
#         """
#         Extract content from multiple pages, with a small pause between calls
#         to avoid hitting Gemini rate limits (429 Too Many Requests).
#         """
#         results: dict[int, str] = {}
#         for i, page in enumerate(pages):
#             results[page.page_number] = self.extract_page(pdf_path, page, dpi)
#             # Pause between calls — skip after the last page
#             if i < len(pages) - 1:
#                 time.sleep(_INTER_PAGE_DELAY_SECONDS)
#         return results

#     # ── Private helpers ───────────────────────────────────────────────────────

#     def _render_page(self, pdf_path: Path, page_number: int, dpi: int) -> bytes:
#         """
#         Render a single PDF page to PNG bytes using pdf2image.

#         page_number is 0-indexed (matching pypdf convention).
#         pdf2image uses 1-indexed first_page/last_page parameters.
#         """
#         from pdf2image import convert_from_path

#         pages = convert_from_path(
#             str(pdf_path),
#             dpi=dpi,
#             first_page=page_number + 1,
#             last_page=page_number + 1,
#             poppler_path=str(POPPLER_PATH) if POPPLER_PATH else None,
#             fmt="png",
#         )

#         if not pages:
#             raise RuntimeError(
#                 f"pdf2image returned no pages for page {page_number} of {pdf_path.name}"
#             )

#         # Convert PIL Image to PNG bytes
#         buf = io.BytesIO()
#         pages[0].save(buf, format="PNG")
#         return buf.getvalue()

#     def _get_prompt(self, page_type: str) -> str:
#         """Load the appropriate extraction prompt for the page type."""
#         if page_type == "table":
#             if self._table_prompt is None:
#                 self._table_prompt = _load_prompt(_TABLE_PROMPT_PATH)
#             return self._table_prompt

#         # "image" or any other visual type
#         if self._image_prompt is None:
#             self._image_prompt = _load_prompt(_IMAGE_PROMPT_PATH)
#         return self._image_prompt


# def _load_prompt(path: str) -> str:
#     """Load a prompt file from disk. Raises FileNotFoundError if missing."""
#     p = Path(path)
#     if not p.exists():
#         raise FileNotFoundError(f"Extraction prompt not found: {path}")
#     return p.read_text(encoding="utf-8")



"""
app/knowledge_ingestions/table_image_extractor.py

TableImageExtractor — renders PDF pages to PNG images and calls a
VisionProvider to extract structured content from tables and diagrams.

Current responsibility:
    - Render a specific PDF page to a PNG image using pdf2image
    - Load the appropriate prompt based on page type
    - Call VisionProvider.extract_page(image_bytes, prompt)
    - Return extracted text for that page

IMPORTANT:
    This version adds observability only.
    It does NOT change the extraction architecture.
    It does NOT batch pages.
    It does NOT change retry behavior.
"""

from __future__ import annotations

import io
import time
from pathlib import Path

from app.core.logger import logger
from app.core.setting import POPPLER_PATH
from app.knowledge_ingestions.page_classifier import PageClassification
from app.knowledge_ingestions.providers.base import (
    VisionProvider,
    VisionProviderError,
)
from app.prompting import PromptManager, PromptContext, PromptKey


# ── Render configuration ─────────────────────────────────────────────────────

_DEFAULT_DPI = 150


# ── Prompt paths ─────────────────────────────────────────────────────────────

_TABLE_PROMPT_PATH = "app/prompts/table_extraction.md"
_IMAGE_PROMPT_PATH = "app/prompts/image_extraction.md"


# ── Rate limiting / retry configuration ──────────────────────────────────────

_INTER_PAGE_DELAY_SECONDS = 2.0

_MAX_RETRIES = 3

_RETRY_BACKOFF = [5, 15, 30]


class TableImageExtractor:
    """
    Extracts business content from table and image pages via a VisionProvider.

    Observability added here is intentionally focused on:

        PDF page
            ↓
        render
            ↓
        Vision request
            ↓
        retry/failure
            ↓
        extracted result

    The public return contract remains:

        dict[int, str]
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
        Render one PDF page and extract content via VisionProvider.

        Returns:
            Extracted text.

        On failure:
            Returns an empty string so the caller can use its fallback logic.
        """

        page_number = page.page_number
        page_type = page.page_type

        logger.info(
            "table_image_extraction_started",
            extra={
                "extra_data": {
                    "pdf": pdf_path.name,
                    "page": page_number,
                    "page_type": page_type,
                    "dpi": dpi,
                    "provider": self._provider.provider_name,
                }
            },
        )

        # ── Render page ─────────────────────────────────────────────────────

        render_started = time.perf_counter()

        try:
            image_bytes = self._render_page(
                pdf_path,
                page_number,
                dpi,
            )

        except Exception as exc:
            render_latency_ms = int(
                (time.perf_counter() - render_started) * 1000
            )

            logger.warning(
                "table_image_extractor_render_failed",
                extra={
                    "extra_data": {
                        "pdf": pdf_path.name,
                        "page": page_number,
                        "page_type": page_type,
                        "dpi": dpi,
                        "latency_ms": render_latency_ms,
                        "error": str(exc)[:300],
                    }
                },
            )

            return ""

        render_latency_ms = int(
            (time.perf_counter() - render_started) * 1000
        )

        logger.info(
            "table_image_extractor_render_complete",
            extra={
                "extra_data": {
                    "pdf": pdf_path.name,
                    "page": page_number,
                    "page_type": page_type,
                    "dpi": dpi,
                    "image_bytes": len(image_bytes),
                    "render_latency_ms": render_latency_ms,
                }
            },
        )

        # ── Prompt ──────────────────────────────────────────────────────────

        try:
            prompt = self._get_prompt(page_type)

        except Exception as exc:
            logger.warning(
                "table_image_extractor_prompt_failed",
                extra={
                    "extra_data": {
                        "pdf": pdf_path.name,
                        "page": page_number,
                        "page_type": page_type,
                        "error": str(exc)[:300],
                    }
                },
            )

            return ""

        logger.info(
            "table_image_extractor_prompt_ready",
            extra={
                "extra_data": {
                    "pdf": pdf_path.name,
                    "page": page_number,
                    "page_type": page_type,
                    "prompt_chars": len(prompt),
                }
            },
        )

        # ── Vision request ─────────────────────────────────────────────────

        for attempt in range(_MAX_RETRIES):

            attempt_number = attempt + 1

            logger.info(
                "table_image_extractor_vision_attempt",
                extra={
                    "extra_data": {
                        "provider": self._provider.provider_name,
                        "pdf": pdf_path.name,
                        "page": page_number,
                        "page_type": page_type,
                        "attempt": attempt_number,
                        "max_retries": _MAX_RETRIES,
                        "image_bytes": len(image_bytes),
                    }
                },
            )

            request_started = time.perf_counter()

            try:

                result = self._provider.extract_page(
                    image_bytes,
                    prompt,
                )

                latency_ms = int(
                    (time.perf_counter() - request_started) * 1000
                )

                logger.info(
                    "table_image_extractor_success",
                    extra={
                        "extra_data": {
                            "provider": self._provider.provider_name,
                            "pdf": pdf_path.name,
                            "page": page_number,
                            "page_type": page_type,
                            "attempt": attempt_number,
                            "result_len": len(result),
                            "latency_ms": latency_ms,
                        }
                    },
                )

                return result

            except VisionProviderError as exc:

                latency_ms = int(
                    (time.perf_counter() - request_started) * 1000
                )

                # Retry only when provider explicitly says the error
                # is retryable.
                if exc.retryable and attempt < _MAX_RETRIES - 1:

                    wait = _RETRY_BACKOFF[attempt]

                    logger.warning(
                        "table_image_extractor_retrying",
                        extra={
                            "extra_data": {
                                "provider": self._provider.provider_name,
                                "pdf": pdf_path.name,
                                "page": page_number,
                                "page_type": page_type,
                                "attempt": attempt_number,
                                "max_retries": _MAX_RETRIES,
                                "wait_s": wait,
                                "retryable": exc.retryable,
                                "latency_ms": latency_ms,
                                "error_type": type(exc).__name__,
                                "error": str(exc)[:300],
                            }
                        },
                    )

                    time.sleep(wait)
                    continue

                logger.warning(
                    "table_image_extractor_provider_failed",
                    extra={
                        "extra_data": {
                            "provider": self._provider.provider_name,
                            "pdf": pdf_path.name,
                            "page": page_number,
                            "page_type": page_type,
                            "attempts": attempt_number,
                            "max_retries": _MAX_RETRIES,
                            "retryable": exc.retryable,
                            "latency_ms": latency_ms,
                            "error_type": type(exc).__name__,
                            "error": str(exc)[:300],
                        }
                    },
                )

                return ""

            except Exception as exc:

                latency_ms = int(
                    (time.perf_counter() - request_started) * 1000
                )

                logger.exception(
                    "table_image_extractor_unexpected_error",
                    extra={
                        "extra_data": {
                            "provider": self._provider.provider_name,
                            "pdf": pdf_path.name,
                            "page": page_number,
                            "page_type": page_type,
                            "attempt": attempt_number,
                            "latency_ms": latency_ms,
                            "error_type": type(exc).__name__,
                            "error": str(exc)[:300],
                        }
                    },
                )

                return ""

        logger.warning(
            "table_image_extractor_retries_exhausted",
            extra={
                "extra_data": {
                    "provider": self._provider.provider_name,
                    "pdf": pdf_path.name,
                    "page": page_number,
                    "page_type": page_type,
                    "max_retries": _MAX_RETRIES,
                }
            },
        )

        return ""

    def extract_pages(
        self,
        pdf_path: Path,
        pages: list[PageClassification],
        dpi: int = _DEFAULT_DPI,
    ) -> dict[int, str]:
        """
        Extract multiple visual pages sequentially.

        Current architecture intentionally remains unchanged.

        We only collect additional observability:

            - total visual pages
            - page ordering
            - success/failure count
            - total output characters
            - total elapsed time
        """

        results: dict[int, str] = {}

        total_pages = len(pages)

        logger.info(
            "table_image_extraction_batch_started",
            extra={
                "extra_data": {
                    "pdf": pdf_path.name,
                    "total_pages": total_pages,
                    "provider": self._provider.provider_name,
                    "dpi": dpi,
                    "inter_page_delay_s": _INTER_PAGE_DELAY_SECONDS,
                    "max_retries": _MAX_RETRIES,
                    "pages": [page.page_number for page in pages],
                }
            },
        )

        batch_started = time.perf_counter()

        success_count = 0
        empty_count = 0
        total_output_chars = 0

        for index, page in enumerate(pages):

            result = self.extract_page(
                pdf_path,
                page,
                dpi,
            )

            results[page.page_number] = result

            result_chars = len(result)

            total_output_chars += result_chars

            if result.strip():
                success_count += 1
            else:
                empty_count += 1

            logger.info(
                "table_image_extraction_page_complete",
                extra={
                    "extra_data": {
                        "pdf": pdf_path.name,
                        "page": page.page_number,
                        "page_type": page.page_type,
                        "page_index": index + 1,
                        "total_pages": total_pages,
                        "status": (
                            "success"
                            if result.strip()
                            else "empty"
                        ),
                        "result_chars": result_chars,
                    }
                },
            )

            # Pause between pages, but not after the final page.
            if index < total_pages - 1:
                time.sleep(_INTER_PAGE_DELAY_SECONDS)

        batch_latency_ms = int(
            (time.perf_counter() - batch_started) * 1000
        )

        logger.info(
            "table_image_extraction_batch_complete",
            extra={
                "extra_data": {
                    "pdf": pdf_path.name,
                    "total_pages": total_pages,
                    "success_pages": success_count,
                    "empty_pages": empty_count,
                    "total_output_chars": total_output_chars,
                    "latency_ms": batch_latency_ms,
                    "provider": self._provider.provider_name,
                }
            },
        )

        return results

    # ── Private helpers ─────────────────────────────────────────────────────

    def _render_page(
        self,
        pdf_path: Path,
        page_number: int,
        dpi: int,
    ) -> bytes:
        """
        Render a single PDF page to PNG bytes using pdf2image.

        page_number:
            0-indexed.

        pdf2image:
            Uses 1-indexed first_page / last_page.
        """

        from pdf2image import convert_from_path

        pages = convert_from_path(
            str(pdf_path),
            dpi=dpi,
            first_page=page_number + 1,
            last_page=page_number + 1,
            poppler_path=(
                str(POPPLER_PATH)
                if POPPLER_PATH
                else None
            ),
            fmt="png",
        )

        if not pages:
            raise RuntimeError(
                f"pdf2image returned no pages for page "
                f"{page_number} of {pdf_path.name}"
            )

        buffer = io.BytesIO()

        pages[0].save(
            buffer,
            format="PNG",
        )

        return buffer.getvalue()

    def _get_prompt(self, page_type: str) -> str:
        """
        Load the appropriate extraction prompt for the page type.
        """

        if page_type == "table":

            if self._table_prompt is None:
                self._table_prompt = _load_prompt(
                    _TABLE_PROMPT_PATH
                )

            return self._table_prompt

        # "image" or any other visual type.
        if self._image_prompt is None:
            self._image_prompt = _load_prompt(
                _IMAGE_PROMPT_PATH
            )

        return self._image_prompt


def _load_prompt(path: str) -> str:
    """
    Load a prompt file from disk.

    Raises:
        FileNotFoundError:
            If the prompt file does not exist.
    """

    path_obj = Path(path)

    if not path_obj.exists():
        raise FileNotFoundError(
            f"Extraction prompt not found: {path}"
        )

    return path_obj.read_text(
        encoding="utf-8"
    )