"""
Verification and tests for DocumentRegistrationService (Step 3).

Uses an in-memory SQLite DB so no Postgres connection is needed.
Run from project root:
    .venv312\Scripts\python.exe verify_step4_registration.py

What is tested:
  A  import and instantiation
  B  _validate_file: empty file rejected
  C  _validate_file: non-PDF rejected (bad magic bytes)
  D  _validate_file: valid PDF accepted
  E  _sha256: hash correctness
  F  _build_storage_key: tenant prefix, structure, sanitisation
  G  _sanitise_filename: special characters replaced
  H  workspace tenant mismatch raises WorkspaceTenantMismatchError
  I  inactive workspace raises WorkspaceNotFoundError
  J  successful registration: BRDDocument + DocumentVersion + IngestionAttempt created
  K  correct storage key written to DocumentVersion.storage_path
  L  content hash written to DocumentVersion.sha256_hash
  M  duplicate upload: returns is_duplicate=True, creates new attempt
  N  storage failure: DB rows not committed, RegistrationError raised
  O  DB failure after storage: stored file cleaned up
  P  retrieve_original: returns original bytes
  Q  cross-tenant isolation: same bytes in different tenant's workspace
     produce separate DocumentVersion rows
"""

import hashlib
import io
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# ── minimal in-memory SQLite setup ───────────────────────────────────────────
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models  # register all models with Base.metadata

failures = []
_PDF = b"%PDF-1.4 fake pdf content for testing"


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _make_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _seed_tenant_workspace(db, tenant_id=1, workspace_id=1):
    """Insert a minimal Tenant and Workspace row."""
    from app.models.tenant import Tenant
    from app.models.workspace import Workspace

    t = Tenant(
        id=tenant_id,
        name=f"test_bank_{tenant_id}",
        slug=f"test-bank-{tenant_id}",
        display_name=f"Test Bank {tenant_id}",
        active=True,
    )
    w = Workspace(
        id=workspace_id,
        tenant_id=tenant_id,
        name="personal_loan",
        display_name="Personal Loan",
        active=True,
    )
    db.add(t)
    db.add(w)
    db.commit()


def _make_storage():
    """Return a FileStorageService backed by a temp directory."""
    from app.storage.service import FileStorageService
    from app.storage.local import LocalStorageProvider

    tmp = tempfile.mkdtemp()
    return FileStorageService(provider=LocalStorageProvider(base_path=tmp)), tmp


print("=" * 65)
print("FlowOS Step 3 — DocumentRegistrationService verification")
print("=" * 65)

# ── A: import ─────────────────────────────────────────────────────
print("\n[A] Import")
try:
    from app.knowledge_ingestions.document_registration import (
        DocumentRegistrationService,
        RegistrationResult,
        RegistrationError,
        InvalidFileError,
        WorkspaceNotFoundError,
        WorkspaceTenantMismatchError,
        _sha256 as _svc_sha256,
        _build_storage_key,
        _sanitise_filename,
    )
    print("  OK  all symbols imported")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("import")

# ── B: empty file rejected ────────────────────────────────────────
print("\n[B] Empty file rejected")
try:
    db  = _make_session()
    svc, _ = _make_storage()
    s = DocumentRegistrationService(db=db, storage=svc)
    try:
        s._validate_file(b"", "empty.pdf")
        print("  FAIL  expected InvalidFileError")
        failures.append("B: empty file")
    except InvalidFileError:
        print("  OK  InvalidFileError raised for empty file")
    db.close()
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("B")

# ── C: non-PDF rejected ───────────────────────────────────────────
print("\n[C] Non-PDF rejected (bad magic bytes)")
try:
    db = _make_session()
    svc, _ = _make_storage()
    s = DocumentRegistrationService(db=db, storage=svc)
    try:
        s._validate_file(b"\x89PNG fake image", "image.png")
        print("  FAIL  expected InvalidFileError")
        failures.append("C: non-PDF")
    except InvalidFileError as e:
        print(f"  OK  InvalidFileError: {e}")
    db.close()
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("C")

# ── D: valid PDF accepted ─────────────────────────────────────────
print("\n[D] Valid PDF accepted by validator")
try:
    db = _make_session()
    svc, _ = _make_storage()
    s = DocumentRegistrationService(db=db, storage=svc)
    s._validate_file(_PDF, "test.pdf")  # must not raise
    print("  OK  valid PDF passes validation")
    db.close()
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("D")

# ── E: SHA-256 correctness ────────────────────────────────────────
print("\n[E] SHA-256 hash correctness")
try:
    data = b"hello world"
    expected = hashlib.sha256(data).hexdigest()
    result   = _svc_sha256(data)
    assert result == expected, f"hash mismatch: {result} != {expected}"
    assert len(result) == 64
    print(f"  OK  sha256(b'hello world') = {result[:16]}...")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("E")

# ── F: storage key structure ──────────────────────────────────────
print("\n[F] Storage key structure")
try:
    key = _build_storage_key(
        tenant_id=1,
        workspace_id=2,
        sha256_hash="abcdef1234567890",
        file_id="deadbeef",
        original_filename="my brd file.pdf",
    )
    print(f"  key: {key}")
    assert key.startswith("1/2/abcdef12/"), f"wrong prefix: {key}"
    assert "deadbeef_" in key
    assert "my_brd_file.pdf" in key, f"filename not sanitised properly: {key}"
    print("  OK  tenant/workspace prefix, hash prefix, file_id, sanitised filename")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("F")

# ── G: filename sanitisation ──────────────────────────────────────
print("\n[G] Filename sanitisation")
try:
    cases = [
        ("normal.pdf",          "normal.pdf"),
        ("my file (v2).pdf",    "my_file__v2_.pdf"),
        ("../../etc/passwd",    ".._.._etc_passwd"),
        ("a" * 300 + ".pdf",    "a" * 200),  # capped at 200
    ]
    for raw, expected_start in cases:
        result = _sanitise_filename(raw)
        assert len(result) <= 200
        # Only check first 10 chars of the expectation to stay robust
        assert result.startswith(expected_start[:10]), \
            f"sanitise({raw!r}) = {result!r}, expected start {expected_start[:10]!r}"
    print("  OK  special chars replaced, length capped")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("G")

# ── H: workspace tenant mismatch ─────────────────────────────────
print("\n[H] WorkspaceTenantMismatchError")
try:
    db = _make_session()
    _seed_tenant_workspace(db, tenant_id=1, workspace_id=1)
    svc, _ = _make_storage()
    s = DocumentRegistrationService(db=db, storage=svc)
    try:
        s.register(
            file_bytes=_PDF,
            original_filename="test.pdf",
            tenant_id=99,          # wrong tenant
            workspace_id=1,
        )
        print("  FAIL  expected WorkspaceTenantMismatchError")
        failures.append("H: no error raised")
    except WorkspaceTenantMismatchError as e:
        print(f"  OK  WorkspaceTenantMismatchError: {e}")
    db.close()
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("H")

# ── I: inactive workspace ─────────────────────────────────────────
print("\n[I] WorkspaceNotFoundError for inactive workspace")
try:
    from app.models.workspace import Workspace
    db = _make_session()
    _seed_tenant_workspace(db, tenant_id=1, workspace_id=10)
    db.query(Workspace).filter(Workspace.id == 10).update({"active": False})
    db.commit()

    svc, _ = _make_storage()
    s = DocumentRegistrationService(db=db, storage=svc)
    try:
        s.register(
            file_bytes=_PDF,
            original_filename="test.pdf",
            tenant_id=1,
            workspace_id=10,
        )
        print("  FAIL  expected WorkspaceNotFoundError")
        failures.append("I: no error raised")
    except WorkspaceNotFoundError as e:
        print(f"  OK  WorkspaceNotFoundError: {e}")
    db.close()
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("I")

# ── J: successful registration ────────────────────────────────────
print("\n[J] Successful registration creates all three rows")
try:
    from app.models.brd_document import BRDDocument
    from app.models.document_version import DocumentVersion
    from app.models.ingestion_attempt import IngestionAttempt, AttemptStatus
    from app.models.brd_document import IngestionStatus

    db = _make_session()
    _seed_tenant_workspace(db, tenant_id=1, workspace_id=1)
    svc, tmp_dir = _make_storage()
    s = DocumentRegistrationService(db=db, storage=svc)

    result = s.register(
        file_bytes=_PDF,
        original_filename="personal_loan_brd.pdf",
        tenant_id=1,
        workspace_id=1,
    )

    assert isinstance(result, RegistrationResult)
    assert not result.is_duplicate
    assert result.document.id is not None
    assert result.version.id  is not None
    assert result.attempt.id  is not None

    assert result.document.tenant_id    == 1
    assert result.document.workspace_id == 1
    assert result.document.ingestion_status == IngestionStatus.REGISTERED.value

    assert result.version.version_number == 1
    assert result.version.document_id   == result.document.id

    assert result.attempt.attempt_number == 1
    assert result.attempt.status == AttemptStatus.PENDING.value
    assert result.attempt.document_version_id == result.version.id

    # Verify rows in DB
    doc_count = db.query(BRDDocument).count()
    ver_count = db.query(DocumentVersion).count()
    att_count = db.query(IngestionAttempt).count()
    assert doc_count == 1 and ver_count == 1 and att_count == 1

    print("  OK  BRDDocument + DocumentVersion + IngestionAttempt created")
    print(f"      doc.id={result.document.id}  ver.id={result.version.id}  "
          f"attempt.id={result.attempt.id}")
    db.close()
except Exception as e:
    import traceback; traceback.print_exc()
    print(f"  FAIL  {e}")
    failures.append("J")

# ── K: storage key written to DocumentVersion ─────────────────────
print("\n[K] Storage key written to DocumentVersion.storage_path")
try:
    db = _make_session()
    _seed_tenant_workspace(db, tenant_id=2, workspace_id=2)
    svc, tmp_dir = _make_storage()
    s = DocumentRegistrationService(db=db, storage=svc)

    result = s.register(
        file_bytes=_PDF,
        original_filename="brd.pdf",
        tenant_id=2,
        workspace_id=2,
    )

    path = result.version.storage_path
    assert path is not None
    assert path.startswith("2/2/")  # tenant/workspace prefix
    assert result.version.storage_file_id is not None

    # File must exist on disk
    full_path = Path(tmp_dir) / path
    assert full_path.exists(), f"file not on disk at {full_path}"
    print(f"  OK  storage_path={path}")
    print(f"  OK  file exists on disk")
    db.close()
except Exception as e:
    import traceback; traceback.print_exc()
    print(f"  FAIL  {e}")
    failures.append("K")

# ── L: content hash correctness ───────────────────────────────────
print("\n[L] Content hash written correctly")
try:
    db = _make_session()
    _seed_tenant_workspace(db, tenant_id=3, workspace_id=3)
    svc, _ = _make_storage()
    s = DocumentRegistrationService(db=db, storage=svc)

    result = s.register(
        file_bytes=_PDF,
        original_filename="hash_test.pdf",
        tenant_id=3,
        workspace_id=3,
    )

    expected = _sha256(_PDF)
    assert result.version.sha256_hash == expected
    assert result.document.sha256_hash == expected
    print(f"  OK  sha256_hash={expected[:16]}...")
    db.close()
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("L")

# ── M: duplicate upload ───────────────────────────────────────────
print("\n[M] Duplicate upload: is_duplicate=True, new attempt created")
try:
    from app.models.ingestion_attempt import IngestionAttempt

    db = _make_session()
    _seed_tenant_workspace(db, tenant_id=4, workspace_id=4)
    svc, _ = _make_storage()
    s = DocumentRegistrationService(db=db, storage=svc)

    r1 = s.register(
        file_bytes=_PDF,
        original_filename="brd.pdf",
        tenant_id=4,
        workspace_id=4,
    )
    assert not r1.is_duplicate

    r2 = s.register(
        file_bytes=_PDF,       # same bytes
        original_filename="brd_copy.pdf",  # different name, same content
        tenant_id=4,
        workspace_id=4,
    )

    assert r2.is_duplicate
    assert r2.document.id == r1.document.id  # same logical document
    assert r2.version.id  == r1.version.id   # same version
    assert r2.attempt.attempt_number == 2     # new attempt

    total_attempts = db.query(IngestionAttempt).filter(
        IngestionAttempt.document_version_id == r1.version.id
    ).count()
    assert total_attempts == 2

    print("  OK  is_duplicate=True")
    print("  OK  same document_id and version_id returned")
    print("  OK  second attempt created (attempt_number=2)")
    db.close()
except Exception as e:
    import traceback; traceback.print_exc()
    print(f"  FAIL  {e}")
    failures.append("M")

# ── N: storage failure → no DB rows committed ─────────────────────
print("\n[N] Storage failure → RegistrationError, no DB rows committed")
try:
    from app.models.brd_document import BRDDocument
    from app.storage.exceptions import StorageWriteError

    db = _make_session()
    _seed_tenant_workspace(db, tenant_id=5, workspace_id=5)
    svc, _ = _make_storage()

    # Patch the provider's save to simulate a storage failure
    svc._provider.save = MagicMock(side_effect=StorageWriteError("disk full"))
    s = DocumentRegistrationService(db=db, storage=svc)

    try:
        s.register(
            file_bytes=_PDF,
            original_filename="fail.pdf",
            tenant_id=5,
            workspace_id=5,
        )
        print("  FAIL  expected RegistrationError")
        failures.append("N: no error raised")
    except RegistrationError as e:
        doc_count = db.query(BRDDocument).count()
        assert doc_count == 0, f"DB rows written despite storage failure: {doc_count}"
        print(f"  OK  RegistrationError raised: {e}")
        print(f"  OK  no BRDDocument rows in DB ({doc_count})")
    db.close()
except Exception as e:
    import traceback; traceback.print_exc()
    print(f"  FAIL  {e}")
    failures.append("N")

# ── O: DB failure after storage → file cleaned up ─────────────────
print("\n[O] DB failure after storage → stored file deleted")
try:
    from app.models.brd_document import BRDDocument

    db = _make_session()
    _seed_tenant_workspace(db, tenant_id=6, workspace_id=6)
    svc, tmp_dir = _make_storage()
    s = DocumentRegistrationService(db=db, storage=svc)

    deleted_keys = []
    original_delete = svc._provider.delete
    def tracking_delete(key):
        deleted_keys.append(key)
        original_delete(key)
    svc._provider.delete = tracking_delete

    # Patch _persist to simulate a DB failure after the file is stored
    original_persist = s._persist
    def failing_persist(**kwargs):
        # Let the file be stored (already happened before _persist is called),
        # then raise to simulate DB failure.
        raise Exception("simulated DB error")
    s._persist = failing_persist

    try:
        s.register(
            file_bytes=_PDF,
            original_filename="dbfail.pdf",
            tenant_id=6,
            workspace_id=6,
        )
        print("  FAIL  expected RegistrationError")
        failures.append("O: no error raised")
    except RegistrationError as e:
        assert len(deleted_keys) == 1, \
            f"cleanup not called (deleted_keys={deleted_keys})"
        print(f"  OK  RegistrationError raised: {e}")
        print(f"  OK  cleanup called for key: {deleted_keys[0][:30]}...")
    db.close()
except Exception as e:
    import traceback; traceback.print_exc()
    print(f"  FAIL  {e}")
    failures.append("O")

# ── P: retrieve_original ──────────────────────────────────────────
print("\n[P] retrieve_original returns original bytes")
try:
    db = _make_session()
    _seed_tenant_workspace(db, tenant_id=7, workspace_id=7)
    svc, _ = _make_storage()
    s = DocumentRegistrationService(db=db, storage=svc)

    result = s.register(
        file_bytes=_PDF,
        original_filename="retrieve_test.pdf",
        tenant_id=7,
        workspace_id=7,
    )

    retrieved = s.retrieve_original(result.version.storage_path)
    assert retrieved == _PDF, "retrieved bytes do not match original"
    print("  OK  retrieve_original returns exact original bytes")
    db.close()
except Exception as e:
    import traceback; traceback.print_exc()
    print(f"  FAIL  {e}")
    failures.append("P")

# ── Q: cross-tenant isolation ─────────────────────────────────────
print("\n[Q] Cross-tenant isolation: same bytes, different tenants → separate rows")
try:
    from app.models.brd_document import BRDDocument
    from app.models.document_version import DocumentVersion
    from app.models.tenant import Tenant
    from app.models.workspace import Workspace

    db = _make_session()
    # Tenant 10 / Workspace 10
    _seed_tenant_workspace(db, tenant_id=10, workspace_id=10)
    # Tenant 11 / Workspace 11
    _seed_tenant_workspace(db, tenant_id=11, workspace_id=11)

    svc, tmp_dir = _make_storage()
    s = DocumentRegistrationService(db=db, storage=svc)

    r_a = s.register(
        file_bytes=_PDF,
        original_filename="shared_policy.pdf",
        tenant_id=10,
        workspace_id=10,
    )
    r_b = s.register(
        file_bytes=_PDF,
        original_filename="shared_policy.pdf",
        tenant_id=11,
        workspace_id=11,
    )

    assert r_a.document.id != r_b.document.id,  "same BRDDocument for different tenants"
    assert r_a.version.id  != r_b.version.id,   "same DocumentVersion for different tenants"

    # Storage keys must be in different directories
    assert r_a.version.storage_path.startswith("10/"), \
        f"tenant 10 key wrong: {r_a.version.storage_path}"
    assert r_b.version.storage_path.startswith("11/"), \
        f"tenant 11 key wrong: {r_b.version.storage_path}"

    # Neither result should be a duplicate
    assert not r_a.is_duplicate
    assert not r_b.is_duplicate

    print(f"  OK  tenant 10 key: {r_a.version.storage_path[:30]}...")
    print(f"  OK  tenant 11 key: {r_b.version.storage_path[:30]}...")
    print("  OK  separate BRDDocument + DocumentVersion rows per tenant")
    db.close()
except Exception as e:
    import traceback; traceback.print_exc()
    print(f"  FAIL  {e}")
    failures.append("Q")

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
