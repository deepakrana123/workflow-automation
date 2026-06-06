# MFlows — Workflow Automation Engine

A production-grade workflow engine that accepts DSL or natural language input, compiles it to a DAG, and executes it with retry, DLQ, reaper recovery, and distributed tracing.

---

## What It Is

MFlows turns workflow rules into executable DAGs.

Supports:
- DSL workflows (`@1: payment_due -> send_reminder`)
- Natural language workflows (`"When payment is due send reminder then notify manager"`)
- DAG execution with dependency scheduling
- Retry with exponential backoff and DLQ
- Reaper recovery for stuck executions
- Distributed execution via Redis queue + worker pool
- Full distributed tracing (trace_id / span_id per step)

---

## Architecture

```
Natural Language / DSL
        ↓
  Intent Extraction / DSL Parser
        ↓
    Parsed Nodes
        ↓
    AST Builder
        ↓
   AST Validator
        ↓
 Workflow Compiler
        ↓
 Workflow Definition          ← stored as parsed_rule_json
        ↓
  Runtime Processor           ← triggered via Redis queue
        ↓
   DAG Execution
   (dependency scheduler → step executor → dispatcher → action handler)
```

---

## Infrastructure

| Component      | Technology                        |
|----------------|-----------------------------------|
| API            | FastAPI                           |
| Database       | PostgreSQL (SQLAlchemy + Alembic) |
| Queue          | Redis (BRPOP + sorted set retry)  |
| LLM Fallback   | Ollama (local) + Gemini REST      |
| Tracing IDs    | ULID                              |
| Workers        | API Worker · Retry Worker · Reaper Worker |

---

## NLP Pipeline

```
app/nlp/
├── nl/
│   ├── patterns.py          # Trigger + action phrase dictionaries
│   ├── intent_extractor.py  # Rule-based NL → trigger + actions (no LLM)
│   └── nl_service.py        # NL sentence → WorkflowAST
├── parsers/
│   └── rule_parser.py       # DSL → ParseNode list
├── ast/
│   ├── schema.py            # WorkflowAST, TriggerNode, StepNode
│   ├── builder.py           # ParseNode list → WorkflowAST
│   └── validator.py         # Cycle detection, dependency check, duplicate IDs
├── complier/
│   ├── workflow_complier.py # WorkflowAST → v2 DAG dict
│   └── complier_service.py  # Full DSL pipeline: parse → build → validate → compile
├── registry/
│   ├── trigger_registry.py  # VALID_TRIGGERS (25 triggers)
│   └── action_registry.py   # VALID_ACTIONS (37 actions)
└── models.py                # ParseNode Pydantic model
```

All input paths (DSL, NL, LLM) produce the same `WorkflowAST`. The compiler and runtime are input-source agnostic.

---

## DSL Format

```
@1: payment_due -> send_reminder
@2 @depends(@1): payment_due -> escalate_case
@3 @depends(@1,@2): sla_breached -> send_sla_breach_alert
```

Rules:
- `@id` — step identifier (required)
- `@depends(@id,...)` — dependency list (optional)
- `trigger -> action` — arrow required; missing arrow is a hard fail
- Lines starting with `#` are ignored

---

## Natural Language Format

```
When payment is due send reminder then notify manager then close case
```

Rule-based extraction — no LLM, no embeddings. Longest-match phrase lookup against `patterns.py`.

---

## Execution Flow

```
POST /api/execute
  → WorkflowRun + WorkflowExecution created
  → lpush to Redis "workflow_events"

Worker (BRPOP)
  → runtime_processor
  → mark RUNNING
  → dag_executor (dependency scheduler)
    → step_executor (per step)
      → dispatcher → action handler
      → SUCCESS: mark COMPLETED, record trace
      → FAILURE: retry_handler → retry / DLQ
  → workflow_finalizer (derive workflow state from step graph)
```

---

## Retry and DLQ

- Exponential backoff: `delay = BASE_DELAY × 2^(attempt-1)`
- Default: 5 retries, 30s base delay
- After max retries: step moves to DLQ (`workflow_dlq` Redis list)
- Reaper worker recovers executions stuck in RUNNING > 60 seconds

---

## Chaos Testing

Set `CHAOS_MODE=true` to route all actions through the chaos engine.

Available modes: `success`, `always_fail`, `timeout`, `slow`, `gateway_error`, `rate_limit`, `auth_error`, `bad_payload`, `payload_overload`, `partial_success`, `flaky`, `fail_on_attempt`, `succeed_after_retries`

---

## Getting Started

```bash
git clone <repo>
cd mflows
cp .env.example .env
# set DATABASE_URL and GEMINI_API_KEY

alembic upgrade head
docker-compose up --build
```

Services started: `api` (port 8000) · `worker` · `retry_worker` · `reaper_worker` · `redis`

---

## API

```http
POST /api/workflows/         # create workflow from DSL
GET  /api/workflows/         # list workflows
POST /api/execute/           # queue workflow execution
POST /api/execute/{id}/pause
POST /api/execute/{id}/resume
POST /api/workflows/debug-parse   # parse without saving
```

---

## Environment Variables

| Variable                  | Description                          |
|---------------------------|--------------------------------------|
| `DATABASE_URL`            | PostgreSQL connection string         |
| `REDIS_HOST`              | Redis hostname (default: localhost)  |
| `GEMINI_API_KEY`          | Google Gemini API key                |
| `GEMINI_MODEL`            | Gemini model name                    |
| `CHAOS_MODE`              | `true` to enable chaos actions       |
| `OLLAMA_TIMEOUT_SECONDS`  | Ollama timeout (default: 5)          |
| `GEMINI_TIMEOUT_SECONDS`  | Gemini timeout (default: 5)          |

---

## Current Status

**Completed**
- Runtime Engine (DAG executor, step executor, finalizer)
- Retry Engine (exponential backoff, DLQ, retry worker)
- Reaper Recovery (stuck execution detection)
- Distributed Locking (Redis NX)
- Distributed Tracing (ULID trace_id / span_id)
- DSL Parser + DAG Validator
- AST Builder + AST Validator
- Workflow Compiler
- Natural Language → AST (Phase 2.4)

**Future**
- Prompt Service (prompt templates → intent extraction)
- Provider Orchestration + Multi-LLM Fallback
- Workflow Retrieval
- Agent Workflows
