"""
app/knowledge_ingestions/table_image_extractor.py

TableImageExtractor — renders PDF pages to PNG images and calls a
VisionProvider to extract structured content from tables and diagrams.

This version adds three capabilities on top of the original per-page renderer,
WITHOUT changing the existing public contracts:

  1. Structured per-page results (PageExtractionResult) that distinguish
     SUCCESS / EMPTY / PROVIDER_FAILED / RATE_LIMITED. An empty page and a
     failed page are no longer conflated.

  2. Rate-limit-aware retry: honour a server Retry-After when present, else
     exponential backoff with jitter. Configurable; no more blind 5/15/30.

  3. Group-aware extraction (extract_groups): independent extraction groups may
     run concurrently up to a bounded, configurable limit
     (VISION_MAX_CONCURRENCY, default 1). Pages inside a continuation group are
     always processed in order, threading a COMPACT accumulated context from
     one page to the next — never resending previous page images or full text.

Backwards compatibility:
  * extract_page(pdf_path, page) -> str            (unchanged signature/return)
  * extract_pages(pdf_path, pages) -> dict[int,str] (unchanged signature/return)
  Both remain thin shims over the richer internal path so existing callers and
  tests keep working. multimodal_extractor uses the richer extract_groups path.

Config note:
  Retry/backoff/concurrency knobs are read from environment variables here with
  conservative defaults, and are also overridable via the constructor (used by
  tests). Step 8 of the rollout centralises these into app/core/config.py.
"""

from __future__ import annotations

import concurrent.futures
import io
import random
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.core.logger import logger
from app.core.setting import POPPLER_PATH
from app.core import config
from app.knowledge_ingestions.page_classifier import PageClassification
from app.knowledge_ingestions.page_metadata import PageMetadata, build_page_metadata
from app.knowledge_ingestions.continuation_detector import ExtractionGroup
from app.knowledge_ingestions.providers.base import (
    VisionProvider,
    VisionProviderError,
)
# NOTE: imported by the original module; retained to avoid unrelated churn.
from app.prompting import PromptManager, PromptContext, PromptKey  # noqa: F401


# ── Render configuration ─────────────────────────────────────────────────────

_DEFAULT_DPI = 150


# ── Prompt paths ─────────────────────────────────────────────────────────────

_TABLE_PROMPT_PATH = "app/prompts/table_extraction.md"
_IMAGE_PROMPT_PATH = "app/prompts/image_extraction.md"


# ── Rate limiting / retry / concurrency configuration ────────────────────────
# Defaults are centralised in app/core/config.py (env-overridable). They remain
# overridable per-instance via the TableImageExtractor constructor (used by
# tests to drive fast, deterministic runs).

_DEFAULT_MAX_RETRIES = config.VISION_MAX_RETRIES
_DEFAULT_BACKOFF_BASE = config.VISION_BACKOFF_BASE_SECONDS
_DEFAULT_BACKOFF_MAX = config.VISION_BACKOFF_MAX_SECONDS
_DEFAULT_BACKOFF_JITTER = config.VISION_BACKOFF_JITTER_SECONDS
_DEFAULT_INTER_PAGE_DELAY = config.VISION_INTER_PAGE_DELAY_SECONDS
_DEFAULT_MAX_CONCURRENCY = config.VISION_MAX_CONCURRENCY

# Upper bound on how much of a previous page's output is carried forward as
# compact continuation context. Keeps the request small — we never resend
# whole pages or images.
_CONTEXT_SUMMARY_MAX_CHARS = 600


# ── Status vocabulary + result ────────────────────────────────────────────────

class ExtractionStatus:
    """Outcome of a single page extraction (plain strings for logs/JSON)."""

    SUCCESS = "SUCCESS"                  # completed, produced meaningful content
    EMPTY = "EMPTY"                      # completed successfully, no content
    PROVIDER_FAILED = "PROVIDER_FAILED"  # request failed after retry handling
    RATE_LIMITED = "RATE_LIMITED"        # 429 / rate-limit exhausted


@dataclass
class PageExtractionResult:
    """
    Structured result for one page. Preserves page_number and provider so the
    caller can tell an EMPTY page from a PROVIDER_FAILED / RATE_LIMITED page and
    still know which page and provider were involved.
    """

    page_number: int
    status: str
    text: str = ""
    provider: str | None = None
    error_type: str | None = None
    attempts: int = 0
    latency_ms: int | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == ExtractionStatus.SUCCESS

    @property
    def is_failure(self) -> bool:
        return self.status in (
            ExtractionStatus.PROVIDER_FAILED,
            ExtractionStatus.RATE_LIMITED,
        )


# ── Compact continuation context ──────────────────────────────────────────────

@dataclass
class ContinuationContext:
    """
    Compact state carried across the pages of a single continuation group.

    Deliberately small: a title, a section, the header row, a structure hint,
    and a truncated summary of the previous page's output. This is appended to
    the prompt for pages 2..n so the model keeps column/structure alignment —
    WITHOUT resending previous page images or full previous text.
    """

    continuation_type: str | None = None
    section: str | None = None
    table_title: str | None = None
    headers: list[str] = field(default_factory=list)
    structure_summary: str | None = None
    last_page_summary: str = ""

    @classmethod
    def initial(cls, meta: PageMetadata, continuation_type: str | None) -> "ContinuationContext":
        """Establish the initial context from the first page of the group."""
        return cls(
            continuation_type=continuation_type,
            section=meta.section_heading,
            table_title=meta.title,
            headers=list(meta.table_headers),
            structure_summary=meta.structure_summary,
            last_page_summary="",
        )

    def update(self, meta: PageMetadata, extracted_text: str) -> None:
        """Fold the just-extracted page into the compact state."""
        # Preserve the group's original title/section/headers (established by
        # the first page); only fill gaps from later pages.
        if not self.section and meta.section_heading:
            self.section = meta.section_heading
        if not self.table_title and meta.title:
            self.table_title = meta.title
        if not self.headers and meta.table_headers:
            self.headers = list(meta.table_headers)

        summary_source = (extracted_text or "").strip() or (meta.ending_text or "")
        summary_source = summary_source.strip()
        if len(summary_source) > _CONTEXT_SUMMARY_MAX_CHARS:
            summary_source = summary_source[-_CONTEXT_SUMMARY_MAX_CHARS:].lstrip()
        self.last_page_summary = summary_source

    def to_prompt_block(self) -> str:
        """Render the compact context as a short prompt suffix."""
        lines = [
            "---",
            "CONTINUATION CONTEXT",
            "This page continues structured content from the previous page of "
            "the same document. Keep the same columns/structure and do NOT "
            "repeat rows already extracted from earlier pages.",
        ]
        if self.continuation_type:
            lines.append(f"Continuation type: {self.continuation_type}")
        if self.table_title:
            lines.append(f"Title: {self.table_title}")
        if self.section:
            lines.append(f"Section: {self.section}")
        if self.headers:
            lines.append("Columns: " + " | ".join(self.headers))
        if self.structure_summary:
            lines.append(f"Structure: {self.structure_summary}")
        if self.last_page_summary:
            lines.append("Previous page ended with:")
            lines.append(self.last_page_summary)
        return "\n".join(lines)


# ── Extractor ─────────────────────────────────────────────────────────────────

class TableImageExtractor:
    """
    Extracts business content from table/image pages via a VisionProvider.

    The provider is injected — never instantiated here. Retry/backoff and
    concurrency are configurable via constructor kwargs (defaulting to the
    env-driven module constants) so tests can drive fast, deterministic runs.
    """

    def __init__(
        self,
        vision_provider: VisionProvider,
        *,
        max_retries: int | None = None,
        backoff_base: float | None = None,
        backoff_max: float | None = None,
        backoff_jitter: float | None = None,
        inter_page_delay: float | None = None,
        max_concurrency: int | None = None,
    ):
        self._provider = vision_provider

        self._max_retries = max_retries if max_retries is not None else _DEFAULT_MAX_RETRIES
        self._backoff_base = backoff_base if backoff_base is not None else _DEFAULT_BACKOFF_BASE
        self._backoff_max = backoff_max if backoff_max is not None else _DEFAULT_BACKOFF_MAX
        self._backoff_jitter = (
            backoff_jitter if backoff_jitter is not None else _DEFAULT_BACKOFF_JITTER
        )
        self._inter_page_delay = (
            inter_page_delay if inter_page_delay is not None else _DEFAULT_INTER_PAGE_DELAY
        )
        self._max_concurrency = max(
            1, max_concurrency if max_concurrency is not None else _DEFAULT_MAX_CONCURRENCY
        )

        self._table_prompt: str | None = None
        self._image_prompt: str | None = None

    # ── Public compatibility shims ────────────────────────────────────────────

    def extract_page(
        self,
        pdf_path: Path,
        page: PageClassification,
        dpi: int = _DEFAULT_DPI,
    ) -> str:
        """
        Backwards-compatible shim: extract one page and return its text.

        Returns "" on failure or empty extraction, exactly as before, so the
        caller's existing fallback logic is unaffected.
        """
        result = self._extract_single(pdf_path, page, dpi=dpi, extra_context=None)
        return result.text

    def extract_pages(
        self,
        pdf_path: Path,
        pages: list[PageClassification],
        dpi: int = _DEFAULT_DPI,
    ) -> dict[int, str]:
        """
        Backwards-compatible shim: extract multiple pages sequentially and
        return {page_number: text}. Preserves the original behaviour (serial,
        inter-page delay, "" on failure) for any existing caller/test.

        The richer, group-aware, status-preserving path is extract_groups().
        """
        results: dict[int, str] = {}
        total = len(pages)
        for index, page in enumerate(pages):
            res = self._extract_single(pdf_path, page, dpi=dpi, extra_context=None)
            results[page.page_number] = res.text
            if index < total - 1:
                self._sleep(self._inter_page_delay)
        return results

    # ── Group-aware extraction (new primary path) ─────────────────────────────

    def extract_groups(
        self,
        pdf_path: Path,
        groups: list[ExtractionGroup],
        page_lookup: dict[int, PageClassification],
        dpi: int = _DEFAULT_DPI,
    ) -> dict[int, PageExtractionResult]:
        """
        Extract all groups and return {page_number: PageExtractionResult}.

        Concurrency model:
          * Each ExtractionGroup is the unit of concurrency. Independent
            (singleton) groups and continuation groups alike are submitted to a
            bounded ThreadPoolExecutor (max_workers = configured concurrency,
            default 1 = fully sequential).
          * Pages WITHIN a continuation group are always processed in order by a
            single worker, threading a compact ContinuationContext.

        Ordering:
          Results are keyed by page_number, so the completion order of
          concurrent groups never affects document order — the caller
          reconstructs order by sorting on page_number.
        """
        results: dict[int, PageExtractionResult] = {}
        if not groups:
            return results

        workers = min(self._max_concurrency, len(groups))

        logger.info(
            "extraction_groups_started",
            extra={"extra_data": {
                "pdf": pdf_path.name,
                "groups": len(groups),
                "pages": sum(len(g.page_numbers) for g in groups),
                "max_concurrency": self._max_concurrency,
                "workers": workers,
                "provider": self._provider.provider_name,
            }},
        )

        if workers <= 1:
            for group in groups:
                results.update(self._extract_group(pdf_path, group, page_lookup, dpi))
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {
                    pool.submit(self._extract_group, pdf_path, group, page_lookup, dpi): group
                    for group in groups
                }
                for future in concurrent.futures.as_completed(futures):
                    results.update(future.result())

        logger.info(
            "extraction_groups_completed",
            extra={"extra_data": {
                "pdf": pdf_path.name,
                "groups": len(groups),
                "pages_extracted": len(results),
                "success": sum(1 for r in results.values() if r.succeeded),
                "empty": sum(1 for r in results.values() if r.status == ExtractionStatus.EMPTY),
                "failed": sum(1 for r in results.values() if r.is_failure),
            }},
        )
        return results

    def _extract_group(
        self,
        pdf_path: Path,
        group: ExtractionGroup,
        page_lookup: dict[int, PageClassification],
        dpi: int,
    ) -> dict[int, PageExtractionResult]:
        """Extract one group. Continuation groups thread a compact context."""
        results: dict[int, PageExtractionResult] = {}
        is_continuation = group.is_continuation
        context: ContinuationContext | None = None
        total = len(group.page_numbers)

        logger.info(
            "extraction_group_started",
            extra={"extra_data": {
                "pdf": pdf_path.name,
                "group_id": group.group_id,
                "pages": list(group.page_numbers),
                "is_continuation": is_continuation,
                "continuation_type": group.continuation_type,
            }},
        )

        for index, page_number in enumerate(group.page_numbers):
            page = page_lookup.get(page_number)
            if page is None:
                # Defensive: a page referenced by a group but absent from the
                # lookup is a caller error; record as a failure, never skip.
                results[page_number] = PageExtractionResult(
                    page_number=page_number,
                    status=ExtractionStatus.PROVIDER_FAILED,
                    provider=self._provider.provider_name,
                    error_type="missing_page",
                )
                continue

            extra_context = None
            if is_continuation and index > 0 and context is not None:
                extra_context = context.to_prompt_block()

            result = self._extract_single(
                pdf_path, page, dpi=dpi, extra_context=extra_context
            )
            results[page_number] = result

            # Maintain compact continuation context across the group.
            if is_continuation:
                meta = build_page_metadata(page)
                if context is None:
                    context = ContinuationContext.initial(meta, group.continuation_type)
                context.update(meta, result.text)

            if index < total - 1:
                self._sleep(self._inter_page_delay)

        logger.info(
            "extraction_group_completed",
            extra={"extra_data": {
                "pdf": pdf_path.name,
                "group_id": group.group_id,
                "pages": list(group.page_numbers),
                "success": sum(1 for r in results.values() if r.succeeded),
                "failed": sum(1 for r in results.values() if r.is_failure),
            }},
        )
        return results

    # ── Single-page extraction with retry/backoff ─────────────────────────────

    def _extract_single(
        self,
        pdf_path: Path,
        page: PageClassification,
        *,
        dpi: int,
        extra_context: str | None,
    ) -> PageExtractionResult:
        """
        Render one page and extract via the VisionProvider, applying
        rate-limit-aware retry/backoff. Returns a PageExtractionResult whose
        status distinguishes SUCCESS / EMPTY / PROVIDER_FAILED / RATE_LIMITED.
        """
        page_number = page.page_number
        page_type = page.page_type
        provider_name = self._provider.provider_name

        logger.info(
            "page_extraction_started",
            extra={"extra_data": {
                "pdf": pdf_path.name,
                "page_number": page_number,
                "page_type": page_type,
                "provider": provider_name,
                "has_context": extra_context is not None,
            }},
        )

        # ── Render ────────────────────────────────────────────────────────────
        try:
            image_bytes = self._render_page(pdf_path, page_number, dpi)
        except Exception as exc:
            logger.warning(
                "page_extraction_failed",
                extra={"extra_data": {
                    "pdf": pdf_path.name,
                    "page_number": page_number,
                    "stage": "render",
                    "error": str(exc)[:300],
                }},
            )
            return PageExtractionResult(
                page_number=page_number,
                status=ExtractionStatus.PROVIDER_FAILED,
                provider=provider_name,
                error_type="render_error",
            )

        # ── Prompt ────────────────────────────────────────────────────────────
        try:
            prompt = self._get_prompt(page_type)
        except Exception as exc:
            logger.warning(
                "page_extraction_failed",
                extra={"extra_data": {
                    "pdf": pdf_path.name,
                    "page_number": page_number,
                    "stage": "prompt",
                    "error": str(exc)[:300],
                }},
            )
            return PageExtractionResult(
                page_number=page_number,
                status=ExtractionStatus.PROVIDER_FAILED,
                provider=provider_name,
                error_type="prompt_error",
            )

        if extra_context:
            prompt = f"{prompt}\n\n{extra_context}"

        # ── Vision request with retry/backoff ─────────────────────────────────
        last_error: VisionProviderError | None = None

        for attempt in range(self._max_retries):
            attempt_number = attempt + 1
            request_started = time.perf_counter()
            try:
                text = self._provider.extract_page(image_bytes, prompt)
                latency_ms = int((time.perf_counter() - request_started) * 1000)
                status = (
                    ExtractionStatus.SUCCESS if text and text.strip()
                    else ExtractionStatus.EMPTY
                )
                logger.info(
                    "page_extraction_completed",
                    extra={"extra_data": {
                        "pdf": pdf_path.name,
                        "page_number": page_number,
                        "page_type": page_type,
                        "provider": provider_name,
                        "status": status,
                        "attempt": attempt_number,
                        "result_chars": len(text or ""),
                        "latency_ms": latency_ms,
                    }},
                )
                return PageExtractionResult(
                    page_number=page_number,
                    status=status,
                    text=text or "",
                    provider=provider_name,
                    attempts=attempt_number,
                    latency_ms=latency_ms,
                )

            except VisionProviderError as exc:
                last_error = exc
                latency_ms = int((time.perf_counter() - request_started) * 1000)

                if exc.is_rate_limited:
                    logger.warning(
                        "provider_rate_limited",
                        extra={"extra_data": {
                            "pdf": pdf_path.name,
                            "page_number": page_number,
                            "provider": provider_name,
                            "attempt": attempt_number,
                            "max_retries": self._max_retries,
                            "retry_after": exc.retry_after,
                            "status_code": exc.status_code,
                            "latency_ms": latency_ms,
                        }},
                    )

                if exc.retryable and attempt < self._max_retries - 1:
                    wait = self._compute_backoff(attempt, exc)
                    logger.warning(
                        "page_extraction_retrying",
                        extra={"extra_data": {
                            "pdf": pdf_path.name,
                            "page_number": page_number,
                            "provider": provider_name,
                            "attempt": attempt_number,
                            "max_retries": self._max_retries,
                            "wait_s": round(wait, 2),
                            "error_type": exc.error_type,
                            "retryable": exc.retryable,
                        }},
                    )
                    self._sleep(wait)
                    continue

                # Exhausted / non-retryable → classify terminal failure.
                return self._failure_result(page_number, provider_name, exc, attempt_number)

            except Exception as exc:
                logger.exception(
                    "page_extraction_failed",
                    extra={"extra_data": {
                        "pdf": pdf_path.name,
                        "page_number": page_number,
                        "stage": "provider_unexpected",
                        "error": str(exc)[:300],
                    }},
                )
                return PageExtractionResult(
                    page_number=page_number,
                    status=ExtractionStatus.PROVIDER_FAILED,
                    provider=provider_name,
                    error_type="unexpected",
                    attempts=attempt_number,
                )

        # Loop exhausted (all attempts retryable failures).
        return self._failure_result(
            page_number, provider_name, last_error, self._max_retries
        )

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _failure_result(
        page_number: int,
        provider_name: str,
        exc: VisionProviderError | None,
        attempts: int,
    ) -> PageExtractionResult:
        """Build a terminal failure result, distinguishing RATE_LIMITED."""
        rate_limited = bool(exc and exc.is_rate_limited)
        return PageExtractionResult(
            page_number=page_number,
            status=(
                ExtractionStatus.RATE_LIMITED if rate_limited
                else ExtractionStatus.PROVIDER_FAILED
            ),
            provider=provider_name,
            error_type=(exc.error_type if exc else None),
            attempts=attempts,
        )

    def _compute_backoff(self, attempt: int, exc: VisionProviderError | None) -> float:
        """
        Compute the wait before the next retry.

        Respect a server Retry-After when provided (capped at backoff_max);
        otherwise exponential backoff (base * 2**attempt) plus uniform jitter,
        capped at backoff_max.
        """
        if exc is not None and exc.retry_after is not None:
            return min(exc.retry_after, self._backoff_max)
        base_wait = min(self._backoff_base * (2 ** attempt), self._backoff_max)
        jitter = random.uniform(0, self._backoff_jitter) if self._backoff_jitter else 0.0
        return min(base_wait + jitter, self._backoff_max)

    @staticmethod
    def _sleep(seconds: float) -> None:
        """Sleep wrapper (kept small so tests can drive zero-delay runs)."""
        if seconds and seconds > 0:
            time.sleep(seconds)

    def _render_page(self, pdf_path: Path, page_number: int, dpi: int) -> bytes:
        """
        Render a single PDF page to PNG bytes using pdf2image.

        page_number is 0-indexed (pypdf convention); pdf2image uses 1-indexed
        first_page/last_page.
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
        buffer = io.BytesIO()
        pages[0].save(buffer, format="PNG")
        return buffer.getvalue()

    def _get_prompt(self, page_type: str) -> str:
        """Load the appropriate extraction prompt for the page type (cached)."""
        if page_type == "table":
            if self._table_prompt is None:
                self._table_prompt = _load_prompt(_TABLE_PROMPT_PATH)
            return self._table_prompt
        # "image" or any other visual type.
        if self._image_prompt is None:
            self._image_prompt = _load_prompt(_IMAGE_PROMPT_PATH)
        return self._image_prompt


def _load_prompt(path: str) -> str:
    """Load a prompt file from disk. Raises FileNotFoundError if missing."""
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Extraction prompt not found: {path}")
    return path_obj.read_text(encoding="utf-8")
