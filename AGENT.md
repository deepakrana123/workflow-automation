# AGENT.md — MFlows Engineering Reference

> This document is for engineers working on or reviewing the MFlows codebase.
> It covers architecture decisions, module contracts, extension points, and invariants.
>
> **Precedence:** where this document and the code disagree, the code and the
> "Current Architecture" section below are authoritative. Older sections are
> kept for context but may describe superseded designs (noted inline).

---

## Current Architecture & Working Agreements (authoritative — read first)

### Product scope (do NOT drift from this)
MFlows is a **banking workflow AI platform**, not a generic automation tool.
Keep it simple, deterministic, and auditable. The following are **deliberate,
accepted decisions — do not "helpfully" add them or argue to change them
without being asked:**

- **No authentication / authorization / multi-tenant enforcement** — intentionally out of scope (demo). The architecture leaves seams for it; don't build it unprompted.
- **No autonomous agents, no planner, no MCP, no multi-agent** — the AI is a **deterministic pipeline** (Workspace → Retrieval → Extraction → Mapping → Compilation → Validation → Execution). Any stage may later be swapped for an agent; today it stays a pipeline.
- **Don't over-engineer for enterprise scale** — target ~40–50 actions, ~20–30 BRDs. No sharding, no event-sourcing, no CQRS.

### How to work in this codebase
- **Audit → design → build.** For anything touching the execution core, confirm the design before coding.
- **New logic ships with unit tests.** Prefer pure, dependency-injected functions so they test without DB/LLM. Tests live in `tests/unit/`; run `python -m pytest tests/unit -q`.
- **Derived-not-stored** for read models (provenance, workspace synthesis) — project over existing data, no new tables unless necessary.
- **Gate risky runtime changes** behind opt-in markers so existing workflows are byte-for-byte unaffected (see the rule-engine `routing` gate).
- Deterministic layers are fully testable here; **DB/Redis/LLM-coupled paths are verified in the deployed environment** — say so honestly.

### Current execution model (SUPERSEDES the old "Dispatcher" section)
Dispatch is via an **ExecutorRegistry**, not a `dispatcher.py` (that source is retired; only a stale `.pyc` remains).

```
step_executor.execute_workflow_step()
  → resolve_action_configuration(action)        → (ActionConfiguration, execution_type)
  → ExecutorRegistry.get_executor(execution_type)
  → executor.execute(configuration, context)     → ActionResult
```

- **`ExecutionType`** (`app/execution/executors/constants.py`): `python`, `http`, `human_task`. (`mcp`, `kafka`, `ai_agent` are reserved in the schema, not built.)
- **`PythonExecutor`** → looks up `configuration["handler"]` in `ACTION_HANDLER_MAP` (`app/execution/python/action_handler_registry.py`). Document generators (`generate_pdf/csv/excel`) are registered here and persist via the file storage layer.
- **`HttpExecutor`** → uses the bound `WorkspaceIntegration` (base_url/auth) + `configuration["response_mapping"]` to normalize the external response into `outputs`.
- **`HumanExecutor`** → returns an `ActionResult` with `metadata["execution_status"] == "WAITING"` + a `human_task` spec; it does **not** complete synchronously.

### Subsystems added since the original doc
- **File storage** (`app/storage/`): `StorageProvider` (ABC) → `LocalStorageProvider`; `FileStorageService.store()/retrieve()`. Generators return `{file_id, storage_path}` in outputs (not raw bytes).
- **Human approval + resumable DAG:** `human_task` executor + `HumanTask` model + `human_task_service` (approve/reject, timeout via reaper). The DAG executor **rehydrates completed/failed/waiting/skipped steps + per-step outputs** from `execution_steps` for **exactly-once** resume. Never re-run a completed step.
- **Rule engine core** (`app/execution/rules/`): `evaluate_condition` (pure, total — never raises), `resolve_activated_children` (parent-decides-child routing), `resolve_skipped_steps` (SKIPPED cascade). Runtime is gated on a compiled step carrying a `routing` key. v1 = tree branches (no diamond merges).
- **Output contract:** `output_validation.py` validates a step's outputs against the action's `output_schema` (non-fatal; attached to `metadata`). Rules ground onto declared fields.
- **Multi-BRD:** `workspace_synthesis` (dedup + provenance across BRDs) and `workspace_workflow_synthesizer` (aggregate → sequential DAG → compile). Workspaces have CRUD.
- **Provenance / Explanation:** `workflow_provenance` (step → source BRD clause + confidence, derived) and `workflow_explainer` (deterministic, catalog-grounded, stored on `Workflow.explanation`).

### Workspace-scoped workflow generation (authoritative — added most recently)

The workspace is now the **primary context** for AI generation. There are two
generation paths and they are deliberately kept separate:

- **Global NL generation (unchanged):** `POST /api/workflows/generate` →
  `NLPWorkflowService.generate(user_request)` grounds the LLM in the **entire**
  global catalog via `CatalogMatcher` + `SemanticCatalogRetriever`. Still the
  behavior of the standalone `/workflows/generate` screen. Untouched.
- **Workspace-scoped generation (new):** `POST /api/workspaces/{id}/generate` →
  `generate_workspace_workflow_service(...)`. Grounds the LLM **only** in the
  workspace's mapped actions/triggers (+ explicitly selected globals) and the
  workspace business rules. The global catalog is never auto-injected.

Key rule: **the global catalog is a library, not an ingredient.** In the
workspace path it is reachable only when the user explicitly passes
`selected_action_ids` (the frontend "+ Add Action" picker). This is enforced
structurally — the workspace matcher never calls `get_active()`.

**New / changed modules:**

| Module | Path | Contract |
|---|---|---|
| `WorkspaceCatalogMatcher` | `app/nlp/catalog/workspace_catalog_matcher.py` | `.match(workspace_id, selected_action_ids) → CatalogMatchResult`. Queries ONLY workspace-mapped `ActionDefinition`/`TriggerDefinition` (joined through `WorkflowActionMapping`/`WorkflowTriggerMapping` by `workspace_id`) + selected globals. Pure assembly split into `build_workspace_match_result(...)`. |
| `WorkspaceContextService` | `app/workflow/workspace_context.py` | `.overview/.documents/.business_rules/.actions(db, workspace_id)` — read-only projections over existing knowledge. Reuses `WorkspaceSynthesisService`. Pure builders: `build_overview`, `build_document_view`, `build_workspace_prompt_vars`. |
| rule conflicts | `app/workflow/rule_conflicts.py` | `detect_rule_conflicts(rules) → [threshold_conflict, ...]`. Pure, deterministic: flags cross-BRD monetary-threshold conflicts (e.g. approval above ₹5L vs ₹10L). Surfaces only — never resolves. |
| workspace generation | `app/services/nl_workflow_service.py` | `generate_workspace_workflow_service(db, workspace_id, name, user_request, domain, selected_action_ids)` — orchestrates matcher + v2 prompt + persist. |
| `NLPWorkflowService.generate` | `app/nlp/services/nl_workflow_service.py` | now accepts `catalog_result=`, `extra_variables=`, `prompt_version=` (all optional, backward-compatible). |

**Prompt:** a new versioned template `app/prompting/versions/workflow_generation/v2.txt`
(= v1 + `{workspace_summary}` + `{business_rules}`) is used **only** via an
explicit `version="v2"` pin. The active global version stays `v1` and
auto-rollback is unaffected.

**New workspace endpoints** (`app/routes/workspaces.py`):
`GET /{id}/overview`, `GET /{id}/documents`, `GET /{id}/business-rules`,
`GET /{id}/actions`, `POST /{id}/generate`. (Existing `/{id}/synthesis` and
`/{id}/synthesize` — deterministic, no LLM — remain.)

**Schema change:** `workflows.workspace_id` (nullable FK → `workspaces.id`,
migration `b8d4e5f6a7c9`). Set by both workspace paths (AI generate +
deterministic synthesize); NULL for global generation. Enables per-workspace
workflow counts (`WorkspaceContextService.overview.workflow_count`).

**Invariants for this feature:**
- Workspace generation NEVER queries the global catalog; leakage is only via
  explicit `selected_action_ids`.
- v1 (global) prompt and its rollback behavior are unchanged.
- Conflicts are surfaced (in `synthesis.review_flags` as `rule_conflict` and on
  `GET /{id}/business-rules`), never auto-resolved.
- Deterministic synthesis and AI generation coexist as distinct actions.
- Pure builders live in dependency-light modules and are unit-tested
  (`tests/unit/test_workspace_*`, `test_rule_conflicts.py`); DB/LLM-coupled
  paths are verified in the running environment.

### Updated invariants (in addition to those below)
- Every executor returns `ActionResult`; the `WAITING` marker in `metadata` is checked **before** success/failure.
- A **completed step never re-runs** on resume (rehydration guarantees exactly-once).
- **Routing is opt-in** — steps without a `routing` key behave exactly as before.
- **Provenance/synthesis are derived** — never persisted as duplicate state.
- `WorkflowContext` lives at `app/workflow_execution/schemas/workflow_context.py` and now carries **both** flat `outputs` and per-step `steps["<id>"]["<field>"]`.

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
- Prompt templates are files in `app/prompting/versions/`. Never hardcode prompts in Python.

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

### Dispatcher  ⚠️ SUPERSEDED — see "Current execution model" at the top
> This `execute_action` / `_PRODUCTION_ACTION_MAP` / `dispatcher.py` model is
> **retired**. Dispatch is now `ExecutorRegistry.get_executor(execution_type)`
> → `executor.execute(configuration, context)`. Python handlers live in
> `ACTION_HANDLER_MAP` (`app/execution/python/action_handler_registry.py`).
> The text below is kept only for historical context.

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

### Adding a new execution type (MCP, Kafka, AI agent)
`python`, `http`, and `human_task` already exist. To add another (the seam is the executor registry — no engine surgery):
1. Add the type to `ExecutionType` (`app/execution/executors/constants.py`).
2. Implement `MyExecutor(BaseExecutor).execute(configuration, context) → ActionResult`, reading `ActionConfiguration.configuration` (and `workspace_integration` for connection/secrets).
3. Register it in `ExecutorRegistry` (`app/execution/executors/registry.py`).
4. No changes to `step_executor`, `retry_handler`, `dag_executor`, or the finalizer — dispatch, retry, tracing, and file storage come for free.

(An action that produces a file should persist via `FileStorageService` and return `{file_id, storage_path}` in `outputs`, like the generators.)

### Adding a new BRD document type (DOCX, HTML)
Extend `DocumentExtractor.extract()` with a new `elif suffix == ".docx":` branch. OCR fallback already handles anything that becomes a rasterized image.

---

## Prompt Versioning

Templates live at `app/prompting/versions/workflow_generation/v1.txt`.

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
