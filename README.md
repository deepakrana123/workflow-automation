# MFlows — AI Workflow Automation Engine

A production-grade workflow engine that converts natural language into executable DAGs — backed by a multi-LLM pipeline, a compiler chain (DSL → AST → DAG), distributed execution with retry/DLQ/reaper, and full observability.

---

## What It Does

You send a sentence. MFlows produces a running workflow.

```
"When payment is missed escalate case and notify manager then create audit record"
                              ↓
          @1: payment_missed -> escalate_case
          @2: payment_missed -> notify_manager
          @3 @depends(@1,@2): payment_missed -> create_audit_record
                              ↓
             Executable DAG — steps 1+2 run in parallel,
             step 3 runs after both complete
                              ↓
             PENDING → RUNNING → COMPLETED
             with retry, DLQ, reaper recovery, and distributed tracing
```

No manual DSL authoring. No drag-and-drop. Natural language in, working automation out.

---

## Test Results (Today)

| Suite | Result |
|---|---|
| `test_full_pipeline.py` — 8 execution patterns | ✅ 8/8 |
| `test_dsl_pipeline.py` — DSL → AST → Compiler | ✅ 5/5 |
| `test_nlp_to_dsl.py` — Real DB + Real LLM | ✅ 3/3 |
| `test.py --category A` — Full API (NL → save) | ✅ 5/5 |

Patterns tested: sequential chain, parallel fan-out, diamond, diamond+tail, deep 4-step chain, 3-way parallel, minimal single-step, full support flow.

---

## Architecture

```
POST /api/workflows/generate
        │
        ▼
   CatalogMatcher          ← DB lookup: active triggers + actions
        │                     substring + alias match on user request
        ▼
   SuitabilityAgent         ← reject if trigger/action/domain missing
        │
        ▼
   PromptBuilder            ← versioned template + token estimate
        │
        ▼
   LLMManager               ← Ollama (primary) → Gemini (fallback)
   (health-tracked)            3 retries + repair loop on failure
        │
        ▼
   WorkflowResponseParser   ← extract + normalize LLM JSON output
        │
        ▼
   SchemaValidator          ← structure check
   WorkflowValidator        ← trigger count, action deps
        │
        ▼
   WorkflowCompilerService  ← DSLGenerator → RuleParser → ASTBuilder
        │                      → ASTValidator → WorkflowCompiler
        ▼
   parsed_rule_json          ← {"version":"v2", "trigger":{}, "steps":[]}
        │
        ▼
   WorkflowPersistenceService ← save to DB
        │
        ▼
POST /api/execute/
        │
        ▼
   Redis queue → consumer worker
        │
        ▼
   runtime_processor → mark RUNNING
   dag_executor → dag_scheduler (ready steps)
     → parallel_step_executor (fan-out)
       → step_executor → dispatcher → action handler
       → retry_handler → exponential backoff → DLQ
   workflow_finalizer → COMPLETED / FAILED / DLQ
        │
        ▼
   reaper_worker — recovers stuck RUNNING executions
   retry_worker  — processes exponential backoff retries
```

---

## Compiler Chain

Natural language → DSL → AST → executable DAG:

```
LLM JSON output
  {"workflow": {"triggers": [...], "actions": [...]}}
        │
        ▼
  DSLGenerator
        │  @1: payment_missed -> escalate_case
        │  @2: payment_missed -> notify_manager
        │  @3 @depends(@1,@2): payment_missed -> create_audit_record
        ▼
  RuleParser          → ParseNode list
  WorkflowASTBuilder  → WorkflowAST (trigger + steps)
  ASTValidator        → cycle detection, duplicate ids, unknown deps
  WorkflowCompiler    → {"version":"v2", "trigger":{}, "steps":[...]}
```

The compiler is fully independent — testable without an LLM. The `test_dsl_pipeline.py` suite validates it with injected JSON.

---

## Infrastructure

| Component | Technology |
|---|---|
| API | FastAPI |
| Database | PostgreSQL · SQLAlchemy · Alembic |
| Hosted DB | Supabase |
| Queue | Redis (BRPOP consumer + sorted set retry) |
| LLM Primary | Ollama (local, configurable model) |
| LLM Fallback | Google Gemini REST |
| Tracing IDs | ULID |
| Workers | consumer · retry_worker · reaper_worker |

---

## NLP Pipeline

```
app/nlp/
├── catalog/            DB-backed trigger + action lookup with alias matching
├── suitability/        Rejects unsupported requests before LLM call
├── prompts/            Versioned templates, auto-rollback, token estimation
├── llm_manager/        Provider routing, health tracking, classified errors
├── services/           NLPWorkflowService — full orchestration with eval logging
├── ast/                ParseNode → WorkflowAST, cycle detection
├── parsers/            RuleParser — @step DSL → ParseNode list
└── complier/           WorkflowAST → v2 DAG dict
```

---

## Execution Patterns Supported

| Pattern | Example |
|---|---|
| Sequential | remind → escalate → notify |
| Parallel fan-out | escalate + notify (no join) |
| Diamond | assign → (notify_customer \|\| notify_manager) → close |
| Diamond + tail | escalate + notify → audit |
| Deep chain | lock → flag → notify → audit |
| Wide parallel | alert + notify + escalate (3-way) |

---

## Prompt System

- Templates in `app/nlp/prompts/versions/<name>/<version>.txt`
- Active version in `PromptVersionStore` (in-memory, swappable to Redis)
- Auto-rollback after 5 consecutive failures on active version
- Every attempt logged: version · provider · latency · success/fail · failure reason

```http
POST /api/prompts/workflow_generation/activate   {"version": "v2"}
POST /api/prompts/workflow_generation/rollback
GET  /api/prompts/stats
```

---

## LLM Health Tracking

| Condition | Behavior |
|---|---|
| 3 consecutive failures | Provider disabled, 5-min cooldown |
| Auth error | Provider disabled immediately, 30-min cooldown |
| Cooldown expired | Auto re-enabled on next call |
| Manual override | `POST /api/health/providers/{name}/reset` |

---

## Retry and Repair Loop

| Phase | What happens |
|---|---|
| Attempt 1–3 | Generate → validate → compile. If fail, repair prompt → retry |
| Fallback 1 | Force Gemini with original prompt |
| Fallback 2 | Repair prompt → retry Gemini |
| Exhausted | `ValueError` with last errors |

---

## Execution Engine

```
POST /api/execute/
  → WorkflowRun + WorkflowExecution created (PENDING)
  → Redis lpush "workflow_events"

consumer worker (BRPOP)
  → runtime_processor → RUNNING
  → dag_executor → dag_scheduler (finds ready steps by dependency)
    → parallel_step_executor (concurrent threads for parallel steps)
      → step_executor → dispatcher → action handler
        SUCCESS: mark COMPLETED + trace event
        FAILURE: retry_handler → exponential backoff (30s, 60s, 120s...)
                 → DLQ after MAX_RETRIES
  → workflow_finalizer
      all COMPLETED → mark workflow COMPLETED
      any DLQ      → mark workflow FAILED
      any RETRY    → defer finalization

reaper_worker (every 5s)
  → finds RUNNING executions stuck > 60s
  → marks FAILED → re-queues → max 3 recovery attempts → DLQ

retry_worker (every 5s)
  → reads sorted set by score (retry_at timestamp)
  → executes due retries atomically (pipeline zrem)
```

---

## Chaos Testing

Set `CHAOS_MODE=true` to route all dispatches through the chaos engine.

Modes: `success` · `always_fail` · `timeout` · `slow` · `gateway_error` · `rate_limit` · `auth_error` · `bad_payload` · `partial_success` · `flaky` · `fail_on_attempt` · `succeed_after_retries`

---

## Getting Started

```bash
git clone <repo>
cd mflows
cp .env.example .env
# Set DATABASE_URL, GEMINI_API_KEY, REDIS_HOST

alembic upgrade head
docker-compose up --build
```

Services started: `api:8000` · `worker` · `retry_worker` · `reaper_worker` · `redis`

**Run only API + Redis (skip workers):**
```bash
docker-compose up --build api redis
```

---

## Quick Test

```bash
# Generate a workflow
curl -X POST http://localhost:8000/api/workflows/generate \
  -H "Content-Type: application/json" \
  -d '{"user_request": "When payment is missed escalate case and notify manager", "name": "payment-flow", "domain": "payments"}'

# Execute it
curl -X POST http://localhost:8000/api/execute/ \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": 1, "entity_id": "customer-001"}'
```

---

## Test Suites

```bash
# DSL → AST → Compiler (no Docker needed)
python test_dsl_pipeline.py

# Real DB + Real LLM → DSL (needs api + redis)
python test_nlp_to_dsl.py

# Full execution: compile → save → execute → COMPLETED (needs all services)
python test_full_pipeline.py
python test_full_pipeline.py --id P03   # single case

# Full API chaos suite
python test.py --category A --verbose
python test.py --verbose
```

---

## API Reference

```http
POST /api/workflows/generate        NL → compile → save
GET  /api/workflows/                list workflows
GET  /api/workflows/{id}            get workflow

POST /api/execute/                  queue execution
POST /api/execute/{id}/pause
POST /api/execute/{id}/resume

GET  /api/health/providers          LLM provider health
POST /api/health/providers/{name}/reset

GET  /api/prompts/                  list prompts + versions
GET  /api/prompts/stats             pass rate by version
POST /api/prompts/{name}/activate   promote version
POST /api/prompts/{name}/rollback
GET  /api/prompts/{name}/failures   last N failures
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | required | PostgreSQL connection string |
| `REDIS_HOST` | `localhost` | Redis hostname |
| `GEMINI_API_KEY` | required | Google Gemini API key |
| `OLLAMA_TIMEOUT_SECONDS` | `10` | Ollama request timeout |
| `GEMINI_TIMEOUT_SECONDS` | `10` | Gemini request timeout |
| `CHAOS_MODE` | `false` | Enable chaos action routing |

---

## Current Status

### Done
- NL → DSL → AST → DAG compiler pipeline
- Multi-LLM routing (Ollama → Gemini) with health tracking + cooldown
- 3-retry repair loop + fallback provider
- Versioned prompt system with auto-rollback
- Eval logging (every attempt: version, provider, latency, outcome)
- Full DAG execution engine (sequential + parallel + diamond)
- Retry engine (exponential backoff, Redis sorted set)
- DLQ after max retries
- Reaper recovery (stuck execution detection + re-queue)
- Distributed locking (Redis NX)
- Distributed tracing (ULID trace_id + span_id per step)
- Chaos testing engine (13 failure modes)
- 8 execution pattern tests all passing

### Next
- Multi-agent architecture (GenerationAgent · ValidationAgent · RepairAgent)
- Semantic search fallback for CatalogMatcher (pgvector)
- RAG-based few-shot examples from generation logs
- MCP integration for external action handlers
