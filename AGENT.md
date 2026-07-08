# AGENT.md — MFlows Engineering Reference

> This document is for engineers working on or reviewing the MFlows codebase.
> It covers architecture decisions, module contracts, extension points, and invariants.

---

## System Overview

MFlows is a workflow automation engine with two ingestion paths and one deterministic execution engine.

**Ingestion Path 1 — Natural Language**
A user writes a plain English sentence. The NLP pipeline extracts intent, matches catalog triggers and actions, calls an LLM, validates and compiles the output to a DAG, and persists it.

**Ingestion Path 2 — BRD Document**
A user uploads a PDF. The system extracts text (with OCR fallback), calls Gemini to extract structured workflow knowledge, maps extracted items to the catalog using vector embeddings, and initializes execution configurations.

**Execution Engine**
Both paths produce a `parsed_rule_json` stored in the `workflows` table. The runtime reads this, builds a DAG, executes steps in dependency order (with parallel fan-out where safe), accumulates outputs in `WorkflowContext`, and handles failures via retry, DLQ, and reaper recovery.

---

## Invariants — Never Break These

- Raw LLM output is never executed. It always passes through compile + validate first.
- LLM calls exist only inside `app/nlp/`. The execution layer is ML-free.
- The execution engine is deterministic. Given the same `parsed_rule_json`, it always produces the same step order.
- Every action must return `ActionResult`. The runtime reads nothing else.
- `result.success` is the only field retry logic reads. Never check `result.error` for retry decisions.
- `WorkflowContext.outputs` is append-only during a run. Steps read previous outputs but cannot remove them.
- Prompt templates are files in `app/nlp/prompts/versions/`. Never hardcode prompts in Python.

---

## NLP Pipeline — Path 1

### Entry Point
`POST /api/workflows/generate` → `app/services/nl_workflow_service.py` → `NLPWorkflowService.generate()`

### Stage 1 — Catalog Matching
`CatalogMatcher` queries `trigger_definitions` and `action_definitions` tables.

Two strategies, in order:
1. **Keyword/alias** — exact substring match on `name`, `display_name`, `aliases` JSON array
2. **Semantic fallback** — fires only when keyword match returns nothing. Uses `SemanticCatalogRetriever` → pgvector cosine distance on 384-dim BAAI embeddings. Threshold: `distance < 0.30`.

The result is a merged list of matched triggers and actions. Both are passed to `SuitabilityAgent`.

### Stage 2 — Suitability
`SuitabilityAgent` rejects if:
- No trigger found → `trigger_not_found`
- No action found → `action_not_found`
- No workflow_type detected → `workflow_type_not_detected`

This is the last guardrail before any LLM call.

### Stage 3 — Prompt Building
`PromptBuilder` reads the active version from `PromptVersionStore` (in-memory), loads the template from `PromptRegistry`, and interpolates `{workflow_type}`, `{triggers}`, `{actions}`, `{user_request}`.

The prompt explicitly instructs the LLM to use action/trigger names **exactly as supplied**. This is critical — LLM hallucination of action names causes DLQ failures in execution.

### Stage 4 — LLM Generation + Retry Loop
`LLMManager` tries providers in order: Ollama → Gemini.

```
Attempt 1–3: primary provider
  → WorkflowGenerator.generate()
  → WorkflowResponseParser.parse()  (extract JSON from output)
  → SchemaValidator + WorkflowValidator
  → WorkflowCompilerService.compile()  (DSL → AST → DAG)
  → if valid: return compile_result
  → if invalid: WorkflowRepairService builds repair prompt → retry

Fallback (gemini forced):
  → same flow, 2 more attempts
  → if all fail: raise ValueError
```

**Provider health tracking** — 3 consecutive failures → provider disabled, 5-min cooldown. `auth_error` → 30-min disable. Success → reset. Auto re-enable after cooldown.

**Prompt auto-rollback** — 5 consecutive failures on active version → roll back to previous version automatically.

### Stage 5 — Compiler Chain
```
WorkflowCompilerService.compile(workflow_type, workflow_json)
    │
    ├── DSLGenerator.generate()
    │     Input: {"workflow": {"triggers": [...], "actions": [...]}}
    │     Output: "@1: payment_missed -> escalate_case\n@2 @depends(@1): ..."
    │
    ├── RuleParser.parse()
    │     Output: [ParseNode(step_id, event, action, depends_on)]
    │
    ├── WorkflowASTBuilder.build()
    │     Output: WorkflowAST(trigger, steps)
    │
    ├── ASTValidator.validate()
    │     Checks: trigger exists, no duplicate step IDs,
    │             all deps exist, no cycles (Kahn's algorithm)
    │
    └── WorkflowCompiler.compile()
          Output: {"version": "v2", "trigger": {event_type}, "steps": [...]}
```

Returns `compile_result = {"dsl": str, "ast": WorkflowAST, "compiled": dict}`.

### Stage 6 — Persistence
`WorkflowPersistenceService.save()` validates domain and writes to `workflows` table. `parsed_rule_json = compiled`.

---

## BRD Ingestion Pipeline — Path 2

### Entry Point
`POST /api/knowledge-ingestion/upload` → `app/routes/knowledge_ingestion.py` → `KnowledgeIngestionService.ingest(file_path)`

### Stage 1 — Document Extraction
`DocumentExtractor` tries PyPDF first. If no text extracted (scanned PDF), falls back to `OCRExtractor` (Tesseract + pdf2image/Poppler).

### Stage 2 — LLM Extraction
`WorkflowExtractor` calls Gemini with `WORKFLOW_EXTRACTION_PROMPT`. The prompt instructs extraction of:
- `triggers` — business events that start a workflow
- `action_references` — things the system does in response
- `business_rules` — conditional statements
- `actors` — people/roles involved
- `external_systems` — systems referenced

Returns validated `WorkflowExtraction` (Pydantic model).

### Stage 3 — Repository Save
`WorkflowRepository.save()` creates:
- `WorkflowKnowledge` (name, summary)
- `WorkflowTriggerMapping` per extracted trigger
- `WorkflowActionMapping` per extracted action
- `WorkflowBusinessRule`, `WorkflowActor`, `WorkflowExternalSystem`

### Stage 4 — Embedding Mapping
`EmbeddingMapper` encodes each extracted name using `all-MiniLM-L6-v2`, then queries `action_definitions` and `trigger_definitions` by cosine distance. Updates `matched_action_definition_id` and `matched_trigger_definition_id` on the mapping rows.

### Stage 5 — Action Configuration
`ActionConfigurationService.initialize_workflow()` creates `ActionConfiguration` rows for every mapped action:
```json
{"execution_type": "python", "handler": "action_definition.handler_name"}
```

This is the lookup path the dispatcher will eventually use.

---

## Execution Engine

### Entry Point
`POST /api/execute/` → Redis lpush `workflow_events` → `consumer.py` BRPOP → `runtime_processor()`

### DAG Execution
`dag_executor.run_dag_execution()` creates a `WorkflowContext`, then loops:

```
1. dag_scheduler.get_ready_steps() → steps whose all deps are in completed_steps
2. If 1 ready step: sequential execution
   If 2+ ready steps: parallel_step_executor (ThreadPoolExecutor)
3. For each result:
   - success → completed_steps.add(step_id)
              → context.update(result.outputs)
   - failure → failed_steps.add(step_id) → break
4. Repeat until no ready steps remain
```

### Step Execution
`step_executor.execute_workflow_step()` uses checkpoint labels for precise error location:

```
INIT → create_step_execution → mark_step_running →
record_step_started → inject_trace_into_payload →
execute_action → mark_step_completed/failed → handle_retry
```

The `checkpoint` variable tells you exactly which operation crashed.

### Dispatcher
`execute_action(action_name, payload, config) → ActionResult`

Resolution order:
1. `_PRODUCTION_ACTION_MAP` (in-memory dict, ~130 entries)
2. DB fallback — `action_definitions.handler_name` column → resolve to map entry
3. Unknown → `ActionResult(success=False, metadata={"skip_retry": True})`

All dict-returning handlers are auto-normalized to `ActionResult`. The normalization preserves all dict keys as `outputs` (excluding `success`, `status`, `skip_retry`, `message`, `error`).

### ActionResult Contract
```python
class ActionResult(BaseModel):
    success: bool
    outputs: dict[str, Any] = {}     # merged into WorkflowContext
    message: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = {}    # skip_retry, provider, latency
```

### WorkflowContext
```python
class WorkflowContext:
    entity_id: str | None
    outputs: dict[str, Any]          # accumulated across all steps

    def update(self, result_outputs) → None
    def to_payload() → dict           # entity_id + all outputs as flat dict
```

### Retry Logic
`retry_handler.handle_retry()` reads `result.success` only.

- `skip_retry=True` in metadata → immediate DLQ, no retries
- `should_retry(attempts)` → True if `attempts <= MAX_RETRIES` (default 5)
- Retry scheduled in Redis sorted set at `now + delay` where `delay = 30 * 2^(attempt-1)`
- `retry_worker` polls sorted set every 5s, atomically claims due items

### Reaper Recovery
`reaper_worker` scans `workflow_executions` for `status=RUNNING` and `updated_at < now - 60s`. Resets to PENDING, increments `attempts`. After 3 resets → DLQ.

---

## Module Reference

| Module | Path | Contract |
|---|---|---|
| `CatalogMatcher` | `app/nlp/catalog/matcher.py` | `.match(db, user_request) → CatalogMatchResult` |
| `SemanticCatalogRetriever` | `app/semantic/semantic_catalog_retriever.py` | `.retrieve(db, query, limit) → (triggers, actions)` |
| `SuitabilityAgent` | `app/nlp/suitability/suitability_agent.py` | `.evaluate(workflow_type, triggers, actions) → SuitabilityResult` |
| `PromptBuilder` | `app/nlp/prompts/builder.py` | `.build(context) → PromptBuildResult` |
| `LLMManager` | `app/nlp/llm_manager/llm_manager.py` | `.generate(prompt) → {success, output, provider, latency_ms}` |
| `WorkflowCompilerService` | `app/workflow/workflow_compiler_service.py` | `.compile(workflow_type, workflow_json) → {dsl, ast, compiled}` |
| `WorkflowPersistenceService` | `app/workflow/workflow_persistence_service.py` | `.save(db, name, domain, user_request, compile_result) → {workflow_id, ...}` |
| `KnowledgeIngestionService` | `app/knowledge_ingestions/service.py` | `.ingest(file_path) → WorkflowKnowledge` |
| `ActionConfigurationService` | `app/action_configuration/action_configuration_service.py` | `.initialize_workflow(workflow_knowledge_id)` |
| `execute_action` | `app/execution/dispatcher.py` | `(action_name, payload, config) → ActionResult` |
| `WorkflowContext` | `app/workflow_execution/context.py` | `.update(outputs)`, `.to_payload()` |

---

## Extension Points

### Adding a new action
1. Write handler in `app/execution/actions.py` or a domain file — return `ActionResult`
2. Register in `_PRODUCTION_ACTION_MAP` in `dispatcher.py`
3. Insert `action_definitions` row with `handler_name` set
4. Add name + aliases to DB catalog
5. Run `backfill_embeddings.py` to embed the new action
6. Add to prompt template `v1.txt` under Available Actions

### Adding a new LLM provider
1. Create `app/nlp/llm_manager/providers/<name>.py` — implement `try_call_<name>(prompt) → {success, output, ...}`
2. Add to `providers` list in `LLMManager.__init__`
3. Add to `FALLBACK_PROVIDERS` in `NLPWorkflowService` if it should be a fallback

### Adding a new execution type (HTTP, MCP, AI agent)
The `ActionConfiguration.configuration` JSONB field carries `execution_type`. The dispatcher currently only handles `python`. To add `http`:
1. Read `execution_type` from the configuration in `execute_action`
2. Route to an HTTP executor that reads `configuration["url"]`, POSTs payload, wraps response in `ActionResult`
3. No changes to step_executor, retry_handler, or dag_executor

### Adding a new BRD document type (DOCX, HTML)
Extend `DocumentExtractor.extract()` with a new `elif suffix == ".docx":` branch. OCR fallback already handles anything that becomes a rasterized image.

---

## Prompt Versioning

Templates live at `app/nlp/prompts/versions/workflow_generation/v1.txt`.

- `PromptRegistry` scans `versions/` at startup, caches all templates
- `PromptVersionStore` (in-memory) tracks `active` and `previous` per prompt name
- Auto-rollback: 5 consecutive failures → roll back to previous, log warning
- Manual rollback: `POST /api/prompts/workflow_generation/rollback`
- Promote: `POST /api/prompts/workflow_generation/activate {"version": "v2"}`

---

## Evaluation Logging

Every LLM generation attempt is logged to `generation_logs`:

| Field | Values |
|---|---|
| `provider` | `ollama` · `gemini` |
| `prompt_version` | `v1` · `v2` · ... |
| `success` | bool |
| `failure_reason` | `schema_fail` · `trigger_fail` · `action_fail` · `compile_fail` · `dependency_fail` · `llm_error` |
| `attempt_number` | 1–5 |
| `is_fallback` | bool |
| `latency_ms` | int |

Query: `GET /api/prompts/stats` → pass rate + avg latency by version.

---

## Startup Health Checks

`app/core/startup.py` runs three checks at startup via FastAPI lifespan:

| Check | What it verifies | On failure |
|---|---|---|
| `check_database()` | `SELECT 1` against Supabase | Logs ERROR, continues |
| `check_redis()` | `PING` to Redis | Logs ERROR, continues |
| `check_embedding_model()` | Encodes "warmup" string | Logs ERROR, continues |

Results cached in `startup_module._startup_results`.
`GET /api/health/ready` returns 503 if DB or Redis failed.

All checks are non-fatal — the app starts regardless. This prevents cold-start failures in environments where DB/Redis may be briefly unavailable.

---

## Known Issues / Technical Debt

| Issue | Location | Impact |
|---|---|---|
| `WorkflowRepairService` is a stub | `app/workflow/workflow_repair_service.py` | Retry loop sends same failed prompt — repair has no LLM call |
| `print` statement | `app/knowledge_ingestions/workflow_repository.py` | Debug artifact |
| CORS wildcard `"*"` | `app/main.py` | Fine for dev, tighten before public deploy |
| Embedding model `all-MiniLM-L6-v2` in `EmbeddingMapper` | Different from catalog embeddings (`BAAI/bge-small-en-v1.5`) | Vectors not comparable — fine since they're used in separate pipelines |
