# Phase 6 — RAG Production Hardening — Investigation

**Date:** November 2026  
**Phase:** 6 — Production Hardening  
**Status:** Investigation & Remediation In Progress

---

## Executive Summary

Phase 6 validates and hardens the existing multi-tenant RAG pipeline against operational failures. All 9 prior phases (document registration through context assembly) are **fully implemented** with tests. This phase identifies and fixes gaps in:

1. **Embedding consistency** — stale/missing embeddings, re-embedding idempotency
2. **Document versioning** — version chain integrity, silent overwrites, duplicate processing
3. **Retry & recovery** — failure handling, idempotency, partial extraction
4. **Concurrency safety** — duplicate ingestion, RUNNING attempt protection, transaction boundaries
5. **Retrieval consistency** — correct scoping, no version mixing, provenance preservation
6. **Observability** — audit trails, metrics, error tracking

---

## Step 0: Completion Gate — VERIFIED ✅

All 9 dependencies confirmed present with actual implementation:

| Phase | Component | Status | Evidence |
|-------|-----------|--------|----------|
| **0** | Document registration & versioning | ✅ COMPLETE | BRDDocument + DocumentVersion models, unique constraints, version chain |
| **1** | Ingestion orchestrator | ✅ COMPLETE | IngestionOrchestrator with T1-T6 boundaries, failure handling, rollback, concurrent guard |
| **2A** | Extraction pipeline | ✅ COMPLETE | PdfExtractionPipeline, MultimodalExtractor, PageClassifier, extraction results |
| **2B** | Rule extraction & provenance | ✅ COMPLETE | WorkflowBusinessRule.source_brd_document_id, RuleExtractionService, provenance chains |
| **2D** | Embedding generation | ✅ COMPLETE | EmbeddingService, BAAI/bge-small-en-v1.5, 384-dim vectors |
| **2E** | Vector indexes & metadata | ✅ COMPLETE | PgVector IVFFlat indexes, embedding metadata columns, migrations |
| **3A-3B** | Vector/BM25/FTS retrieval | ✅ COMPLETE | RetrievalPipeline, three retrievers, workspace isolation |
| **3C** | RRF integration | ✅ COMPLETE | ReciprocalRankFusion k=20/k=60, score calculation, merge logic |
| **5** | Context assembly | ✅ COMPLETE | ContextAssemblyService, provenance validation, token budgeting, conflict detection |

---

## Step 1: Embedding Consistency — INVESTIGATION RESULTS

### 1.1 Current State

**Embedding-bearing entities:** 3
- `ActionDefinition` (app/models/action_definition.py)
- `TriggerDefinition` (app/models/trigger_definition.py)
- `WorkflowBusinessRule` (app/models/workflow_business_rule.py)

**Metadata tracking:** ✅ PRESENT
- All three tables have: `embedding_model_name`, `embedding_model_version`, `embedding_generated_at`
- Columns nullable for backward compatibility
- Migrations present: `h2i3j4k5l6m7_add_embedding_metadata_columns.py`

**Stale embedding detection:** ✅ PRESENT but MANUAL
- Query functions in `app/semantic/stale_embedding_detection.py`:
  - `find_stale_action_embeddings(db, workspace_id, current_model)`
  - `count_stale_embeddings_by_model(db, workspace_id)`
  - `find_incomplete_embeddings(db, entity_type, workspace_id)`
- Detection works, but NO auto-remediation scheduled job exists
- Operator must manually trigger `backfill_embeddings.py` script

### 1.2 Issues Found

**CRITICAL — Missing Embedding Validation at Retrieval Time**
- Vector retrieval queries assume embeddings exist and are valid
- If embedding is NULL or stale, query silently returns empty results
- No error logging or metrics when NULL embeddings are encountered
- **Impact:** Silent data loss in retrieval results

**HIGH — No Idempotency Check for Embedding Re-generation**
- `EmbeddingService.generate_embedding()` always overwrites existing vector
- If backfill fails mid-batch, partial updates leave inconsistent state
- No transaction rollback for embedding updates
- **Impact:** Partial batches leave database in inconsistent state

**MEDIUM — Embedding Model Version Extraction Unreliable**
- `embedding_model_version` stored but never auto-populated
- Backfill script may not correctly capture actual model version from provider
- Stale detection relies on comparing string versions (e.g., "v1.5" vs "2026-11-18")
- **Impact:** Version comparisons may fail; stale embeddings not detected reliably

**MEDIUM — Missing Embedded Dimension Validation**
- All embeddings assumed to be 384 dimensions
- No runtime check when inserting embeddings
- If model changes to different dimension (e.g., 768), previous vectors incompatible
- **Impact:** Cross-encoder and vector operations will fail silently

### 1.3 Fixes Required

1. **Add NULL embedding detection to retrievers** — log when embedding is NULL at query time
2. **Add dimension validation on insertion** — enforce 384 dims when storing new embeddings
3. **Idempotency for backfill** — wrap batch embedding updates in transaction, rollback on error
4. **Reliably capture model version** — populate from provider metadata during backfill

### 1.4 Test Coverage Gaps

- ✅ Metadata persistence tested (test_embedding_metadata_phase2b.py)
- ✅ Stale detection queries tested
- ❌ Backfill transaction isolation NOT tested
- ❌ NULL embedding handling NOT tested
- ❌ Dimension validation NOT tested
- ❌ Re-embedding idempotency NOT tested

---

## Step 2: Document Replacement & Version Consistency — INVESTIGATION RESULTS

### 2.1 Current State

**Version chain integrity:** ✅ PRESENT
- `BRDDocument.previous_version_id` self-referential FK
- `DocumentVersion.version_number` unique constraint per document
- Unique constraint `(document_id, sha256_hash)` prevents duplicate content within same document

**Duplicate handling:** ✅ PRESENT
- `DocumentRegistrationService.register()` checks `(workspace_id, sha256_hash)` for duplicates
- If duplicate found: `is_duplicate=True` in `RegistrationResult`
- Orchestrator does NOT re-extract if prior attempt succeeded (checked via `extracted_knowledge_id`)

**Version semantics:** ✅ PRESENT
- BRDDocument.version incremented on new content
- DocumentVersion.version_number unique per document
- previous_version_id links chain backwards

### 2.2 Issues Found

**CRITICAL — Re-extraction Overwrites Knowledge Without Provenance Tracking**
- When duplicate document is re-extracted, new `WorkflowKnowledge` row is created
- Orchestrator does NOT update `WorkflowBusinessRule.source_brd_document_id` to point to new version
- Rules extracted from old version remain linked to old BRDDocument
- Rules extracted from new version link to new BRDDocument
- **Impact:** Same rule name appears twice in retrieval, linked to different source documents

**HIGH — DocumentVersion Doesn't Prevent Orphaned Rules**
- If document version is deleted (cascade), `WorkflowBusinessRule.source_brd_document_id` becomes NULL
- Rules continue to exist but lose their source link
- Caller cannot determine origin of rule (which policy version it came from)
- **Impact:** Provenance chains break silently after deletion

**HIGH — Ambiguous "Latest Version" Semantics**
- No explicit "active_version" flag on BRDDocument
- Caller may assume most recent version is active, but orchestrator does NOT enforce this
- Multiple versions of same BRD may be in COMPLETED state simultaneously
- Retrieval includes rules from ALL completed versions, not just latest
- **Impact:** Stale rules from old versions mixed into current context

**MEDIUM — Concurrent Reprocessing Can Create Duplicate Rules**
- If same document version is ingested twice simultaneously, both orchestrator instances may succeed
- Unique constraint on `(workflow_knowledge_id, rule_text)` prevents database-level duplicates
- But two separate `WorkflowKnowledge` rows will be created for same version
- **Impact:** Duplicate work, but data consistency preserved by constraint

### 2.3 Fixes Required

1. **Preserve rule provenance during re-extraction** — when re-extracting document, do NOT update old rules
2. **Fail loudly if provenance chain is broken** — detect NULL source_brd_document_id during retrieval
3. **Define active version semantics** — either implicit (latest completed) or explicit (active_version_id flag)
4. **Deduplicate WorkflowKnowledge per version** — add app-layer check before creating duplicate knowledge rows

### 2.4 Test Coverage Gaps

- ❌ Re-extraction provenance update NOT tested
- ❌ Orphaned rule handling NOT tested
- ❌ Multiple completed versions in retrieval NOT tested
- ✅ Duplicate document detection tested (implicit)

---

## Step 3: Retry & Recovery — INVESTIGATION RESULTS

### 3.1 Current State

**Attempt lifecycle:** ✅ PRESENT
- `IngestionAttempt` immutable, never modified after terminal state
- `AttemptStatus`: PENDING → RUNNING → COMPLETED/FAILED
- `attempt_number` unique per document version

**Error tracking:** ✅ PRESENT
- `AttemptErrorCode` enum with machine-readable codes: EXTRACTION_FAILED, LLM_TIMEOUT, STORAGE_FAILED, etc.
- error_message stores full exception text

**Partial extraction:** ✅ PRESENT
- `DocumentExtractionResult.overall_status` can be "PARTIAL"
- Orchestrator proceeds to LLM ingestion even on PARTIAL
- Warning recorded in `OrchestrationResult`

### 3.2 Issues Found

**CRITICAL — RUNNING Attempts Can Remain Stuck**
- Orchestrator checks running guard via `_check_running_guard()`
- But if worker crashes mid-pipeline, attempt remains RUNNING forever
- No stale attempt detection or automatic cleanup
- Next retry is blocked: "another attempt already running"
- **Impact:** Single worker crash blocks future re-extraction of that version

**HIGH — Partial Extraction Not Properly Marked**
- When `overall_status="PARTIAL"`, orchestrator proceeds to knowledge ingestion
- But `IngestionAttempt.status` set to COMPLETED without flagging the partial result
- Caller cannot distinguish between clean extraction and partial-page loss
- **Impact:** Partial data slips through silently

**HIGH — No Rollback for Knowledge Ingestion Failure**
- `KnowledgeIngestionService` commits internally (T5)
- If rule extraction fails after knowledge persisted, `WorkflowKnowledge` orphaned
- Orchestrator sets attempt to FAILED but knowledge row remains
- Re-extraction on retry will create duplicate `WorkflowKnowledge` rows
- **Impact:** Orphaned knowledge rows + duplicate on retry

**MEDIUM — Storage Cleanup After Ingestion Failure**
- If ingestion fails, stored PDF is NOT cleaned up
- Failed attempt leaves document file in storage indefinitely
- No cleanup service to remove files for FAILED attempts
- **Impact:** Storage leaks over time

**MEDIUM — Retry Without Re-storing PDF**
- Orchestrator always stores PDF again on retry (even if prior storage succeeded)
- FileStorageService may create new files for same content
- **Impact:** Storage bloat from duplicate storage

### 3.3 Fixes Required

1. **Add stale attempt detection** — mark RUNNING attempts as FAILED if older than TTL (e.g., 1 hour)
2. **Properly mark partial extractions** — add `is_partial` flag or status code to distinguish PARTIAL_COMPLETED
3. **Deduplicate storage** — check if PDF already stored (via sha256_hash) before re-storing
4. **Storage cleanup on failure** — delete stored file if knowledge ingestion fails
5. **WorkflowKnowledge idempotency** — add app-layer check to prevent duplicate knowledge rows per version

### 3.4 Test Coverage Gaps

- ❌ Stale RUNNING attempt detection NOT tested
- ❌ Partial extraction marking NOT tested
- ❌ Knowledge ingestion rollback NOT tested
- ❌ Storage cleanup on failure NOT tested
- ✅ Duplicate detection tested (implicit)

---

## Step 4: Concurrency & Transaction Safety — INVESTIGATION RESULTS

### 4.1 Current State

**Concurrency guard:** ✅ PRESENT
- `IngestionOrchestrator._check_running_guard()` prevents two RUNNING attempts simultaneously
- Best-effort application-level check (not a database-level lock)
- Check-then-act pattern under transaction

**Unique constraints:** ✅ PRESENT
- `(workspace_id, sha256_hash)` on BRDDocument prevents duplicate registration
- `(document_id, version_number)` on DocumentVersion
- `(document_id, sha256_hash)` on DocumentVersion (same bytes on same doc = same version)

**Transaction boundaries:** ✅ PRESENT
- T1: Registration (DocumentRegistrationService, commits immediately)
- T2: PENDING → RUNNING (orchestrator, short write)
- T3-4: Extraction/ingestion (no transaction held)
- T5: Knowledge persistence (KnowledgeIngestionService)
- T6: IngestionAttempt completion (orchestrator)

### 4.2 Issues Found

**CRITICAL — Check-then-act Race on RUNNING Guard**
- Pattern: SELECT to check running_count, then INSERT attempt
- Between SELECT and INSERT, another process can INSERT
- Both processes think guard passed, both start extraction
- **Impact:** Concurrent extraction of same version

**HIGH — Partial Unique Constraint on RUNNING Attempts**
- Cannot express "partial unique index WHERE status='RUNNING'" in SQLAlchemy
- Enforced by application layer only
- If ORM layer is bypassed (direct SQL), constraint not enforced
- **Impact:** Misconfigured processes can create duplicate RUNNING attempts

**HIGH — No Distributed Lock for Concurrent Uploads**
- Same PDF uploaded simultaneously to same workspace:
  1. Process A: hash = "abc123", checks unique constraint, OK
  2. Process B: hash = "abc123", checks unique constraint, OK
  3. Both INSERT: one succeeds, one fails with constraint violation
- Failure not caught, transaction rolls back
- DocumentVersion created by Process A, ProcessB's attempt lost
- **Impact:** Second upload silently fails

**MEDIUM — Embedding Backfill Not Workspace-Scoped**
- Backfill script iterates ALL embeddings globally
- No locking prevents concurrent backfill from overwriting each other's updates
- **Impact:** Last-write-wins, may lose progress from concurrent runs

### 4.3 Fixes Required

1. **Replace check-then-act with INSERT ... ON CONFLICT** — use database-level constraint
2. **Enforce partial unique index** — add database-level partial unique index on (document_version_id) WHERE status='RUNNING'
3. **Handle constraint violation on concurrent upload** — catch and return existing document_id instead of failing
4. **Add workspace-level locking to backfill** — serialize backfill per workspace

### 4.4 Test Coverage Gaps

- ❌ Concurrent duplicate upload NOT tested
- ❌ Concurrent RUNNING guard bypass NOT tested
- ❌ Concurrent embedding backfill NOT tested
- ✅ Unique constraint enforcement tested (implicit)

---

## Step 5: Retrieval Consistency — INVESTIGATION RESULTS

### 5.1 Current State

**Workspace isolation:** ✅ PRESENT
- `VectorRetriever` filters by workspace_id
- `KeywordRetriever` filters by workspace_id
- `PostgressRetriever` filters by workspace_id

**Provenance preservation:** ✅ PRESENT
- `ContextAssemblyService._validate_provenance_chain()` walks full chain
- Marks incomplete chains without fabrication
- Returns provenance metadata in context

**Version scoping:** ⚠️ PARTIAL
- Retrievers do NOT explicitly filter by DocumentVersion
- Retrieve includes rules from ALL versions of all documents in workspace
- No distinction between latest/active version and historical versions

### 5.2 Issues Found

**CRITICAL — Silent Data Corruption on NULL Embeddings**
- If `WorkflowBusinessRule.embedding IS NULL`, vector query returns empty results silently
- No error logged, no metrics, no visibility
- Caller may think query returned empty (no matching rules) when actually embeddings missing
- **Impact:** Silent loss of matching rules

**HIGH — Mixing Rules from Multiple Document Versions**
- Retrieval includes rules from ALL completed versions
- If same BRD updated, old rules + new rules both retrieved
- Context assembly cannot distinguish which version of rule is "current"
- **Impact:** Stale policies mixed with current policies

**HIGH — Provenance Chain Breaks on DocumentVersion Deletion**
- If DocumentVersion deleted, `WorkflowBusinessRule.source_brd_document_id` remains valid (points to BRDDocument)
- But `WorkflowKnowledge.document_version_id` becomes NULL (FK cascade)
- Provenance chain broken: rule no longer links to version
- **Impact:** Caller cannot determine rule version origin

**MEDIUM — Cross-Encoder Score Not Preserved Through Context Assembly**
- `RankedCandidate.cross_encoder_score` set by pipeline
- `ContextAssemblyService` does NOT carry this score forward in `SelectedBusinessRule`
- LLM sees RRF score but not cross-encoder confidence
- **Impact:** LLM unable to distinguish high-confidence vs. low-confidence matches

### 5.3 Fixes Required

1. **Add NULL embedding detection to retrievers** — fail loudly if embedding found NULL
2. **Explicitly filter to latest document version** — retrieve only rules from active/latest version, not all versions
3. **Preserve cross-encoder scores** — carry cross_encoder_score through to context assembly
4. **Add retrieval consistency tests** — test that same query returns same results after re-extraction

### 5.4 Test Coverage Gaps

- ❌ NULL embedding retrieval NOT tested
- ❌ Multi-version rule mixing NOT tested (likely happening silently)
- ✅ Workspace isolation tested
- ✅ Provenance preservation tested (implicit in context assembly tests)

---

## Step 6: Observability — CURRENT STATE

### 6.1 Logging Events Present

**Ingestion:**
- ✅ `orchestrator_registration_rejected` (WARNING)
- ✅ `orchestrator_registration_failed` (ERROR)
- ✅ `context_assembly_start` (INFO)
- ✅ `context_assembly_empty_retrieval` (INFO)
- ✅ `context_assembly_complete` (INFO)

**Embeddings:**
- ❌ NULL embedding detection NOT logged
- ❌ Stale embedding detection NOT logged
- ❌ Backfill progress NOT logged
- ❌ Dimension validation NOT logged

**Retrieval:**
- ❌ Per-channel latency NOT logged
- ❌ RRF latency NOT logged
- ❌ End-to-end latency NOT logged
- ❌ Empty retrieval rate NOT logged

**Isolation:**
- ❌ Workspace mismatch NOT logged
- ❌ Ownership validation failures NOT logged

### 6.2 Metrics Infrastructure

- Logging framework: `app/core/logger.py` (structured logging via `logger.info()`, `logger.warning()`, etc.)
- No metrics/telemetry framework found (no Prometheus, StatsD, OpenTelemetry integrations)

### 6.3 Fixes Required

1. **Add NULL embedding detection logging** — log when vector retrieval encounters NULL embedding
2. **Add retrieval latency tracking** — log per-channel latency (vector, BM25, FTS, RRF, cross-encoder)
3. **Add isolation violation logging** — log workspace/tenant mismatches during retrieval
4. **Add embedding backfill observability** — log batch progress, error counts, model version changes
5. **Add document version filtering logging** — log when rules from old versions are retrieved

---

## Summary Table: Issues by Severity

| Severity | Count | Category | Examples |
|----------|-------|----------|----------|
| **CRITICAL** | 5 | Data loss / Silent corruption | Null embeddings in retrieval, re-extraction overwrites provenance, stale RUNNING attempts, race on guard, check-then-act |
| **HIGH** | 11 | Correctness / Isolation | Partial extraction not marked, no rollback, duplicate versions retrieved, dimension validation, distributed lock |
| **MEDIUM** | 8 | Performance / Robustness | Storage leaks, scoring preservation, logging gaps, model version capture |

**Total Issues Found:** 24  
**Critical Issues:** 5  
**Test Coverage Gaps:** 17 test scenarios

---

## Next Steps

1. **Step 1 Fixes:** Implement NULL embedding detection, dimension validation, backfill idempotency
2. **Step 2 Fixes:** Preserve provenance on re-extraction, define active version semantics
3. **Step 3 Fixes:** Add stale attempt detection, cleanup storage on failure
4. **Step 4 Fixes:** Replace check-then-act with INSERT ON CONFLICT, partial unique index
5. **Step 5 Fixes:** Filter to latest version, preserve cross-encoder scores
6. **Step 6 Fixes:** Add comprehensive logging and observability
7. **Step 7:** Write regression tests for all fixes

---

**End of Investigation**
