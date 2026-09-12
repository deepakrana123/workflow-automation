"""
app/knowledge_ingestions/page_classifier.py

PageClassifier — classifies each PDF page into one of four types:
  text      — narrative paragraphs, standard body content
  table     — page contains a data grid / approval matrix / threshold table
  image     — page is dominated by a diagram, flowchart, or scanned image
  appendix  — supplementary section (Appendix, Annex, Schedule, Exhibit, etc.)

Why local, no LLM:
  Classification runs on every page of every BRD before any extraction.
  Using an LLM here would add one API call per page just for routing —
  a 40-page BRD would burn 40 API calls before any useful work happens.
  pypdf gives us enough signal (text length, image count, keyword presence)
  to classify pages accurately without any model call.

Classification logic (revised):
  1. Detect an explicit appendix/annex/schedule heading at the top of the page.
     This is done with a line-level regex, NOT a simple substring match, to
     avoid classifying body pages that merely reference an appendix ("See Annex
     A for details") as appendix pages.

  2. If strong table OR image evidence is present, use that classification even
     if the heading check fired — appendix heading does not override structural
     visual content. This prevents a threshold table inside an appendix from
     losing vision extraction.

  3. If only appendix heading evidence is present (no strong table/image), use
     "appendix".

  4. Table check — heuristic combination of structural signals (see _is_table).

  5. Image check — requires pypdf page.images to be non-empty AND text thin.
     NOTE: pypdf page.images only detects embedded raster objects (JPEG/PNG).
     Vector diagrams drawn with PDF path operators are invisible to this check.
     This limitation is preserved deliberately — introducing PDF rendering here
     would make classification expensive and architecturally incorrect.

  6. Text — everything else.

Outputs a PageClassification dataclass per page.
The MultiModalDocumentExtractor uses this to route pages to the right extractor.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader

# ── Thresholds ────────────────────────────────────────────────────────────────

# A page with images and fewer than this many text characters is "image"
IMAGE_TEXT_THRESHOLD = 150

# A page with at least this ratio of numeric lines is likely a table
TABLE_NUMERIC_LINE_RATIO = 0.35

# Minimum number of short lines (< 60 chars) to flag as potential table layout
TABLE_SHORT_LINE_COUNT = 6

# For currency-based table detection we additionally require that the page
# has a compact, line-structured layout. A prose narrative can legitimately
# contain many ₹ amounts; requiring short-line density prevents those pages
# from being mis-classified as tables.
# Minimum fraction of short lines required when relying on currency evidence.
# Set at 0.60 so that a page must have the majority of its lines be compact
# (< 60 chars) — as a genuine data grid would — before currency hits alone
# contribute to table classification. A page with one short header and one long
# prose paragraph produces ~0.50 short-line fraction and does NOT meet this bar.
TABLE_CURRENCY_SHORT_LINE_FRACTION = 0.60

# Minimum number of currency hits still required for Signal D to fire.
TABLE_CURRENCY_MIN_HITS = 3

# ── Regex patterns ────────────────────────────────────────────────────────────

# Common banking table content indicators
_NUMERIC_PATTERN  = re.compile(r"[\d,]+(?:\.\d+)?")
_CURRENCY_PATTERN = re.compile(r"[₹$€£][\d,]+|[\d,]+\s*(?:lakh|crore|thousand|L\b)")
_PIPE_PATTERN     = re.compile(r"\|")

# ── Appendix heading detection ────────────────────────────────────────────────
# Matches a LINE that IS an appendix/annex/schedule/exhibit heading.
#
# Accepted forms (case-insensitive, optional leading whitespace):
#   Appendix
#   Appendix A
#   Appendix 1
#   Annexure A
#   Annexure 1
#   Annex A
#   Annex 1
#   Schedule
#   Schedule 1
#   Schedule A
#   Exhibit A
#   Exhibit 1
#   Addendum
#   Addendum A
#   Attachment
#   Attachment 1
#
# NOT matched (these reference an appendix but are not a heading):
#   "See Appendix A for details"
#   "As per Schedule 1, the following..."
#   "Refer to Exhibit B"
#
# The pattern anchors to the START of a line. After the keyword + optional
# identifier, only whitespace / punctuation / end-of-line is allowed.
# A word like "See" or "Refer" before the keyword would prevent matching.
_APPENDIX_HEADING_RE = re.compile(
    r"""
    ^\s*                                        # optional leading whitespace
    (?:
        appendix(?:ure)?                        # Appendix / Annexure
      | annex(?:ure)?                           # Annex / Annexure
      | schedule
      | exhibit
      | addendum
      | attachment
    )
    (?:                                         # optional identifier
        \s+                                     # space before id
        (?:
            [A-Z0-9]                            # single letter/digit  (A, 1)
          | [A-Z0-9]{1,3}[-–][A-Z0-9]{1,3}     # range like A-1, 1-A
          | \d{1,3}(?:\.\d{1,3})*              # numeric like 1, 1.2
        )
    )?
    \s*[:\-–]?\s*$                              # optional colon/dash, then EOL
    """,
    re.IGNORECASE | re.VERBOSE | re.MULTILINE,
)

# How many lines from the top of the page to search for an appendix heading.
# Keeps detection focused on the page title area without scanning the full body.
_APPENDIX_HEADING_SEARCH_LINES = 6


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class PageClassification:
    page_number: int          # 0-indexed
    page_type:   str          # "text" | "table" | "image" | "appendix"
    text:        str          # raw text from pypdf (may be empty for image pages)
    has_images:  bool         # True if pypdf found embedded raster images
    confidence:  float = 1.0  # reserved for future probabilistic classifiers


@dataclass
class DocumentClassification:
    total_pages:    int
    text_pages:     list[PageClassification] = field(default_factory=list)
    table_pages:    list[PageClassification] = field(default_factory=list)
    image_pages:    list[PageClassification] = field(default_factory=list)
    appendix_pages: list[PageClassification] = field(default_factory=list)

    def all_pages(self) -> list[PageClassification]:
        """Return all pages in original page order."""
        all_p = (
            self.text_pages
            + self.table_pages
            + self.image_pages
            + self.appendix_pages
        )
        return sorted(all_p, key=lambda p: p.page_number)

    def has_rich_content(self) -> bool:
        """True when the document has table or image pages beyond plain text."""
        return bool(self.table_pages or self.image_pages)


# ── Classifier ────────────────────────────────────────────────────────────────

class PageClassifier:
    """
    Classify every page of a PDF using only local heuristics (no LLM, no I/O).

    Usage:
        classifier = PageClassifier()
        doc = classifier.classify(Path("loan_policy.pdf"))
        for page in doc.table_pages:
            print(f"Table on page {page.page_number}")
    """

    def classify(self, pdf_path: Path) -> DocumentClassification:
        reader = PdfReader(pdf_path)
        total  = len(reader.pages)
        result = DocumentClassification(total_pages=total)

        for page_number, page in enumerate(reader.pages):
            text = page.extract_text() or ""

            # NOTE: pypdf page.images only detects embedded raster objects
            # (JPEG, PNG stored as XObject streams). Vector diagrams drawn with
            # PDF path operators are NOT detected here. This is a known
            # limitation — avoid expensive rendering in this classifier.
            has_images = bool(getattr(page, "images", []))

            page_type = self._classify_page(
                page_number=page_number,
                text=text,
                has_images=has_images,
            )

            classification = PageClassification(
                page_number=page_number,
                page_type=page_type,
                text=text,
                has_images=has_images,
            )

            if page_type == "text":
                result.text_pages.append(classification)
            elif page_type == "table":
                result.table_pages.append(classification)
            elif page_type == "image":
                result.image_pages.append(classification)
            elif page_type == "appendix":
                result.appendix_pages.append(classification)

        return result

    # ── Internal classification logic ────────────────────────────────────────

    def _classify_page(
        self,
        page_number: int,
        text: str,
        has_images: bool,
    ) -> str:
        is_appendix_heading = self._is_appendix(text)
        is_image            = has_images and len(text.strip()) < IMAGE_TEXT_THRESHOLD
        is_table            = self._is_table(text)

        # Rule: strong visual/structural evidence overrides appendix heading.
        # A table inside an appendix must not lose vision extraction by being
        # routed only to AppendixExtractor (text-only).
        if is_image:
            return "image"

        if is_table:
            return "table"

        # Only classify as appendix when there is no table/image evidence.
        if is_appendix_heading:
            return "appendix"

        return "text"

    def _is_appendix(self, text: str) -> bool:
        """
        True when the page begins with an explicit appendix/annex/schedule
        heading.

        Uses a line-level regex anchored to the start of a line, not a simple
        substring search, so body text that merely references an appendix
        ("See Appendix A for details") does NOT trigger this.

        Only the first _APPENDIX_HEADING_SEARCH_LINES lines are checked to
        keep detection focused on the page's title area.
        """
        if not text.strip():
            return False

        lines = text.splitlines()
        head  = "\n".join(lines[:_APPENDIX_HEADING_SEARCH_LINES])
        return bool(_APPENDIX_HEADING_RE.search(head))

    def _is_table(self, text: str) -> bool:
        """
        Heuristic table detection. Returns True when the page looks like a
        data grid based on multiple independent signals:

          Signal A — pipe characters   (markdown / ASCII tables)
          Signal B — short-line density (cell-like layout)
          Signal C — numeric-line ratio (numeric content in cells)
          Signal D — currency values + compact structure

        Signal D was previously triggered by currency hits alone, which caused
        narrative pages describing monetary products to be misclassified.
        It now additionally requires that the page has a compact, line-heavy
        structure (>= TABLE_CURRENCY_SHORT_LINE_FRACTION short lines), which
        genuine financial tables satisfy but prose paragraphs do not.
        """
        if not text.strip():
            return False

        lines = [ln for ln in text.split("\n") if ln.strip()]
        if not lines:
            return False

        # Signal A — explicit pipe-separated table structure
        pipe_lines = sum(1 for ln in lines if _PIPE_PATTERN.search(ln))
        if pipe_lines >= 3:
            return True

        # Signal B — high density of short lines (cell-like)
        short_lines = sum(1 for ln in lines if len(ln.strip()) < 60)
        if short_lines >= TABLE_SHORT_LINE_COUNT:
            # Signal C — high numeric line ratio on top of short lines
            numeric_lines = sum(
                1 for ln in lines
                if _NUMERIC_PATTERN.search(ln)
            )
            numeric_ratio = numeric_lines / len(lines)
            if numeric_ratio >= TABLE_NUMERIC_LINE_RATIO:
                return True

        # Signal D — currency/threshold patterns WITH compact line structure.
        # Requiring short-line density prevents narrative paragraphs listing
        # several loan amounts from being classified as tables.
        currency_hits        = len(_CURRENCY_PATTERN.findall(text))
        short_line_fraction  = short_lines / len(lines) if lines else 0.0

        if (
            currency_hits >= TABLE_CURRENCY_MIN_HITS
            and short_line_fraction >= TABLE_CURRENCY_SHORT_LINE_FRACTION
        ):
            return True

        return False
