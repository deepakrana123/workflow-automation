"""
Verification script for BRDDocument model — Step 1.
Run from project root:
    .venv312\Scripts\python.exe verify_brd_document.py
"""

import sys

failures = []

print("=" * 65)
print("FlowOS — BRDDocument model verification")
print("=" * 65)

# ── 1. Direct import ──────────────────────────────────────────────
print("\n[1] Direct imports")
try:
    from app.models.brd_document import BRDDocument, IngestionStatus, DocumentType
    print("  OK  BRDDocument, IngestionStatus, DocumentType")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("direct import")

# ── 2. Package import (triggers __init__.py chain) ────────────────
print("\n[2] Package import (app.models)")
try:
    import app.models
    print("  OK  app.models loaded")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("app.models package")

# ── 3. Table in Base.metadata ─────────────────────────────────────
print("\n[3] SQLAlchemy metadata")
try:
    from app.db.base import Base
    tables = sorted(Base.metadata.tables.keys())
    print(f"  registered tables: {tables}")
    if "brd_documents" in tables:
        print("  OK  'brd_documents' in metadata")
    else:
        print("  FAIL  'brd_documents' NOT in metadata")
        failures.append("brd_documents in metadata")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("metadata check")

# ── 4. Columns ────────────────────────────────────────────────────
print("\n[4] BRDDocument mapper columns")
try:
    from sqlalchemy import inspect as sa_inspect
    from app.models.brd_document import BRDDocument
    cols = [c.key for c in sa_inspect(BRDDocument).mapper.column_attrs]
    print(f"  columns: {cols}")
    expected = {
        "id", "tenant_id", "workspace_id",
        "original_filename", "sha256_hash", "mime_type",
        "file_size_bytes", "page_count",
        "storage_path", "storage_file_id",
        "document_type", "ingestion_status", "failure_reason", "attempt_count",
        "version", "previous_version_id",
        "created_at", "updated_at",
    }
    missing = expected - set(cols)
    if missing:
        print(f"  FAIL  missing columns: {missing}")
        failures.append(f"missing columns: {missing}")
    else:
        print("  OK  all 18 columns present")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("column inspection")

# ── 5. Foreign keys ───────────────────────────────────────────────
print("\n[5] Foreign keys")
try:
    from app.db.base import Base
    t = Base.metadata.tables["brd_documents"]
    fk_map = {
        col.name: [fk.target_fullname for fk in col.foreign_keys]
        for col in t.columns
        if col.foreign_keys
    }
    print(f"  FK map: {fk_map}")
    checks = {
        "tenant_id":          "tenants.id",
        "workspace_id":       "workspaces.id",
        "previous_version_id":"brd_documents.id",
    }
    for col, target in checks.items():
        targets = fk_map.get(col, [])
        if target in targets:
            print(f"  OK  {col} → {target}")
        else:
            print(f"  FAIL  {col} → {target}  (got {targets})")
            failures.append(f"FK {col}")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("FK inspection")

# ── 6. Unique constraint ──────────────────────────────────────────
print("\n[6] Unique constraint uq_brd_document_workspace_hash")
try:
    from app.db.base import Base
    t = Base.metadata.tables["brd_documents"]
    names = [c.name for c in t.constraints]
    print(f"  constraint names: {names}")
    if "uq_brd_document_workspace_hash" in names:
        print("  OK  uq_brd_document_workspace_hash")
    else:
        print("  FAIL  uq_brd_document_workspace_hash not found")
        failures.append("unique constraint")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("constraint check")

# ── 7. Check constraints ──────────────────────────────────────────
print("\n[7] Check constraints")
try:
    from app.db.base import Base
    t = Base.metadata.tables["brd_documents"]
    names = [c.name for c in t.constraints]
    for ck in ("ck_brd_document_ingestion_status", "ck_brd_document_type"):
        if ck in names:
            print(f"  OK  {ck}")
        else:
            print(f"  FAIL  {ck} not found")
            failures.append(f"check constraint {ck}")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("check constraint inspection")

# ── 8. Relationships ──────────────────────────────────────────────
print("\n[8] Relationships")
try:
    from sqlalchemy import inspect as sa_inspect
    from app.models.brd_document import BRDDocument
    rels = [r.key for r in sa_inspect(BRDDocument).mapper.relationships]
    print(f"  relationships: {rels}")
    for expected_rel in ("tenant", "workspace", "previous_version", "newer_versions"):
        if expected_rel in rels:
            print(f"  OK  BRDDocument.{expected_rel}")
        else:
            print(f"  FAIL  BRDDocument.{expected_rel} missing")
            failures.append(f"relationship {expected_rel}")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("relationship inspection")

# ── 9. IngestionStatus enum ───────────────────────────────────────
print("\n[9] IngestionStatus enum values")
try:
    from app.models.brd_document import IngestionStatus
    values = [s.value for s in IngestionStatus]
    print(f"  values: {values}")
    expected_values = {
        "REGISTERED", "PROCESSING", "COMPLETED", "FAILED", "RETRY_PENDING"
    }
    missing = expected_values - set(values)
    if missing:
        print(f"  FAIL  missing: {missing}")
        failures.append(f"IngestionStatus missing: {missing}")
    else:
        print("  OK  all 5 status values present")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("IngestionStatus enum")

# ── 10. Helper methods ────────────────────────────────────────────
print("\n[10] Helper methods")
try:
    from app.models.brd_document import BRDDocument, IngestionStatus

    doc = BRDDocument()
    doc.ingestion_status = IngestionStatus.COMPLETED.value
    assert doc.is_terminal() is True,  "COMPLETED should be terminal"
    assert doc.can_retry()  is False,  "COMPLETED should not allow retry"

    doc.ingestion_status = IngestionStatus.FAILED.value
    assert doc.is_terminal() is True,  "FAILED should be terminal"
    assert doc.can_retry()   is True,  "FAILED should allow retry"

    doc.ingestion_status = IngestionStatus.PROCESSING.value
    assert doc.is_terminal() is False, "PROCESSING should not be terminal"

    print("  OK  is_terminal() and can_retry() behave correctly")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("helper methods")

# ── 11. __init__.py exports ───────────────────────────────────────
print("\n[11] __init__.py exports")
try:
    from app.models import BRDDocument, IngestionStatus, DocumentType
    print("  OK  BRDDocument, IngestionStatus, DocumentType in app.models")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("__init__.py exports")

# ── Summary ───────────────────────────────────────────────────────
print("\n" + "=" * 65)
if failures:
    print(f"FAILED — {len(failures)} check(s) did not pass:")
    for f in failures:
        print(f"  • {f}")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
    sys.exit(0)
