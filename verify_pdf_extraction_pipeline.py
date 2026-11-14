"""
Verification for pdf_extraction_pipeline.py + multimodal_extractor.py changes.
No real LLM calls. Uses in-memory SQLite + temp files.
Run from project root:
    .venv312\Scripts\python.exe verify_pdf_extraction_pipeline.py

Checks:
  A  imports
  B  ownership mismatch (wrong tenant) → FAILED result
  C  ownership mismatch (wrong workspace) → FAILED result
  D  storage_path missing → FAILED result
  E  file not in storage → FAILED result
  F  corrupt PDF → typed result, no raise
  G  extract_structured() on MultiModalDocumentExtractor returns 3-tuple
  H  extract() still returns str (backward compatibility)
  I  PdfExtractionPipeline calls extract_structured (structured path)
  J  successful registration → DocumentExtractionResult with pages
  K  temp file always cleaned up
  L  temp file cleaned up after extractor raise
  M  ownership context carried through to result
  N  _parse_visual_sections is gone (no string parsing)
"""

import hashlib
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models

failures = []

_MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
    b"/Resources<</Font<</F1 4 0 R>>>>>>endobj\n"
    b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"5 0 obj<</Length 44>>\nstream\n"
    b"BT /F1 12 Tf 100 700 Td (Hello World) Tj ET\n"
    b"endstream\nendobj\n"
    b"xref\n0 6\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"0000000266 00000 n \n"
    b"0000000347 00000 n \n"
    b"trailer<</Size 6/Root 1 0 R>>\n"
    b"startxref\n447\n%%EOF\n"
)
_CORRUPT_PDF = b"this is not a valid pdf at all"


def _make_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _seed(db, tenant_id=1, workspace_id=1, doc_id=1, ver_id=1,
          sha256=None, storage_path=None):
    from app.models.tenant import Tenant
    from app.models.workspace import Workspace
    from app.models.brd_document import BRDDocument, IngestionStatus
    from app.models.document_version import DocumentVersion, VersionStatus
    t = Tenant(id=tenant_id, name=f"bank{tenant_id}",
               slug=f"bank-{tenant_id}", display_name=f"Bank {tenant_id}", active=True)
    w = Workspace(id=workspace_id, tenant_id=tenant_id,
                  name="personal_loan", display_name="Personal Loan", active=True)
    d = BRDDocument(id=doc_id, tenant_id=tenant_id, workspace_id=workspace_id,
                    original_filename="brd.pdf", sha256_hash=sha256 or "a"*64,
                    mime_type="application/pdf", document_type="brd",
                    ingestion_status=IngestionStatus.REGISTERED.value,
                    attempt_count=0, version=1)
    v = DocumentVersion(id=ver_id, document_id=doc_id, version_number=1,
                        original_filename="brd.pdf", sha256_hash=sha256 or "a"*64,
                        mime_type="application/pdf",
                        storage_path=storage_path or "1/1/abcdef12/abc_brd.pdf",
                        status=VersionStatus.REGISTERED.value)
    db.add_all([t, w, d, v])
    db.commit()
    return t, w, d, v


def _make_storage(pdf_bytes=_MINIMAL_PDF, key="1/1/abcdef12/abc_brd.pdf"):
    from app.storage.service import FileStorageService
    from app.storage.local import LocalStorageProvider
    tmp = tempfile.mkdtemp()
    svc = FileStorageService(provider=LocalStorageProvider(base_path=tmp))
    svc._provider.save(key, pdf_bytes)
    return svc, tmp


def _ownership(tenant_id=1, workspace_id=1, doc_id=1, ver_id=1, attempt_id=1):
    from app.knowledge_ingestions.extraction_result import ExtractionOwnership
    return ExtractionOwnership(tenant_id=tenant_id, workspace_id=workspace_id,
                               document_id=doc_id, document_version_id=ver_id,
                               ingestion_attempt_id=attempt_id)


print("=" * 65)
print("FlowOS — PdfExtractionPipeline + extract_structured() verification")
print("=" * 65)

# ── A: imports ────────────────────────────────────────────────────
print("\n[A] Imports")
try:
    from app.knowledge_ingestions.pdf_extraction_pipeline import PdfExtractionPipeline
    from app.knowledge_ingestions.multimodal_extractor import MultiModalDocumentExtractor
    from app.knowledge_ingestions.extraction_result import (
        DocumentExtractionResult, ExtractionOwnership, PageStatus,
    )
    print("  OK  all imports succeed")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("A imports")
    sys.exit(1)

# ── B: wrong tenant → FAILED ──────────────────────────────────────
print("\n[B] Wrong tenant → FAILED result")
try:
    db = _make_session(); _, _, _, ver = _seed(db, tenant_id=1)
    svc, _ = _make_storage(); pipeline = PdfExtractionPipeline(db=db, storage=svc)
    result = pipeline.extract(ver, _ownership(tenant_id=99))
    assert result.overall_status == "FAILED"
    assert "Ownership validation failed" in (result.error_message or "")
    print("  OK")
    db.close()
except Exception as e:
    import traceback; traceback.print_exc()
    print(f"  FAIL  {e}"); failures.append("B")

# ── C: wrong workspace → FAILED ───────────────────────────────────
print("\n[C] Wrong workspace → FAILED result")
try:
    db = _make_session(); _, _, _, ver = _seed(db)
    svc, _ = _make_storage(); pipeline = PdfExtractionPipeline(db=db, storage=svc)
    result = pipeline.extract(ver, _ownership(workspace_id=99))
    assert result.overall_status == "FAILED"
    print("  OK")
    db.close()
except Exception as e:
    print(f"  FAIL  {e}"); failures.append("C")

# ── D: storage_path None → FAILED ────────────────────────────────
print("\n[D] storage_path=None → FAILED result")
try:
    db = _make_session(); _, _, _, ver = _seed(db, storage_path="1/1/x.pdf")
    ver.storage_path = None
    svc, _ = _make_storage(); pipeline = PdfExtractionPipeline(db=db, storage=svc)
    result = pipeline.extract(ver, _ownership())
    assert result.overall_status == "FAILED"
    print("  OK")
    db.close()
except Exception as e:
    print(f"  FAIL  {e}"); failures.append("D")

# ── E: file not in storage → FAILED ──────────────────────────────
print("\n[E] File not in storage → FAILED result")
try:
    db = _make_session(); _, _, _, ver = _seed(db, storage_path="1/1/nosuch.pdf")
    svc, _ = _make_storage(); pipeline = PdfExtractionPipeline(db=db, storage=svc)
    result = pipeline.extract(ver, _ownership())
    assert result.overall_status == "FAILED"
    print("  OK")
    db.close()
except Exception as e:
    print(f"  FAIL  {e}"); failures.append("E")

# ── F: corrupt PDF → typed result, no raise ───────────────────────
print("\n[F] Corrupt PDF → typed result, no raise")
try:
    key = "1/1/abcdef12/abc_brd.pdf"
    db = _make_session(); _, _, _, ver = _seed(db, storage_path=key)
    svc, _ = _make_storage(pdf_bytes=_CORRUPT_PDF, key=key)
    pipeline = PdfExtractionPipeline(db=db, storage=svc)
    result = pipeline.extract(ver, _ownership())
    assert isinstance(result, DocumentExtractionResult)
    print(f"  OK  status={result.overall_status}")
    db.close()
except Exception as e:
    print(f"  FAIL  {e}"); failures.append("F")

# ── G: extract_structured returns 3-tuple ────────────────────────
print("\n[G] MultiModalDocumentExtractor.extract_structured() returns 3-tuple")
try:
    # Mock providers so no real API calls happen
    mock_vision = MagicMock()
    mock_vision.provider_name = "mock_vision"
    mock_vision.extract_page.return_value = "table content"

    mock_text = MagicMock()
    mock_text.provider_name = "mock_text"
    mock_text.generate.return_value = "appendix content"

    from app.knowledge_ingestions.page_classifier import PageClassifier
    extractor = MultiModalDocumentExtractor(
        vision_provider=mock_vision,
        text_provider=mock_text,
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        f.write(_MINIMAL_PDF)
        tmp = Path(f.name)

    try:
        result = extractor.extract_structured(tmp)
        assert isinstance(result, tuple), f"expected tuple, got {type(result)}"
        assert len(result) == 3, f"expected 3-tuple, got {len(result)}-tuple"
        merged_text, doc_cls, visual_results = result
        assert isinstance(merged_text, str)
        # doc_cls may be None (plain-text fast path) or DocumentClassification
        assert isinstance(visual_results, dict)
        print(f"  OK  3-tuple: str + {type(doc_cls).__name__} + dict({len(visual_results)} visual pages)")
    finally:
        tmp.unlink(missing_ok=True)
except Exception as e:
    import traceback; traceback.print_exc()
    print(f"  FAIL  {e}"); failures.append("G")

# ── H: extract() still returns str ───────────────────────────────
print("\n[H] extract() backward compatibility — still returns str")
try:
    mock_vision = MagicMock(); mock_vision.provider_name = "mock"
    mock_vision.extract_page.return_value = ""
    mock_text = MagicMock(); mock_text.provider_name = "mock"
    mock_text.generate.return_value = ""
    extractor = MultiModalDocumentExtractor(
        vision_provider=mock_vision, text_provider=mock_text
    )
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        f.write(_MINIMAL_PDF)
        tmp = Path(f.name)
    try:
        result = extractor.extract(tmp)
        assert isinstance(result, str), f"expected str, got {type(result)}"
        print("  OK  extract() still returns str")
    finally:
        tmp.unlink(missing_ok=True)
except Exception as e:
    print(f"  FAIL  {e}"); failures.append("H")

# ── I: pipeline uses extract_structured ───────────────────────────
print("\n[I] PdfExtractionPipeline calls extract_structured (not extract)")
try:
    key = "1/1/abcdef12/abc_brd.pdf"
    db = _make_session(); _, _, _, ver = _seed(db, storage_path=key)
    svc, _ = _make_storage(key=key)

    mock_extractor = MagicMock()
    # extract_structured must be called; extract must NOT be called
    mock_extractor.extract_structured.return_value = (
        "some extracted text", None, {}
    )
    mock_extractor.extract.side_effect = AssertionError(
        "extract() called — pipeline should call extract_structured() instead"
    )

    pipeline = PdfExtractionPipeline(db=db, storage=svc, extractor=mock_extractor)
    result = pipeline.extract(ver, _ownership())

    assert mock_extractor.extract_structured.called, \
        "extract_structured was not called"
    assert not mock_extractor.extract.called, \
        "extract() was called — should not be"
    assert isinstance(result, DocumentExtractionResult)
    print("  OK  extract_structured() called, extract() not called")
    db.close()
except Exception as e:
    import traceback; traceback.print_exc()
    print(f"  FAIL  {e}"); failures.append("I")

# ── J: successful extraction returns result with pages ────────────
print("\n[J] Successful extraction → result with pages")
try:
    key = "1/1/abcdef12/abc_brd.pdf"
    db = _make_session(); _, _, _, ver = _seed(db, storage_path=key)
    svc, _ = _make_storage(key=key)

    mock_extractor = MagicMock()
    mock_extractor.extract_structured.return_value = ("body text", None, {})

    pipeline = PdfExtractionPipeline(db=db, storage=svc, extractor=mock_extractor)
    result = pipeline.extract(ver, _ownership())

    assert isinstance(result, DocumentExtractionResult)
    assert result.ownership.tenant_id == 1
    assert result.ownership.workspace_id == 1
    assert result.extractor_version == "1.0.0"
    print(f"  OK  status={result.overall_status}  pages={len(result.pages)}")
    db.close()
except Exception as e:
    import traceback; traceback.print_exc()
    print(f"  FAIL  {e}"); failures.append("J")

# ── K: temp file always deleted ───────────────────────────────────
print("\n[K] Temp file cleaned up after extraction")
try:
    import glob
    key = "1/1/abcdef12/abc_brd.pdf"
    db = _make_session(); _, _, _, ver = _seed(db, storage_path=key)
    svc, _ = _make_storage(key=key)
    before = set(glob.glob(tempfile.gettempdir() + "/mflows_extract_*.pdf"))

    mock_extractor = MagicMock()
    mock_extractor.extract_structured.return_value = ("text", None, {})
    PdfExtractionPipeline(db=db, storage=svc, extractor=mock_extractor).extract(
        ver, _ownership()
    )

    after = set(glob.glob(tempfile.gettempdir() + "/mflows_extract_*.pdf"))
    leftover = after - before
    assert not leftover, f"leftover: {leftover}"
    print("  OK  no temp files left")
    db.close()
except Exception as e:
    print(f"  FAIL  {e}"); failures.append("K")

# ── L: temp file deleted even when extractor raises ───────────────
print("\n[L] Temp file cleaned up after extractor raise")
try:
    import glob
    key = "1/1/abcdef12/abc_brd.pdf"
    db = _make_session(); _, _, _, ver = _seed(db, storage_path=key)
    svc, _ = _make_storage(key=key)
    before = set(glob.glob(tempfile.gettempdir() + "/mflows_extract_*.pdf"))

    mock_extractor = MagicMock()
    mock_extractor.extract_structured.side_effect = RuntimeError("boom")
    result = PdfExtractionPipeline(db=db, storage=svc, extractor=mock_extractor).extract(
        ver, _ownership()
    )

    after = set(glob.glob(tempfile.gettempdir() + "/mflows_extract_*.pdf"))
    leftover = after - before
    assert not leftover, f"leftover after raise: {leftover}"
    assert result.overall_status in ("FAILED", "EMPTY", "PARTIAL", "SUCCESS")
    print("  OK  temp file cleaned up after raise")
    db.close()
except Exception as e:
    print(f"  FAIL  {e}"); failures.append("L")

# ── M: ownership context carried through ──────────────────────────
print("\n[M] Ownership context in result")
try:
    key = "2/3/abcdef12/brd.pdf"
    db = _make_session()
    _, _, _, ver = _seed(db, tenant_id=2, workspace_id=3, doc_id=4, ver_id=5,
                         storage_path=key)
    svc, _ = _make_storage(key=key)
    mock_extractor = MagicMock()
    mock_extractor.extract_structured.return_value = ("text", None, {})
    pipeline = PdfExtractionPipeline(db=db, storage=svc, extractor=mock_extractor)
    o = _ownership(tenant_id=2, workspace_id=3, doc_id=4, ver_id=5, attempt_id=7)
    result = pipeline.extract(ver, o)
    assert result.ownership.tenant_id            == 2
    assert result.ownership.workspace_id         == 3
    assert result.ownership.document_id          == 4
    assert result.ownership.document_version_id  == 5
    assert result.ownership.ingestion_attempt_id == 7
    print("  OK  all ownership fields preserved")
    db.close()
except Exception as e:
    print(f"  FAIL  {e}"); failures.append("M")

# ── N: _parse_visual_sections is gone ────────────────────────────
print("\n[N] _parse_visual_sections removed (no string parsing in pipeline)")
try:
    import app.knowledge_ingestions.pdf_extraction_pipeline as _mod
    assert not hasattr(_mod, "_parse_visual_sections"), \
        "_parse_visual_sections still exists in the module"
    print("  OK  _parse_visual_sections not present")
except AssertionError as e:
    print(f"  FAIL  {e}"); failures.append("N")
except Exception as e:
    print(f"  FAIL  {e}"); failures.append("N")

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
