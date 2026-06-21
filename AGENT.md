# AGENT.md — MFlows Development Guide

## Purpose

MFlows is an AI-powered workflow automation engine. It accepts a natural language request, runs it through a multi-stage NLP pipeline backed by LLMs, compiles the output to a validated AST, and executes it as a deterministic DAG with retry, DLQ, reaper recovery, and distributed tracing.

---

## Core Principle

All workflow creation paths converge at the same AST before compilation and execution.

```
Natural Language
        ↓
  CatalogMatcher (DB: trigger/action lookup)
        ↓
  DomainDetector + SuitabilityAgent
        ↓
  PromptBuilder (versioned template + token estimate)
        ↓
  LLMManager (Ollama → Gemini, health-tracked, timeout-bound)
        ↓
  WorkflowGenerator (LLM call → parse JSON response)
        ↓
  _validate_workflow()
  (SchemaValidator → WorkflowValidator → DSLGenerator → DSLValidator)
        ↓
  [repair loop: max 3 retries + gemini fallback]
        ↓
  dag_orchestrator.parse_dag_workflow(dsl)
        ↓
  parsed_rule_json saved to DB
        ↓
  Runtime Processor (Redis queue → DAG execution)
```

The runtime never knows or cares how the workflow was produced.

---

## Rules

- Never execute raw LLM output. Always validate through the pipeline first.
- Never bypass `_validate_workflow()`. Schema + business rules + DSL must all pass.
- LLM calls only happen inside `app/nlp/` — never inside `app/execution/`.
- Keep runtime deterministic — no ML or LLM calls inside the execution layer.
- Do not place business logic inside `runtime_processor`.
- Prompt templates live in `app/nlp/prompts/versions/`. Never hardcode prompts inline.
- All trigger and action names must stay in sync across registries — see Registries section.

---

## Module Boundaries

| Layer | Location | Responsibility |
|---|---|---|
| Catalog | `app/nlp/catalog/` | DB lookup of active triggers + actions |
| Domain Detection | `app/nlp/domain/` | workflow_type detection from matched catalog |
| Suitability | `app/nlp/suitability/` | guardrail — rejects unsupported requests |
| Prompt System | `app/nlp/prompts/` | versioned templates, builder, version store, eval |
| LLM Manager | `app/nlp/llm_manager/` | provider routing, health tracking, timeouts |
| NLP Pipeline | `app/nlp/services/` | orchestrates full NL → DSL generation |
| Workflow Objects | `app/workflow/` | generator, validator, repair, DSL builder |
| DSL Layer | `app/dsl/` | DSL generation and validation |
| Parser | `app/parsers/` | DSL → steps, DAG validation, LLM repair |
| NL Extraction | `app/nlp/nl/` | rule-based NL → ParseNode list (no LLM) |
| AST | `app/nlp/ast/` | ParseNode list → WorkflowAST, validation |
| Compiler | `app/nlp/complier/` | WorkflowAST → v2 DAG dict |
| Runtime | `app/execution/runtime/` | DAG dict → step execution |
| Dispatcher | `app/execution/dispatcher.py` | action name → handler function |

---

## Prompt System — How It Works

### Directory layout
```
app/nlp/prompts/
├── versions/
│   └── workflow_generation/
│       ├── v1.txt       ← active
│       └── v2.txt       ← future
├── builder.py           ← builds prompt, returns PromptBuildResult
├── prompt_context.py    ← PromptContext dataclass (input to builder)
├── prompt_registry.py   ← loads all versions from disk at startup
├── prompt_version.py    ← PromptVersion dataclass
├── prompt_version_store.py  ← tracks active/previous version + auto-rollback
└── token_estimator.py   ← estimates token count (len // 4 heuristic)
```

### PromptBuildResult
Every `PromptBuilder.build()` call returns:
```python
PromptBuildResult(
    prompt="...",           # interpolated template string
    prompt_name="workflow_generation",
    version="v1",           # active version at call time
    estimated_tokens=312,   # len(prompt) // 4
)
```
This is logged on every generation attempt.

### Versioning
- `PromptRegistry` — scans `versions/` at startup, caches all templates
- `PromptVersionStore` — in-memory active/previous state per prompt_name
- `set_active(name, version)` — promotes version, saves current as rollback target
- `rollback(name)` — swaps active ↔ previous

### Auto-rollback (Phase 5)
After 5 consecutive failures on the active version, the system automatically rolls back to the previous version and logs a warning. Threshold is `AUTO_ROLLBACK_THRESHOLD = 5` in `prompt_version_store.py`.

---

## LLM Layer — How It Works

### Providers
```
app/nlp/llm_manager/
├── providers/
│   ├── ollama.py        ← primary, configurable timeout, classified errors
│   └── gemini_rest.py   ← secondary, auth error → immediate 30-min disable
├── llm_manager.py       ← provider routing + health tracking
└── provider_health.py   ← in-memory health state, cooldown logic
```

### Health tracking
- 3 consecutive failures → provider disabled, 5-minute cooldown
- `auth_error` → disabled immediately, 30-minute cooldown
- Success → failure count reset
- Cooldown expired → auto re-enabled on next call

### Timeouts (env vars)
| Variable | Default |
|---|---|
| `OLLAMA_TIMEOUT_SECONDS` | 10 |
| `GEMINI_TIMEOUT_SECONDS` | 10 |

### Error types classified
`timeout` · `connection_error` · `auth_error` · `http_error` · `unexpected`

---

## Generation Retry Loop

Inside `NLPWorkflowService.generate()`:

```
Attempt 1–3  (primary provider, ollama → gemini order)
    → generate → validate → if fail → repair prompt → retry

Attempt 4–5  (fallback: gemini forced)
    → generate with gemini → validate → if fail → one repair → retry

All exhausted → raise ValueError with last errors
```

---

## Evaluation Logging (Phase 3)

Every attempt is logged to `generation_logs` table:

| Field | Description |
|---|---|
| `user_request` | Original NL input |
| `prompt_name` | e.g. `workflow_generation` |
| `prompt_version` | e.g. `v1` |
| `estimated_tokens` | Token estimate |
| `provider` | `ollama` or `gemini` |
| `attempt_number` | 1–5 |
| `is_fallback` | True if fallback provider |
| `success` | True/False |
| `failure_reason` | `schema_fail` · `dsl_fail` · `trigger_fail` · etc. |
| `latency_ms` | Time for that attempt |

Query stats with `GET /api/prompts/stats`.

---

## Registries

Triggers and actions must stay in sync across these locations:

| File | Purpose |
|---|---|
| `app/parsers/schemas.py` | Single source of truth — ALLOWED_TRIGGERS, ALLOWED_ACTIONS |
| `app/parsers/dag_validator.py` | DSL DAG validation (imports from schemas.py) |
| `app/nlp/nl/patterns.py` | NL phrase → canonical identifier mapping |
| `app/nlp/prompts/versions/workflow_generation/v1.txt` | LLM prompt lists |

When adding a new trigger or action — update all four.

---

## Protected — Do Not Modify

Only bug fixes allowed on these:

- `app/execution/runtime/runtime_processor.py`
- `app/execution/runtime/dag_executor.py`
- `app/workers/retry_worker.py`
- `app/workers/reaper_worker.py`
- `app/execution/dedupe.py`
- `app/execution/runtime/workflow_finalizer.py`
- `app/db/` and `alembic/` (existing migrations)

---

## API Surface

```
POST   /api/workflows/generate          NL → workflow (full pipeline)
GET    /api/workflows/                  list workflows
GET    /api/workflows/{id}              get workflow

POST   /api/execute/                    queue execution
POST   /api/execute/{id}/pause
POST   /api/execute/{id}/resume

GET    /api/health/providers            LLM provider health state
POST   /api/health/providers/{name}/reset   manually re-enable provider

GET    /api/prompts/                    list prompts + active versions
GET    /api/prompts/stats               pass rate / avg retries by version
GET    /api/prompts/{name}/state        version state for one prompt
POST   /api/prompts/{name}/activate     promote a version
POST   /api/prompts/{name}/rollback     manual rollback
GET    /api/prompts/{name}/failures     last N failures for debugging
```

---

## Adding a New Trigger or Action

1. Add to `app/parsers/schemas.py` — `ALLOWED_TRIGGERS` or `ALLOWED_ACTIONS`
2. Add phrase mappings to `app/nlp/nl/patterns.py`
3. Add to `app/nlp/prompts/versions/workflow_generation/v1.txt`
4. Add handler in `app/execution/dispatcher.py`
5. Add domain action if needed in `app/execution/domain_actions/`

---

## Adding a New Prompt Version

1. Create `app/nlp/prompts/versions/workflow_generation/v2.txt`
2. Test via `test.py`
3. Promote via `POST /api/prompts/workflow_generation/activate` with `{"version": "v2"}`
4. Monitor via `GET /api/prompts/stats`
5. Rollback via `POST /api/prompts/workflow_generation/rollback` if pass rate drops
