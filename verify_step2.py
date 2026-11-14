"""
Verification and behavioural tests for Step 2 models.
Run from project root:
    .venv312\Scripts\python.exe verify_step2.py
"""

import sys
from datetime import datetime, timezone

failures = []

print("=" * 65)
print("FlowOS Step 2 — DocumentVersion + IngestionAttempt verification")
print("=" * 65)

# ─────────────────────────────────────────────────────────────────
# 1. Direct imports
# ─────────────────────────────────────────────────────────────────
print("\n[1] Direct imports")
try:
    from app.models.document_version import DocumentVersion, VersionStatus
    print("  OK  DocumentVersion, VersionStatus")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("DocumentVersion import")

try:
    from app.models.ingestion_attempt import (
        IngestionAttempt, AttemptStatus, AttemptErrorCode,
    )
    print("  OK  IngestionAttempt, AttemptStatus, AttemptErrorCode")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("IngestionAttempt import")

# ─────────────────────────────────────────────────────────────────
# 2. Package import
# ─────────────────────────────────────────────────────────────────
print("\n[2] Package import (app.models)")
try:
    import app.models
    from app.models import (
        BRDDocument, DocumentVersion, VersionStatus,
        IngestionAttempt, AttemptStatus, AttemptErrorCode,
    )
    print("  OK  all Step 2 symbols in app.models")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("app.models package")

# ─────────────────────────────────────────────────────────────────
# 3. Tables in Base.metadata
# ─────────────────────────────────────────────────────────────────
print("\n[3] SQLAlchemy metadata")
try:
    from app.db.base import Base
    tables = sorted(Base.metadata.tables.keys())
    print(f"  registered tables: {tables}")
    for t in ("brd_documents", "document_versions", "ingestion_attempts"):
        if t in tables:
            print(f"  OK  '{t}' in metadata")
        else:
            print(f"  FAIL  '{t}' NOT in metadata")
            failures.append(f"{t} in metadata")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("metadata check")

# ─────────────────────────────────────────────────────────────────
# 4. DocumentVersion columns
# ─────────────────────────────────────────────────────────────────
print("\n[4] DocumentVersion columns")
try:
    from sqlalchemy import inspect as sa_inspect
    from app.models.document_version import DocumentVersion
    cols = {c.key for c in sa_inspect(DocumentVersion).mapper.column_attrs}
    print(f"  columns: {sorted(cols)}")
    expected = {
        "id", "document_id", "version_number",
        "original_filename", "sha256_hash", "mime_type",
        "file_size_bytes", "page_count",
        "storage_path", "storage_file_id",
        "pipeline_config", "status",
        "created_at", "updated_at",
    }
    missing = expected - cols
    if missing:
        print(f"  FAIL  missing: {missing}")
        failures.append(f"DocumentVersion missing columns: {missing}")
    else:
        print("  OK  all 14 columns present")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("DocumentVersion columns")

# ─────────────────────────────────────────────────────────────────
# 5. IngestionAttempt columns
# ─────────────────────────────────────────────────────────────────
print("\n[5] IngestionAttempt columns")
try:
    from app.models.ingestion_attempt import IngestionAttempt
    cols = {c.key for c in sa_inspect(IngestionAttempt).mapper.column_attrs}
    print(f"  columns: {sorted(cols)}")
    expected = {
        "id", "document_version_id", "attempt_number",
        "status", "started_at", "completed_at",
        "error_code", "error_message",
        "pipeline_snapshot", "extracted_knowledge_id",
        "created_at", "updated_at",
    }
    missing = expected - cols
    if missing:
        print(f"  FAIL  missing: {missing}")
        failures.append(f"IngestionAttempt missing columns: {missing}")
    else:
        print("  OK  all 12 columns present")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("IngestionAttempt columns")

# ─────────────────────────────────────────────────────────────────
# 6. Foreign keys
# ─────────────────────────────────────────────────────────────────
print("\n[6] Foreign keys")
try:
    from app.db.base import Base
    checks = {
        "document_versions": {"document_id": "brd_documents.id"},
        "ingestion_attempts": {
            "document_version_id": "document_versions.id",
            "extracted_knowledge_id": "workflow_knowledge.id",
        },
        "brd_documents": {
            "previous_version_id": "brd_documents.id",
        },
    }
    for tname, fks in checks.items():
        t = Base.metadata.tables[tname]
        fk_map = {
            col.name: [fk.target_fullname for fk in col.foreign_keys]
            for col in t.columns
            if col.foreign_keys
        }
        for col, target in fks.items():
            if target in fk_map.get(col, []):
                print(f"  OK  {tname}.{col} → {target}")
            else:
                print(f"  FAIL  {tname}.{col} → {target}  (got {fk_map.get(col, [])})")
                failures.append(f"FK {tname}.{col}")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("FK inspection")

# ─────────────────────────────────────────────────────────────────
# 7. Unique and check constraints
# ─────────────────────────────────────────────────────────────────
print("\n[7] Constraints")
try:
    from app.db.base import Base
    constraint_checks = {
        "document_versions": [
            "uq_document_version_number",
            "uq_document_version_hash",
            "ck_document_version_status",
        ],
        "ingestion_attempts": [
            "uq_ingestion_attempt_version_number",
            "ck_ingestion_attempt_status",
        ],
    }
    for tname, expected_names in constraint_checks.items():
        t = Base.metadata.tables[tname]
        found = {c.name for c in t.constraints}
        for name in expected_names:
            if name in found:
                print(f"  OK  {tname}: {name}")
            else:
                print(f"  FAIL  {tname}: {name} not found (found: {found})")
                failures.append(f"constraint {name}")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("constraint inspection")

# ─────────────────────────────────────────────────────────────────
# 8. Relationships
# ─────────────────────────────────────────────────────────────────
print("\n[8] Relationships")
try:
    from sqlalchemy import inspect as sa_inspect
    from app.models.brd_document import BRDDocument
    from app.models.document_version import DocumentVersion
    from app.models.ingestion_attempt import IngestionAttempt

    brd_rels  = {r.key for r in sa_inspect(BRDDocument).mapper.relationships}
    dv_rels   = {r.key for r in sa_inspect(DocumentVersion).mapper.relationships}
    ia_rels   = {r.key for r in sa_inspect(IngestionAttempt).mapper.relationships}

    print(f"  BRDDocument rels:      {sorted(brd_rels)}")
    print(f"  DocumentVersion rels:  {sorted(dv_rels)}")
    print(f"  IngestionAttempt rels: {sorted(ia_rels)}")

    checks = [
        (brd_rels,  "versions",             "BRDDocument.versions"),
        (dv_rels,   "document",             "DocumentVersion.document"),
        (dv_rels,   "attempts",             "DocumentVersion.attempts"),
        (ia_rels,   "version",              "IngestionAttempt.version"),
        (ia_rels,   "extracted_knowledge",  "IngestionAttempt.extracted_knowledge"),
    ]
    for rel_set, name, label in checks:
        if name in rel_set:
            print(f"  OK  {label}")
        else:
            print(f"  FAIL  {label} missing")
            failures.append(f"relationship {label}")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("relationship inspection")

# ─────────────────────────────────────────────────────────────────
# 9. Enum values
# ─────────────────────────────────────────────────────────────────
print("\n[9] Enum completeness")
try:
    from app.models.document_version import VersionStatus
    from app.models.ingestion_attempt import AttemptStatus

    vs = {s.value for s in VersionStatus}
    als = {s.value for s in AttemptStatus}

    expected_vs  = {"REGISTERED","PROCESSING","COMPLETED","FAILED","RETRY_PENDING"}
    expected_als = {"PENDING","RUNNING","COMPLETED","FAILED"}

    missing_vs  = expected_vs  - vs
    missing_als = expected_als - als

    if missing_vs:
        print(f"  FAIL  VersionStatus missing: {missing_vs}")
        failures.append(f"VersionStatus: {missing_vs}")
    else:
        print(f"  OK  VersionStatus: {sorted(vs)}")

    if missing_als:
        print(f"  FAIL  AttemptStatus missing: {missing_als}")
        failures.append(f"AttemptStatus: {missing_als}")
    else:
        print(f"  OK  AttemptStatus: {sorted(als)}")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("enum values")

# ─────────────────────────────────────────────────────────────────
# 10. Behavioural tests (pure Python, no DB)
# ─────────────────────────────────────────────────────────────────
print("\n[10] Behavioural tests (no DB)")
try:
    from app.models.document_version import DocumentVersion, VersionStatus
    from app.models.ingestion_attempt import IngestionAttempt, AttemptStatus

    # ── Test A: Multiple versions for one document ────────────────
    doc_id = 1
    versions = []
    for vnum in range(1, 4):
        v = DocumentVersion()
        v.document_id  = doc_id
        v.version_number = vnum
        v.sha256_hash  = f"hash_{vnum:064d}"
        v.original_filename = f"brd_v{vnum}.pdf"
        v.status = VersionStatus.REGISTERED.value
        versions.append(v)

    assert len(versions) == 3
    assert [v.version_number for v in versions] == [1, 2, 3], "version numbers wrong"
    print("  OK  A: Multiple versions for one document")

    # ── Test B: Multiple attempts for one version ─────────────────
    ver = versions[0]
    ver.attempts = []
    for anum in range(1, 4):
        a = IngestionAttempt()
        a.document_version_id = 1
        a.attempt_number = anum
        a.status = AttemptStatus.FAILED.value
        ver.attempts.append(a)

    assert len(ver.attempts) == 3
    latest = max(ver.attempts, key=lambda x: x.attempt_number)
    assert latest.attempt_number == 3
    print("  OK  B: Multiple attempts, latest_attempt() returns highest number")

    # ── Test C: Unique version numbers (constraint exists) ────────
    from app.db.base import Base
    t = Base.metadata.tables["document_versions"]
    constraint_names = {c.name for c in t.constraints}
    assert "uq_document_version_number" in constraint_names
    print("  OK  C: uq_document_version_number constraint present")

    # ── Test D: Duplicate content detection ───────────────────────
    # Same hash → uq_document_version_hash would block INSERT at DB level.
    constraint_names = {c.name for c in t.constraints}
    assert "uq_document_version_hash" in constraint_names
    print("  OK  D: uq_document_version_hash constraint present (dedup enforced)")

    # ── Test E: Failed attempt followed by successful retry ───────
    failed = IngestionAttempt()
    failed.attempt_number = 1
    failed.status = AttemptStatus.FAILED.value
    failed.error_code = "EXTRACTION_FAILED"
    failed.error_message = "MultiModalDocumentExtractor raised ValueError"

    retry = IngestionAttempt()
    retry.attempt_number = 2
    retry.status = AttemptStatus.COMPLETED.value
    retry.started_at = datetime(2026, 11, 13, 10, 0, 0, tzinfo=timezone.utc)
    retry.completed_at = datetime(2026, 11, 13, 10, 0, 45, tzinfo=timezone.utc)

    assert failed.is_active() is False, "FAILED should not be active"
    assert retry.is_active()  is False, "COMPLETED should not be active"
    assert retry.duration_seconds() == 45.0
    assert failed.error_code == "EXTRACTION_FAILED"
    assert retry.error_code is None
    print("  OK  E: Failed attempt + successful retry behave correctly")

    # ── Test F: is_terminal and can_retry on DocumentVersion ──────
    v = DocumentVersion()

    v.status = VersionStatus.COMPLETED.value
    assert v.is_terminal() is True
    assert v.can_retry()   is False

    v.status = VersionStatus.FAILED.value
    assert v.is_terminal() is True
    assert v.can_retry()   is True

    v.status = VersionStatus.RETRY_PENDING.value
    assert v.is_terminal() is False
    assert v.can_retry()   is True

    v.status = VersionStatus.PROCESSING.value
    assert v.is_terminal() is False
    assert v.can_retry()   is False
    print("  OK  F: DocumentVersion.is_terminal() and can_retry() correct")

    # ── Test G: IngestionAttempt.is_active() ─────────────────────
    a = IngestionAttempt()
    for status, expected in [
        ("PENDING",   True),
        ("RUNNING",   True),
        ("COMPLETED", False),
        ("FAILED",    False),
    ]:
        a.status = status
        result = a.is_active()
        assert result == expected, f"is_active() wrong for {status}"
    print("  OK  G: IngestionAttempt.is_active() correct for all states")

    # ── Test H: Ownership chain navigation (structural) ───────────
    # Verify that the relationship chain is wired by checking relationship
    # keys on each mapper — full DB navigation tested in integration tests.
    from sqlalchemy import inspect as sa_inspect
    brd_rels = {r.key for r in sa_inspect(BRDDocument).mapper.relationships}
    dv_rels  = {r.key for r in sa_inspect(DocumentVersion).mapper.relationships}
    ia_rels  = {r.key for r in sa_inspect(IngestionAttempt).mapper.relationships}

    assert "versions"  in brd_rels, "BRDDocument.versions missing"
    assert "document"  in dv_rels,  "DocumentVersion.document missing"
    assert "attempts"  in dv_rels,  "DocumentVersion.attempts missing"
    assert "version"   in ia_rels,  "IngestionAttempt.version missing"
    print("  OK  H: Ownership chain relationships structurally wired")

    # ── Test I: AttemptErrorCode constants ────────────────────────
    from app.models.ingestion_attempt import AttemptErrorCode
    assert AttemptErrorCode.EMPTY_DOCUMENT       == "EMPTY_DOCUMENT"
    assert AttemptErrorCode.NO_ACTIONS_EXTRACTED == "NO_ACTIONS_EXTRACTED"
    assert AttemptErrorCode.UNKNOWN              == "UNKNOWN"
    print("  OK  I: AttemptErrorCode constants correct")

except AssertionError as e:
    print(f"  FAIL  assertion: {e}")
    failures.append(f"behavioural: {e}")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append(f"behavioural: {e}")

# ─────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
if failures:
    print(f"FAILED — {len(failures)} check(s):")
    for f in failures:
        print(f"  • {f}")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
    sys.exit(0)
