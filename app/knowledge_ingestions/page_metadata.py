"""
app/knowledge_ingestions/page_metadata.py

PageMetadata — a lightweight, structural fingerprint of a single PDF page,
derived entirely from the raw pypdf text that PageClassifier already extracted.

Why this exists
---------------
The continuation detector (see continuation_detector.py) needs to decide
whether a table/image page is a *continuation* of the previous page or the
start of *new* content. Making that decision by sending page images to a
Vision model would defeat the purpose — it would add exactly the API calls we
are trying to reduce.

Instead we compute a cheap, text-only fingerprint per page. The raw text is
already available on every ``PageClassification`` (pypdf extracted it during
classification at zero extra cost), so building metadata is essentially free:
no rendering, no I/O, no model calls.

The metadata deliberately contains ONLY the signals useful for structural
continuity:

    page_number             0-indexed page number (mirrors PageClassification)
    page_type               "text" | "table" | "image" | "appendix"
    section_heading         explicit section/numbered heading if present
    title                   first heading-like line at the top of the page
    table_headers           best-effort top row of a pipe table (soft signal)
    starting_text           first meaningful line(s), truncated
    ending_text             last meaningful line(s), truncated
    structure_summary       compact machine description of the layout
    has_continuation_marker True if the page text contains "continued" etc.
    has_new_heading         True if a heading/title was detected at the top

Design notes
------------
* Deterministic and local. No LLM. No network.
* Best-effort. When pypdf yields little/no text (scanned/vector pages), most
  fields are empty. The continuation detector treats missing evidence as a
  reason to default to NEW_CONTENT, so degraded metadata is always safe.
* ``table_headers`` is the first non-separator pipe row. On a continuation
  page that begins mid-table this may actually be a *data* row, not a header.
  That is intentional: the detector treats header equality as a soft signal
  and never relies on it alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.knowledge_ingestions.page_classifier import PageClassification


# ── Tunables ──────────────────────────────────────────────────────────────────

# How many lines from the top of the page to scan for a heading/title.
_HEADING_SEARCH_LINES = 6

# Max characters kept for starting_text / ending_text. Enough to compare the
# boundary between two pages without carrying whole paragraphs around.
_EDGE_TEXT_MAX_CHARS = 240

# Number of non-empty lines combined into starting_text / ending_text.
_EDGE_TEXT_LINES = 2

# A "short" line is treated as heading-eligible only below this length.
_HEADING_MAX_CHARS = 80

# Upper bound on the word count of a heading-like line.
_HEADING_MAX_WORDS = 10


# ── Regex patterns ──────────────────────────────────────────────────────────

# Explicit continuation markers. Matched case-insensitively anywhere on the
# page. Word boundaries keep "continued" from matching inside longer words and
# the optional parenthesis/punctuation covers "(continued)", "contd.", "cont'd".
_CONTINUATION_MARKER_RE = re.compile(
    r"""
    \(?\s*
    (?:
        continued
      | continuation
      | cont(?:'|’)?d\.?          # contd / cont'd / cont’d
      | cont\.                    # cont.
      | table\s+continued
      | continued\s+from
      | continued\s+on
    )
    \s*\)?
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Explicit section headings: numbered (1, 1.2, 1.2.3) or keyword-led
# (Section / Chapter / Part / Clause / Article / Table / Appendix ...).
_SECTION_HEADING_RE = re.compile(
    r"""
    ^\s*
    (?:
        \d+(?:\.\d+)*            # 1  | 1.2 | 1.2.3
        (?:[.)]|\s)\s*\S         # followed by . or ) or space then a word
      |
        (?:section|chapter|part|clause|article|schedule|annex(?:ure)?|
           appendix|exhibit|table|figure)
        \b
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# A pipe-table separator row, e.g. "| --- | :---: |" or "|===|===|".
_PIPE_SEPARATOR_RE = re.compile(r"^\s*\|?[\s:|=+-]+\|?\s*$")

# Enumerated headings that begin NEW content but are not numbered/keyword
# sections, e.g. "Scenario 9: ...", "Case 3", "Step 2", "Phase 1".
_ENUM_HEADING_RE = re.compile(
    r"^\s*(?:scenario|case|example|step|phase|stage|exhibit|note)\s+[0-9ivxlc]+\b",
    re.IGNORECASE,
)

# How much of the page tail to keep for cross-page continuation checks. When a
# table spills across a page break, its header/columns sit at the bottom of the
# previous page and repeat at the top of the next. Bounded so metadata stays
# small — this text is used ONLY for local detection and is NEVER sent to the
# Vision provider (ContinuationContext, which IS sent, stays compact).
_BODY_TAIL_MAX_CHARS = 1400

# Minimal stopword set so header-token overlap compares meaningful words only.
_HEADER_STOPWORDS = frozenset(
    {"the", "and", "for", "with", "per", "from", "into", "not", "range"}
)


# ── Data class ────────────────────────────────────────────────────────────────

@dataclass
class PageMetadata:
    """Cheap structural fingerprint of one page. See module docstring."""

    page_number: int
    page_type: str

    section_heading: str | None = None
    title: str | None = None
    table_headers: list[str] = field(default_factory=list)
    starting_text: str = ""
    ending_text: str = ""
    structure_summary: str = ""
    has_continuation_marker: bool = False
    has_new_heading: bool = False
    # Significant lowercase tokens from the page's leading header line — used to
    # detect a repeated table header on a continuation page.
    header_tokens: list[str] = field(default_factory=list)
    # Normalised tail of the page text (bounded), used to detect a table header
    # that crossed the page break (present at the bottom of the previous page).
    body_tail: str = ""


# ── Public builder ────────────────────────────────────────────────────────────

def build_page_metadata(page: PageClassification) -> PageMetadata:
    """
    Build a PageMetadata fingerprint from an already-classified page.

    Cost: pure string processing over ``page.text`` — no rendering, no I/O,
    no model call. Safe to run on every page of every document.

    Args:
        page: a PageClassification carrying page_number, page_type and the
              raw pypdf text.

    Returns:
        PageMetadata with structural signals populated on a best-effort basis.
        Pages with little/no extractable text yield mostly-empty metadata,
        which the continuation detector correctly reads as "insufficient
        evidence" (→ NEW_CONTENT).
    """
    text = page.text or ""

    # Non-empty, stripped lines preserve reading order for edge extraction.
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    section_heading = _detect_section_heading(lines)
    title = _detect_title(lines)
    table_headers = _detect_table_headers(lines)
    starting_text = _edge_text(lines, from_start=True)
    ending_text = _edge_text(lines, from_start=False)
    has_marker = bool(_CONTINUATION_MARKER_RE.search(text))
    has_new_heading = section_heading is not None or title is not None
    structure_summary = _summarize_structure(
        lines=lines,
        page_type=page.page_type,
        table_headers=table_headers,
    )

    return PageMetadata(
        page_number=page.page_number,
        page_type=page.page_type,
        section_heading=section_heading,
        title=title,
        table_headers=table_headers,
        starting_text=starting_text,
        ending_text=ending_text,
        structure_summary=structure_summary,
        has_continuation_marker=has_marker,
        has_new_heading=has_new_heading,
        header_tokens=_header_tokens(starting_text),
        body_tail=_body_tail(text),
    )


# ── Detection helpers ─────────────────────────────────────────────────────────

def _detect_section_heading(lines: list[str]) -> str | None:
    """
    Return the first explicit section/numbered heading within the top of the
    page, or None. Only the first _HEADING_SEARCH_LINES lines are scanned so a
    numbered list buried in the body does not register as a page heading.
    """
    for line in lines[:_HEADING_SEARCH_LINES]:
        if "|" in line:
            continue
        if _SECTION_HEADING_RE.match(line) or _ENUM_HEADING_RE.match(line):
            return line
    return None


def _detect_title(lines: list[str]) -> str | None:
    """
    Return the first heading-like line at the top of the page, or None.

    "Heading-like" is deliberately conservative — it favours NOT detecting a
    heading over a false positive, because a false heading on a continuation
    page would incorrectly break a continuation group. A line qualifies when it
    is short, is not a table row, and looks like a title (explicit section
    heading, ALL CAPS, or Title Case without sentence punctuation).
    """
    for line in lines[:_HEADING_SEARCH_LINES]:
        if _looks_like_heading(line):
            return line
    return None


def _looks_like_heading(line: str) -> bool:
    """Heuristic, deterministic heading test for a single line."""
    stripped = line.strip()
    if not stripped:
        return False
    if "|" in stripped:            # table row, not a heading
        return False
    if len(stripped) > _HEADING_MAX_CHARS:
        return False

    # Explicit section/keyword/numbered heading.
    if _SECTION_HEADING_RE.match(stripped):
        return True

    words = stripped.split()
    if not (1 <= len(words) <= _HEADING_MAX_WORDS):
        return False

    # A heading rarely ends with sentence punctuation.
    if stripped.endswith((".", ",", ";", ":")):
        # Allow a trailing colon (common in "Eligibility Rules:") but reject
        # other sentence-terminal punctuation.
        if not stripped.endswith(":"):
            return False

    letters = [c for c in stripped if c.isalpha()]
    if not letters:
        return False

    # ALL CAPS heading (e.g. "LOAN ELIGIBILITY RULES").
    if stripped.upper() == stripped:
        return True

    # Title Case heading: every alphabetic word starts uppercase. Short
    # connector words (of, the, and, ...) are allowed to stay lowercase.
    _CONNECTORS = {"of", "the", "and", "or", "for", "to", "in", "on", "a", "an", "by"}
    significant = [w for w in words if w.lower() not in _CONNECTORS]
    if significant and all(w[0].isupper() for w in significant if w[0].isalpha()):
        return True

    return False


def _detect_table_headers(lines: list[str]) -> list[str]:
    """
    Best-effort extraction of a pipe table's top row.

    Returns the cells of the first non-separator pipe row, or [] when the page
    has no pipe-delimited table. This is a SOFT signal: on a continuation page
    that starts mid-table the returned cells may be a data row rather than the
    header. The continuation detector accounts for that.
    """
    for line in lines:
        if "|" not in line:
            continue
        if _PIPE_SEPARATOR_RE.match(line):
            continue
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]   # drop empty edges from leading/trailing |
        if cells:
            return cells
    return []


def _edge_text(lines: list[str], *, from_start: bool) -> str:
    """
    Join the first (or last) few non-empty lines into a compact edge string,
    truncated to _EDGE_TEXT_MAX_CHARS. Used to compare the boundary where one
    page ends and the next begins.
    """
    if not lines:
        return ""
    selected = lines[:_EDGE_TEXT_LINES] if from_start else lines[-_EDGE_TEXT_LINES:]
    joined = " ".join(selected).strip()
    if len(joined) > _EDGE_TEXT_MAX_CHARS:
        joined = joined[:_EDGE_TEXT_MAX_CHARS].rstrip()
    return joined


def _header_tokens(starting_text: str) -> list[str]:
    """
    Significant lowercase word tokens from the page's leading header line.

    Used by the continuation detector to check whether the current page's
    header repeats columns that appear in the previous page's tail (a table
    that crossed the page break). Alphabetic tokens of length >= 3 only, minus
    a small stopword set; de-duplicated, order preserved.
    """
    seen: list[str] = []
    for word in re.findall(r"[A-Za-z]{3,}", starting_text or ""):
        w = word.lower()
        if w in _HEADER_STOPWORDS or w in seen:
            continue
        seen.append(w)
    return seen


def _body_tail(text: str) -> str:
    """
    Normalised (whitespace-collapsed, lowercased) tail of the page text,
    bounded to _BODY_TAIL_MAX_CHARS. Local-only; never sent to any provider.
    """
    if not text:
        return ""
    normalized = " ".join(text.split()).lower()
    return normalized[-_BODY_TAIL_MAX_CHARS:]


def _summarize_structure(
    *,
    lines: list[str],
    page_type: str,
    table_headers: list[str],
) -> str:
    """
    Produce a compact, human/machine readable description of the page layout.

    Examples:
        "empty"
        "pipe_table:cols=3;rows=5"
        "short_line_grid:lines=12"
        "prose:lines=8"

    This is intended to be stable and cheap — it summarises shape, not content,
    so it can be logged and compared without leaking full page text.
    """
    if not lines:
        return "empty"

    pipe_rows = sum(1 for ln in lines if "|" in ln and not _PIPE_SEPARATOR_RE.match(ln))
    if pipe_rows >= 2:
        cols = len(table_headers) if table_headers else 0
        return f"pipe_table:cols={cols};rows={pipe_rows}"

    short_lines = sum(1 for ln in lines if len(ln) < 60)
    if short_lines >= max(6, int(0.6 * len(lines))):
        return f"short_line_grid:lines={len(lines)}"

    return f"prose:lines={len(lines)}"
