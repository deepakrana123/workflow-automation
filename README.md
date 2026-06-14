# MFlows — AI Workflow Automation Engine

A production-grade workflow engine that converts natural language requests into executable DAGs, backed by a multi-LLM pipeline with retry, repair, provider health tracking, versioned prompts, and full execution observability.

---

## What It Does

You send a sentence. MFlows produces a running workflow.

```
"When payment is due send reminder then notify manager"
                    ↓
         Executable DAG with retry, DLQ,
         distributed tracing, and reaper recovery
```

No manual DSL authoring. No drag-and-drop. Natural language in, working automation out.

---

## Architecture

```
POST /api/workflows/generate
        │
        ▼
   CatalogMatcher          ← DB lookup: find matching triggers + actions
        │
        ▼
   DomainDetector           ← detect workflow domain (finance, health, support...)
        │
        ▼
   SuitabilityAgent         ← reject unsupported or ambiguous requests
        │
        ▼
   PromptBuilder            ← load versioned template, interpolate context,
        │                      estimate token count
        ▼
   LLMManager               ← health-tracked, timeout-bound
   (Ollama → Gemini)           3 retries + gemini fallback
        │
        ▼
   WorkflowGenerator        ← parse LLM JSON response
        │
        ▼
   _validate_workflow()     ← schema → business rules → DSL → DAG
        │
   [repair loop if fail]    ← WorkflowRepairService → retry
        │
        ▼
   dag_orchestrator         ← parse DSL → v2 step format
        │
        ▼
   parsed_rule_json → DB    ← workflow persisted
        │
        ▼
POST /api/execute/
        │
        ▼
   Redis queue → Worker
        │
        ▼
   DAG Execution
   (scheduler → step executor → dispatcher → action handler)
        │
        ▼
   Retry / DLQ / Reaper / Tracing
```

---

## Infrastructure

| Component | Technology |
|---|---|
| API | FastAPI |
| Database | PostgreSQL · SQLAlchemy · Alembic |
| Queue | Redis (BRPOP + sorted set retry) |
| LLM Primary | Ollama (local, qwen2.5:7b) |
| LLM Fallback | Google Gemini REST |
| Tracing IDs | ULID |
| Workers | API · Retry · Reaper |

---

## NLP Pipeline

```
app/nlp/
├── catalog/                 DB-backed trigger + action lookup
│   ├── matcher.py           CatalogMatcher — matches user request against catalog
│   ├── triggerRepository.py TriggerDefinitionRepository
│   └── actionRepository.py  ActionDefinitionRepository
├── domain/
│   └── domain_detector.py   Detects workflow_type from matched catalog entries
├── suitability/
│   └── suitability_agent.py Rejects if domain/trigger/action missing
├── prompts/
│   ├── versions/
│   │   └── workflow_generation/
│   │       └── v1.txt       Active prompt template
│   ├── builder.py           Builds PromptBuildResult (prompt + version + tokens)
│   ├── prompt_registry.py   Loads all versions from disk at startup
│   ├── prompt_version_store.py  Active version tracking + auto-rollback
│   └── token_estimator.py   Token count estimate (len // 4)
├── llm_manager/
│   ├── providers/
│   │   ├── ollama.py        10s timeout, classified errors
│   │   └── gemini_rest.py   10s timeout, auth error → 30-min disable
│   ├── llm_manager.py       Provider routing + health integration
│   └── provider_health.py   In-memory health state, cooldown, auto re-enable
├── services/
│   └── nl_workflow_service.py  Full pipeline orchestrator with eval logging
├── ast/                     ParseNode list → WorkflowAST
├── complier/                WorkflowAST → v2 DAG dict
└── nl/                      Rule-based NL → ParseNode (no LLM)
```

---

## Prompt System

Every generation uses a versioned prompt template:

- Templates live in `app/nlp/prompts/versions/<name>/<version>.txt`
- Active version tracked in `PromptVersionStore` (in-memory, swappable to Redis)
- Promote a version: `POST /api/prompts/workflow_generation/activate`
- Roll back: `POST /api/prompts/workflow_generation/rollback`
- Auto-rollback: after 5 consecutive failures on active version, system rolls back automatically

Every attempt logs: prompt version · provider · attempt number · success/fail · failure reason · latency · estimated tokens.

---

## LLM Health Tracking

| Condition | Behavior |
|---|---|
| 3 consecutive failures | Provider disabled, 5-min cooldown |
| Auth error (401/403) | Provider disabled immediately, 30-min cooldown |
| Cooldown expired | Auto re-enabled on next call |
| Manual override | `POST /api/health/providers/{name}/reset` |

Check state: `GET /api/health/providers`

---

## Retry and Repair

| Phase | What happens |
|---|---|
| Attempt 1 | Generate with primary provider |
| Attempts 2–3 | Repair prompt (errors + original) → retry primary |
| Fallback 1 | Force Gemini with original prompt |
| Fallback 2 | Repair prompt → retry Gemini |
| Exhausted | `ValueError` with last errors |

---

## Execution Engine

```
POST /api/execute/
  → WorkflowRun + WorkflowExecution created
  → Redis lpush "workflow_events"

Worker (BRPOP)
  → runtime_processor → mark RUNNING
  → dag_executor (dependency scheduler)
    → parallel_step_executor
      → step_executor → dispatcher → action handler
      → SUCCESS: mark COMPLETED, trace event written
      → FAILURE: retry_handler → exponential backoff → DLQ after max retries
  → workflow_finalizer (derives final state from step graph)

Reaper Worker
  → scans for RUNNING executions stuck > 60s → marks FAILED → recovers
```

---

## Chaos Testing

Set `CHAOS_MODE=true` to route all action dispatches through the chaos engine.

Modes: `success` · `always_fail` · `timeout` · `slow` · `gateway_error` · `rate_limit` · `auth_error` · `bad_payload` · `partial_success` · `flaky` · `fail_on_attempt` · `succeed_after_retries`

---

## Getting Started

```bash
git clone <repo>
cd mflows
cp .env.example .env
# Set DATABASE_URL, GEMINI_API_KEY, GEMINI_MODEL, REDIS_HOST

alembic upgrade head
docker-compose up --build
```

Services: `api` (8000) · `worker` · `retry_worker` · `reaper_worker` · `redis`

---

## API Reference

```http
# Workflow Creation
POST /api/workflows/generate
Body: { "user_request": "...", "name": "...", "domain": "..." }

# Workflow Read
GET  /api/workflows/
GET  /api/workflows/{id}

# Execution
POST /api/execute/
POST /api/execute/{id}/pause
POST /api/execute/{id}/resume

# LLM Health
GET  /api/health/providers
POST /api/health/providers/{name}/reset

# Prompt Management
GET  /api/prompts/
GET  /api/prompts/stats
GET  /api/prompts/{name}/state
POST /api/prompts/{name}/activate     Body: { "version": "v2" }
POST /api/prompts/{name}/rollback
GET  /api/prompts/{name}/failures
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | required | PostgreSQL connection string |
| `REDIS_HOST` | `localhost` | Redis hostname |
| `GEMINI_API_KEY` | required | Google Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name |
| `OLLAMA_URL` | `host.docker.internal:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Ollama model |
| `OLLAMA_TIMEOUT_SECONDS` | `10` | Ollama request timeout |
| `GEMINI_TIMEOUT_SECONDS` | `10` | Gemini request timeout |
| `CHAOS_MODE` | `false` | Enable chaos action routing |

---

## Current Status

### Completed
- NL → Workflow pipeline (CatalogMatcher → LLM → Validate → DSL → DB)
- Multi-LLM provider routing (Ollama primary, Gemini fallback)
- LLM health tracking with cooldown and auto re-enable
- Configurable timeouts with classified error types
- 3-retry repair loop + provider fallback
- Versioned prompt system with file-based templates
- Prompt evaluation logging (every attempt recorded)
- Auto-rollback on 5 consecutive prompt failures
- Token estimation per prompt build
- Runtime Engine (DAG executor, step executor, finalizer)
- Retry Engine (exponential backoff, DLQ, retry worker)
- Reaper Recovery (stuck execution detection)
- Distributed Locking (Redis NX)
- Distributed Tracing (ULID trace_id / span_id)
- DSL Parser + DAG Validator
- AST Builder + AST Validator + Workflow Compiler
- Chaos testing engine (13 modes)
- Full API surface with health + prompt management endpoints

### Next
- 500+ chaos test suite across all pipeline stages
- Semantic search for CatalogMatcher (pgvector on Supabase)
- Multi-tenant workflow isolation
- Agent workflows (multi-step LLM reasoning)
