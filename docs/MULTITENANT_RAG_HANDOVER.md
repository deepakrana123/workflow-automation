# Multi-Tenant RAG Pipeline — Complete Engineering Handover
## FlowOS AI · Personal Loan Knowledge Pipeline

> **Scope freeze:** This document covers only the Multi-Tenant RAG Pipeline for Personal Loan (PL) Knowledge.
> Read alongside `docs/RAG_PIPELINE_FUNCTION_REFERENCE.md` for function-level detail.

---

## 1. Executive Summary

The Multi-Tenant RAG pipeline extracts structured business knowledge from bank-uploaded BRD PDFs, maps extracted actions and triggers to a global capability catalog, stores business rules per tenant, and provides hybrid retrieval (vector + BM25 + FTS) scoped to each tenant's workspace.

**What works correctly today:**
- Multimodal PDF extraction (text, table, image, appendix) with per-page status tracking
- LLM extraction with Gemini → OpenRouter → waterfall fallback
- Pydantic schema validation with LLM output normalization
- Action mapping with full diagnostics (confidence, top-K candidates, query text)
- Hybrid retrieval (vector + BM25 + Postgres FTS + RRF + cross-encoder) for actions/triggers
- Rule evaluation at execution time (`evaluate_condition`, `RuntimeRuleEngine`)
- Workspace hierarchy (`global → region → zone → branch`)
- Rule inheritance (`resolve_effective_rules`)
- RBAC permission checking (`PermissionChecker.can()`)

**What is broken or missing:**
- No authentication on ingestion, execution, or workflow endpoints
- Action/trigger mapping processes ALL workspaces, not the uploading workspace
- Trigger mapping diagnostics silently dropped (no DB columns)
- Rule RAG (vector/BM25/FTS retrieval for rules) exists only as an eval script — no API
- IVFFlat index on rule embeddings dropped by latest migration, not recreated
- RRF k=20 at ingestion vs k=60 at runtime — same query ranks differently
- Debug artifact files have fixed names — concurrent ingestions corrupt each other

---

## 2. Current Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INGESTION PIPELINE                                    │
│                                                                              │
│  POST /api/knowledge-ingestion/upload                                        │
│    ↓ workspace_id from Form (no auth) ⚠️                                    │
│  KnowledgeIngestionService.ingest()                                          │
│    ↓                           ↓                              ↓              │
│  MultiModalDocumentExtractor  WorkflowExtractor          WorkflowRepository  │
│  (PDF → structured text)      (LLM → WorkflowExtraction) (saves 5 tables)   │
│    ↓                                                          ↓              │
│  PageClassifier          PromptManager + LLMManager    workflow_knowledge    │
│  ContinuationDetector    (Gemini→OpenRouter→waterfall)  workflow_action_mapping│
│  TableImageExtractor                                    workflow_trigger_mapping│
│  AppendixExtractor                                      workflow_business_rule│
│                                                         workflow_actors      │
│    ↓                                                                         │
│  EmbeddingMapper.map_actions() / map_triggers()                              │
│    → get_unmapped_actions() [NO workspace filter ⚠️]                        │
│    → RetrievalPipeline: Vector + BM25 + Postgres → RRF(k=20) → CrossEncoder │
│    → update_action_mapping() / mark_action_unmapped()                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        RUNTIME RETRIEVAL                                     │
│                                                                              │
│  POST /api/runtime/retrieve (requires X-User-Id + X-Workspace-Id headers)   │
│    ↓                                                                         │
│  WorkflowRuntimeOrchestrator                                                 │
│    → RBACCapabilityResolver → allowed_action_ids                             │
│    → ScopedRetrievalService.retrieve()                                       │
│        → RetrievalPipeline (singleton, k=60) ⚠️ k mismatch                 │
│        → Vector + BM25 + Postgres → RRF(k=60) → CrossEncoder                │
│        → RBAC filter (post-rerank) → top_k authorized                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        RULE RAG (EVAL ONLY — NOT WIRED TO API)               │
│                                                                              │
│  scripts/test_rule_retrieval.py --workspace-id 2                             │
│    → extract_rich_intent(query)                                              │
│    → MetadataCandidateSelector → allowed_ids (workspace-scoped) ✓           │
│    → RuleVectorRetriever + RuleKeywordRetriever + RulePostgresRetriever      │
│    → RRF(k=60) → EvidenceValidator (annotation, no re-sort)                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. End-to-End Call Graph

```
PDF Upload
│
├── [routes/knowledge_ingestion.py] upload_brds()
│     workspace_id = Form(1)  ← no auth ⚠️
│     validates workspace exists
│
├── [knowledge_ingestions/service.py] KnowledgeIngestionService.ingest()
│     │
│     ├── [multimodal_extractor.py] MultiModalDocumentExtractor.extract()
│     │     ├── [page_classifier.py] PageClassifier.classify()     ← local, no LLM
│     │     │     └── classifies: text | table | image | appendix
│     │     │
│     │     ├── ThreadPoolExecutor(3):
│     │     │     Thread A: _extract_body_text()   ← already done, zero cost
│     │     │     Thread B: _extract_visual()
│     │     │     │   ├── build_page_metadata() per page
│     │     │     │   ├── ContinuationDetector → build_extraction_groups()
│     │     │     │   └── TableImageExtractor.extract_groups()
│     │     │     │         └── per group: render PNG → VisionProvider.extract_page()
│     │     │     │               retries: Retry-After | exp backoff (3 attempts)
│     │     │     │               saves: PageExtractionResult {SUCCESS|EMPTY|FAILED|RATE_LIMITED}
│     │     │     Thread C: AppendixExtractor.extract()
│     │     │               └── TextProvider.generate(combined_appendix_text)
│     │     │
│     │     └── _merge_results() → "=== DOCUMENT BODY ===" + tables + appendix
│     │
│     ├── [worfklow_extractors.py] WorkflowExtractor.extract()
│     │     ├── PromptManager.build(WORKFLOW_EXTRACTION, {schema, text})
│     │     ├── LLM waterfall: Gemini → OpenRouter → general waterfall
│     │     ├── WorkflowExtraction.model_validate_json()   ← Pydantic + normalizers
│     │     └── saves debug files (FIXED NAMES ⚠️)
│     │
│     ├── [workflow_repository.py] WorkflowRepository.save()
│     │     ├── INSERT workflow_knowledge (workspace_id here)
│     │     ├── INSERT workflow_trigger_mapping × N (status=PENDING)
│     │     ├── INSERT workflow_action_mapping × N (status=PENDING)
│     │     ├── INSERT workflow_business_rule × N (embedding=NULL)
│     │     └── INSERT workflow_actors × N
│     │
│     ├── [embedding_mapper.py] EmbeddingMapper.map_actions()
│     │     ├── get_unmapped_actions() ← ALL workspaces ⚠️
│     │     ├── per action:
│     │     │     _normalize_query() → SentenceTransformer.encode() → 384-dim
│     │     │     pipeline.retrieve_actions(query, embedding)
│     │     │       VectorRetriever → DB cosine distance (global catalog)
│     │     │       KeywordRetriever → BM25 (global catalog)
│     │     │       PostgressRetriever → FTS (global catalog)
│     │     │       ReciprocalRankFusion(k=20).fuse()
│     │     │       CrossEncoderReRanker(top_k=50).rerank()   ← re-sorts by logit
│     │     │     MappingDecisionEngine.decide() → sigmoid(score) >= 0.40?
│     │     └── update_action_mapping() or mark_action_unmapped()
│     │
│     └── EmbeddingMapper.map_triggers()
│           └── [same pattern — trigger diagnostics dropped ⚠️]
│
└── db.commit()

─────────────────────────────────────────────────────────────────────────────

Runtime Query (workspace-scoped)
│
├── [routes/runtime.py] POST /runtime/retrieve
│     _require_caller() → user_id, workspace_id from headers
│
├── [runtime/orchestrator.py] WorkflowRuntimeOrchestrator.retrieve()
│     ├── RBACCapabilityResolver → allowed_action_ids for user+workspace
│     └── ScopedRetrievalService.retrieve(query, ctx, top_k)
│           ├── embedder(query) → 384-dim
│           ├── pipeline.retrieve_actions(query, embedding, limit=50)
│           │     [singleton pipeline with k=60 ⚠️]
│           │     Vector + BM25 + Postgres → RRF(k=60) → CrossEncoder
│           ├── RBAC filter: action_id NOT in allowed_ids → unauthorized
│           └── return top_k authorized candidates

─────────────────────────────────────────────────────────────────────────────

Rule RAG (eval script only — not an API)
│
└── scripts/test_rule_retrieval.py
      ├── extract_rich_intent(query) → {zone, applicant_type, policy_intent, raw_query}
      ├── MetadataCandidateSelector.select_candidates(intent)
      │     reads workflow_rule_metadata WHERE workspace_id=X ✓
      │     → allowed_ids set
      ├── RuleVectorRetriever.search(embedding, limit, allowed_ids)   DB-level filter ✓
      ├── RuleKeywordRetriever.search(query, limit, allowed_ids)       pre-filter ✓
      ├── RulePostgresRetriever.search(query, limit, allowed_ids)      SQL-level ✓
      ├── ReciprocalRankFusion(k=60).fuse()
      └── EvidenceValidator.apply()   annotates but does NOT re-sort
```

---

## 4. Artifact Inventory

### A. Source Files

| File | Purpose | Status |
|---|---|---|
| `app/routes/knowledge_ingestion.py` | BRD upload endpoint | Active, no auth ⚠️ |
| `app/knowledge_ingestions/service.py` | Ingestion orchestrator | Active |
| `app/knowledge_ingestions/multimodal_extractor.py` | Parallel PDF extraction | Active |
| `app/knowledge_ingestions/page_classifier.py` | Page type classification | Active |
| `app/knowledge_ingestions/table_image_extractor.py` | Vision extraction with retry | Active |
| `app/knowledge_ingestions/appendix_extractor.py` | Appendix text extraction | Active |
| `app/knowledge_ingestions/continuation_detector.py` | Multi-page table detection | Active |
| `app/knowledge_ingestions/worfklow_extractors.py` | LLM workflow extraction | Active |
| `app/knowledge_ingestions/schemas.py` | Pydantic extraction schemas | Active |
| `app/knowledge_ingestions/workflow_repository.py` | Ingestion persistence | Active, unscoped ⚠️ |
| `app/knowledge_ingestions/embedding_mapper.py` | Action/trigger mapping | Active, unscoped ⚠️ |
| `app/knowledge_ingestions/rule_repository.py` | Rule retrieval (workspace-scoped) | Active |
| `app/knowledge_ingestions/providers/base.py` | Provider ABC + exceptions | Active |
| `app/knowledge_ingestions/providers/registry.py` | Provider factory registry | Active |
| `app/knowledge_ingestions/providers/gemini.py` | Gemini vision + text | Active |
| `app/knowledge_ingestions/providers/openrouter.py` | OpenRouter vision + text | Active |
| `app/retrieval/pipeline.py` | Action/trigger retrieval pipeline | Active |
| `app/retrieval/vector_retriever.py` | pgvector cosine distance | Active |
| `app/retrieval/keyword_retriever.py` | BM25 in-memory retrieval | Active |
| `app/retrieval/postgress_retriever.py` | PostgreSQL FTS | Active |
| `app/retrieval/reciprocal_rank_fusion.py` | RRF fusion | Active |
| `app/retrieval/cross_encoder.py` | Cross-encoder re-ranking | Active |
| `app/retrieval/decision_engine.py` | Confidence threshold gate | Active |
| `app/retrieval/confidene_estimator.py` | sigmoid(cross_encoder_score) | Active |
| `app/retrieval/unknown_detector.py` | Threshold comparison | Active |
| `app/retrieval/thresholds.py` | Threshold constants | Active |
| `app/retrieval/hybrid_retriever.py` | Thin wrapper for eval | Active (eval only) |
| `app/retrieval/rule_vector_retriever.py` | Rule pgvector retrieval | Active (scripts only) |
| `app/retrieval/rule_keyword_retriever.py` | Rule BM25 retrieval | Active (scripts only) |
| `app/retrieval/rule_postgres_retriever.py` | Rule FTS retrieval | Active (scripts only) |
| `app/retrieval/query_intent.py` | Intent extraction (rule queries) | Active (scripts only) |
| `app/retrieval/models.py` | RetrievalCandidate, RankedCandidate | Active |
| `app/rbac/rule_extractor.py` | BRD text → BusinessRuleDefinition | Active (manual API) |
| `app/rbac/rule_inheritance.py` | resolve_effective_rules() | Active |
| `app/rbac/hierarchy.py` | get_ancestor_chain() | Active |
| `app/rbac/permission_checker.py` | RBAC can() check | Active |
| `app/runtime/scoped_retrieval.py` | RBAC-filtered retrieval | Active |
| `app/runtime/dependencies.py` | Singleton pipeline (k=60) ⚠️ | Active |
| `app/runtime/rule_engine.py` | RuntimeRuleEngine | Active |
| `scripts/test_rule_retrieval.py` | Rule RAG eval (not API) | Active (scripts only) |
| `scripts/backfill_embeddings.py` | Embedding generation | Manual script |
| `scripts/extract_rule_metadata.py` | Rule metadata extraction | Manual script |
| `scripts/remap_unmapped.py` | Re-run action/trigger mapping | Manual script |

### B. Database Models

| Model file | Table | Workspace-scoped? |
|---|---|---|
| `app/models/workspace.py` | `workspaces` | Self (is the tenant) |
| `app/models/workflow_knowledge.py` | `workflow_knowledge` | ✓ `workspace_id FK` |
| `app/models/workflow_action_mapping.py` | `workflow_action_mapping` | ✓ via FK chain |
| `app/models/workflow_trigger_mapping.py` | `workflow_trigger_mapping` | ✓ via FK chain |
| `app/models/workflow_business_rule.py` | `workflow_business_rule` | ✓ via FK chain |
| `app/models/workflow_actor.py` | `workflow_actors` | ✓ via FK chain |
| `app/models/business_rule_definition.py` | `business_rule_definitions` | ✓ `scope_workspace_id` |
| `app/models/workflow_rule_metadata.py` | `workflow_rule_metadata` | ✓ via FK → `workflow_business_rule` |
| `app/models/role_assignment.py` | `role_assignments` | ✓ `workspace_id FK` |
| `app/models/action_definitions.py` | `action_definitions` | ✗ GLOBAL CATALOG |
| `app/models/trigger_definitions.py` | `trigger_definitions` | ✗ GLOBAL CATALOG |

### C. Alembic Migrations (in dependency order)

```
868d6c9195f3  fresh_baseline         ← creates all base tables
  ↓
a1b2c3d4e5f6  resize_embeddings_to_384   ← action/trigger embeddings 1024→384
  ↓
b2c3d4e5f6a7  add_embedding_to_wbr   ← adds Vector(384) + IVFFlat to workflow_business_rule
  ↓
99e9cf39be25  add_workflow_rule_metadata_table   ← adds workflow_rule_metadata ⚠️ drops IVFFlat
```

**⚠️ Migration 99e9cf39be25 drops the IVFFlat index without recreating it:**
```python
# In upgrade():
op.drop_index('ix_workflow_business_rule_embedding', ...)
# Missing: CREATE INDEX replacement
```

### D. Prompts

| File | Used by | Purpose |
|---|---|---|
| `app/prompts/extractor.md` | `WorkflowExtractor` | Main BRD → workflow extraction |
| `app/prompts/table_extraction.md` | `TableImageExtractor` | Vision: table pages |
| `app/prompts/image_extraction.md` | `TableImageExtractor` | Vision: diagram pages |
| `app/prompts/appendix_extraction.md` | `AppendixExtractor` | Text: appendix pages |

---

## 5. Database Schema and Migration Map

### Key tables for RAG pipeline

```sql
-- GLOBAL CATALOG (not tenant-specific)
action_definitions
  id, name UNIQUE, display_name, description, workflow_type
  aliases JSONB, input_schema JSONB, output_schema JSONB, execution_template JSONB
  active BOOL, is_state_changing BOOL
  embedding VECTOR(384)   ← indexed by pgvector

trigger_definitions
  id, name UNIQUE, display_name, description, workflow_type
  aliases JSONB, active BOOL
  embedding VECTOR(384)

-- TENANT KNOWLEDGE
workspaces
  id, name UNIQUE, level (global|region|zone|branch), parent_id FK→self

workflow_knowledge                          ← one row per BRD upload
  id, workflow_name, summary, source_document
  workspace_id FK→workspaces NOT NULL       ← TENANT ANCHOR

workflow_action_mapping                     ← one row per extracted action
  id, workflow_knowledge_id FK, extract_name, description
  status ENUM(PENDING|MAPPED|UNMAPPED|FAILED)
  matched_action_definition_id FK→action_definitions (nullable)
  similarity_score FLOAT, confidence FLOAT
  query_text TEXT, top_candidates JSONB     ← diagnostics
  -- snapshot columns (copied from ActionDefinition at mapping time):
  action_name, display_name, catalog_description, aliases JSONB
  workflow_type, input_schema JSONB, output_schema JSONB, execution_template JSONB
  applicable_rules JSONB, responsible_actors JSONB
  embedding VECTOR(384)

workflow_trigger_mapping                    ← one row per extracted trigger
  id, workflow_knowledge_id FK, extracted_name, description
  status ENUM(PENDING|MAPPED|UNMAPPED|FAILED)
  matched_trigger_definition_id FK→trigger_definitions (nullable)
  similarity_score FLOAT, confidence FLOAT
  -- snapshot columns: trigger_name, display_name, catalog_description, aliases JSONB
  -- ⚠️ NO query_text, NO top_candidates columns

workflow_business_rule                      ← one row per extracted rule
  id, workflow_knowledge_id FK
  rule TEXT NOT NULL, condition TEXT, outcome TEXT
  responsible_role TEXT, threshold TEXT      ← often NULL despite LLM guidance
  embedding VECTOR(384)                      ← nullable, populated by backfill script

workflow_actors                             ← one row per extracted actor
  id, workflow_knowledge_id FK, name, role

-- STRUCTURED / EVALUABLE RULES
business_rule_definitions
  id, scope_workspace_id FK→workspaces NOT NULL
  source_workflow_knowledge_id FK (nullable)
  field VARCHAR(255), op VARCHAR(20), value JSONB   ← NULL = description-only
  description TEXT NOT NULL
  allowed_roles JSONB, locked BOOL, active BOOL

-- RULE METADATA (for RAG Stage 2 pre-filter)
workflow_rule_metadata
  id, rule_id FK→workflow_business_rule CASCADE
  policy_id, policy_level (GLOBAL|ZONE|REGION|BRANCH)
  product, zone, applicant_type, rule_type, status (ACTIVE|EXPIRED|PROPOSED|UNKNOWN)
  effective_from DATE, effective_to DATE, metadata_source
  CHECK constraints on policy_level and status
  UNIQUE(rule_id)
```

---

## 6. Tenant/Workspace Isolation Matrix

| Component | Tenant filter | Enforcement location | Pre or post ranking | Verified by test? |
|---|---|---|---|---|
| `WorkflowRepository.save()` | `workspace_id` on `workflow_knowledge` | Insert | N/A | No |
| `get_unmapped_actions()` | ❌ NONE | — | — | No |
| `get_unmapped_triggers()` | ❌ NONE | — | — | No |
| `get_unmapped_actions_for_workspace()` | `workspace_id` via JOIN | SQL | N/A | No |
| `VectorRetriever` (actions) | ❌ Global catalog | No filter | — | No |
| `KeywordRetriever` (actions) | ❌ Global catalog | No filter | — | No |
| `PostgressRetriever` (actions) | ❌ Global catalog | No filter | — | No |
| `ScopedRetrievalService` | RBAC `allowed_action_ids` | Post-rerank Python | **After** | No |
| `RuleVectorRetriever` | `workspace_id` via JOIN | SQL `IN allowed_ids` | **Before** ranking | No |
| `RuleKeywordRetriever` | `workspace_id` on index build | Pre-filter scores | **Before** ranking | No |
| `RulePostgresRetriever` | `workspace_id` + `ANY(:ids)` | SQL | **Before** ranking | No |
| `MetadataCandidateSelector` | `workspace_id` via JOIN | SQL | Pre-retrieval | No |
| `resolve_effective_rules()` | `scope_workspace_id IN chain` | SQL | N/A | No |
| `PermissionChecker.can()` | `workspace_id IN ancestor_chain` | SQL | N/A | No |
| `analytics endpoints` | ❌ NONE | No filter anywhere | — | No |
| `traces endpoints` | ❌ NONE | No filter anywhere | — | No |
| `WorkflowExecution` table | ❌ No workspace_id column | — | — | No |
| `TraceEvent` table | ❌ No workspace_id column | — | — | No |
| Singleton `KeywordRetriever` | ❌ Global BM25 index shared | Constructor | — | No |

**Global vs tenant-owned data:**
- **Global catalog:** `action_definitions`, `trigger_definitions` — shared across all tenants. Intentional.
- **Tenant knowledge:** everything rooted in `workflow_knowledge.workspace_id`
- **Tenant rules:** `business_rule_definitions.scope_workspace_id`
- **Inherited rules:** global workspace rules visible to all via `resolve_effective_rules()`

---

## 7. Existing Tests and Coverage

### Only test file: `tests/test_evidence_validator.py`
44–45 unit tests, all isolated (no DB). Run: `.venv312\Scripts\python.exe -m pytest tests/test_evidence_validator.py -v`

| Test class | Covers | Count |
|---|---|---|
| `TestMetadataRowIsActive` | Status normalization, effective dates, uncertain status | 14 |
| `TestThresholdValidation` | CIBIL comparisons, cross-metric rejection, date/year guards, FOIR, direction | 15 |
| `TestScopeMatching` | zone match/miss/unknown, all-open rule, conflicting product | 7 |
| `TestCandidateSelector` | Overlap counts, expired/uncertain exclusion, fallback, zone conflict | 6 |
| `TestExceptionReviewRequired` | No EXPLICIT_OVERRIDE label, verification required in detail | 2 |
| `TestApplyPreservesRRFOrder` | THRESHOLD_FAIL does not demote candidates | 1 |

### Missing tests (critical for multi-tenant correctness)

| Missing test | Priority |
|---|---|
| `get_unmapped_actions()` returns only current workspace rows | P0 |
| Bank A upload does not appear in Bank B's mapping queue | P0 |
| Trigger diagnostics are persisted (requires column migration) | P0 |
| Rule vector search returns only workspace-N rules | P0 |
| Rule BM25 index built per workspace, not globally | P1 |
| Re-upload of same BRD creates new rows, not duplicate-merged | P1 |
| `resolve_effective_rules()` returns global + zone + branch chain | P1 |
| `PermissionChecker` ancestor chain lookup | P1 |
| RRF k=20 at ingestion vs k=60 at runtime produces same winner for confident matches | P2 |
| IVFFlat index exists after migration 99e9cf39be25 | P2 |
| Debug artifact names are unique per ingestion run | P2 |
| `MetadataCandidateSelector` excludes EXPIRED and uncertain-status rules | P1 |
| `EvidenceValidator` does not demote THRESHOLD_FAIL candidates in ranking | P1 |

---

## 8. Configuration and Dependencies

### Environment variables (names only)

| Variable | Purpose | Default | Required for |
|---|---|---|---|
| `DATABASE_URL` | PostgreSQL connection | — | Everything |
| `REDIS_URL` | Redis connection | — | Execution workers |
| `GEMINI_API_KEY` | Gemini provider | — | BRD extraction |
| `OPENROUTER_API_KEY` | OpenRouter fallback | — | BRD extraction fallback |
| `VISION_PROVIDER` | Vision provider name | `gemini` | Table/image extraction |
| `TEXT_PROVIDER` | Text provider name | `gemini` | Appendix extraction |
| `BRD_EXTRACTION_OPENROUTER_MODEL` | OpenRouter model for BRD | `inclusionai/ling-3.0-flash-fin:free` | BRD extraction |
| `VISION_MAX_CONCURRENCY` | Vision extraction parallelism | `1` | Performance |
| `VISION_MAX_RETRIES` | Per-page retry count | `3` | Reliability |
| `VISION_BACKOFF_BASE_SECONDS` | Backoff base | `2.0` | Rate limit handling |
| `VISION_BACKOFF_MAX_SECONDS` | Backoff cap | `30.0` | Rate limit handling |
| `GENERATION_BUDGET_SECONDS` | LLM total budget | `30` | Workflow generation |
| `TESSERACT_PATH` | OCR binary | `/usr/bin/tesseract` | OCR fallback |
| `POPPLER_PATH` | PDF render binary | `/usr/bin` | Vision extraction |
| `FILE_STORAGE_PATH` | Skill file storage | `/data/mflows/files` | Publication |

### Key dependency versions

| Package | Version | Used for |
|---|---|---|
| `sentence-transformers` | 5.7.0 | BAAI/bge-small-en-v1.5, ms-marco-MiniLM |
| `pgvector` | 0.3.6 | Vector column + cosine distance |
| `rank-bm25` | 0.2.2 | BM25Okapi |
| `pypdf` | 6.15.0 | PDF text extraction |
| `pdf2image` | 1.17.0 | PDF → PNG for vision |
| `sqlalchemy` | 2.0.40 | ORM |
| `pydantic` | 2.11.3 | Schema validation |

### Embedding configuration

| Setting | Value |
|---|---|
| Model | `BAAI/bge-small-en-v1.5` |
| Dimensions | 384 |
| Normalization | L2-normalized (`normalize_embeddings=True`) |
| Distance metric | Cosine distance (pgvector `<=>`) |
| Index type | IVFFlat (lists=100) on `action_definitions.embedding`, `trigger_definitions.embedding` |
| Rule index | IVFFlat was on `workflow_business_rule.embedding` — **dropped by migration 99e9cf39be25 ⚠️** |

### Retrieval configuration

| Setting | Ingestion | Runtime | Match? |
|---|---|---|---|
| RRF k | 20 | 60 | ❌ No |
| Cross-encoder model | `ms-marco-MiniLM-L-6-v2` | Same | ✓ |
| Cross-encoder top_k | 50 | 50 | ✓ |
| Confidence threshold | 0.40 | 0.40 | ✓ |
| Trigger threshold | 0.40 | 0.40 | ✓ |

---

## 9. Confirmed Defects

### D1 — Global pending-mapping query
- **File:** `app/knowledge_ingestions/workflow_repository.py`
- **Functions:** `get_unmapped_actions()`, `get_unmapped_triggers()`
- **Problem:** no `workspace_id` filter — processing Bank A's BRD runs Bank B's pending mappings
- **Fix:**
  ```python
  def get_unmapped_actions(self, workspace_id: int):
      return (
          self.db.query(WorkflowActionMapping)
          .join(WorkflowKnowledge, WorkflowKnowledge.id == WorkflowActionMapping.workflow_knowledge_id)
          .filter(
              WorkflowKnowledge.workspace_id == workspace_id,
              WorkflowActionMapping.status.in_([MappingStatus.PENDING, MappingStatus.UNMAPPED])
          )
          .all()
      )
  ```
- **Also fix:** `EmbeddingMapper.__init__` must accept and store `workspace_id`; `KnowledgeIngestionService.ingest` must pass it

### D2 — Trigger diagnostics silently dropped
- **File:** `app/knowledge_ingestions/workflow_repository.py`
- **Function:** `mark_trigger_unmapped()`
- **Problem:** `query_text` and `top_candidates` parameters are `pass`-ed — no columns
- **Fix:** Add migration; then:
  ```python
  mapping.status = MappingStatus.UNMAPPED
  if query_text is not None:
      mapping.query_text = query_text
  if top_candidates is not None:
      mapping.top_candidates = top_candidates
  ```

### D3 — RRF k mismatch
- **Files:** `service.py _build_pipeline()` k=20 vs `runtime/dependencies.py _build_pipeline()` k=60
- **Fix:** Use same k in both, or make k a config constant

### D4 — Rule RAG not wired to any API
- **Missing:** `POST /api/rules/query` endpoint
- **Fix:** Create route, instantiate `RuleRepository` + three rule retrievers, run 3-stage pipeline

### D5 — IVFFlat index dropped
- **File:** `alembic/versions/99e9cf39be25_add_workflow_rule_metadata_table.py`
- **Fix:** Add `CREATE INDEX` in same migration's `upgrade()`:
  ```python
  op.execute("""
      CREATE INDEX ix_workflow_business_rule_embedding
      ON workflow_business_rule
      USING ivfflat (embedding vector_cosine_ops)
      WITH (lists = 100)
      WHERE embedding IS NOT NULL
  """)
  ```

### D6 — Debug artifact fixed names
- **File:** `app/knowledge_ingestions/worfklow_extractors.py`
- **Fix:** Use ingestion run ID in filename:
  ```python
  path = _DEBUG_DIR / f"workflow_llm_input_{run_id}.txt"
  ```

---

## 10. Recommended Implementation Sequence

### Milestone 1 — Multi-tenant safety (2 days)
1. `workflow_repository.py`: add `workspace_id` parameter to `get_unmapped_actions()`, `get_unmapped_triggers()`
2. `embedding_mapper.py`: accept `workspace_id` in `__init__`, pass to repository
3. `service.py`: pass `workspace_id` to `EmbeddingMapper`
4. Migration: add `query_text TEXT`, `top_candidates JSONB` to `workflow_trigger_mapping`
5. `workflow_repository.py`: populate those columns in `mark_trigger_unmapped()`
6. Write tests: Bank A mapping does not touch Bank B rows

### Milestone 2 — Re-create IVFFlat index (0.5 days)
1. New migration: add `CREATE INDEX` for `workflow_business_rule.embedding`
2. Run `scripts/backfill_embeddings.py --force` to repopulate embeddings

### Milestone 3 — Rule RAG API endpoint (3 days)
1. Create `app/routes/rules.py` → `POST /api/rules/query`
2. Requires `X-User-Id` + `X-Workspace-Id` headers
3. Instantiates `RuleRepository`, three rule retrievers, `RRF(k=60)`, `EvidenceValidator`
4. Returns top-K annotated rules with evidence labels and source citations

### Milestone 4 — RRF consistency (0.5 days)
1. Create `RRF_K_INGESTION` and `RRF_K_RUNTIME` constants in `app/core/config.py`
2. Update both `_build_pipeline()` calls

### Milestone 5 — Auth middleware (2 days)
1. Add FastAPI middleware that extracts user identity from Bearer token or header
2. Apply to ingestion, execution, workflow endpoints

### Milestone 6 — Tests (3 days)
1. Tenant isolation tests (Bank A / Bank B isolation)
2. Rule retrieval workspace scoping
3. Duplicate ingestion handling

---

## 11. First Milestone — Acceptance Criteria

### Milestone 1: Workspace-scoped mapping

**Files to change:**
- `app/knowledge_ingestions/workflow_repository.py` (2 functions)
- `app/knowledge_ingestions/embedding_mapper.py` (constructor + 2 calls)
- `app/knowledge_ingestions/service.py` (1 call)
- New migration file

**Acceptance criteria:**
1. Upload Bank A BRD → `get_unmapped_actions(workspace_id=A)` returns only Bank A rows
2. Upload Bank B BRD → `get_unmapped_actions(workspace_id=B)` returns only Bank B rows
3. Mapping Bank A's BRD does not change status of Bank B's `workflow_action_mapping` rows
4. UNMAPPED trigger rows have `query_text` and `top_candidates` populated
5. All 44 existing unit tests continue to pass
6. New test: `test_mapping_does_not_cross_tenant_boundary()` passes

**Test to write:**
```python
def test_mapping_does_not_cross_tenant_boundary(db):
    # Arrange: two workspaces with their own BRDs
    ws_a = create_workspace(db, "bank_a")
    ws_b = create_workspace(db, "bank_b")
    brd_a = ingest_brd(db, workspace_id=ws_a.id, source="bank_a_pl.pdf")
    brd_b = ingest_brd(db, workspace_id=ws_b.id, source="bank_b_pl.pdf")

    # Act: run mapping for workspace A only
    mapper = EmbeddingMapper(repository, pipeline, workspace_id=ws_a.id)
    mapper.map_actions()

    # Assert: Bank B rows untouched
    b_rows = db.query(WorkflowActionMapping).join(WorkflowKnowledge).filter(
        WorkflowKnowledge.workspace_id == ws_b.id
    ).all()
    assert all(row.status == MappingStatus.PENDING for row in b_rows)
```

---

*Last updated: October 2026 — based on direct code inspection, no assumptions.*
