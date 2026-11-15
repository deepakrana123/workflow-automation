"""
scripts/test_document_registration.py

Unit tests for DocumentRegistrationService.
Uses in-memory SQLite + temp directories — no Postgres, no LLM, no network.

Run:
    .venv312\\Scripts\\python.exe scripts/test_document_registration.py
"""
from __future__ import annotations
import hashlib, sys, tempfile, traceback
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
_PDF_B = _PDF.replace(b"BRD", b"BRD v2")


def _session():
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy import JSON
    for t in Base.metadata.tables.values():
        for c in t.columns:
            if isinstance(c.type, JSONB):
                c.type = JSON()
    e = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(e)
    return sessionmaker(bind=e)()


def _storage():
    from app.storage.service import FileStorageService
    from app.storage.local import LocalStorageProvider
    return FileStorageService(provider=LocalStorageProvider(tempfile.mkdtemp()))


def _seed(db, t=1, w=1):
    from app.models.tenant import Tenant
    from app.models.workspace import Workspace
    db.add_all([
        Tenant(id=t, name=f"b{t}", slug=f"b-{t}", display_name=f"B{t}", active=True),
        Workspace(id=w, tenant_id=t, name="pl", display_name="PL", active=True),
    ])
    db.commit()


def chk(name, cond, detail=""):
    icon = "✓" if cond else "✗"
    print(f"  {icon}  {name}" + (f"  — {detail}" if detail else ""))
    if not cond:
        failures.append(name)


# ── tests ─────────────────────────────────────────────────────────────────────

def test_happy_path():
    print("\n[1] Successful registration")
    from app.knowledge_ingestions.document_registration import DocumentRegistrationService, RegistrationResult
    from app.models.brd_document import IngestionStatus
    from app.models.document_version import VersionStatus
    from app.models.ingestion_attempt import AttemptStatus
    db = _session(); _seed(db); svc = DocumentRegistrationService(db, _storage())
    r = svc.register(file_bytes=_PDF, original_filename="brd.pdf", tenant_id=1, workspace_id=1)
    chk("RegistrationResult returned", isinstance(r, RegistrationResult))
    chk("not duplicate", not r.is_duplicate)
    chk("document.id > 0", r.document.id > 0)
    chk("version.id > 0", r.version.id > 0)
    chk("attempt.id > 0", r.attempt.id > 0)
    chk("attempt PENDING", r.attempt.status == AttemptStatus.PENDING.value)
    chk("document REGISTERED", r.document.ingestion_status == IngestionStatus.REGISTERED.value)
    chk("version REGISTERED", r.version.status == VersionStatus.REGISTERED.value)
    chk("sha256 correct", r.document.sha256_hash == hashlib.sha256(_PDF).hexdigest())
    chk("storage_path tenant-scoped", (r.version.storage_path or "").startswith("1/"))
    chk("file on disk", Path(svc._storage._provider._base_path / r.version.storage_path).exists())
    chk("version_number = 1", r.version.version_number == 1)
    chk("attempt_number = 1", r.attempt.attempt_number == 1)
    db.close()


def test_empty_file_rejected():
    print("\n[2] Empty file rejected")
    from app.knowledge_ingestions.document_registration import DocumentRegistrationService, InvalidFileError
    db = _session(); _seed(db); svc = DocumentRegistrationService(db, _storage())
    try:
        svc.register(file_bytes=b"", original_filename="empty.pdf", tenant_id=1, workspace_id=1)
        chk("InvalidFileError raised", False)
    except InvalidFileError:
        chk("InvalidFileError raised", True)
    db.close()


def test_non_pdf_rejected():
    print("\n[3] Non-PDF rejected")
    from app.knowledge_ingestions.document_registration import DocumentRegistrationService, InvalidFileError
    db = _session(); _seed(db); svc = DocumentRegistrationService(db, _storage())
    try:
        svc.register(file_bytes=b"\x89PNG fake", original_filename="img.png", tenant_id=1, workspace_id=1)
        chk("InvalidFileError raised", False)
    except InvalidFileError:
        chk("InvalidFileError raised", True)
    db.close()


def test_wrong_tenant():
    print("\n[4] Wrong tenant raises WorkspaceTenantMismatchError")
    from app.knowledge_ingestions.document_registration import DocumentRegistrationService, WorkspaceTenantMismatchError
    db = _session(); _seed(db); svc = DocumentRegistrationService(db, _storage())
    try:
        svc.register(file_bytes=_PDF, original_filename="brd.pdf", tenant_id=99, workspace_id=1)
        chk("error raised", False)
    except WorkspaceTenantMismatchError:
        chk("WorkspaceTenantMismatchError raised", True)
    db.close()


def test_inactive_workspace():
    print("\n[5] Inactive workspace raises WorkspaceNotFoundError")
    from app.knowledge_ingestions.document_registration import DocumentRegistrationService, WorkspaceNotFoundError
    from app.models.workspace import Workspace
    db = _session(); _seed(db)
    db.query(Workspace).filter(Workspace.id == 1).update({"active": False})
    db.commit()
    svc = DocumentRegistrationService(db, _storage())
    try:
        svc.register(file_bytes=_PDF, original_filename="brd.pdf", tenant_id=1, workspace_id=1)
        chk("error raised", False)
    except WorkspaceNotFoundError:
        chk("WorkspaceNotFoundError raised", True)
    db.close()


def test_duplicate_same_bytes():
    print("\n[6] Duplicate: same bytes → is_duplicate=True, new attempt")
    from app.knowledge_ingestions.document_registration import DocumentRegistrationService
    from app.models.ingestion_attempt import IngestionAttempt
    db = _session(); _seed(db); svc = DocumentRegistrationService(db, _storage())
    r1 = svc.register(file_bytes=_PDF, original_filename="brd.pdf", tenant_id=1, workspace_id=1)
    r2 = svc.register(file_bytes=_PDF, original_filename="brd_copy.pdf", tenant_id=1, workspace_id=1)
    chk("r2.is_duplicate=True", r2.is_duplicate)
    chk("same document_id", r1.document.id == r2.document.id)
    chk("same version_id", r1.version.id == r2.version.id)
    chk("r2.attempt_number=2", r2.attempt.attempt_number == 2)
    total = db.query(IngestionAttempt).filter(IngestionAttempt.document_version_id == r1.version.id).count()
    chk("2 attempts in DB", total == 2)
    db.close()


def test_different_bytes_new_document():
    print("\n[7] Different bytes → new BRDDocument")
    from app.knowledge_ingestions.document_registration import DocumentRegistrationService
    db = _session(); _seed(db); svc = DocumentRegistrationService(db, _storage())
    r1 = svc.register(file_bytes=_PDF,   original_filename="v1.pdf", tenant_id=1, workspace_id=1)
    r2 = svc.register(file_bytes=_PDF_B, original_filename="v2.pdf", tenant_id=1, workspace_id=1)
    chk("not duplicate", not r2.is_duplicate)
    chk("different document_id", r1.document.id != r2.document.id)
    chk("r2 sha256 differs", r1.document.sha256_hash != r2.document.sha256_hash)
    db.close()


def test_storage_failure_no_db_rows():
    print("\n[8] Storage failure → RegistrationError, no DB rows")
    from app.knowledge_ingestions.document_registration import DocumentRegistrationService, RegistrationError
    from app.storage.exceptions import StorageWriteError
    from app.models.brd_document import BRDDocument
    db = _session(); _seed(db)
    s = _storage(); s._provider.save = MagicMock(side_effect=StorageWriteError("disk full"))
    svc = DocumentRegistrationService(db, s)
    try:
        svc.register(file_bytes=_PDF, original_filename="brd.pdf", tenant_id=1, workspace_id=1)
        chk("RegistrationError raised", False)
    except RegistrationError:
        chk("RegistrationError raised", True)
    chk("no BRDDocument rows", db.query(BRDDocument).count() == 0)
    db.close()


def test_db_failure_cleans_up_file():
    print("\n[9] DB failure after storage → file cleaned up")
    from app.knowledge_ingestions.document_registration import DocumentRegistrationService, RegistrationError
    from app.models.brd_document import BRDDocument
    db = _session(); _seed(db); s = _storage()
    deleted = []
    orig = s._provider.delete
    s._provider.delete = lambda k: deleted.append(k) or orig(k)
    svc = DocumentRegistrationService(db, s)
    svc._persist = MagicMock(side_effect=Exception("DB exploded"))
    try:
        svc.register(file_bytes=_PDF, original_filename="brd.pdf", tenant_id=1, workspace_id=1)
    except RegistrationError:
        pass
    chk("cleanup called", len(deleted) == 1)
    chk("no DB rows", db.query(BRDDocument).count() == 0)
    db.close()


def test_retrieve_original():
    print("\n[10] retrieve_original returns exact bytes")
    from app.knowledge_ingestions.document_registration import DocumentRegistrationService
    db = _session(); _seed(db); svc = DocumentRegistrationService(db, _storage())
    r = svc.register(file_bytes=_PDF, original_filename="brd.pdf", tenant_id=1, workspace_id=1)
    chk("retrieved == original", svc.retrieve_original(r.version.storage_path) == _PDF)
    db.close()


def test_cross_tenant_isolation():
    print("\n[11] Cross-tenant isolation: separate files per tenant")
    from app.knowledge_ingestions.document_registration import DocumentRegistrationService
    db = _session(); _seed(db, t=1, w=1); _seed(db, t=2, w=2)
    s = _storage(); svc = DocumentRegistrationService(db, s)
    r1 = svc.register(file_bytes=_PDF, original_filename="brd.pdf", tenant_id=1, workspace_id=1)
    r2 = svc.register(file_bytes=_PDF, original_filename="brd.pdf", tenant_id=2, workspace_id=2)
    chk("different document rows", r1.document.id != r2.document.id)
    chk("r1 key starts with 1/", (r1.version.storage_path or "").startswith("1/"))
    chk("r2 key starts with 2/", (r2.version.storage_path or "").startswith("2/"))
    chk("neither is duplicate", not r1.is_duplicate and not r2.is_duplicate)
    db.close()


def main():
    print("=" * 60)
    print("DocumentRegistrationService — Unit Tests")
    print("=" * 60)
    for t in [
        test_happy_path, test_empty_file_rejected, test_non_pdf_rejected,
        test_wrong_tenant, test_inactive_workspace, test_duplicate_same_bytes,
        test_different_bytes_new_document, test_storage_failure_no_db_rows,
        test_db_failure_cleans_up_file, test_retrieve_original,
        test_cross_tenant_isolation,
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
