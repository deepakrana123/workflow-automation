"""
Verification for extraction_result.py — Step 4 file 1.
No DB, no network, no filesystem.
Run from project root:
    .venv312\Scripts\python.exe verify_extraction_result.py
"""

import sys
from datetime import timezone

failures = []

print("=" * 65)
print("FlowOS Step 4 file 1 — extraction_result.py")
print("=" * 65)

# ── 1. Import ─────────────────────────────────────────────────────
print("\n[1] Imports")
try:
    from app.knowledge_ingestions.extraction_result import (
        PageStatus, PageType, ExtractionProvider,
        PageExtractionOutput, ExtractionOwnership,
        DocumentExtractionResult,
        compute_overall_status, make_failed_document,
    )
    print("  OK  all symbols imported")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("import")
    sys.exit(1)  # nothing else can run

# ── 2. PageStatus enum ────────────────────────────────────────────
print("\n[2] PageStatus values")
expected = {"SUCCESS", "EMPTY", "FAILED", "SKIPPED"}
got = {s.value for s in PageStatus}
missing = expected - got
if missing:
    print(f"  FAIL  missing: {missing}")
    failures.append("PageStatus")
else:
    print(f"  OK  {sorted(got)}")

# ── 3. PageType enum ──────────────────────────────────────────────
print("\n[3] PageType values")
expected = {"text", "table", "image", "appendix", "unknown"}
got = {t.value for t in PageType}
if expected - got:
    print(f"  FAIL  missing: {expected - got}")
    failures.append("PageType")
else:
    print(f"  OK  {sorted(got)}")

# ── 4. ExtractionProvider enum ────────────────────────────────────
print("\n[4] ExtractionProvider values")
expected = {"pypdf", "ocr", "vision", "text_llm", "none"}
got = {p.value for p in ExtractionProvider}
if expected - got:
    print(f"  FAIL  missing: {expected - got}")
    failures.append("ExtractionProvider")
else:
    print(f"  OK  {sorted(got)}")

# ── 5. PageExtractionOutput defaults ─────────────────────────────
print("\n[5] PageExtractionOutput defaults")
try:
    p = PageExtractionOutput(
        page_number=1,
        page_type=PageType.TEXT,
        status=PageStatus.SUCCESS,
        provider=ExtractionProvider.PYPDF,
        text="Hello from page 1.",
    )
    assert p.tables == []
    assert p.image_descriptions == []
    assert p.warnings == []
    assert p.error_message is None
    assert p.source_metadata == {}
    assert p.succeeded is True
    assert p.has_content is True
    assert p.needs_review is False
    print("  OK  defaults, succeeded, has_content, needs_review")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("PageExtractionOutput defaults")

# ── 6. PageExtractionOutput FAILED page ──────────────────────────
print("\n[6] PageExtractionOutput FAILED page")
try:
    p = PageExtractionOutput(
        page_number=3,
        page_type=PageType.IMAGE,
        status=PageStatus.FAILED,
        provider=ExtractionProvider.VISION,
        text="",
        error_message="Provider timed out",
        warnings=["Vision provider timed out after 3 retries"],
    )
    assert p.succeeded is False
    assert p.has_content is False
    assert p.needs_review is True
    assert p.error_message == "Provider timed out"
    print("  OK  FAILED page properties")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("FAILED page")

# ── 7. ExtractionOwnership ────────────────────────────────────────
print("\n[7] ExtractionOwnership")
try:
    o = ExtractionOwnership(
        tenant_id=1,
        workspace_id=2,
        document_id=3,
        document_version_id=4,
        ingestion_attempt_id=5,
    )
    assert o.tenant_id == 1
    assert o.ingestion_attempt_id == 5

    o2 = ExtractionOwnership(
        tenant_id=1, workspace_id=2, document_id=3, document_version_id=4
    )
    assert o2.ingestion_attempt_id is None
    print("  OK  ownership fields, optional ingestion_attempt_id")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("ExtractionOwnership")

# ── 8. DocumentExtractionResult.full_text ────────────────────────
print("\n[8] DocumentExtractionResult.full_text")
try:
    ownership = ExtractionOwnership(1, 1, 1, 1)
    pages = [
        PageExtractionOutput(1, PageType.TEXT,  PageStatus.SUCCESS, ExtractionProvider.PYPDF,  text="Page one content."),
        PageExtractionOutput(2, PageType.TABLE, PageStatus.SUCCESS, ExtractionProvider.VISION, text="| Col A | Col B |"),
        PageExtractionOutput(3, PageType.TEXT,  PageStatus.FAILED,  ExtractionProvider.PYPDF,  text=""),
    ]
    result = DocumentExtractionResult(
        ownership=ownership,
        pages=pages,
        total_pages=3,
    )
    ft = result.full_text
    assert "[Page 1]" in ft
    assert "Page one content." in ft
    assert "[Page 2]" in ft
    assert "[Page 3]" not in ft  # empty text, should not appear
    print("  OK  full_text includes non-empty pages in order")
    print(f"  full_text preview: {ft[:80]!r}...")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("full_text")

# ── 9. DocumentExtractionResult.page() lookup ─────────────────────
print("\n[9] DocumentExtractionResult.page() lookup")
try:
    ownership = ExtractionOwnership(1, 1, 1, 1)
    pages = [
        PageExtractionOutput(1, PageType.TEXT,  PageStatus.SUCCESS, ExtractionProvider.PYPDF, text="p1"),
        PageExtractionOutput(2, PageType.TABLE, PageStatus.EMPTY,   ExtractionProvider.VISION, text=""),
    ]
    result = DocumentExtractionResult(ownership=ownership, pages=pages, total_pages=2)
    assert result.page(1).text == "p1"
    assert result.page(2).status == PageStatus.EMPTY
    assert result.page(99) is None
    print("  OK  page() lookup and None for missing page")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("page() lookup")

# ── 10. DocumentExtractionResult computed properties ──────────────
print("\n[10] succeeded_pages / failed_pages / has_usable_content")
try:
    ownership = ExtractionOwnership(1, 1, 1, 1)
    pages = [
        PageExtractionOutput(1, PageType.TEXT,  PageStatus.SUCCESS, ExtractionProvider.PYPDF,  text="ok"),
        PageExtractionOutput(2, PageType.IMAGE, PageStatus.FAILED,  ExtractionProvider.VISION, text=""),
        PageExtractionOutput(3, PageType.TEXT,  PageStatus.SKIPPED, ExtractionProvider.NONE,   text=""),
    ]
    result = DocumentExtractionResult(ownership=ownership, pages=pages, total_pages=3)
    assert len(result.succeeded_pages) == 1
    assert len(result.failed_pages) == 1
    assert result.has_usable_content is True
    print("  OK  succeeded=1  failed=1  has_usable_content=True")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("computed properties")

# ── 11. compute_overall_status ────────────────────────────────────
print("\n[11] compute_overall_status")
try:
    def _page(status: PageStatus, text: str = "x") -> PageExtractionOutput:
        return PageExtractionOutput(
            1, PageType.TEXT, status, ExtractionProvider.PYPDF, text=text
        )

    cases = [
        # (pages, expected_status)
        ([], "EMPTY"),
        ([_page(PageStatus.SKIPPED, "")], "EMPTY"),
        ([_page(PageStatus.SUCCESS)], "SUCCESS"),
        ([_page(PageStatus.SUCCESS), _page(PageStatus.FAILED, "")], "PARTIAL"),
        ([_page(PageStatus.FAILED, "")], "FAILED"),
        ([_page(PageStatus.SUCCESS), _page(PageStatus.EMPTY, "")], "SUCCESS"),
    ]
    for pages, expected in cases:
        got = compute_overall_status(pages)
        assert got == expected, f"compute_overall_status({[p.status for p in pages]}) = {got!r}, expected {expected!r}"
        print(f"  OK  {[p.status.value for p in pages]} → {expected}")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("compute_overall_status")

# ── 12. make_failed_document ──────────────────────────────────────
print("\n[12] make_failed_document")
try:
    ownership = ExtractionOwnership(1, 2, 3, 4)
    result = make_failed_document(
        ownership=ownership,
        error_message="PdfReadError: EOF marker not found",
        total_pages=0,
    )
    assert result.overall_status == "FAILED"
    assert result.error_message == "PdfReadError: EOF marker not found"
    assert result.pages == []
    assert result.ownership.document_id == 3
    print("  OK  make_failed_document populates all fields correctly")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("make_failed_document")

# ── 13. extracted_at is UTC-aware ─────────────────────────────────
print("\n[13] DocumentExtractionResult.extracted_at is UTC-aware")
try:
    ownership = ExtractionOwnership(1, 1, 1, 1)
    result = DocumentExtractionResult(ownership=ownership, pages=[], total_pages=0)
    assert result.extracted_at.tzinfo is not None
    assert result.extracted_at.tzinfo == timezone.utc
    print("  OK  extracted_at has UTC timezone")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("extracted_at timezone")

# ── 14. tables and image_descriptions fields ──────────────────────
print("\n[14] tables and image_descriptions fields")
try:
    p = PageExtractionOutput(
        page_number=5,
        page_type=PageType.TABLE,
        status=PageStatus.SUCCESS,
        provider=ExtractionProvider.VISION,
        text="Loan Amount | Rate\n500000 | 8.5%",
        tables=[
            ["Loan Amount", "Rate"],
            ["500000", "8.5%"],
        ],
        image_descriptions=["Bar chart showing approval rates by region"],
        source_metadata={"latency_ms": 1240, "model": "gemini-1.5-pro"},
    )
    assert len(p.tables) == 2
    assert p.tables[0] == ["Loan Amount", "Rate"]
    assert len(p.image_descriptions) == 1
    assert p.source_metadata["latency_ms"] == 1240
    assert p.has_content is True
    print("  OK  tables, image_descriptions, source_metadata populated")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("tables/image_descriptions")

# ── 15. No dependencies on DB, network or models ──────────────────
print("\n[15] Module has no heavy runtime dependencies")
try:
    import ast, pathlib
    src = pathlib.Path("app/knowledge_ingestions/extraction_result.py").read_text()
    tree = ast.parse(src)
    imports = [
        node.names[0].name if isinstance(node, ast.Import) else node.module
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    heavy = [i for i in imports if i and any(
        h in i for h in ("sqlalchemy", "fastapi", "torch", "transformers", "sentence")
    )]
    if heavy:
        print(f"  FAIL  heavy imports found: {heavy}")
        failures.append("heavy dependencies")
    else:
        print("  OK  no DB / ML / HTTP imports")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("dependency check")

# ── Summary ───────────────────────────────────────────────────────
print("\n" + "=" * 65)
if failures:
    print(f"FAILED — {len(failures)} check(s):")
    for f in failures:
        print(f"  • {f}")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
    sys.exit(0)
