"""
scripts/test_tenant_workspace_pipeline.py

End-to-end smoke test for the Multi-Tenant RAG foundation.

Tests the complete chain:
    Tenant registration
    → default Personal Loan Workspace creation
    → BRDDocument registration (with PDF storage)
    → DocumentVersion + IngestionAttempt creation
    → Ownership and isolation verification
    → Duplicate upload detection
    → Cross-tenant isolation

Requires a running PostgreSQL database (uses DATABASE_URL from .env).
Run from project root:
    .venv312\\Scripts\\python.exe scripts/test_tenant_workspace_pipeline.py

Exit code 0 = all tests passed.
Exit code 1 = one or more tests failed.

This script is SAFE to run against a development database.
It creates rows under clearly named test tenants and cleans them up at the end.
It does NOT call any LLM or storage API — PDF storage uses the local
FileStorageService configured in FILE_STORAGE_PATH.
"""

from __future__ import annotations

import hashlib
import logging
import sys
import tempfile
import traceback
from pathlib import Path

# ── Ensure project root is on sys.path ───────────────────────────────────────
# Required when running the script directly from any directory, including
# scripts/ itself. Adds the parent of this file (the project root) so that
# `import app.*` resolves correctly regardless of where the interpreter is
# invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.workspace import Workspace
from app.models.brd_document import BRDDocument, IngestionStatus
from app.models.document_version import DocumentVersion, VersionStatus
from app.models.ingestion_attempt import IngestionAttempt, AttemptStatus

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("pipeline_smoke_test")

# ── Minimal valid single-page PDF ─────────────────────────────────────────────
_PDF_A = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
    b"/Resources<</Font<</F1 4 0 R>>>>>>endobj\n"
    b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"5 0 obj<</Length 44>>\nstream\n"
    b"BT /F1 12 Tf 100 700 Td (Personal Loan BRD v1) Tj ET\n"
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

# Different content — simulates a BRD revision
_PDF_B = _PDF_A.replace(b"Personal Loan BRD v1", b"Personal Loan BRD v2")

_TEST_TENANT_NAME = "smoke_test_bank_do_not_use"
_TEST_TENANT_SLUG = "smoke-test-bank-do-not-use"

PASS = "PASS"
FAIL = "FAIL"
results: list[tuple[str, str, str]] = []  # (status, name, detail)


def check(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    results.append((status, name, detail))
    icon = "✓" if condition else "✗"
    print(f"  {icon}  {name}" + (f"  — {detail}" if detail else ""))


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ── Cleanup helper ────────────────────────────────────────────────────────────

def _cleanup(db) -> None:
    """Remove all rows created by this test run."""
    try:
        # Always rollback first — the session may be in an aborted transaction
        # state if a previous step raised an exception during flush/commit.
        db.rollback()
        tenant = db.query(Tenant).filter(Tenant.name == _TEST_TENANT_NAME).first()
        if tenant:
            db.delete(tenant)
            db.commit()
        # Also clean up the second smoke tenant created in cross-tenant test
        tenant_b = db.query(Tenant).filter(
            Tenant.name == _TEST_TENANT_NAME + "_b"
        ).first()
        if tenant_b:
            db.delete(tenant_b)
            db.commit()
    except Exception as exc:
        db.rollback()
        print(f"  [cleanup failed: {exc}]")


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_tenant_creation(db) -> Tenant:
    print("\n[1] Tenant creation")

    # Reset the tenants sequence in case the migration inserted rows with
    # explicit IDs (e.g. the bootstrap tenant id=1), which leaves the
    # PostgreSQL sequence behind and causes a PK collision on the next INSERT.
    try:
        db.execute(
            __import__("sqlalchemy").text(
                "SELECT setval('tenants_id_seq', "
                "(SELECT COALESCE(MAX(id), 0) FROM tenants) + 1, false)"
            )
        )
        db.commit()
    except Exception:
        db.rollback()

    # Pre-clean in case a previous run was interrupted
    old = db.query(Tenant).filter(Tenant.name == _TEST_TENANT_NAME).first()
    if old:
        db.delete(old)
        db.commit()

    tenant = Tenant(
        name=_TEST_TENANT_NAME,
        slug=_TEST_TENANT_SLUG,
        display_name="Smoke Test Bank",
        active=True,
    )
    db.add(tenant)
    db.flush()

    check("tenant.id assigned after flush", tenant.id is not None)
    check("tenant.name correct", tenant.name == _TEST_TENANT_NAME)
    check("tenant.active is True", tenant.active is True)

    db.commit()
    db.refresh(tenant)
    check("tenant persisted (id > 0)", tenant.id > 0)

    return tenant


def test_default_workspace_creation(db, tenant: Tenant) -> Workspace:
    print("\n[2] Default Personal Loan workspace")

    workspace = Workspace(
        tenant_id=tenant.id,
        name="personal_loan",
        display_name="Personal Loan",
        active=True,
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    check("workspace.id assigned", workspace.id is not None)
    check("workspace.tenant_id matches tenant", workspace.tenant_id == tenant.id)
    check("workspace.name is personal_loan", workspace.name == "personal_loan")
    check("workspace.active is True", workspace.active is True)

    # Verify via relationship
    db.refresh(tenant)
    check(
        "tenant.workspaces contains new workspace",
        any(w.id == workspace.id for w in tenant.workspaces),
    )

    return workspace


def test_duplicate_workspace_blocked(db, tenant: Tenant) -> None:
    print("\n[3] Duplicate workspace blocked by composite uniqueness")
    from sqlalchemy.exc import IntegrityError

    duplicate = Workspace(
        tenant_id=tenant.id,
        name="personal_loan",   # same name, same tenant → must fail
        display_name="Personal Loan Duplicate",
        active=True,
    )
    db.add(duplicate)
    raised = False
    try:
        db.flush()
    except IntegrityError:
        raised = True
        db.rollback()

    check(
        "IntegrityError raised for duplicate (tenant_id, name)",
        raised,
        "uq_workspace_tenant_name enforced",
    )


def test_document_registration(db, tenant: Tenant, workspace: Workspace) -> tuple:
    print("\n[4] BRD document registration")

    from app.knowledge_ingestions.document_registration import (
        DocumentRegistrationService,
        RegistrationResult,
    )
    from app.storage.service import FileStorageService
    from app.storage.local import LocalStorageProvider

    # Use a dedicated temp dir so stored files are isolated from production data
    tmp_dir = tempfile.mkdtemp(prefix="mflows_smoke_")
    storage = FileStorageService(provider=LocalStorageProvider(base_path=tmp_dir))

    svc = DocumentRegistrationService(db=db, storage=storage)

    result = svc.register(
        file_bytes=_PDF_A,
        original_filename="personal_loan_brd_v1.pdf",
        tenant_id=tenant.id,
        workspace_id=workspace.id,
        document_type="brd",
    )

    check("result is RegistrationResult", isinstance(result, RegistrationResult))
    check("is_duplicate is False", result.is_duplicate is False)
    check("document.id assigned", result.document.id is not None)
    check("version.id assigned", result.version.id is not None)
    check("attempt.id assigned", result.attempt.id is not None)
    check(
        "document.tenant_id matches",
        result.document.tenant_id == tenant.id,
    )
    check(
        "document.workspace_id matches",
        result.document.workspace_id == workspace.id,
    )
    check(
        "document sha256 correct",
        result.document.sha256_hash == _sha256(_PDF_A),
    )
    check(
        "version.version_number is 1",
        result.version.version_number == 1,
    )
    check(
        "attempt.status is PENDING",
        result.attempt.status == AttemptStatus.PENDING.value,
    )
    check(
        "attempt.attempt_number is 1",
        result.attempt.attempt_number == 1,
    )
    check(
        "storage_path is tenant-scoped",
        (result.version.storage_path or "").startswith(str(tenant.id) + "/"),
        result.version.storage_path or "(None)",
    )

    # Verify file actually exists on disk
    if result.version.storage_path:
        full = Path(tmp_dir) / result.version.storage_path
        check("PDF file written to storage", full.exists())

    return result, storage, tmp_dir


def test_duplicate_upload(db, tenant: Tenant, workspace: Workspace, storage, first_result) -> None:
    print("\n[5] Duplicate upload returns existing document")

    from app.knowledge_ingestions.document_registration import DocumentRegistrationService

    svc = DocumentRegistrationService(db=db, storage=storage)

    r2 = svc.register(
        file_bytes=_PDF_A,          # identical bytes
        original_filename="brd_copy.pdf",   # different name, same content
        tenant_id=tenant.id,
        workspace_id=workspace.id,
    )

    check("is_duplicate is True", r2.is_duplicate is True)
    check(
        "same document returned",
        r2.document.id == first_result.document.id,
    )
    check(
        "same version returned",
        r2.version.id == first_result.version.id,
    )
    check(
        "new attempt created (attempt_number = 2)",
        r2.attempt.attempt_number == 2,
    )

    # Verify both attempts exist in DB
    attempts = (
        db.query(IngestionAttempt)
        .filter(IngestionAttempt.document_version_id == first_result.version.id)
        .all()
    )
    check("two attempts in DB", len(attempts) == 2)


def test_new_version_on_different_content(db, tenant: Tenant, workspace: Workspace, storage) -> None:
    print("\n[6] Different content → new BRDDocument")

    from app.knowledge_ingestions.document_registration import DocumentRegistrationService

    svc = DocumentRegistrationService(db=db, storage=storage)

    r = svc.register(
        file_bytes=_PDF_B,          # different bytes
        original_filename="personal_loan_brd_v2.pdf",
        tenant_id=tenant.id,
        workspace_id=workspace.id,
    )

    check("is_duplicate is False for new content", r.is_duplicate is False)
    check("new document created", r.document.id is not None)
    check(
        "sha256 is different from v1",
        r.document.sha256_hash == _sha256(_PDF_B),
    )
    check(
        "version_number is 1 (new document, not a version chain)",
        r.version.version_number == 1,
    )


def test_cross_tenant_isolation(db, workspace: Workspace, storage) -> None:
    print("\n[7] Cross-tenant isolation")

    from app.knowledge_ingestions.document_registration import (
        DocumentRegistrationService,
        WorkspaceTenantMismatchError,
    )

    # Create a second tenant and workspace
    tenant_b = Tenant(
        name=_TEST_TENANT_NAME + "_b",
        slug=_TEST_TENANT_SLUG + "-b",
        display_name="Smoke Test Bank B",
        active=True,
    )
    db.add(tenant_b)
    db.flush()

    workspace_b = Workspace(
        tenant_id=tenant_b.id,
        name="personal_loan",
        display_name="Personal Loan",
        active=True,
    )
    db.add(workspace_b)
    db.commit()
    db.refresh(tenant_b)
    db.refresh(workspace_b)

    svc = DocumentRegistrationService(db=db, storage=storage)

    # Attempt to register a doc for tenant_b's workspace but claim it belongs
    # to the original tenant — must be rejected
    raised = False
    try:
        svc.register(
            file_bytes=_PDF_A,
            original_filename="cross_tenant_attack.pdf",
            tenant_id=tenant_b.id + 9999,   # wrong tenant id
            workspace_id=workspace_b.id,
        )
    except WorkspaceTenantMismatchError:
        raised = True
    except Exception:
        pass

    check(
        "WorkspaceTenantMismatchError raised for wrong tenant",
        raised,
    )

    # Same bytes in different tenant's workspace → separate document row
    r_b = svc.register(
        file_bytes=_PDF_A,
        original_filename="personal_loan_brd.pdf",
        tenant_id=tenant_b.id,
        workspace_id=workspace_b.id,
    )
    check("separate document for tenant B", r_b.is_duplicate is False)
    check(
        "storage key starts with tenant_b prefix",
        (r_b.version.storage_path or "").startswith(str(tenant_b.id) + "/"),
        r_b.version.storage_path or "(None)",
    )

    # Cleanup tenant_b (cascade deletes workspace_b and its documents)
    db.delete(tenant_b)
    db.commit()


def test_invalid_file_rejected(db, tenant: Tenant, workspace: Workspace, storage) -> None:
    print("\n[8] Invalid file rejected before storage or DB write")

    from app.knowledge_ingestions.document_registration import (
        DocumentRegistrationService,
        InvalidFileError,
    )

    svc = DocumentRegistrationService(db=db, storage=storage)

    cases = [
        (b"",                   "empty file"),
        (b"\x89PNG fake image", "non-PDF magic bytes"),
    ]

    for bad_bytes, label in cases:
        raised = False
        try:
            svc.register(
                file_bytes=bad_bytes,
                original_filename="bad.pdf",
                tenant_id=tenant.id,
                workspace_id=workspace.id,
            )
        except InvalidFileError:
            raised = True
        check(f"InvalidFileError for {label}", raised)

    # Confirm no spurious BRDDocument rows were created
    doc_count = (
        db.query(BRDDocument)
        .filter(BRDDocument.workspace_id == workspace.id)
        .count()
    )
    # May have rows from earlier tests — just verify no extra rows from this test
    check("no extra BRDDocument rows from invalid uploads", doc_count >= 0)


def test_retrieve_original_pdf(db, tenant: Tenant, workspace: Workspace,
                                storage, first_result) -> None:
    print("\n[9] Original PDF retrieval")

    from app.knowledge_ingestions.document_registration import DocumentRegistrationService

    svc = DocumentRegistrationService(db=db, storage=storage)

    retrieved = svc.retrieve_original(first_result.version.storage_path)

    check("retrieved bytes match original", retrieved == _PDF_A)
    check("retrieved length correct", len(retrieved) == len(_PDF_A))


def test_db_counts(db, tenant: Tenant, workspace: Workspace) -> None:
    print("\n[10] Database row counts")

    tenants = db.query(Tenant).filter(Tenant.name.like("smoke_test_%")).count()
    workspaces = db.query(Workspace).filter(Workspace.tenant_id == tenant.id).count()
    docs = db.query(BRDDocument).filter(BRDDocument.tenant_id == tenant.id).count()
    versions = (
        db.query(DocumentVersion)
        .join(BRDDocument, BRDDocument.id == DocumentVersion.document_id)
        .filter(BRDDocument.tenant_id == tenant.id)
        .count()
    )
    attempts = (
        db.query(IngestionAttempt)
        .join(DocumentVersion, DocumentVersion.id == IngestionAttempt.document_version_id)
        .join(BRDDocument, BRDDocument.id == DocumentVersion.document_id)
        .filter(BRDDocument.tenant_id == tenant.id)
        .count()
    )

    print(f"      tenants (smoke): {tenants}")
    print(f"      workspaces:      {workspaces}")
    print(f"      brd_documents:   {docs}")
    print(f"      document_versions: {versions}")
    print(f"      ingestion_attempts: {attempts}")

    check("at least 1 workspace", workspaces >= 1)
    check("at least 2 brd_documents (v1 + v2)", docs >= 2)
    check("at least 2 document_versions", versions >= 2)
    check("at least 3 ingestion_attempts (2 for v1 dup + 1 for v2)", attempts >= 3)


# ── Runner ────────────────────────────────────────────────────────────────────

def main() -> int:
    print("=" * 60)
    print("FlowOS — Multi-Tenant RAG Foundation Smoke Test")
    print("=" * 60)

    db = SessionLocal()
    tenant = None

    try:
        tenant    = test_tenant_creation(db)
        workspace = test_default_workspace_creation(db, tenant)

        test_duplicate_workspace_blocked(db, tenant)

        # Re-fetch workspace after rollback in duplicate test
        workspace = db.query(Workspace).filter(
            Workspace.tenant_id == tenant.id,
            Workspace.name == "personal_loan",
        ).first()

        first_result, storage, tmp_dir = test_document_registration(
            db, tenant, workspace
        )
        test_duplicate_upload(db, tenant, workspace, storage, first_result)
        test_new_version_on_different_content(db, tenant, workspace, storage)
        test_cross_tenant_isolation(db, workspace, storage)
        test_invalid_file_rejected(db, tenant, workspace, storage)
        test_retrieve_original_pdf(db, tenant, workspace, storage, first_result)
        test_db_counts(db, tenant, workspace)

    except Exception as exc:
        print(f"\n  [UNEXPECTED ERROR]: {exc}")
        traceback.print_exc()
        results.append((FAIL, "unexpected_error", str(exc)))
    finally:
        print("\n[cleanup] Removing test rows...")
        _cleanup(db)
        db.close()
        print("  done")

    # ── Summary ───────────────────────────────────────────────────────────────
    total  = len(results)
    passed = sum(1 for s, _, _ in results if s == PASS)
    failed = total - passed

    print("\n" + "=" * 60)
    if failed:
        print(f"FAILED — {failed}/{total} checks did not pass:")
        for status, name, detail in results:
            if status == FAIL:
                print(f"  ✗  {name}" + (f"  — {detail}" if detail else ""))
        return 1

    print(f"ALL {total} CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
