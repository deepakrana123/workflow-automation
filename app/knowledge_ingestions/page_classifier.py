"""
app/knowledge_ingestions/page_classifier.py

PageClassifier — classifies each PDF page into one of four types:
  text      — narrative paragraphs, standard body content
  table     — page contains a data grid / approval matrix / threshold table
  image     — page is dominated by a diagram, flowchart, or scanned image
  appendix  — supplementary section (Appendix, Annex, Schedule, Exhibit)

Why local, no LLM:
  Classification runs on every page of every BRD before any extraction.
  Using an LLM here would add one API call per page just for routing —
  a 40-page BRD would burn 40 API calls before any useful work happens.
  pypdf gives us enough signal (text length, image count, keyword presence)
  to classify pages accurately without any model call.

Classification logic:
  1. Appendix check first — keyword match on the first 200 chars of page text.
     Appendix pages may also contain tables or images, but the appendix
     designation takes priority because the extraction prompt is different.
  2. Image check — pypdf page.images is non-empty and text content is thin
     (< IMAGE_TEXT_THRESHOLD chars). A page with a large diagram and a
     short caption is an image page.
  3. Table check — heuristic combination of:
       a. Multiple short lines (cell-like structure)
       b. Presence of table-indicator characters (|, tabs, ₹, %, numeric
          patterns like "50,000" or "5L")
       c. High ratio of lines with numbers to total lines
  4. Text — everything else.

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

# Keywords that identify the start of an appendix section
APPENDIX_KEYWORDS = (
    "appendix",
    "annex",
    "schedule",
    "exhibit",
    "addendum",
    "attachment",
)

# Regex for common banking table content indicators
_NUMERIC_PATTERN  = re.compile(r"[\d,]+(?:\.\d+)?")
_CURRENCY_PATTERN = re.compile(r"[₹$€£][\d,]+|[\d,]+\s*(?:lakh|crore|thousand|L\b)")
_PIPE_PATTERN     = re.compile(r"\|")


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class PageClassification:
    page_number: int          # 0-indexed
    page_type:   str          # "text" | "table" | "image" | "appendix"
    text:        str          # raw text from pypdf (may be empty for image pages)
    has_images:  bool         # True if pypdf found embedded images on this page
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
        # Rule 1 — Appendix (checked first, takes priority over other types)
        if self._is_appendix(text):
            return "appendix"

        # Rule 2 — Image (dominant image with thin text)
        if has_images and len(text.strip()) < IMAGE_TEXT_THRESHOLD:
            return "image"

        # Rule 3 — Table (grid structure heuristics)
        if self._is_table(text):
            return "table"

        # Rule 4 — Mixed page with images but enough text to be table-like
        if has_images and self._is_table(text):
            return "table"

        return "text"

    def _is_appendix(self, text: str) -> bool:
        """True when the page starts an appendix/annex/schedule section."""
        # Check the first 300 characters (title area) case-insensitively
        header = text[:300].lower()
        return any(kw in header for kw in APPENDIX_KEYWORDS)

    def _is_table(self, text: str) -> bool:
        """
        Heuristic table detection. Returns True when the page looks like a
        data grid based on multiple independent signals:
          - Presence of pipe characters (markdown or ASCII tables)
          - High density of short lines (cell-like layout)
          - High ratio of lines containing numbers
          - Currency / threshold values (common in approval matrices)
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
            if len(lines) > 0:
                numeric_ratio = numeric_lines / len(lines)
                if numeric_ratio >= TABLE_NUMERIC_LINE_RATIO:
                    return True

        # Signal D — currency/threshold patterns (approval matrices)
        currency_hits = len(_CURRENCY_PATTERN.findall(text))
        if currency_hits >= 3:
            return True

        return False
