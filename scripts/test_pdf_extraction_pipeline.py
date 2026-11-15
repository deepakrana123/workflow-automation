"""
scripts/test_pdf_extraction_pipeline.py

Unit tests for PdfExtractionPipeline.
Mocks MultiModalDocumentExtractor and FileStorageService — no real PDF extraction.

Run:
    .venv312\\Scripts\\python.exe scripts/test_pdf_extraction_pipeline.py
"""
from __future__ import annotations
import sys, tempfile, traceback
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv; load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.base import Base
import app.models

failures: list[str] = []

_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
    b"/Resources<</Font<</F1 4 0 R>>>>>>endobj\n"
    b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"5 0 obj<</Length 44>>\nstream\nBT /F1 12 Tf 72 700 Td (BRD) Tj ET\n"
    b"endstream\nendobj\nxref\n0 6\n"
    b"0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
    b"0000000115 00000 n \n0000000266 00000 n \n0000000347 00000 n \n"
    b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n447\n%%EOF\n"
)


def _session():
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy import JSON
    for t in Base.metadata.tables.values():
        for c in t.columns:
            if isinstance(c.type, JSONB): c.type = JSON()
    e = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(e)
    return sessionmaker(bind=e)()


def _seed(db, t=1, w=1, doc_id=1, ver_id=1, storage_path="1/1/abc/f_brd.pdf"):
    from app.models.tenant import Tenant
    from app.models.workspace import Workspace
    from app.models.brd_document import BRDDocument, IngestionStatus
    from app.models.document_version import DocumentVersion, VersionStatus
    db.add_all([
        Tenant(id=t, name=f"b{t}", slug=f"b-{t}", display_name=f"B{t}", active=True),
        Workspace(id=w, tenant_id=t, name="pl", display_name="PL", active=True),
        BRDDocument(id=doc_id, tenant_id=t, workspace_id=w, original_filename="brd.pdf",
                    sha256_hash="a"*64, mime_type="application/pdf", document_type="brd",
                    ingestion_status=IngestionStatus.REGISTERED.value, attempt_count=0, version=1),
        DocumentVersion(id=ver_id, document_id=doc_id, version_number=1,
                        original_filename="brd.pdf", sha256_hash="a"*64,
                        mime_type="application/pdf", storage_path=storage_path,
                        status=VersionStatus.REGISTERED.value),
    ])
    db.commit()


def _storage_with(pdf_bytes, key):
    from app.storage.service import FileStorageService
    from app.storage.local import LocalStorageProvider
    s = FileStorageService(provider=LocalStorageProvider(tempfile.mkdtemp()))
    s._provider.save(key, pdf_bytes)
    return s


def _ownership(t=1, w=1, doc=1, ver=1, att=1):
    from app.knowledge_ingestions.extraction_result import ExtractionOwnership
    return ExtractionOwnership(tenant_id=t, workspace_id=w, document_id=doc,
                               document_version_id=ver, ingestion_attempt_id=att)


def _mock_extractor(text="Loan eligibility rules.", status="SUCCESS"):
    m = MagicMock()
    m.extract_structured.return_value = (text, None, {})
    return m


def chk(name, cond, detail=""):
    icon = "✓" if cond else "✗"
    print(f"  {icon}  {name}" + (f"  — {detail}" if detail else ""))
    if not cond: failures.append(name)


# ── tests ─────────────────────────────────────────────────────────────────────

def test_successful_extraction():
    print("\n[1] Successful extraction → DocumentExtractionResult")
    from app.knowledge_ingestions.pdf_extraction_pipeline import PdfExtractionPipeline
    key = "1/1/abc/f_brd.pdf"
    db = _session(); _seed(db, storage_path=key)
    db_ver = db.query(__import__("app.models.document_version", fromlist=["DocumentVersion"]).DocumentVersion).first()
    s = _storage_with(_PDF, key)
    p = PdfExtractionPipeline(db=db, storage=s, extractor=_mock_extractor("Loan rules."))
    r = p.extract(version=db_ver, ownership=_ownership())
    from app.knowledge_ingestions.extraction_result import DocumentExtractionResult
    chk("returns DocumentExtractionResult", isinstance(r, DocumentExtractionResult))
    chk("has usable content", r.has_usable_content)
    chk("extractor_version set", r.extractor_version == "1.0.0")
    chk("extracted_at UTC", r.extracted_at.tzinfo is not None)
    db.close()


def test_ownership_mismatch_wrong_tenant():
    print("\n[2] Wrong tenant → FAILED result")
    from app.knowledge_ingestions.pdf_extraction_pipeline import PdfExtractionPipeline
    key = "1/1/abc/f_brd.pdf"
    db = _session(); _seed(db, storage_path=key)
    db_ver = db.query(__import__("app.models.document_version", fromlist=["DocumentVersion"]).DocumentVersion).first()
    s = _storage_with(_PDF, key)
    p = PdfExtractionPipeline(db=db, storage=s, extractor=_mock_extractor())
    r = p.extract(version=db_ver, ownership=_ownership(t=99))
    chk("FAILED status", r.overall_status == "FAILED")
    chk("error_message set", "Ownership validation failed" in (r.error_message or ""))
    db.close()


def test_ownership_mismatch_wrong_workspace():
    print("\n[3] Wrong workspace → FAILED result")
    from app.knowledge_ingestions.pdf_extraction_pipeline import PdfExtractionPipeline
    key = "1/1/abc/f_brd.pdf"
    db = _session(); _seed(db, storage_path=key)
    db_ver = db.query(__import__("app.models.document_version", fromlist=["DocumentVersion"]).DocumentVersion).first()
    p = PdfExtractionPipeline(db=db, storage=_storage_with(_PDF, key), extractor=_mock_extractor())
    r = p.extract(version=db_ver, ownership=_ownership(w=99))
    chk("FAILED status", r.overall_status == "FAILED")
    db.close()


def test_storage_path_missing():
    print("\n[4] storage_path is None → FAILED result")
    from app.knowledge_ingestions.pdf_extraction_pipeline import PdfExtractionPipeline
    from app.models.document_version import DocumentVersion, VersionStatus
    db = _session(); _seed(db, storage_path="1/1/abc/f.pdf")
    db_ver = db.query(DocumentVersion).first()
    db_ver.storage_path = None
    p = PdfExtractionPipeline(db=db, storage=_storage_with(_PDF, "x"), extractor=_mock_extractor())
    r = p.extract(version=db_ver, ownership=_ownership())
    chk("FAILED status", r.overall_status == "FAILED")
    chk("error mentions storage_path", "storage_path" in (r.error_message or "").lower())
    db.close()


def test_file_not_in_storage():
    print("\n[5] File not in storage → FAILED result, no raise")
    from app.knowledge_ingestions.pdf_extraction_pipeline import PdfExtractionPipeline
    from app.models.document_version import DocumentVersion
    db = _session(); _seed(db, storage_path="1/1/abc/missing.pdf")
    db_ver = db.query(DocumentVersion).first()
    s = _storage_with(_PDF, "1/1/abc/different.pdf")  # different key
    p = PdfExtractionPipeline(db=db, storage=s, extractor=_mock_extractor())
    r = p.extract(version=db_ver, ownership=_ownership())
    chk("FAILED result returned (not raised)", r.overall_status == "FAILED")
    db.close()


def test_extraction_error_returns_result():
    print("\n[6] Extractor raises → FAILED result, no raise to caller")
    from app.knowledge_ingestions.pdf_extraction_pipeline import PdfExtractionPipeline
    from app.knowledge_ingestions.exceptions import DocumentExtractionError
    from app.models.document_version import DocumentVersion
    key = "1/1/abc/f.pdf"
    db = _session(); _seed(db, storage_path=key)
    db_ver = db.query(DocumentVersion).first()
    mock_ext = MagicMock()
    mock_ext.extract_structured.side_effect = DocumentExtractionError("corrupt PDF")
    p = PdfExtractionPipeline(db=db, storage=_storage_with(_PDF, key), extractor=mock_ext)
    r = p.extract(version=db_ver, ownership=_ownership())
    chk("FAILED result", r.overall_status == "FAILED")
    chk("error_message set", r.error_message is not None)
    db.close()


def test_temp_file_always_cleaned_up():
    print("\n[7] Temp file cleaned up after extraction")
    import glob
    from app.knowledge_ingestions.pdf_extraction_pipeline import PdfExtractionPipeline
    from app.models.document_version import DocumentVersion
    key = "1/1/abc/f.pdf"
    db = _session(); _seed(db, storage_path=key)
    db_ver = db.query(DocumentVersion).first()
    before = set(glob.glob(tempfile.gettempdir() + "/mflows_extract_*.pdf"))
    p = PdfExtractionPipeline(db=db, storage=_storage_with(_PDF, key), extractor=_mock_extractor("text"))
    p.extract(version=db_ver, ownership=_ownership())
    after = set(glob.glob(tempfile.gettempdir() + "/mflows_extract_*.pdf"))
    chk("no leftover temp files", not (after - before))
    db.close()


def test_temp_file_cleaned_up_on_extractor_crash():
    print("\n[8] Temp file cleaned up when extractor raises")
    import glob
    from app.knowledge_ingestions.pdf_extraction_pipeline import PdfExtractionPipeline
    from app.models.document_version import DocumentVersion
    key = "1/1/abc/f.pdf"
    db = _session(); _seed(db, storage_path=key)
    db_ver = db.query(DocumentVersion).first()
    mock_ext = MagicMock(); mock_ext.extract_structured.side_effect = RuntimeError("boom")
    before = set(glob.glob(tempfile.gettempdir() + "/mflows_extract_*.pdf"))
    p = PdfExtractionPipeline(db=db, storage=_storage_with(_PDF, key), extractor=mock_ext)
    p.extract(version=db_ver, ownership=_ownership())
    after = set(glob.glob(tempfile.gettempdir() + "/mflows_extract_*.pdf"))
    chk("no leftover temp files after crash", not (after - before))
    db.close()


def test_ownership_carried_through():
    print("\n[9] Ownership context carried through to result")
    from app.knowledge_ingestions.pdf_extraction_pipeline import PdfExtractionPipeline
    from app.models.document_version import DocumentVersion
    from app.models.tenant import Tenant
    from app.models.workspace import Workspace
    key = "2/3/abc/f.pdf"
    db = _session(); _seed(db, t=2, w=3, doc_id=4, ver_id=5, storage_path=key)
    db_ver = db.query(DocumentVersion).first()
    p = PdfExtractionPipeline(db=db, storage=_storage_with(_PDF, key), extractor=_mock_extractor("text"))
    o = _ownership(t=2, w=3, doc=4, ver=5, att=7)
    r = p.extract(version=db_ver, ownership=o)
    chk("tenant_id preserved",           r.ownership.tenant_id == 2)
    chk("workspace_id preserved",        r.ownership.workspace_id == 3)
    chk("document_id preserved",         r.ownership.document_id == 4)
    chk("document_version_id preserved", r.ownership.document_version_id == 5)
    chk("ingestion_attempt_id preserved",r.ownership.ingestion_attempt_id == 7)
    db.close()


def test_every_page_has_a_record():
    print("\n[10] Every page has a result record — no silent drops")
    from app.knowledge_ingestions.pdf_extraction_pipeline import PdfExtractionPipeline
    from app.knowledge_ingestions.page_classifier import PageClassifier, DocumentClassification, PageClassification
    from app.models.document_version import DocumentVersion
    key = "1/1/abc/f.pdf"
    db = _session(); _seed(db, storage_path=key)
    db_ver = db.query(DocumentVersion).first()
    mock_cls = MagicMock()
    doc_cls = DocumentClassification(total_pages=3)
    doc_cls.text_pages = [
        PageClassification(page_number=0, page_type="text", text="page one content", has_images=False),
        PageClassification(page_number=1, page_type="text", text="page two content", has_images=False),
        PageClassification(page_number=2, page_type="text", text="", has_images=False),  # empty
    ]
    mock_cls.classify.return_value = doc_cls
    mock_ext = MagicMock()
    mock_ext.extract_structured.return_value = ("page one content\npage two content", doc_cls, {})
    p = PdfExtractionPipeline(db=db, storage=_storage_with(_PDF, key), extractor=mock_ext, classifier=mock_cls)
    r = p.extract(version=db_ver, ownership=_ownership())
    chk("3 page records", len(r.pages) == 3)
    chk("total_pages = 3", r.total_pages == 3)
    page_numbers = {p.page_number for p in r.pages}
    chk("page numbers are 1,2,3", page_numbers == {1, 2, 3})
    db.close()


def main():
    print("=" * 60)
    print("PdfExtractionPipeline — Unit Tests")
    print("=" * 60)
    for t in [
        test_successful_extraction, test_ownership_mismatch_wrong_tenant,
        test_ownership_mismatch_wrong_workspace, test_storage_path_missing,
        test_file_not_in_storage, test_extraction_error_returns_result,
        test_temp_file_always_cleaned_up, test_temp_file_cleaned_up_on_extractor_crash,
        test_ownership_carried_through, test_every_page_has_a_record,
    ]:
        try: t()
        except Exception as e:
            print(f"  [UNEXPECTED] {e}"); traceback.print_exc(); failures.append(t.__name__)
    print("\n" + "=" * 60)
    if failures:
        print(f"FAILED — {len(failures)}: " + ", ".join(failures))
        return 1
    print("ALL TESTS PASSED")
    return 0

if __name__ == "__main__":
    sys.exit(main())
