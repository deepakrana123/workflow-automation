# RAG Pipeline — Every Function, Call Chain, Saves & Re-ranking
## Complete Function-Level Reference for Multi-Tenant RAG Pipeline

---

## How to read this document

Each section follows this pattern:

```
FILE PATH
  FUNCTION NAME
    Receives   : what comes in
    Calls      : what it invokes (file → function)
    Saves      : what it writes to DB / disk
    Returns    : what it hands back
    Failure    : what happens on error
    Re-ranking : if this function is part of ranking
```

Arrow notation: `A → B` means "A calls B directly".

---

## 1. Document Ingestion Entry Point

### `app/routes/knowledge_ingestion.py`
#### `upload_brds(files, workspace_id, db)`
- **Receives:** `list[UploadFile]`, `workspace_id: int = Form(1)`, `Session`
- **Calls:** validates workspace exists in DB → `KnowledgeIngestionService(db)` → `_ingest_one(service, file, workspace_id, db)` per file
- **Saves:** nothing directly
- **Returns:** `{workspace_id, total, succeeded, failed, results: list}`
- **Failure:** per-file errors caught in `_ingest_one`; partial success reported
- **Defect:** `workspace_id` defaults to 1; no authentication; no ownership check

#### `_ingest_one(service, file, workspace_id, db)`
- **Receives:** `KnowledgeIngestionService`, `UploadFile`, `int`, `Session`
- **Calls:** saves upload to temp file → `service.ingest(file_path, workspace_id, source_document)`
- **Saves:** temp file to disk (cleaned up after)
- **Returns:** `{filename, status: "success"|"error", workflow_knowledge_id?, error?}`
- **Failure:** `WorkflowExtractionError` or `RepositoryError` caught → returns error dict

---

## 2. Ingestion Service Orchestrator

### `app/knowledge_ingestions/service.py`
#### `KnowledgeIngestionService.__init__(db, ...)`
- **Receives:** `Session`, optional injected components
- **Calls:** `WorkflowRepository(db)`, `MultiModalDocumentExtractor()`, `WorkflowExtractor()`, `_build_pipeline(repository)`, `EmbeddingMapper(repository, pipeline)`
- **Saves:** nothing
- **Returns:** self
- **Note:** `_build_pipeline` builds fresh `CrossEncoderReRanker` (model load) and `BM25Okapi` per instance — no singleton

#### `KnowledgeIngestionService.ingest(file_path, workspace_id, source_document)`
- **Receives:** `Path`, `int`, `str | None`
- **Calls:**
  1. `self.document_extractor.extract(file_path)` → document text
  2. `self.workflow_extractor.extract(document_text)` → `WorkflowExtraction`
  3. Guard: raises if `workflow.action_references` is empty
  4. `self.repository.save(workflow, workspace_id, source_document)` → persists all rows
  5. `self.embedding_mapper.map_actions()`
  6. `self.embedding_mapper.map_triggers()`
  7. `self.db.commit()`
- **Saves:** all rows via repository (see §6)
- **Returns:** `WorkflowKnowledge` ORM object
- **Failure:** `db.rollback()` on any exception; raises `RepositoryError`

#### `_build_pipeline(repository)`
- **Receives:** `WorkflowRepository`
- **Calls:** constructs `VectorRetriever`, `KeywordRetriever`, `PostgressRetriever`, `ReciprocalRankFusion()`, `CrossEncoderReRanker()`, `MappingDecisionEngine(ConfidenceEstimator(), RetrievalThresholds(), UnknownDetector())`
- **Saves:** nothing
- **Returns:** `RetrievalPipeline`
- **Re-ranking config here:** `ReciprocalRankFusion()` uses default `k=20`

---

## 3. Document Extraction — Multimodal

### `app/knowledge_ingestions/multimodal_extractor.py`
#### `MultiModalDocumentExtractor.__init__(vision_provider, text_provider, classifier, continuation_detector)`
- **Receives:** optional injected providers
- **Calls:** `get_vision_provider()`, `get_text_provider()` from registry if not injected; constructs `TableImageExtractor(vision_provider)`, `AppendixExtractor(text_provider)`, `DocumentExtractor()`
- **Saves:** nothing

#### `MultiModalDocumentExtractor.extract(file_path) → str`
- **Receives:** `Path`
- **Calls:**
  1. `self._classifier.classify(file_path)` → `DocumentClassification`
  2. If plain text only → `self._plain_extractor.extract(file_path)` and return
  3. `ThreadPoolExecutor(max_workers=3)`:
     - Thread A: `self._extract_body_text(doc)` — assembles text from already-extracted pages (zero API cost)
     - Thread B: `self._extract_visual(file_path, visual_pages)` → `dict[int, PageExtractionResult]`
     - Thread C: `self._appendix_extractor.extract(doc.appendix_pages)` → `str`
  4. `_merge_results(doc, body_text, visual_result, appendix_text)` → structured string
- **Saves:** nothing
- **Returns:** merged document string with sections: `=== DOCUMENT BODY ===`, `=== TABLE AND DIAGRAM EXTRACTIONS ===`, `=== APPENDIX ===`
- **Failure:** vision thread failure → all visual pages marked `VISION FAILED, RAW TEXT`; appendix failure → raw pypdf text; classification failure → falls back to plain extractor

#### `MultiModalDocumentExtractor._extract_visual(file_path, visual_pages) → dict[int, PageExtractionResult]`
- **Receives:** `Path`, `list[PageClassification]`
- **Calls:**
  1. `build_page_metadata(p)` per page → list of `PageMetadata`
  2. `build_extraction_groups(metas, self._continuation_detector)` → `list[ExtractionGroup]`
  3. `self._table_image_extractor.extract_groups(file_path, groups, page_lookup)`
- **Returns:** `dict[int, PageExtractionResult]`

---

## 4. Page Classification

### `app/knowledge_ingestions/page_classifier.py`
#### `PageClassifier.classify(pdf_path) → DocumentClassification`
- **Receives:** `Path`
- **Calls:** `PdfReader(pdf_path)` → iterates pages → `page.extract_text()` → `page.images` → `self._classify_page(page_number, text, has_images)`
- **Saves:** nothing (pure local computation)
- **Returns:** `DocumentClassification` with `.text_pages`, `.table_pages`, `.image_pages`, `.appendix_pages`

#### `PageClassifier._classify_page(page_number, text, has_images) → str`
- **Logic:**
  1. Image: `has_images AND len(text) < 150` → `"image"`
  2. Table: pipe characters ≥3, OR short-line density + numeric ratio, OR currency hits + compact layout → `"table"`
  3. Appendix: first 6 lines match `_APPENDIX_HEADING_RE` (anchored line regex) → `"appendix"`
  4. Otherwise → `"text"`
- **Important:** table/image overrides appendix heading (a table inside an appendix keeps vision extraction)

---

## 5. Continuation Detection & Grouping

### `app/knowledge_ingestions/continuation_detector.py`
#### `ContinuationDetector.detect(prev, curr) → ContinuationResult`
- **Receives:** two `PageMetadata` objects
- **Calls:** `self._detect_deterministic(prev, curr)` → `self._resolve_ambiguous(prev, curr, result)` (hook for future LLM)
- **Logic order:**
  1. Empty current page → `NEW_CONTENT` (0.90)
  2. Explicit `continued` marker → `CONTINUATION` (0.95)
  3. New section heading on current → `NEW_CONTENT` (0.90)
  4. Distinct new title on current → `NEW_CONTENT` (0.85)
  5. Repeated table header (long contiguous alnum run) → `CONTINUATION` (0.88)
  6. Similar pipe headers (sim ≥ 0.85) → `CONTINUATION`
  7. Mid-structure start + previous structured → `CONTINUATION` (0.72–0.78)
  8. Default → `NEW_CONTENT` (0.60)

#### `build_extraction_groups(pages, detector) → list[ExtractionGroup]`
- **Receives:** `list[PageMetadata]` in document order
- **Logic:** adjacent pages + `CONTINUATION` → same group; non-adjacent or `NEW_CONTENT` → new group
- **Returns:** `list[ExtractionGroup]`, each with `.page_numbers`, `.is_continuation`, `.continuation_type`

---

## 6. Table/Image Extraction with Vision

### `app/knowledge_ingestions/table_image_extractor.py`
#### `TableImageExtractor.extract_groups(file_path, groups, page_lookup) → dict[int, PageExtractionResult]`
- **Receives:** `Path`, `list[ExtractionGroup]`, `dict[int, PageClassification]`
- **Calls:** `ThreadPoolExecutor(max_workers=VISION_MAX_CONCURRENCY)` → `self._extract_group(file_path, group, page_lookup, dpi)` per group
- **Returns:** `dict[int, PageExtractionResult]` — keyed by page_number

#### `TableImageExtractor._extract_group(file_path, group, page_lookup, dpi)`
- **For single-page groups:** calls `_extract_single` once
- **For continuation groups:** calls `_extract_single` per page in order, threading `ContinuationContext` (compact previous-page summary injected into prompt, NOT full text/image)
- **Returns:** `dict[int, PageExtractionResult]`

#### `TableImageExtractor._extract_single(file_path, page, dpi, extra_context) → PageExtractionResult`
- **Calls:**
  1. `self._render_page(pdf_path, page_number, dpi)` → PNG bytes via `pdf2image.convert_from_path`
  2. `self._get_prompt(page_type)` → loads `app/prompts/table_extraction.md` or `image_extraction.md`
  3. Retry loop (up to `VISION_MAX_RETRIES=3`):
     - `self._provider.extract_page(image_bytes, prompt)` → text
     - On `VisionProviderError.is_rate_limited`: honour `retry_after` or exponential backoff
     - Non-retryable: return `PROVIDER_FAILED` immediately
- **Returns:** `PageExtractionResult` with `.status` ∈ {SUCCESS, EMPTY, PROVIDER_FAILED, RATE_LIMITED}
- **Saves:** nothing (result carried in memory to merge step)

---

## 7. Appendix Extraction

### `app/knowledge_ingestions/appendix_extractor.py`
#### `AppendixExtractor.extract(appendix_pages) → str`
- **Receives:** `list[PageClassification]`
- **Calls:**
  1. `_combine_appendix_text(appendix_pages)` → joins pages with `[Page N]` markers
  2. `self._build_prompt(combined_text)` → loads `app/prompts/appendix_extraction.md`
  3. `self._provider.generate(prompt)` → `TextProvider.generate()` → one API call for all appendix pages combined
- **Returns:** extracted string
- **Failure:** `TextProviderError` → returns `""` (logged, never raises)

---

## 8. Provider Registry & Fallback

### `app/knowledge_ingestions/providers/registry.py`
#### `get_vision_provider() → VisionProvider`
- **Reads:** env var `VISION_PROVIDER` (default: `"gemini"`)
- **Returns:** new instance of `GeminiVisionProvider` or `OpenRouterVisionProvider`
- **Failure:** raises `ValueError` if name not in registry

#### `get_text_provider() → TextProvider`
- **Reads:** env var `TEXT_PROVIDER` (default: `"gemini"`)
- **Returns:** new instance
- **Note:** factories use lambdas — fresh instance per call, no shared state

---

## 9. Workflow Extraction (LLM)

### `app/knowledge_ingestions/worfklow_extractors.py`
#### `WorkflowExtractor.extract(document_text) → WorkflowExtraction`
- **Receives:** merged document string from `MultiModalDocumentExtractor`
- **Calls:**
  1. `self.prompt_manager.build(WORKFLOW_EXTRACTION, {schema: _OUTPUT_EXAMPLE, text: document_text})` → prompt string
  2. `self._save_debug_input(prompt)` → writes `debug_workflow_extraction/workflow_llm_input.txt` ⚠️ FIXED NAME
  3. Provider waterfall:
     - `health.is_healthy("gemini")` → `self._llm.generate_with_provider(prompt, "gemini")`
     - On fail/skip → `health.is_healthy("openrouter")` → `self._llm.generate_with_provider(prompt, "openrouter", model=BRD_EXTRACTION_OPENROUTER_MODEL)`
     - On fail/skip → `self._llm.generate(prompt)` (remaining waterfall)
  4. `WorkflowExtraction.model_validate_json(raw_output)` → Pydantic validation
  5. `self._save_debug_output(raw_output)` → `debug_workflow_extraction/workflow_llm_output.txt` ⚠️ FIXED NAME
  6. `self._save_debug_json(extraction)` → `debug_workflow_extraction/workflow_extraction.json` ⚠️ FIXED NAME
- **Returns:** `WorkflowExtraction` Pydantic object
- **Failure:** `WorkflowExtractionError` on all provider failures or Pydantic `ValidationError`
- **⚠️ Defect:** 3 debug files have fixed names — concurrent ingestions overwrite each other

---

## 10. Pydantic Schema Validation

### `app/knowledge_ingestions/schemas.py`
#### `WorkflowExtraction.model_validate_json(raw_output)`
- **Pydantic v2 validator `_normalise_shapes`** runs before field assignment:
  - `business_rules`: `["rule text"]` → `[{"rule": "rule text"}]`
  - `responsible_role` list → comma-joined string
  - `action_references`: ensures `description` exists
  - `actors`: `["name"]` → `[{"name": "name"}]`
  - `responsible_actors` on triggers/actions: `[{"name": X, "role": Y}]` → `["X (Y)"]`
- **Fields extracted:**
  | Field | Type | Note |
  |---|---|---|
  | `workflow_name` | `str` | Required |
  | `summary` | `str` | Required |
  | `triggers` | `list[TriggerExtraction]` | name, description, applicable_rules, responsible_actors |
  | `action_references` | `list[ActionReference]` | name, description, applicable_rules, responsible_actors |
  | `business_rules` | `list[BusinessRule]` | rule, condition, outcome, responsible_role, threshold |
  | `actors` | `list[Actor]` | name, role |
  | `external_systems` | `list[ExternalSystem]` | name, description — **NEVER PERSISTED** |
  | `assumptions` | `list[str]` | **NEVER PERSISTED** |

---

## 11. Knowledge Persistence

### `app/knowledge_ingestions/workflow_repository.py`
#### `WorkflowRepository.save(workflow, workspace_id, source_document)`
- **Receives:** `WorkflowExtraction`, `int`, `str | None`
- **Writes to DB (5 tables in one transaction):**

  **Table 1: `workflow_knowledge`**
  ```
  workflow_name    = workflow.workflow_name
  summary          = workflow.summary
  workspace_id     = workspace_id          ← tenant anchor
  source_document  = source_document       ← original filename
  ```

  **Table 2: `workflow_trigger_mapping`** (1 row per trigger)
  ```
  workflow_knowledge_id = knowledge.id
  extracted_name        = trigger.name
  description           = trigger.description
  applicable_rules      = trigger.applicable_rules (JSONB) | None
  responsible_actors    = trigger.responsible_actors (JSONB) | None
  status                = PENDING (implicit default)
  ```

  **Table 3: `workflow_action_mapping`** (1 row per action)
  ```
  workflow_knowledge_id = knowledge.id
  extract_name          = action.name
  description           = action.description
  applicable_rules      = action.applicable_rules (JSONB) | None
  responsible_actors    = action.responsible_actors (JSONB) | None
  status                = PENDING (implicit default)
  ```

  **Table 4: `workflow_business_rule`** (1 row per rule)
  ```
  workflow_knowledge_id = knowledge.id
  rule                  = rule.rule
  condition             = rule.condition | None
  outcome               = rule.outcome | None
  responsible_role      = rule.responsible_role | None
  threshold             = rule.threshold | None     ← often NULL despite LLM guidance
  embedding             = None                      ← populated by backfill_embeddings.py
  ```

  **Table 5: `workflow_actors`** (1 row per actor)
  ```
  workflow_knowledge_id = knowledge.id
  name                  = actor.name
  role                  = actor.role | None
  ```
- **NOT persisted:** `external_systems`, `assumptions` — extracted by LLM, silently dropped
- **Returns:** `WorkflowKnowledge` ORM object

---

## 12. Action Mapping

### `app/knowledge_ingestions/embedding_mapper.py`
#### `EmbeddingMapper.map_actions(embedding_variant="name_description")`
- **Receives:** nothing (operates on repository state)
- **Calls:**
  1. `self.repository.get_unmapped_actions()` → PENDING+UNMAPPED across **ALL workspaces** ⚠️ **Defect**
  2. Per action:
     a. `_normalize_query(extract_name + description)` — strips boilerplate
     b. `self._embed(embedding_text)` → `SentenceTransformer.encode()` → 384-dim vector
     c. `self.pipeline.retrieve_actions(query, embedding)` → `list[RankedCandidate]`
     d. `_serialize_candidates(all_candidates, top_k=10)` → JSONB for diagnostics
     e. `self.pipeline._decision.decide(all_candidates, RetrievalType.ACTION)` → best or None
     f. If matched: `self.repository.update_action_mapping(...)` → writes MAPPED + full snapshot
     g. If not: `self.repository.mark_action_unmapped(...)` → writes UNMAPPED + diagnostics

#### `EmbeddingMapper.map_triggers(embedding_variant="name_description")`
- **Same pattern as map_actions** with these differences:
  - Uses `repository.get_unmapped_triggers()` ⚠️ also unscoped
  - On failure: `repository.mark_trigger_unmapped()` is called but `query_text` and `top_candidates` are **silently dropped** (columns don't exist on `workflow_trigger_mapping`) ⚠️ **Defect**

---

## 13. Full Retrieval Pipeline — Action/Trigger Mapping

### Stage 1: Vector Retrieval
#### `app/retrieval/vector_retriever.py` → `VectorRetriever.search_actions(embedding, limit)`
- **Calls:** `repository.search_actions_by_embedding(embedding, limit)`
- **DB query:** `SELECT action_definitions WHERE active=True ORDER BY embedding <=> query_vector LIMIT limit`
- **No workspace filter** — global catalog, no tenant boundary (correct: catalog is global)
- **Returns:** `list[RetrievalCandidate]` with `source="vector"`, `score=cosine_distance` (lower=better)

### Stage 2: BM25 Retrieval
#### `app/retrieval/keyword_retriever.py` → `KeywordRetriever.search_actions(query, limit)`
- **Index corpus:** `name (underscores→spaces) + display_name + aliases + description` per `ActionDefinition`
- **Index built at:** `refresh()` called in `__init__` — queries ALL active actions once
- **Tokenization:** lowercase, strip non-alphanumeric, split on whitespace
- **Calls:** `self.action_index.get_scores(tokens)` → scores array → sort → top `limit`
- **Returns:** `list[RetrievalCandidate]` with `source="bm25"`, `score=BM25 score` (higher=better)
- **Note:** BM25 score filter `> 0.001` exists on rule retriever but NOT here — zero-score actions included

### Stage 3: PostgreSQL FTS Retrieval
#### `app/retrieval/postgress_retriever.py` → `PostgressRetriever.search_actions(query, limit)`
- **Calls:** `repository.search_actions_by_postgress(query, limit)`
- **DB query:**
  ```sql
  SELECT action_definitions, ts_rank(tsvector, tsquery) AS rank
  FROM action_definitions
  WHERE (to_tsvector('english', name||' '||display_name||' '||description)
         || jsonb_to_tsvector('english', aliases, '["string"]'))
        @@ websearch_to_tsquery('english', :query)
  ORDER BY rank DESC
  LIMIT :limit
  ```
- **No workspace filter** — correct (global catalog)
- **Returns:** `list[RetrievalCandidate]` with `source="postgres"`, `score=ts_rank` (higher=better)

### Stage 4: Reciprocal Rank Fusion
#### `app/retrieval/reciprocal_rank_fusion.py` → `ReciprocalRankFusion.fuse(vector, keyword, postgres)`
- **Receives:** 3 `list[RetrievalCandidate]`
- **Formula:** `RRF(doc) = Σ 1/(k + rank)` for each list containing the doc
- **k value:**
  - Ingestion pipeline (`service.py _build_pipeline`): `k=20` (default)
  - Runtime pipeline (`runtime/dependencies.py`): `k=60` (explicit) ⚠️ **Inconsistency**
- **Algorithm:**
  1. Build `{entity_id: 1-based rank}` map per source list
  2. Union all entity IDs
  3. For each ID: sum `1/(k+rank)` from each list (0 if absent)
  4. Build `RankedCandidate` with `vector_rank`, `bm25_rank`, `postgres_rank`, `rrf_score`
  5. Sort descending by `rrf_score`
- **Returns:** `list[RankedCandidate]` sorted by `rrf_score` descending

### Stage 5: Cross-Encoder Re-ranking ← THE KEY RE-RANKING STEP
#### `app/retrieval/cross_encoder.py` → `CrossEncoderReRanker.rerank(query, candidates)`
- **Receives:** query string, `list[RankedCandidate]` from RRF
- **Takes:** top `top_k=50` candidates (rest discarded at this point)
- **Document text built as:** `f"{display_name} {name} {alias_text} {description}".strip()`
- **Calls:** `self.model.predict(pairs)` — `ms-marco-MiniLM-L-6-v2` cross-encoder
  - Input: `[(query, doc_text), ...]` — 50 pairs in one forward pass
  - Output: raw logits (higher = more relevant)
- **Attaches:** `candidate.cross_encoder_score = float(score)` per candidate
- **Re-sorts:** list by `cross_encoder_score` descending ← **This is the final ranking order**
- **Returns:** `list[RankedCandidate]` re-sorted by cross-encoder score

### Stage 6: Decision (Threshold Gate)
#### `app/retrieval/decision_engine.py` → `MappingDecisionEngine.decide(candidates, entity_type)`
- **Calls:** `ConfidenceEstimator.estimate(best_candidate)` → `sigmoid(cross_encoder_score)` → float in [0,1]
- **Threshold check:** `UnknownDetector.is_unknown(confidence, threshold)` → `confidence < 0.40`
- **Returns:** `RankedCandidate` (the top one) if confidence ≥ 0.40, else `None`
- **Unknown margin:** `0.08` — reserved for future "close but uncertain" handling

### Full retrieval call graph (ingestion path):
```
EmbeddingMapper.map_actions()
  → pipeline.retrieve_actions(query, embedding)        ← returns FULL list, no threshold
      → _retrieve_and_rank_actions(query, embedding)
          → VectorRetriever.search_actions(embedding)   [DB: action_definitions]
          → KeywordRetriever.search_actions(query)      [in-memory BM25]
          → PostgressRetriever.search_actions(query)    [DB: action_definitions FTS]
          → ReciprocalRankFusion.fuse(v, kw, pg)        [RRF k=20]
          → CrossEncoderReRanker.rerank(query, fused)   [ms-marco, top-50, re-sorts]
  → pipeline._decision.decide(candidates, ACTION)      ← applies threshold (0.40)
  → update_action_mapping / mark_action_unmapped        [DB: workflow_action_mapping]
```

---

## 14. Persistence — Mapping Results

### `app/knowledge_ingestions/workflow_repository.py`
#### `update_action_mapping(mapping_id, action_definition_id, similarity_score, confidence, query_text, top_candidates, ...snapshot fields)`
- **Writes to `workflow_action_mapping`:**
  ```
  matched_action_definition_id = action_definition_id
  status                       = MAPPED
  similarity_score             = rrf_score of winner
  confidence                   = sigmoid(cross_encoder_score)
  query_text                   = normalized query sent to retrievers
  top_candidates               = [{name, rrf_score, cross_encoder_score, v_rank, b_rank, p_rank}, ...] (JSONB)
  action_name                  = snapshot from ActionDefinition.name
  display_name                 = snapshot
  catalog_description          = snapshot
  aliases                      = snapshot (JSONB)
  workflow_type                = snapshot
  input_schema                 = snapshot (JSONB)
  output_schema                = snapshot (JSONB)
  execution_template           = snapshot (JSONB)
  ```

#### `mark_action_unmapped(mapping_id, query_text, top_candidates)`
- **Writes to `workflow_action_mapping`:**
  ```
  status         = UNMAPPED
  query_text     = query that was tried
  top_candidates = top-10 rejected candidates with scores (JSONB)
  ```

#### `mark_trigger_unmapped(mapping_id, query_text, top_candidates)`
- **Writes to `workflow_trigger_mapping`:**
  ```
  status = UNMAPPED
  ```
- ⚠️ `query_text` and `top_candidates` parameters are accepted but `pass`-ed — no columns exist — diagnostics silently lost

---

## 15. Business Rule Retrieval Pipeline (Rule RAG)

### Stage 1: Candidate Selection (Metadata Pre-filter) — scripts only
#### `scripts/test_rule_retrieval.py` → `MetadataCandidateSelector.select_candidates(intent)`
- **Reads:** `workflow_rule_metadata` JOIN `workflow_business_rule` JOIN `workflow_knowledge`
- **Filtered by:** `workspace_id` ✓
- **Produces 4 buckets (union = `allowed_ids`):**
  - `scoped`: rules whose zone/product/applicant_type are compatible with intent
  - `global`: `policy_level == 'GLOBAL'` — always included
  - `exception`: `rule_type == 'exception'` with compatible scope
  - `fallback`: rules with NO metadata row — never silently dropped
- **Excludes:** EXPIRED status, uncertain status (PROPOSED/UNKNOWN/None)

### Stage 2: Rule Vector Retrieval
#### `app/retrieval/rule_vector_retriever.py` → `RuleVectorRetriever.search(embedding, limit, allowed_ids)`
- **Calls:** `RuleRepository.search_by_embedding(workspace_id, embedding, limit, allowed_ids)`
- **DB query:**
  ```sql
  SELECT workflow_business_rule, embedding <=> :vec AS distance
  FROM workflow_business_rule
  JOIN workflow_knowledge ON wk.id = r.workflow_knowledge_id
  WHERE wk.workspace_id = :ws_id
    AND embedding IS NOT NULL
    [AND id = ANY(:allowed_ids)]   ← pre-filter BEFORE ranking
  ORDER BY distance ASC
  LIMIT :limit
  ```
- **Filter applied:** SQL-level, before ranking ✓
- **Returns:** `list[RetrievalCandidate]` with `source="vector"`, `score=cosine_distance`

### Stage 3: Rule BM25 Retrieval
#### `app/retrieval/rule_keyword_retriever.py` → `RuleKeywordRetriever.search(query, limit, allowed_ids)`
- **Index built over:** `rule + condition + outcome + responsible_role + threshold` per `WorkflowBusinessRule`
- **Workspace-scoped:** index built from `get_all_rules_for_workspace(workspace_id)` ✓
- **`allowed_ids` filter:** applied by masking BM25 scores array BEFORE returning results
  ```python
  filtered_pairs = [(i, doc) for i, doc in enumerate(self._documents) if doc.id in allowed_ids]
  all_scores = self._index.get_scores(tokens)
  ranked = sorted([(self._documents[i], all_scores[i]) for i, _ in filtered_pairs], ...)
  ```
- **Note:** IDF statistics computed over full workspace corpus — not recomputed per filter. Correct design.
- **Score filter:** `score > 0.001`
- **Returns:** `list[RetrievalCandidate]`

### Stage 4: Rule PostgreSQL FTS Retrieval
#### `app/retrieval/rule_postgres_retriever.py` → `RulePostgresRetriever.search(query, limit, allowed_ids)`
- **Calls:** `RuleRepository.search_by_fts(workspace_id, query, limit, allowed_ids)`
- **Strategy:** AND-first (all tokens must appear), OR-fallback if zero results
- **Filter:** `AND r.id = ANY(:ids)` in both AND and OR SQL — applied at DB level before ranking ✓
- **Returns:** `list[RetrievalCandidate]`

### Stage 5: RRF for Rules
#### `ReciprocalRankFusion(k=60)` — rule eval script explicitly passes `k=60`
- Same formula as action/trigger RRF but `k=60` (ingestion uses `k=20`) — ⚠️ inconsistency exists but rule RRF is correctly scoped

### Stage 6: Evidence Validation — NOT re-ranking
#### `scripts/test_rule_retrieval.py` → `EvidenceValidator.apply(fused, intent, selector)`
- **Does NOT re-sort** — RRF order preserved
- **Annotates each candidate with:**
  - `THRESHOLD_MATCH` / `THRESHOLD_FAIL` — same `+0.015` delta (fail rule stays in top-K)
  - `THRESHOLD_METRIC_MISMATCH` — `-0.010` (mild demotion for wrong metric type)
  - `THRESHOLD_AMBIGUOUS` — `0.0` (date fields, year values, direction unclear)
  - `EXCEPTION_SCOPE_MATCH` — `+0.020`
  - `EXCEPTION_SCOPE_UNKNOWN` — `+0.005` (absent query dimension ≠ match)
  - `EXCEPTION_SCOPE_MISS` — `-0.020`
  - `APPROVAL_REQUIRED` — `+0.010`
  - `GLOBAL_BASELINE` — `+0.005`
  - `EXPIRED` — `-0.060`
  - `NO_METADATA` — `0.0`
- **Metric-aware threshold comparison:**
  - Detects metric type from rule text: `credit_score`, `income`, `age`, `loan_amount`, `foir`
  - Detects query metric from `intent.raw_query`
  - If both detected and different → `THRESHOLD_METRIC_MISMATCH`
  - If query metric known but rule metric unknown → `THRESHOLD_METRIC_MISMATCH`
- **Range handling:** `_parse_numeric_range("640-679")` → `(640.0, 679.0)` — evaluated as inclusive interval

### Rule retrieval call graph (eval script path):
```
test_rule_retrieval.py::evaluate_case()
  → extract_rich_intent(query)                           [Stage 1: intent]
  → MetadataCandidateSelector.select_candidates(intent)  [Stage 2: metadata pre-filter]
      → reads workflow_rule_metadata WHERE workspace_id=X
      → produces allowed_ids set
  → RuleVectorRetriever.search(embedding, limit, allowed_ids)   [DB: workspace-scoped]
  → RuleKeywordRetriever.search(query, limit, allowed_ids)      [BM25: pre-filtered]
  → RulePostgresRetriever.search(query, limit, allowed_ids)     [DB: workspace-scoped]
  → ReciprocalRankFusion(k=60).fuse(v, b, p)                    [RRF]
  → EvidenceValidator.apply(fused, intent, selector)             [annotation, NO re-sort]
```
⚠️ **This entire rule RAG path exists only in `scripts/test_rule_retrieval.py`. No production API endpoint calls it.**

---

## 16. Rule Extraction (BRD → Structured Rules)

### `app/rbac/rule_extractor.py`
#### `RuleExtractionService.extract_for_workspace(db, workspace_id)`
- **Reads:** `workflow_knowledge WHERE workspace_id=X` → all BRDs for workspace
- **Per BRD:**
  - `_extract_rules(db, wk, workspace_id)` — parses `workflow_business_rule` text → `business_rule_definitions`
  - `_extract_roles(db, wk, workspace_id)` — parses `workflow_actors` → `role_assignments`

#### `_extract_rules(db, wk, workspace_id)`
- **Reads:** `workflow_business_rule WHERE workflow_knowledge_id = wk.id`
- **Also reads:** all `workflow_actors` for the BRD → extracts roles → assigns to ALL rules ⚠️ **Defect: BRD-wide actors applied to every rule, not per-rule actors**
- **Per rule:**
  - `extract_amounts(rule_text)` → list of numeric values (regex)
  - `_infer_field(rule_text)` → field name hint (`"loan_amount"`, `"credit_score"`, etc.)
  - `_infer_operator(rule_text)` → `">="` or `"<="` from direction words
  - Idempotency check: skip if `description` already exists for this workspace
  - Writes `BusinessRuleDefinition` row
- **Writes to `business_rule_definitions`:**
  ```
  scope_workspace_id               = workspace_id
  source_workflow_knowledge_id     = wk.id
  field                            = inferred or None (description-only if None)
  op                               = inferred or None
  value                            = first amount or None (JSONB)
  description                      = raw rule text
  allowed_roles                    = all BRD-wide actor roles (JSONB) ⚠️
  locked                           = False
  active                           = True
  ```

---

## 17. Rule Inheritance

### `app/rbac/rule_inheritance.py`
#### `resolve_effective_rules(workspace_id, db, field=None) → list[BusinessRuleDefinition]`
- **Calls:** `get_ancestor_chain(workspace_id, db)` → `[global_id, region_id, zone_id, branch_id]`
- **DB query:**
  ```sql
  SELECT * FROM business_rule_definitions
  WHERE scope_workspace_id IN (ancestor_chain)
    AND active = True
    [AND field = :field]
  ```
- **Sorts:** by chain position (global rules first, branch rules last)
- **Returns:** ordered `list[BusinessRuleDefinition]`
- **Used by:** `RuntimeRuleEngine.evaluate()`, `WorkflowPublicationService._check_rule_conflicts()`

---

## 18. Runtime Action Retrieval (ScopedRetrieval)

### `app/runtime/scoped_retrieval.py`
#### `ScopedRetrievalService.retrieve(query, ctx, top_k, include_unauthorized_diagnostics)`
- **Receives:** query string, `RetrievalContext` (with `allowed_action_ids` pre-resolved by RBAC)
- **Calls:**
  1. `self._embedder(query)` → 384-dim vector (optional; falls back to keyword-only)
  2. `self._pipeline.retrieve_actions(query, embedding, limit=max(top_k*5, 50))` — full list, no threshold
  3. RBAC filter loop: for each candidate, check `action_id in ctx.allowed_action_ids`
     - `allowed_action_ids=None` → all allowed (global search)
     - `action_id NOT in allowed_ids` → `authorized=False`, `rejection_reason="ACTION_NOT_IN_ALLOWED_SCOPE"`
  4. Take top `top_k` authorized candidates
- **Re-ranking:** uses existing RRF + cross-encoder order — no additional re-ranking here
- **Returns:** `ScopedRetrievalResult` with `.candidates` (authorized only), `.diagnostics` (all if requested)
- **Filter applied:** AFTER cross-encoder re-ranking (retrieval → rerank → then filter)

### `app/runtime/dependencies.py`
#### `_build_pipeline()` — module-level singleton
- **Called:** lazily on first request, then cached
- **Uses:** `SessionLocal()` → opens DB session → builds `WorkflowRepository(db)` → builds pipeline → **closes DB session**
- **⚠️ Defect:** `WorkflowRepository` is instantiated with a session that is then closed. The `KeywordRetriever.refresh()` runs at construction (session alive). But BM25 index is in-memory — subsequent queries don't need the session.
- **RRF k:** `k=60` — different from ingestion pipeline's `k=20`

---

## 19. What Gets Saved — Complete Table

| Data | Table | Saved when | Workspace scoped? |
|---|---|---|---|
| BRD parent record | `workflow_knowledge` | `WorkflowRepository.save()` | ✓ via `workspace_id` |
| Actions (extracted) | `workflow_action_mapping` | `WorkflowRepository.save()` | ✓ via `workflow_knowledge_id → workspace_id` |
| Triggers (extracted) | `workflow_trigger_mapping` | `WorkflowRepository.save()` | ✓ via FK chain |
| Business rules (text) | `workflow_business_rule` | `WorkflowRepository.save()` | ✓ via FK chain |
| Actors | `workflow_actors` | `WorkflowRepository.save()` | ✓ via FK chain |
| External systems | — | **NEVER** | — |
| Assumptions | — | **NEVER** | — |
| Action mapping result | `workflow_action_mapping` | `update_action_mapping()` | ✓ |
| Action mapping failure | `workflow_action_mapping` | `mark_action_unmapped()` | ✓ |
| Trigger mapping result | `workflow_trigger_mapping` | `update_trigger_mapping()` | ✓ |
| Trigger diagnostics | — | **NEVER** (columns missing) | — |
| Rule embeddings | `workflow_business_rule.embedding` | `backfill_embeddings.py` (manual) | ✓ via FK |
| Rule metadata | `workflow_rule_metadata` | `extract_rule_metadata.py` (manual) | ✓ via FK |
| Structured rules | `business_rule_definitions` | `RuleExtractionService` (manual via API) | ✓ via `scope_workspace_id` |
| Role shapes | `role_assignments` | `RuleExtractionService` (manual via API) | ✓ |
| Debug LLM input | `debug_workflow_extraction/workflow_llm_input.txt` | every extraction | ✗ shared file |
| Debug LLM output | `debug_workflow_extraction/workflow_llm_output.txt` | every extraction | ✗ shared file |
| Debug JSON | `debug_workflow_extraction/workflow_extraction.json` | every extraction | ✗ shared file |
| Trace events | `trace_events` | execution only | ✗ no workspace_id |
| Audit log | `audit_logs` | publish, RBAC assign | ✓ optional workspace_id |

---

## 20. Known Defects — Function-Level Evidence

### D1: Global pending-mapping query
- **File:** `app/knowledge_ingestions/workflow_repository.py`
- **Function:** `get_unmapped_actions()`, `get_unmapped_triggers()`
- **Code:**
  ```python
  def get_unmapped_actions(self):
      return (
          self.db.query(WorkflowActionMapping)
          .filter(WorkflowActionMapping.status.in_([PENDING, UNMAPPED]))
          .all()          # ← NO workspace_id filter
      )
  ```
- **Fix:** add `.join(WorkflowKnowledge).filter(WorkflowKnowledge.workspace_id == workspace_id)` — but requires `workspace_id` to be passed to `EmbeddingMapper`

### D2: Trigger diagnostics silently dropped
- **File:** `app/knowledge_ingestions/workflow_repository.py`
- **Function:** `mark_trigger_unmapped()`
- **Code:**
  ```python
  if query_text is not None:
      pass  # ← intentionally dropped — no column
  if top_candidates is not None:
      pass  # ← same
  ```
- **Fix:** add `query_text TEXT` and `top_candidates JSONB` columns to `workflow_trigger_mapping` via migration

### D3: RRF k mismatch
- **File 1:** `app/knowledge_ingestions/service.py` → `_build_pipeline()` → `ReciprocalRankFusion()` → k=20
- **File 2:** `app/runtime/dependencies.py` → `_build_pipeline()` → `ReciprocalRankFusion(k=60)` → k=60
- **Impact:** same query at ingestion time and runtime produces different candidate orderings — confidence scores differ — a borderline match may map at ingestion but not be retrievable at runtime

### D4: Rule RAG not connected to any API
- **Scripts only:** `scripts/test_rule_retrieval.py` contains the full 3-stage rule pipeline
- **No FastAPI endpoint** imports `RuleVectorRetriever`, `RuleKeywordRetriever`, or `RulePostgresRetriever`
- **Fix:** create `POST /api/rules/query` endpoint

### D5: IVFFlat index dropped by migration
- **File:** `alembic/versions/99e9cf39be25_add_workflow_rule_metadata_table.py`
- **Code in `upgrade()`:**
  ```python
  op.drop_index('ix_workflow_business_rule_embedding', ...)
  ```
- **Missing:** no `CREATE INDEX` replacement in the same migration
- **Impact:** rule vector search is now a full table scan

### D6: Debug files have fixed names
- **File:** `app/knowledge_ingestions/worfklow_extractors.py`
- **Paths:** `debug_workflow_extraction/workflow_llm_input.txt` (3 files, all fixed names)
- **Impact:** concurrent ingestions overwrite each other's debug artifacts

---

*Last updated: October 2026 — based on direct code inspection, no assumptions.*
