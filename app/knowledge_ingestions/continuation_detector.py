"""
app/knowledge_ingestions/continuation_detector.py

ContinuationDetector — decides, using cheap deterministic signals only,
whether one page is a structural *continuation* of the page immediately
before it, or the start of *new* content. It also groups a document's
ordered visual pages into extraction groups.

Where this sits in the pipeline
--------------------------------
    PageClassifier            → classifies pages (text/table/image/appendix)
    build_page_metadata       → cheap text fingerprint per page (Step 1)
    ContinuationDetector      → THIS FILE: CONTINUATION vs NEW_CONTENT
    build_extraction_groups   → THIS FILE: fold adjacent CONTINUATION pages
    TableImageExtractor       → extracts each group (Step 5)

The detector does NOT render pages, call any model, or do any I/O. It reads
only the PageMetadata produced in Step 1. It is intentionally deterministic:
identical inputs always yield identical decisions, which makes grouping
reproducible and unit-testable.

Guiding rules (from the design)
-------------------------------
* Two adjacent table pages are NOT automatically a continuation.
* A new table title / section heading normally means NEW_CONTENT.
* Explicit "continued" markers are the strongest continuation signal.
* Same/similar table headers with no new heading is a continuation signal.
* A page that begins mid-structure (a table row / list item) with no new
  heading is a continuation signal.
* Insufficient or contradictory evidence ⇒ NEW_CONTENT (never guess).
* The detector never performs workflow extraction.

Extensibility (future LLM disambiguation — NOT implemented here)
----------------------------------------------------------------
``detect()`` computes a deterministic result and then passes it through
``_resolve_ambiguous()``, which by default returns the deterministic result
unchanged. A future LLM-backed detector can subclass ContinuationDetector and
override ``_resolve_ambiguous()`` to break ties inside the ambiguous
confidence band — without touching the deterministic core or any caller.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from app.core.text_similarity import text_similarity
from app.knowledge_ingestions.page_metadata import (
    PageMetadata,
    _CONTINUATION_MARKER_RE,
)


# ── Vocabulary (plain string constants — JSON/log friendly) ───────────────────

class Relationship:
    CONTINUATION = "CONTINUATION"
    NEW_CONTENT = "NEW_CONTENT"


class ContinuationType:
    TABLE = "TABLE"
    LIST = "LIST"
    SECTION = "SECTION"
    PROCEDURE = "PROCEDURE"
    OTHER = "OTHER"
    # NONE is represented as Python None.


# ── Tunables ──────────────────────────────────────────────────────────────────

# Header-string similarity (via app.core.text_similarity, range 0..1) at/above
# which repeated headers count as a strong continuation signal. text_similarity
# returns 1.0 for exact and 0.85 for substring matches, so 0.85 captures
# "same headers, possibly with an extra trailing column".
_HEADER_SIM_STRONG = 0.85

# Lower similarity bound that, combined with a mid-structure page start,
# still supports continuation.
_HEADER_SIM_MIN = 0.60

# Repeated-header continuation via a whitespace-insensitive CONTIGUOUS match:
# the current page's header line (separators stripped) must appear as a
# contiguous substring in the previous page's tail. Whitespace-insensitivity
# survives pypdf concatenating adjacent column labels ("CategoryLoan"); the
# contiguity requirement avoids false merges from scattered common words
# (System/Process/Decision) that unrelated tables happen to share.
_HEADER_SIG_MIN_CHARS = 20

# Below this title similarity, two titles are considered distinct.
_TITLE_DISTINCT_BELOW = 0.60

# Page types that may continue into one another (a rendered table page may be
# classified "image" on a scanned continuation, and vice versa).
_VISUAL_TYPES = {"table", "image"}

# Leading tokens that indicate a page begins mid-list.
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*•·]|\(?\d+[.)]|\(?[a-z][.)]|[ivx]+[.)])\s+", re.IGNORECASE)


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class ContinuationResult:
    """Outcome of comparing a (previous, current) page pair."""

    relationship: str                       # Relationship.*
    confidence: float                       # 0.0 – 1.0
    reason: str                             # human-readable justification
    continuation_type: str | None = None    # ContinuationType.* or None

    @property
    def is_continuation(self) -> bool:
        return self.relationship == Relationship.CONTINUATION


@dataclass
class ExtractionGroup:
    """
    An ordered set of page numbers to be extracted together.

    A singleton group (one page) is an independent unit and may be processed
    concurrently with other independent groups. A multi-page group is a
    continuation chain whose pages MUST be extracted in order, threading a
    compact accumulated context from one page to the next.
    """

    group_id: int
    page_numbers: list[int] = field(default_factory=list)
    continuation_type: str | None = None
    # Per-adjacent-pair detection results, kept for observability/logging.
    detections: list[ContinuationResult] = field(default_factory=list)

    @property
    def is_continuation(self) -> bool:
        return len(self.page_numbers) > 1

    @property
    def first_page(self) -> int:
        return self.page_numbers[0]


# ── Detector ──────────────────────────────────────────────────────────────────

class ContinuationDetector:
    """
    Deterministic continuation detector.

    Usage:
        detector = ContinuationDetector()
        result = detector.detect(prev_meta, curr_meta)
        if result.is_continuation:
            ...
    """

    def detect(self, prev: PageMetadata, curr: PageMetadata) -> ContinuationResult:
        """
        Classify the relationship between ``curr`` and the page immediately
        before it, ``prev``.

        Adjacency (curr.page_number == prev.page_number + 1) is enforced by
        build_extraction_groups, not here — detect() is a pure pairwise
        comparison so it can be unit-tested in isolation.
        """
        deterministic = self._detect_deterministic(prev, curr)
        return self._resolve_ambiguous(prev, curr, deterministic)

    # ── Deterministic core ────────────────────────────────────────────────────

    def _detect_deterministic(
        self, prev: PageMetadata, curr: PageMetadata
    ) -> ContinuationResult:
        # 0. No usable structure on the current page ⇒ not enough evidence.
        if curr.structure_summary == "empty" and not curr.has_continuation_marker:
            return ContinuationResult(
                Relationship.NEW_CONTENT,
                confidence=0.90,
                reason="current page has no extractable structure",
            )

        # 1. Explicit continuation marker — strongest signal.
        if curr.has_continuation_marker or _ending_marks_continuation(prev):
            return ContinuationResult(
                Relationship.CONTINUATION,
                confidence=0.95,
                reason="explicit continuation marker present",
                continuation_type=_infer_type(prev, curr),
            )

        # 2. A genuine new SECTION heading on the current page ⇒ new content.
        #    Only explicit numbered/keyword/enumerated headings force this
        #    (e.g. "3.", "4.2", "Section 5", "Scenario 9:"). A generic
        #    title-case first line does NOT — on a real (pipe-less) table that
        #    line is usually the repeated column header of a continued table,
        #    which must be handled as a continuation (rule 3), not new content.
        section_heading = curr.section_heading
        if section_heading and not _line_is_marker(section_heading):
            return ContinuationResult(
                Relationship.NEW_CONTENT,
                confidence=0.90,
                reason=f"current page starts a new section heading: {section_heading!r}",
            )

        # From here: current page has no explicit section heading and no marker.

        # 3. A genuinely NEW title on the current page ⇒ new content. This is
        #    checked BEFORE the continuation signals so a new table with the
        #    same column headers (but its own distinct title) is not merged.
        #    _distinct_new_title excludes titles that are really a header
        #    repeated from the previous page (those fall through to rule 4).
        if _distinct_new_title(prev, curr):
            return ContinuationResult(
                Relationship.NEW_CONTENT,
                confidence=0.85,
                reason=f"current page starts a distinct new title: {curr.title!r}",
            )

        types_compatible = _types_compatible(prev, curr)

        if types_compatible:
            # 4. Repeated table header across a page break: the current page's
            #    header reappears as a long contiguous run in the previous
            #    page's tail (the table crossed the boundary). Works for
            #    pipe-less real-world tables; a long contiguous match avoids
            #    merging unrelated tables that share only scattered words.
            if _repeated_header(prev, curr):
                return ContinuationResult(
                    Relationship.CONTINUATION,
                    confidence=0.88,
                    reason="repeated table header across page break",
                    continuation_type=ContinuationType.TABLE,
                )

            # 5. Same / highly similar PIPE headers ⇒ continuation.
            header_sim = _header_similarity(prev, curr)
            if header_sim >= _HEADER_SIM_STRONG:
                return ContinuationResult(
                    Relationship.CONTINUATION,
                    confidence=min(0.95, 0.75 + header_sim * 0.2),
                    reason=f"repeated/similar table headers (sim={header_sim:.2f})",
                    continuation_type=_infer_type(prev, curr),
                )

            # 6. Current page begins mid-structure (table row / list item) and
            #    the previous page was itself structured ⇒ continuation without
            #    a repeated header.
            if _begins_mid_structure(curr) and _is_structured(prev):
                confidence = 0.72
                if header_sim >= _HEADER_SIM_MIN:
                    confidence = 0.78
                return ContinuationResult(
                    Relationship.CONTINUATION,
                    confidence=confidence,
                    reason=(
                        "current page begins mid-structure; previous page is "
                        "structured"
                    ),
                    continuation_type=_infer_type(prev, curr),
                )

        # 7. Default — insufficient evidence ⇒ new content.
        return ContinuationResult(
            Relationship.NEW_CONTENT,
            confidence=0.60,
            reason="insufficient evidence for continuation",
        )

    # ── Extension point (future LLM disambiguation) ────────────────────────────

    def _resolve_ambiguous(
        self,
        prev: PageMetadata,
        curr: PageMetadata,
        deterministic: ContinuationResult,
    ) -> ContinuationResult:
        """
        Hook for a future LLM-backed detector to break ties in the ambiguous
        confidence band. The deterministic detector returns the result
        unchanged — no model is called and no per-page cost is incurred.

        A subclass may override this to, for example, ask an LLM only when
        ``deterministic.confidence`` falls within a narrow ambiguous range,
        while still defaulting to NEW_CONTENT if the LLM is unavailable.
        """
        return deterministic


# ── Grouping ──────────────────────────────────────────────────────────────────

def build_extraction_groups(
    pages: list[PageMetadata],
    detector: ContinuationDetector | None = None,
) -> list[ExtractionGroup]:
    """
    Fold an ordered list of page metadata into extraction groups.

    Two pages are placed in the same group only when BOTH hold:
      1. They are physically adjacent (curr.page_number == prev.page_number+1).
      2. detector.detect(prev, curr) returns CONTINUATION.

    A non-adjacent page (a gap, e.g. a text/body page sat between two table
    pages) always starts a new group — a break in physical continuity breaks
    structural continuity.

    Args:
        pages:    page metadata IN DOCUMENT ORDER (typically the visual pages
                  the Vision provider will process).
        detector: detector to use (defaults to the deterministic detector).

    Returns:
        Groups in document order. Each group's page_numbers are ordered.
    """
    detector = detector or ContinuationDetector()

    groups: list[ExtractionGroup] = []
    if not pages:
        return groups

    ordered = sorted(pages, key=lambda m: m.page_number)

    current = ExtractionGroup(group_id=0, page_numbers=[ordered[0].page_number])
    prev_meta = ordered[0]

    for meta in ordered[1:]:
        adjacent = meta.page_number == prev_meta.page_number + 1
        result = detector.detect(prev_meta, meta) if adjacent else None

        if adjacent and result is not None and result.is_continuation:
            current.page_numbers.append(meta.page_number)
            current.detections.append(result)
            if current.continuation_type is None:
                current.continuation_type = result.continuation_type
        else:
            groups.append(current)
            current = ExtractionGroup(
                group_id=len(groups),
                page_numbers=[meta.page_number],
            )

        prev_meta = meta

    groups.append(current)
    return groups


# ── Pure signal helpers ───────────────────────────────────────────────────────

def _line_is_marker(line: str | None) -> bool:
    """True when a heading/title line is itself a continuation marker."""
    if not line:
        return False
    return bool(_CONTINUATION_MARKER_RE.search(line))


def _ending_marks_continuation(prev: PageMetadata) -> bool:
    """
    True when the previous page's trailing text announces a continuation
    ("continued on next page", "table continued", ...).
    """
    return bool(_CONTINUATION_MARKER_RE.search(prev.ending_text or ""))


def _types_compatible(prev: PageMetadata, curr: PageMetadata) -> bool:
    """
    Two pages may continue into one another only when their page types are
    compatible: the same type, or both visual (table/image).
    """
    if prev.page_type == curr.page_type:
        return True
    return prev.page_type in _VISUAL_TYPES and curr.page_type in _VISUAL_TYPES


def _header_similarity(prev: PageMetadata, curr: PageMetadata) -> float:
    """
    Similarity between the two pages' detected header rows in [0, 1].

    Returns 0.0 when either page has no detected headers (no evidence — must
    not be read as a match). Otherwise defers to app.core.text_similarity on
    the normalised header strings so the signal reuses the existing utility.
    """
    if not prev.table_headers or not curr.table_headers:
        return 0.0
    a = " ".join(h.lower().strip() for h in prev.table_headers)
    b = " ".join(h.lower().strip() for h in curr.table_headers)
    if not a or not b:
        return 0.0
    return text_similarity(a, b)


def _alnum_signature(text: str) -> str:
    """Lowercase, strip everything except a-z0-9 — a whitespace/separator
    insensitive signature (robust to pypdf concatenating column labels)."""
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def _longest_common_run(a: str, b: str) -> int:
    """Length of the longest contiguous substring shared by a and b."""
    if not a or not b:
        return 0
    return SequenceMatcher(None, a, b, autojunk=False).find_longest_match(
        0, len(a), 0, len(b)
    ).size


def _repeated_header(prev: PageMetadata, curr: PageMetadata) -> bool:
    """
    True when the current page's header reappears — as a long CONTIGUOUS,
    whitespace-insensitive run — in the previous page's tail. That is the
    signature of one table's header repeating after a page break (the table
    crossed the boundary), even for pipe-less tables where pypdf concatenates
    column labels.

    A long *contiguous* run is what separates a genuine repeat (the header
    phrase reappears, e.g. "productcategoryloantypeticketsize…") from unrelated
    tables that merely share scattered generic words (system/process/decision),
    which never form a long contiguous match.
    """
    head = _alnum_signature(curr.starting_text)[:200]
    if len(head) < _HEADER_SIG_MIN_CHARS:
        return False
    tail = _alnum_signature(prev.body_tail)
    if len(tail) < _HEADER_SIG_MIN_CHARS:
        return False
    return _longest_common_run(head, tail) >= _HEADER_SIG_MIN_CHARS


def _distinct_new_title(prev: PageMetadata, curr: PageMetadata) -> bool:
    """
    True when the current page introduces a genuinely NEW title — one that is
    clearly different from the previous page's title AND does not already appear
    in the previous page's tail.

    The second condition is the key guard: on a continued table the current
    page's leading line is the repeated column header, which DOES appear in the
    previous page's tail — that is a continuation, not a new title, so it must
    not be treated as distinct.
    """
    curr_title = (curr.title or "").strip()
    if not curr_title or _line_is_marker(curr_title):
        return False
    # If this "title" already appears in the previous page's tail, it is a
    # header repeated from a table that crossed the page break — a
    # continuation, NOT a new title (handled by rule 4). This holds for any
    # title length, so short repeated headers ("Scenario / Mismatch") are not
    # mistaken for new titles.
    title_sig = _alnum_signature(curr_title)
    prev_tail_sig = _alnum_signature(prev.body_tail)
    if title_sig and prev_tail_sig and title_sig in prev_tail_sig:
        return False
    prev_title = (prev.title or "").strip()
    if not prev_title:
        return True  # current page introduces a title where the previous had none
    return text_similarity(prev_title.lower(), curr_title.lower()) < _TITLE_DISTINCT_BELOW


def _begins_mid_structure(curr: PageMetadata) -> bool:
    """
    True when the current page begins directly with a table row or list item
    (rather than prose or a heading).
    """
    start = (curr.starting_text or "").lstrip()
    if not start:
        return False
    if start.startswith("|"):
        return True
    return bool(_LIST_ITEM_RE.match(start))


def _is_structured(prev: PageMetadata) -> bool:
    """True when the previous page looks like a table or grid/list layout."""
    summary = prev.structure_summary or ""
    if summary.startswith("pipe_table") or summary.startswith("short_line_grid"):
        return True
    return prev.page_type in _VISUAL_TYPES


def _infer_type(prev: PageMetadata, curr: PageMetadata) -> str:
    """Infer the continuation_type from the pages' structure/layout."""
    for meta in (curr, prev):
        summary = meta.structure_summary or ""
        if summary.startswith("pipe_table"):
            return ContinuationType.TABLE
    if _begins_mid_structure(curr) and _LIST_ITEM_RE.match(
        (curr.starting_text or "").lstrip()
    ):
        return ContinuationType.LIST
    if (curr.starting_text or "").lstrip().startswith("|"):
        return ContinuationType.TABLE
    if prev.page_type in _VISUAL_TYPES or curr.page_type in _VISUAL_TYPES:
        return ContinuationType.TABLE
    if prev.section_heading or curr.section_heading:
        return ContinuationType.SECTION
    return ContinuationType.OTHER
