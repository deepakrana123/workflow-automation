# MFlows — AI-Powered Banking Workflow Engine

> Natural Language → Compiled DAG → Deterministic Execution

MFlows converts plain English banking instructions into executable workflow DAGs. Upload a BRD or type a sentence — the platform extracts intent, maps to a 500+ banking action catalog, compiles a dependency graph, and executes it with retry, tracing, and dead-letter recovery.

---

## What It Does

```
"When payment is missed, send reminder, then escalate to collections"
                              ↓
              NLP Pipeline (Gemini + Semantic Search)
                              ↓
           Compiled DAG: @1 → send_reminder, @2 → escalate_case
                              ↓
             Deterministic Execution (parallel, retry, DLQ)
```

**Two ingestion paths. One execution engine.**

| Path | Input | Output |
|------|-------|--------|
| Natural Language | "freeze account on fraud detection" | Compiled workflow |
| BRD Upload | Banking requirement PDF | Mapped workflow knowledge |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI (14 endpoints)                    │
└──────────┬────────────────────────────────────┬─────────────┘
           │                                    │
    ┌──────▼──────┐                     ┌──────▼──────┐
    │ NLP Pipeline │                     │   BRD       │
    │              │                     │   Ingestion │
    │ Catalog Match│                     │   OCR+LLM   │
    │ LLM Generate │                     │   Embedding │
    │ Validate+    │                     │   Mapping   │
    │ Compile      │                     │             │
    └──────┬───────┘                     └──────┬──────┘
           │                                    │
           └────────────────┬───────────────────┘
                            ▼
              ┌──────────────────────────┐
              │    Compiled Workflow      │
              │    (parsed_rule_json)     │
              └────────────┬─────────────┘
                           ▼
    ┌──────────────────────────────────────────────┐
    │           Execution Engine                    │
    │                                              │
    │  Redis Queue → DAG Executor → Step Executor  │
    │  Parallel Fan-out │ Retry (exp backoff)      │
    │  DLQ │ Reaper Recovery │ Distributed Tracing │
    └──────────────────────────────────────────────┘
                           ▼
              ┌──────────────────────────┐
              │  PostgreSQL + Redis       │
              │  pgvector (384-dim)       │
              └──────────────────────────┘
```

---

## Key Engineering Decisions

| Decision | Why |
|----------|-----|
| LLM output is never executed directly | Always passes compile → validate → AST → DAG |
| Execution engine is ML-free | Deterministic. Same DAG = same execution order. Always. |
| 500+ banking action catalog with semantic search | Vector embeddings + BM25 + RRF + Cross-Encoder re-ranking |
| Prompt versioning with auto-rollback | 5 consecutive failures → automatic rollback to previous version |
| Exponential backoff retry + DLQ | 5 retries (30s, 60s, 120s, 240s, 480s) then dead-letter |
| Reaper worker recovers stuck executions | Timeout detection + automatic re-queue |
| Per-action execution configuration | Same action, different execution per workflow (Python handler or HTTP endpoint) |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI · Python 3.12 |
| Database | PostgreSQL (Supabase) · pgvector |
| Queue | Redis (event queue + sorted set retries) |
| LLM | Gemini 2.5 Flash · Ollama (local) |
| Embeddings | BAAI/bge-small-en-v1.5 · all-MiniLM-L6-v2 |
| OCR | Tesseract · pdf2image · Poppler |
| Container | Docker · Docker Compose |

---

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd mflows
cp .env.example .env  # Add your GEMINI_API_KEY and DATABASE_URL

# Run everything
docker-compose up

# Seed the banking catalog (500+ actions)
docker-compose exec api python scripts/seed_banking_catalog.py

# Generate embeddings
docker-compose exec api python scripts/backfill_embeddings.py
```

**Services running:**
- API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Redis: `localhost:6379`

---

## Core Capabilities

### NLP → Workflow Generation
```bash
curl -X POST http://localhost:8000/api/workflows/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "when loan payment is missed send reminder then assign recovery agent",
    "name": "loan_collection_flow",
    "domain": "finance"
  }'
```

### BRD Document Ingestion
```bash
curl -X POST http://localhost:8000/api/knowledge-ingestion/upload \
  -F "file=@loan_origination_brd.pdf"
```

### Execute Workflow
```bash
curl -X POST http://localhost:8000/api/execute/ \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": 1, "entity_id": "LOAN-2024-001"}'
```

---

## Banking Domains Covered

| Domain | Actions |
|--------|---------|
| Customer Onboarding & KYC | PAN/Aadhaar verification, CKYC, Video KYC, PEP screening |
| Loan Origination | CIBIL check, underwriting, sanction letter, disbursement |
| Loan Servicing | EMI reminders, NPA classification, collections, SARFAESI |
| Payments | NEFT, RTGS, IMPS, UPI, SWIFT, NACH mandates |
| Cards | Block/replace, credit limit, rewards, disputes |
| Fraud & Risk | AML screening, sanctions check, transaction monitoring |
| Compliance | RBI returns, FATCA, Basel reporting, GST/TDS |
| Trade Finance | Letter of Credit, Bank Guarantee, Bill Discounting |
| Treasury | Forex deals, forward contracts, ALM reporting |

---

## Project Structure

```
app/
├── core/          # Infrastructure (config, logging, Redis, tracing)
├── models/        # SQLAlchemy ORM (12 models)
├── routes/        # FastAPI routers (14 endpoints)
├── services/      # Business orchestration
├── repositories/  # Data access layer
├── execution/     # DAG executor, retry, dispatcher, workers
├── nlp/           # LLM pipeline, catalog matching, AST compiler
├── prompting/     # Unified prompt management (versioned)
├── knowledge_ingestions/  # BRD processing pipeline
├── retrieval/     # Vector + BM25 + RRF + Cross-Encoder
├── semantic/      # Embedding service + pgvector
├── workflow/      # Compiler chain (DSL → AST → DAG)
└── evaluation/    # Retrieval accuracy framework
```

---

## Execution Engine Highlights

- **DAG Scheduling** — Dependency-ordered step execution with parallel fan-out
- **Dual Executors** — Python (internal handlers) + HTTP (external APIs via workspace integrations)
- **Checkpoint-based Error Handling** — Precise failure location in execution lifecycle
- **Distributed Tracing** — trace_id + span_id for full execution timeline
- **Idempotent Dispatch** — Redis lock + DB duplicate guard prevents double execution

---

## Documentation

Full technical documentation in [`docs/`](./docs/):

1. [System Overview](docs/01-system-overview.md)
2. [Domain Model](docs/02-domain-model.md)
3. [Database Schema](docs/03-database.md)
4. [BRD Ingestion](docs/04-brd-ingestion.md)
5. [Action Mapping](docs/05-action-mapping.md)
6. [Execution Engine](docs/06-execution-engine.md)
7. [Workspaces](docs/07-workspaces.md)
8. [Action Configurations](docs/08-action-configurations.md)
9. [Runtime Architecture](docs/09-runtime.md)
10. [Retry System](docs/10-retry-system.md)
11. [API Design](docs/11-api-design.md)
12. [Folder Structure](docs/12-folder-structure.md)
13. [Security](docs/13-security.md)
14. [Future Roadmap](docs/14-future-roadmap.md)

---

## Design Principles

- **Banking-first** — Every action, trigger, and workflow is banking domain terminology
- **LLM as compiler input, not runtime** — The execution engine never calls an LLM
- **Deterministic execution** — Same DAG always produces same step ordering
- **Fail-safe** — Retry with backoff → DLQ → Reaper recovery. No silent failures.
- **Observable** — Every step traced, every retry logged, every LLM call metered

---

## Workspace-Scoped Workflow Generation

The **workspace** is the primary context for AI generation. Inside a workspace,
MFlows generates workflows from that workspace's BRD-derived knowledge — not the
full global catalog.

- **Global catalog = a library, not an ingredient.** Workspace generation is
  grounded only in the workspace's mapped actions/triggers + business rules.
  Global actions are added **explicitly** via the "+ Add Action" picker
  (`selected_action_ids`), never auto-injected.
- **Two distinct build paths:**
  - **Synthesize from BRDs** — deterministic, no LLM (`POST /api/workspaces/{id}/synthesize`).
  - **Build with AI** — workspace-scoped LLM (`POST /api/workspaces/{id}/generate`).
- **Explainability first** — documents, extracted business rules, and workspace
  actions are visible before generation; cross-BRD threshold conflicts (e.g.
  approval above ₹5L vs ₹10L) are surfaced for review, not silently resolved.

### New backend endpoints

```
GET  /api/workspaces/{id}/overview        # counts + summary + derived domain + status
GET  /api/workspaces/{id}/documents       # per-BRD extraction/mapping status + counts
GET  /api/workspaces/{id}/business-rules  # extracted rules (+ detected conflicts)
GET  /api/workspaces/{id}/actions         # workspace-scoped actions (+ unresolved) + triggers
POST /api/workspaces/{id}/generate        # AI generation grounded in the workspace
```

Request body for `/generate`:

```json
{
  "name": "personal_loan_approval_flow",
  "user_request": "Create a workflow for a personal loan application after KYC verification.",
  "domain": "finance",
  "selected_action_ids": []
}
```

### Frontend

- `/workspaces/:id` — tabs: Overview, Documents, Business Rules, Actions, Triggers.
- `/workspaces/:id/build` — "Build with AI": workspace context + instruction +
  global "+ Add Action" picker + generated-workflow review.

### Run & test locally

```bash
# 1. Redis (matches .env REDIS_HOST=localhost)
docker run -d --rm --name mflows-redis -p 6379:6379 redis:7

# 2. Python env (project targets 3.12)
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt

# 3. Apply DB migrations (adds workflows.workspace_id)
.venv\Scripts\python -m alembic upgrade head

# 4. (first time only) seed the catalog + embeddings
.venv\Scripts\python scripts/seed_banking_catalog.py
.venv\Scripts\python scripts/backfill_embeddings.py

# 5. API + workers (run each in its own terminal)
.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
.venv\Scripts\python -m app.workers.consumer
.venv\Scripts\python -m app.workers.retry_worker
.venv\Scripts\python -m app.workers.reaper_worker

# 6. Frontend
cd mflows/web && npm install && npm run dev   # http://localhost:5173 (proxies /api → :8000)
```

Smoke-testing the workspace pipeline (after seeding a catalog and ingesting at
least one BRD into a workspace so it has mapped actions):

```bash
# inspect what the workspace understood
curl http://localhost:8000/api/workspaces/1/overview
curl http://localhost:8000/api/workspaces/1/business-rules
curl http://localhost:8000/api/workspaces/1/actions

# generate a workflow grounded in that workspace
curl -X POST http://localhost:8000/api/workspaces/1/generate \
  -H "Content-Type: application/json" \
  -d '{"name":"loan_flow","user_request":"process a personal loan after KYC","domain":"finance"}'
```

> Note: `/generate` requires the workspace to have BRD actions mapped to the
> catalog. If none are mapped it returns HTTP 400 ("Workspace has no mapped
> actions…") — ingest a BRD first, or add actions explicitly.

### Unit tests (deterministic layers)

```bash
.venv\Scripts\python -m pytest tests/unit -q
```

Covers the workspace synthesis, context builders, workspace catalog matcher,
prompt-var builder, and rule-conflict detector. DB/LLM-coupled paths are verified
against the running environment.
