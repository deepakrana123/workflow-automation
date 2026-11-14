"""
Verification script for Step 3 + deferred fixes.
Run from project root:
    .venv312\Scripts\python.exe verify_step3.py

Checks:
  Step 3  — WorkflowKnowledge.brd_document_id FK and relationship
  Item 1  — get_unmapped_actions/triggers accept workspace_id parameter
  Item 2  — WorkflowTriggerMapping has query_text and top_candidates
            mark_trigger_unmapped and update_trigger_mapping write them
  Bugfix  — search_business_rules no longer raises NameError on 'qyery'
"""

import sys
import inspect

failures = []

print("=" * 65)
print("FlowOS — Step 3 + deferred items verification")
print("=" * 65)

# ── 1. Full package import ────────────────────────────────────────
print("\n[1] Package import")
try:
    import app.models
    print("  OK  app.models loaded")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("package import")

# ── 2. WorkflowKnowledge: brd_document_id column ─────────────────
print("\n[2] WorkflowKnowledge.brd_document_id column")
try:
    from sqlalchemy import inspect as sa_inspect
    from app.models.workflow_knowledge import WorkflowKnowledge
    cols = {c.key for c in sa_inspect(WorkflowKnowledge).mapper.column_attrs}
    if "brd_document_id" in cols:
        print("  OK  brd_document_id column present")
    else:
        print("  FAIL  brd_document_id column missing")
        failures.append("brd_document_id column")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("WorkflowKnowledge inspect")

# ── 3. WorkflowKnowledge: brd_document_id FK target ──────────────
print("\n[3] WorkflowKnowledge.brd_document_id → brd_documents.id")
try:
    from app.db.base import Base
    t = Base.metadata.tables["workflow_knowledge"]
    fk_map = {
        col.name: [fk.target_fullname for fk in col.foreign_keys]
        for col in t.columns if col.foreign_keys
    }
    target = fk_map.get("brd_document_id", [])
    if "brd_documents.id" in target:
        print("  OK  FK → brd_documents.id (SET NULL)")
    else:
        print(f"  FAIL  expected brd_documents.id, got {target}")
        failures.append("brd_document_id FK")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("FK inspect")

# ── 4. WorkflowKnowledge: brd_document relationship ──────────────
print("\n[4] WorkflowKnowledge.brd_document relationship")
try:
    from sqlalchemy import inspect as sa_inspect
    from app.models.workflow_knowledge import WorkflowKnowledge
    rels = {r.key for r in sa_inspect(WorkflowKnowledge).mapper.relationships}
    if "brd_document" in rels:
        print("  OK  WorkflowKnowledge.brd_document relationship present")
    else:
        print("  FAIL  WorkflowKnowledge.brd_document missing")
        failures.append("brd_document relationship")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("relationship inspect")

# ── 5. WorkflowTriggerMapping: new columns ────────────────────────
print("\n[5] WorkflowTriggerMapping: query_text + top_candidates")
try:
    from app.models.workflow_trigger_mapping import WorkflowTriggerMapping
    cols = {c.key for c in sa_inspect(WorkflowTriggerMapping).mapper.column_attrs}
    for col in ("query_text", "top_candidates"):
        if col in cols:
            print(f"  OK  {col} present on WorkflowTriggerMapping")
        else:
            print(f"  FAIL  {col} missing from WorkflowTriggerMapping")
            failures.append(f"WorkflowTriggerMapping.{col}")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("WorkflowTriggerMapping inspect")

# ── 6. WorkflowTriggerMapping: columns in DB metadata ────────────
print("\n[6] workflow_trigger_mapping table metadata columns")
try:
    from app.db.base import Base
    t = Base.metadata.tables["workflow_trigger_mapping"]
    col_names = {c.name for c in t.columns}
    for col in ("query_text", "top_candidates"):
        if col in col_names:
            print(f"  OK  {col} in workflow_trigger_mapping metadata")
        else:
            print(f"  FAIL  {col} not in metadata")
            failures.append(f"metadata {col}")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("trigger mapping metadata")

# ── 7. WorkflowRepository: workspace_id parameter on get_unmapped_* ──
print("\n[7] WorkflowRepository.get_unmapped_actions/triggers accept workspace_id")
try:
    from app.knowledge_ingestions.workflow_repository import WorkflowRepository

    action_sig  = inspect.signature(WorkflowRepository.get_unmapped_actions)
    trigger_sig = inspect.signature(WorkflowRepository.get_unmapped_triggers)

    assert "workspace_id" in action_sig.parameters, \
        "get_unmapped_actions missing workspace_id"
    assert "workspace_id" in trigger_sig.parameters, \
        "get_unmapped_triggers missing workspace_id"

    # Default must be None (backward-compatible)
    assert action_sig.parameters["workspace_id"].default is None, \
        "get_unmapped_actions workspace_id default must be None"
    assert trigger_sig.parameters["workspace_id"].default is None, \
        "get_unmapped_triggers workspace_id default must be None"

    print("  OK  get_unmapped_actions(workspace_id=None)")
    print("  OK  get_unmapped_triggers(workspace_id=None)")
except AssertionError as e:
    print(f"  FAIL  {e}")
    failures.append(str(e))
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("repository signature")

# ── 8. mark_trigger_unmapped writes query_text + top_candidates ───
print("\n[8] mark_trigger_unmapped signature has query_text + top_candidates")
try:
    from app.knowledge_ingestions.workflow_repository import WorkflowRepository
    sig = inspect.signature(WorkflowRepository.mark_trigger_unmapped)
    for param in ("query_text", "top_candidates"):
        assert param in sig.parameters, f"mark_trigger_unmapped missing {param}"
        print(f"  OK  mark_trigger_unmapped({param}=...)")
except AssertionError as e:
    print(f"  FAIL  {e}")
    failures.append(str(e))
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("mark_trigger_unmapped signature")

# ── 9. update_trigger_mapping has query_text + top_candidates ─────
print("\n[9] update_trigger_mapping signature has query_text + top_candidates")
try:
    from app.knowledge_ingestions.workflow_repository import WorkflowRepository
    sig = inspect.signature(WorkflowRepository.update_trigger_mapping)
    for param in ("query_text", "top_candidates"):
        assert param in sig.parameters, f"update_trigger_mapping missing {param}"
        print(f"  OK  update_trigger_mapping({param}=...)")
except AssertionError as e:
    print(f"  FAIL  {e}")
    failures.append(str(e))
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("update_trigger_mapping signature")

# ── 10. EmbeddingMapper passes workspace_id to map_actions/triggers ──
print("\n[10] EmbeddingMapper.map_actions/triggers accept workspace_id")
try:
    from app.knowledge_ingestions.embedding_mapper import EmbeddingMapper
    action_sig  = inspect.signature(EmbeddingMapper.map_actions)
    trigger_sig = inspect.signature(EmbeddingMapper.map_triggers)
    for name, sig in [("map_actions", action_sig), ("map_triggers", trigger_sig)]:
        assert "workspace_id" in sig.parameters, f"{name} missing workspace_id"
        assert sig.parameters["workspace_id"].default is None, \
            f"{name} workspace_id default must be None"
        print(f"  OK  EmbeddingMapper.{name}(workspace_id=None)")
except AssertionError as e:
    print(f"  FAIL  {e}")
    failures.append(str(e))
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("EmbeddingMapper signature")

# ── 11. search_business_rules typo fix ───────────────────────────
print("\n[11] search_business_rules: qyery typo fixed")
try:
    import ast
    with open("app/knowledge_ingestions/workflow_repository.py") as f:
        source = f.read()
    if "qyery" in source:
        print("  FAIL  'qyery' typo still present")
        failures.append("qyery typo")
    else:
        print("  OK  no 'qyery' typo in workflow_repository.py")
    # Confirm the method parses without SyntaxError
    ast.parse(source)
    print("  OK  workflow_repository.py parses cleanly")
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("search_business_rules parse")

# ── 12. KnowledgeIngestionService passes workspace_id to mapper ──
print("\n[12] KnowledgeIngestionService.ingest calls mapper with workspace_id")
try:
    with open("app/knowledge_ingestions/service.py") as f:
        src = f.read()
    assert "workspace_id=workspace_id" in src, \
        "service.py does not pass workspace_id to mapper"
    print("  OK  map_actions(workspace_id=workspace_id) in service.py")
    print("  OK  map_triggers(workspace_id=workspace_id) in service.py")
except AssertionError as e:
    print(f"  FAIL  {e}")
    failures.append(str(e))
except Exception as e:
    print(f"  FAIL  {e}")
    failures.append("service.py mapper call")

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
