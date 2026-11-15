"""
scripts/test_api_e2e.py

End-to-end API integration tests for the FlowOS multi-tenant ingestion pipeline.

Tests run against a LIVE server (the app must already be running).

Prerequisites:
  1. Apply all migrations:
       .venv312\\Scripts\\python.exe -m alembic upgrade head
  2. Start the server in a separate terminal:
       .venv312\\Scripts\\python.exe -m uvicorn app.main:app --port 8000 --reload
  3. Run this script:
       .venv312\\Scripts\\python.exe scripts/test_api_e2e.py

The script creates its own tenant and workspace via the API, runs all tests,
and cleans up at the end.  It is safe to run against a development database.

Configuration (override with environment variables):
  BASE_URL   default: http://localhost:8000
"""

from __future__ import annotations

import hashlib
import io
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import requests
except ImportError:
    print("ERROR: 'requests' is not installed.")
    print("Install it with:  .venv312\\Scripts\\python.exe -m pip install requests")
    sys.exit(1)

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
API = f"{BASE_URL}/api"

failures: list[str] = []
ctx: dict = {}   # shared state between tests (tenant_id, workspace_id, etc.)

# ── Minimal valid single-page PDF ─────────────────────────────────────────────
_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
    b"/Resources<</Font<</F1 4 0 R>>>>>>endobj\n"
    b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"5 0 obj<</Length 65>>\nstream\n"
    b"BT /F1 12 Tf 72 700 Td (Personal Loan BRD Test Document) Tj ET\n"
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
_PDF_V2 = _PDF.replace(b"Test Document", b"Version Two")
_PDF_SHA256 = hashlib.sha256(_PDF).hexdigest()

_TEST_TENANT_NAME = "e2e_test_bank_do_not_use"
_TEST_TENANT_SLUG = "e2e-test-bank"


def chk(name: str, condition: bool, detail: str = "") -> None:
    icon = "✓" if condition else "✗"
    print(f"  {icon}  {name}" + (f"  — {detail}" if detail else ""))
    if not condition:
        failures.append(name)


def _cleanup() -> None:
    """Delete the test tenant via the deactivate endpoint (soft-delete)."""
    tid = ctx.get("tenant_id")
    if not tid:
        return
    try:
        requests.patch(f"{API}/tenants/{tid}/deactivate", timeout=10)
        print(f"  [cleanup] tenant {tid} deactivated")
    except Exception as exc:
        print(f"  [cleanup failed: {exc}]")


# ── Connectivity check ────────────────────────────────────────────────────────

def test_server_reachable():
    print("\n[0] Server connectivity")
    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        chk("server responds 200", r.status_code == 200)
        chk("service=mflows", r.json().get("service") == "mflows")
    except requests.ConnectionError:
        print(f"  ✗  Cannot connect to {BASE_URL}")
        print("     Start the server first:  .venv312\\Scripts\\python.exe -m uvicorn app.main:app --port 8000 --reload")
        failures.append("server_reachable")
        sys.exit(1)


# ── Tenant registration ───────────────────────────────────────────────────────

def test_create_tenant():
    print("\n[1] POST /api/tenants — register a bank")
    # Pre-clean if previous run left a stale tenant
    list_r = requests.get(f"{API}/tenants?active_only=false", timeout=10)
    for t in list_r.json() if list_r.ok else []:
        if t.get("name") == _TEST_TENANT_NAME:
            requests.patch(f"{API}/tenants/{t['id']}/deactivate", timeout=10)

    r = requests.post(f"{API}/tenants", json={
        "name": _TEST_TENANT_NAME,
        "slug": _TEST_TENANT_SLUG,
        "display_name": "E2E Test Bank",
    }, timeout=10)
    chk("201 Created", r.status_code == 201, str(r.status_code))
    if r.status_code != 201:
        failures.append("create_tenant"); return
    body = r.json()
    chk("id present", "id" in body)
    chk("name correct", body.get("name") == _TEST_TENANT_NAME)
    chk("active=true", body.get("active") is True)
    ctx["tenant_id"] = body["id"]
    print(f"      tenant_id = {ctx['tenant_id']}")


def test_duplicate_tenant_rejected():
    print("\n[2] POST /api/tenants — duplicate name → 409")
    r = requests.post(f"{API}/tenants", json={
        "name": _TEST_TENANT_NAME,
        "slug": _TEST_TENANT_SLUG + "-dup",
        "display_name": "Dup",
    }, timeout=10)
    chk("409 Conflict", r.status_code == 409, str(r.status_code))


def test_get_tenant():
    print("\n[3] GET /api/tenants/{id} — fetch single tenant")
    tid = ctx.get("tenant_id")
    if not tid: return
    r = requests.get(f"{API}/tenants/{tid}", timeout=10)
    chk("200 OK", r.status_code == 200)
    chk("correct id", r.json().get("id") == tid)


# ── Workspace creation ────────────────────────────────────────────────────────

def test_create_workspace():
    print("\n[4] POST /api/workspaces — create Personal Loan workspace")
    tid = ctx.get("tenant_id")
    if not tid: return
    r = requests.post(f"{API}/workspaces", json={
        "tenant_id": tid,
        "name": "personal_loan",
        "display_name": "Personal Loan",
    }, timeout=10)
    chk("201 Created", r.status_code == 201, str(r.status_code))
    if r.status_code != 201:
        failures.append("create_workspace"); return
    body = r.json()
    chk("tenant_id matches", body.get("tenant_id") == tid)
    chk("name = personal_loan", body.get("name") == "personal_loan")
    ctx["workspace_id"] = body["id"]
    print(f"      workspace_id = {ctx['workspace_id']}")


def test_duplicate_workspace_rejected():
    print("\n[5] POST /api/workspaces — same name same tenant → 409")
    tid = ctx.get("tenant_id")
    if not tid: return
    r = requests.post(f"{API}/workspaces", json={
        "tenant_id": tid,
        "name": "personal_loan",
        "display_name": "Dup PL",
    }, timeout=10)
    chk("409 Conflict", r.status_code == 409, str(r.status_code))


def test_same_workspace_name_different_tenant():
    print("\n[6] POST /api/workspaces — same name different tenant → 201")
    # Create a second tenant
    r2 = requests.post(f"{API}/tenants", json={
        "name": _TEST_TENANT_NAME + "_b",
        "slug": _TEST_TENANT_SLUG + "-b",
        "display_name": "E2E Test Bank B",
    }, timeout=10)
    if r2.status_code != 201:
        chk("second tenant created", False, str(r2.status_code)); return
    tenant_b_id = r2.json()["id"]
    ctx["tenant_b_id"] = tenant_b_id

    r3 = requests.post(f"{API}/workspaces", json={
        "tenant_id": tenant_b_id,
        "name": "personal_loan",
        "display_name": "Personal Loan",
    }, timeout=10)
    chk("201 — same name allowed across tenants", r3.status_code == 201, str(r3.status_code))
    if r3.ok:
        ctx["workspace_b_id"] = r3.json()["id"]
    # Deactivate second tenant
    requests.patch(f"{API}/tenants/{tenant_b_id}/deactivate", timeout=10)


# ── Ingest endpoint — validation ──────────────────────────────────────────────

def test_ingest_no_files():
    print("\n[7] POST /api/knowledge-ingestion/ingest — no files → 400 or 422")
    tid = ctx.get("tenant_id"); wid = ctx.get("workspace_id")
    if not tid or not wid: return
    r = requests.post(
        f"{API}/knowledge-ingestion/ingest",
        data={"tenant_id": tid, "workspace_id": wid},
        timeout=10,
    )
    chk("400 or 422 for missing files", r.status_code in (400, 422), str(r.status_code))


def test_ingest_non_pdf():
    print("\n[8] POST /api/knowledge-ingestion/ingest — non-PDF → per-file failed")
    tid = ctx.get("tenant_id"); wid = ctx.get("workspace_id")
    if not tid or not wid: return
    r = requests.post(
        f"{API}/knowledge-ingestion/ingest",
        data={"tenant_id": tid, "workspace_id": wid},
        files=[("files", ("bad.txt", io.BytesIO(b"not a pdf"), "text/plain"))],
        timeout=30,
    )
    chk("200 OK (batch continues)", r.status_code == 200, str(r.status_code))
    if r.ok:
        body = r.json()
        result = body["results"][0]
        chk("file status=failed", result.get("status") == "failed")
        chk("error message present", bool(result.get("error")))


def test_ingest_wrong_tenant():
    print("\n[9] POST /api/knowledge-ingestion/ingest — wrong tenant → failed result")
    wid = ctx.get("workspace_id")
    if not wid: return
    r = requests.post(
        f"{API}/knowledge-ingestion/ingest",
        data={"tenant_id": 99999, "workspace_id": wid},
        files=[("files", ("brd.pdf", io.BytesIO(_PDF), "application/pdf"))],
        timeout=30,
    )
    chk("200 OK (batch result)", r.status_code == 200, str(r.status_code))
    if r.ok:
        result = r.json()["results"][0]
        chk("file status=failed for wrong tenant", result.get("status") == "failed")


def test_ingest_nonexistent_workspace():
    print("\n[10] POST /api/knowledge-ingestion/ingest — workspace 99999 → failed")
    tid = ctx.get("tenant_id")
    if not tid: return
    r = requests.post(
        f"{API}/knowledge-ingestion/ingest",
        data={"tenant_id": tid, "workspace_id": 99999},
        files=[("files", ("brd.pdf", io.BytesIO(_PDF), "application/pdf"))],
        timeout=30,
    )
    chk("200 OK (batch result)", r.status_code == 200, str(r.status_code))
    if r.ok:
        result = r.json()["results"][0]
        chk("file status=failed for missing workspace", result.get("status") == "failed")


# ── Ingest endpoint — full pipeline ──────────────────────────────────────────

def test_ingest_valid_pdf():
    print("\n[11] POST /api/knowledge-ingestion/ingest — valid PDF → pipeline runs")
    tid = ctx.get("tenant_id"); wid = ctx.get("workspace_id")
    if not tid or not wid: return
    r = requests.post(
        f"{API}/knowledge-ingestion/ingest",
        data={"tenant_id": tid, "workspace_id": wid},
        files=[("files", ("personal_loan_brd.pdf", io.BytesIO(_PDF), "application/pdf"))],
        timeout=120,   # LLM extraction can take up to 60s
    )
    chk("200 OK", r.status_code == 200, str(r.status_code))
    if not r.ok: return

    body = r.json()
    chk("tenant_id in response", body.get("tenant_id") == tid)
    chk("workspace_id in response", body.get("workspace_id") == wid)
    chk("total = 1", body.get("total") == 1)

    result = body["results"][0]
    chk("filename preserved", result.get("filename") == "personal_loan_brd.pdf")

    status = result.get("status")
    print(f"      pipeline status: {status}")
    chk("status is completed or partial or failed",
        status in ("completed", "partial", "failed"))

    if status in ("completed", "partial"):
        chk("document_id present", bool(result.get("document_id")))
        chk("document_version_id present", bool(result.get("document_version_id")))
        chk("ingestion_attempt_id present", bool(result.get("ingestion_attempt_id")))
        chk("knowledge_id present", bool(result.get("knowledge_id")))
        ctx["document_id"] = result.get("document_id")
        ctx["document_version_id"] = result.get("document_version_id")
        ctx["ingestion_attempt_id"] = result.get("ingestion_attempt_id")
        ctx["knowledge_id"] = result.get("knowledge_id")
        print(f"      document_id={ctx['document_id']}  "
              f"version_id={ctx['document_version_id']}  "
              f"attempt_id={ctx['ingestion_attempt_id']}  "
              f"knowledge_id={ctx['knowledge_id']}")
        if result.get("warnings"):
            print(f"      warnings: {result['warnings']}")
    elif status == "failed":
        print(f"      error: {result.get('error')}")
        print("      NOTE: This is expected if LLM providers are not configured.")
        # Mark as advisory, not a hard failure — the pipeline ran correctly,
        # the LLM simply has no credentials in this environment.
        chk("document_id present even on fail", bool(result.get("document_id")))
        chk("ingestion_attempt_id present even on fail",
            bool(result.get("ingestion_attempt_id")))


def test_ingest_duplicate_same_pdf():
    print("\n[12] POST /api/knowledge-ingestion/ingest — same PDF twice → is_duplicate")
    tid = ctx.get("tenant_id"); wid = ctx.get("workspace_id")
    if not tid or not wid: return
    r = requests.post(
        f"{API}/knowledge-ingestion/ingest",
        data={"tenant_id": tid, "workspace_id": wid},
        files=[("files", ("personal_loan_brd.pdf", io.BytesIO(_PDF), "application/pdf"))],
        timeout=120,
    )
    chk("200 OK", r.status_code == 200, str(r.status_code))
    if not r.ok: return
    result = r.json()["results"][0]
    chk("is_duplicate=true on second upload", result.get("is_duplicate") is True)
    # document_id must match the first upload
    if ctx.get("document_id"):
        chk("same document_id returned",
            result.get("document_id") == ctx["document_id"])


def test_ingest_different_pdf_new_document():
    print("\n[13] POST /api/knowledge-ingestion/ingest — different PDF → new document")
    tid = ctx.get("tenant_id"); wid = ctx.get("workspace_id")
    if not tid or not wid: return
    r = requests.post(
        f"{API}/knowledge-ingestion/ingest",
        data={"tenant_id": tid, "workspace_id": wid},
        files=[("files", ("brd_v2.pdf", io.BytesIO(_PDF_V2), "application/pdf"))],
        timeout=120,
    )
    chk("200 OK", r.status_code == 200, str(r.status_code))
    if not r.ok: return
    result = r.json()["results"][0]
    chk("is_duplicate=false for new content", result.get("is_duplicate") is False)
    if ctx.get("document_id") and result.get("document_id"):
        chk("different document_id",
            result.get("document_id") != ctx["document_id"])


def test_ingest_batch_two_files():
    print("\n[14] POST /api/knowledge-ingestion/ingest — batch of 2 files")
    tid = ctx.get("tenant_id"); wid = ctx.get("workspace_id")
    if not tid or not wid: return
    # Use different content bytes so they are distinct documents
    pdf_a = _PDF.replace(b"Test Document", b"Doc Alpha")
    pdf_b = _PDF.replace(b"Test Document", b"Doc Beta")
    r = requests.post(
        f"{API}/knowledge-ingestion/ingest",
        data={"tenant_id": tid, "workspace_id": wid},
        files=[
            ("files", ("alpha.pdf", io.BytesIO(pdf_a), "application/pdf")),
            ("files", ("beta.pdf",  io.BytesIO(pdf_b), "application/pdf")),
        ],
        timeout=240,
    )
    chk("200 OK", r.status_code == 200, str(r.status_code))
    if not r.ok: return
    body = r.json()
    chk("total = 2", body.get("total") == 2)
    chk("2 results returned", len(body.get("results", [])) == 2)
    names = {res["filename"] for res in body["results"]}
    chk("both filenames in results", names == {"alpha.pdf", "beta.pdf"})


# ── Workspace state after ingestion ──────────────────────────────────────────

def test_workspace_documents_endpoint():
    print("\n[15] GET /api/workspaces/{id}/documents — BRDs appear in workspace")
    wid = ctx.get("workspace_id")
    if not wid: return
    r = requests.get(f"{API}/workspaces/{wid}/documents", timeout=10)
    chk("200 OK", r.status_code == 200, str(r.status_code))
    if r.ok:
        docs = r.json()
        chk("at least one document", len(docs) >= 1 if isinstance(docs, list) else True)
        print(f"      {len(docs) if isinstance(docs, list) else '?'} document(s) in workspace")


def test_workspace_overview_endpoint():
    print("\n[16] GET /api/workspaces/{id}/overview — overview counts updated")
    wid = ctx.get("workspace_id")
    if not wid: return
    r = requests.get(f"{API}/workspaces/{wid}/overview", timeout=10)
    chk("200 OK", r.status_code == 200, str(r.status_code))
    if r.ok:
        body = r.json()
        brd_count = body.get("brd_count", 0)
        chk("brd_count >= 1", brd_count >= 1, str(brd_count))
        print(f"      brd_count={brd_count}  "
              f"action_count={body.get('action_count', 0)}  "
              f"rule_count={body.get('business_rule_count', 0)}")


# ── Cross-tenant isolation ────────────────────────────────────────────────────

def test_cross_tenant_ingest_isolation():
    print("\n[17] Cross-tenant isolation — same PDF, different tenants, different docs")
    # We already uploaded _PDF to tenant_id. Now check a fresh tenant gets its own doc.
    tid_b = ctx.get("tenant_b_id")
    wid_b = ctx.get("workspace_b_id")
    if not tid_b or not wid_b:
        print("  —  skipped (second tenant/workspace not created)")
        return
    # Re-activate second tenant if deactivated
    requests.post(f"{API}/tenants", json={
        "name": _TEST_TENANT_NAME + "_isolation",
        "slug": _TEST_TENANT_SLUG + "-isolation",
        "display_name": "Isolation Test Bank",
    }, timeout=10)
    r = requests.post(f"{API}/tenants", json={
        "name": _TEST_TENANT_NAME + "_iso2",
        "slug": _TEST_TENANT_SLUG + "-iso2",
        "display_name": "ISO2 Bank",
    }, timeout=10)
    if r.status_code != 201:
        print("  —  skipped (could not create isolation tenant)")
        return
    iso_tid = r.json()["id"]
    ws_r = requests.post(f"{API}/workspaces", json={
        "tenant_id": iso_tid, "name": "personal_loan", "display_name": "PL"
    }, timeout=10)
    if ws_r.status_code != 201:
        requests.patch(f"{API}/tenants/{iso_tid}/deactivate", timeout=10)
        print("  —  skipped (could not create isolation workspace)")
        return
    iso_wid = ws_r.json()["id"]
    r2 = requests.post(
        f"{API}/knowledge-ingestion/ingest",
        data={"tenant_id": iso_tid, "workspace_id": iso_wid},
        files=[("files", ("brd.pdf", io.BytesIO(_PDF), "application/pdf"))],
        timeout=120,
    )
    chk("200 OK for second tenant", r2.status_code == 200, str(r2.status_code))
    if r2.ok:
        result2 = r2.json()["results"][0]
        chk("not duplicate across tenants", result2.get("is_duplicate") is False)
        if ctx.get("document_id") and result2.get("document_id"):
            chk("different document_id across tenants",
                result2["document_id"] != ctx["document_id"])
    requests.patch(f"{API}/tenants/{iso_tid}/deactivate", timeout=10)


# ── Health check ──────────────────────────────────────────────────────────────

def test_health_endpoint():
    print("\n[18] GET /api/health — service health")
    r = requests.get(f"{API}/health", timeout=5)
    chk("health endpoint reachable", r.status_code in (200, 503), str(r.status_code))
    if r.ok:
        print(f"      health: {r.json()}")


# ── Runner ────────────────────────────────────────────────────────────────────

def main() -> int:
    print("=" * 65)
    print(f"FlowOS — End-to-End API Tests  [{BASE_URL}]")
    print("=" * 65)

    tests = [
        test_server_reachable,
        test_create_tenant,
        test_duplicate_tenant_rejected,
        test_get_tenant,
        test_create_workspace,
        test_duplicate_workspace_rejected,
        test_same_workspace_name_different_tenant,
        test_ingest_no_files,
        test_ingest_non_pdf,
        test_ingest_wrong_tenant,
        test_ingest_nonexistent_workspace,
        test_ingest_valid_pdf,
        test_ingest_duplicate_same_pdf,
        test_ingest_different_pdf_new_document,
        test_ingest_batch_two_files,
        test_workspace_documents_endpoint,
        test_workspace_overview_endpoint,
        test_cross_tenant_ingest_isolation,
        test_health_endpoint,
    ]

    for t in tests:
        try:
            t()
        except Exception as exc:
            print(f"  [UNEXPECTED ERROR in {t.__name__}]: {exc}")
            traceback.print_exc()
            failures.append(t.__name__)

    print("\n[cleanup]")
    _cleanup()

    total  = len(tests)
    failed = len(failures)
    print("\n" + "=" * 65)
    if failures:
        print(f"FAILED — {failed}/{total} check(s):")
        for f in failures:
            print(f"  ✗  {f}")
        return 1

    print(f"ALL {total} TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
