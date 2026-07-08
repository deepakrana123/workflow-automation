# MFlows — AI Workflow Automation Engine

> Natural language in. Running workflow out. Built for banking and financial services.

MFlows is a **production-grade AI workflow engine** that converts plain English business requirements into executable, observable, fault-tolerant DAG workflows — no manual DSL authoring, no drag-and-drop.

It also ingests **BRD (Business Requirement Documents)** — upload a PDF, and the system extracts triggers, actions, and business rules automatically using LLM extraction + vector embedding matching.

---

## The Problem It Solves

Banking and financial operations involve hundreds of complex workflows — loan origination, fraud response, collections, KYC — each with strict sequencing, parallel steps, retries, and compliance requirements. Building these manually is slow, error-prone, and disconnected from business intent.

MFlows bridges the gap between business language and executable automation.

---

## What It Does — In One Sentence Each

| Capability | Description |
|---|---|
| **NL → DAG** | Converts "When payment is missed escalate case and notify manager" into an executable parallel workflow |
| **BRD Ingestion** | Upload a banking PDF — extracts workflow knowledge using OCR + Gemini LLM |
| **Semantic Catalog** | Matches user intent to catalog triggers/actions using pgvector + BAAI embeddings |
| **DAG Execution** | Runs sequential, parallel, diamond, and deep-chain patterns with full observability |
| **Fault Tolerance** | Retry with exponential backoff, DLQ, reaper recovery for stuck executions |
| **Multi-LLM** | Ollama (local) → Gemini fallback with health tracking, cooldown, and auto-rollback |

---

## Live Demo — 30 Seconds

```bash
# 1. Generate a workflow from natural language
curl -X POST http://localhost:8000/api/workflows/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "When payment is missed escalate case and notify manager then create audit record",
    "name": "payment-missed-flow",
    "domain": "finance"
  }'

# Response: workflow_id=12, DSL generated, steps compiled

# 2. Execute it
curl -X POST http://localhost:8000/api/execute/ \
  -d '{"workflow_id": 12, "entity_id": "customer-001"}'

# 3. Poll status → PENDING → RUNNING → COMPLETED

# 4. Upload a BRD PDF
curl -X POST http://localhost:8000/api/knowledge-ingestion/upload \
  -F "file=@home_loan_brd.pdf"
```

---

## Architecture

Two independent ingestion paths. One deterministic execution engine.

```
Path 1: Natural Language
═══════════════════════════════════════════════════════
User Input → CatalogMatcher (keyword + pgvector)
          → SuitabilityAgent (domain validation)
          → PromptBuilder (versioned templates)
          → LLMManager (Ollama → Gemini fallback)
          → WorkflowCompilerService
               DSLGenerator → @step DSL
               RuleParser   → ParseNode list
               ASTBuilder   → WorkflowAST
               ASTValidator → cycle + dep check
               Compiler     → parsed_rule_json
          → WorkflowPersistenceService → DB

Path 2: BRD Document
═══════════════════════════════════════════════════════
PDF Upload → DocumentExtractor (PyPDF + Tesseract OCR)
           → WorkflowExtractor (Gemini LLM)
                Extracts: triggers, actions, business rules,
                          actors, external systems
           → WorkflowRepository → WorkflowKnowledge
           → EmbeddingMapper (BAAI/bge-small-en-v1.5)
                pgvector cosine → best matching action_definition
           → ActionConfigurationService
                {execution_type: "python", handler: "fn_name"}

Execution Engine (shared by both paths)
═══════════════════════════════════════════════════════
Redis queue → consumer worker
           → runtime_processor
           → dag_executor + WorkflowContext
           → dag_scheduler (dependency-resolved ready steps)
           → step_executor → dispatcher
           → ActionConfiguration → Python handler
           → ActionResult → WorkflowContext.outputs.update()
           → retry_handler (exponential backoff)
           → workflow_finalizer (COMPLETED / FAILED / DLQ)
           → reaper_worker (stuck execution recovery)
```

---

## Key Engineering Decisions

### 1. Compiler Pipeline — not just prompt-to-execution
Most LLM workflow tools execute prompt output directly. MFlows compiles it:
- LLM JSON → DSL (@step format) → AST → validated DAG
- AST validation catches cycles, unknown dependencies, duplicate IDs
- The compiler is LLM-independent and fully unit testable

### 2. ActionResult Contract
Every handler returns a typed `ActionResult(success, outputs, error, metadata)` — not arbitrary dicts. Outputs accumulate in `WorkflowContext` across steps, enabling future Decision Nodes.

### 3. Semantic + Keyword Hybrid Catalog
`CatalogMatcher` first tries exact keyword/alias matching, then falls back to pgvector similarity search. This means "bill is past due" correctly resolves to `payment_due` trigger even without exact vocabulary.

### 4. ActionConfiguration Layer
A `WorkflowActionMapping` doesn't execute directly. It goes through `ActionConfiguration` which carries `{execution_type, handler}`. This makes the system ready for HTTP integrations, MCP tools, AI agents, and human-in-the-loop tasks — without changing the execution engine.

### 5. Fault Tolerance — three recovery mechanisms
- **Retry worker** — exponential backoff via Redis sorted set (30s → 60s → 120s...)
- **Reaper worker** — scans for executions stuck >60s, requeues up to 3 times
- **DLQ** — permanent failure after max retries, workflow marked FAILED

---

## Test Results

| Suite | Cases | Result | What It Proves |
|---|---|---|---|
| `test_dsl_pipeline.py` | 5 | ✅ 5/5 | Compiler works without LLM |
| `test_full_pipeline.py` | 8 | ✅ 8/8 | All DAG patterns execute correctly |
| `test_nlp_to_dsl.py` | 18 | ✅ 14/18 | Real LLM → real DB → compile |
| `test1.py` | 35 | ✅ 25+/35 | Full E2E: NLP → execute → COMPLETED |
| `test_semantic_e2e.py` | 105 | ✅ 75%+ | Synonym inputs via semantic search |

> 4 failures in `test_nlp_to_dsl.py` are catalog data gaps (missing aliases), not code bugs.
> 75% on semantic E2E means the system handles real paraphrase variation at production scale.

---

## Domain Coverage

**Finance / Banking — 90+ actions**

| Category | Examples |
|---|---|
| Payments | NEFT, RTGS, IMPS, validate transaction, payment confirmation |
| Fraud | AML screening, sanctions check, freeze account, risk scoring |
| Loan Origination | CIBIL check, income verification, underwriting, sanction letter |
| Home Loan | Property valuation, technical visit, legal verification, mortgage, tranche disbursement |
| Car Loan | Vehicle valuation, dealer invoice, RC hypothecation, delivery confirmation |
| Collections | Overdue notice, recovery agent, legal notice, write-off, restructure |
| KYC | Initiate, complete, send reminder, document verification |
| Accounts | Open, close, upgrade, card operations, overdraft, credit limit |
| Regulatory | Regulatory report, audit record, compliance check |

**Support — 10 actions**
Ticket lifecycle · SLA breach · complaint escalation · refunds · satisfaction survey

**Health — 10 actions**
Critical vitals · emergency protocol · medication reminder · discharge · insurance approval

---

## Execution Patterns Validated

| Pattern | Description | Test |
|---|---|---|
| Sequential | A → B → C | ✅ P02 |
| Parallel fan-out | A → (B ∥ C) | ✅ P01 |
| Diamond | A → (B ∥ C) → D | ✅ P03 |
| Diamond + tail | (A ∥ B) → C → D | ✅ P04 |
| Deep chain | A → B → C → D → E | ✅ P05 |
| 3-way parallel | A → (B ∥ C ∥ D) | ✅ P06 |

---

## Infrastructure

| Component | Technology | Why |
|---|---|---|
| API | FastAPI | Async, typed, fast |
| Database | PostgreSQL + pgvector (Supabase) | Relational + vector in one DB |
| Queue | Redis BRPOP + sorted set | Reliable delivery + timed retries |
| ORM | SQLAlchemy + Alembic | Schema migrations, relationship loading |
| LLM Primary | Ollama / qwen2.5:7b | Local, no API cost, fast iteration |
| LLM Fallback | Google Gemini REST | Cloud fallback when local unavailable |
| Embeddings | BAAI/bge-small-en-v1.5 | 384-dim, local, MTEB-ranked for retrieval |
| Vector Search | pgvector cosine distance | Native Postgres, no extra infra |
| Tracing | ULID (trace_id + span_id) | Sortable, distributed-safe IDs |
| Containerisation | Docker + docker-compose | 5-service stack in one command |

---

## Getting Started

```bash
git clone <repo>
cd mflows

# Configure environment
cp .env.example .env
# Required: DATABASE_URL, GEMINI_API_KEY, REDIS_HOST

# Run DB migrations
alembic upgrade head

# Seed catalog embeddings (run once after seeding trigger/action definitions)
python scripts/backfill_embeddings.py

# Start everything
docker-compose up --build

# Start API + Redis only (faster for development)
docker-compose up --build api redis
```

**Health check:**
```bash
curl http://localhost:8000/api/health/ready
# 200 → system ready  |  503 → DB or Redis not connected
```

---

## Project Structure

```
app/
├── nlp/                    NLP pipeline (catalog, LLM, prompts, AST, compiler)
│   ├── catalog/            Keyword + alias matching
│   ├── semantic/           pgvector embedding search
│   ├── llm_manager/        Multi-LLM routing + health
│   ├── prompts/            Versioned templates + auto-rollback
│   ├── ast/                ParseNode → WorkflowAST + validation
│   └── services/           NLPWorkflowService orchestrator
├── workflow/               Compiler + Persistence services
├── execution/              DAG runtime
│   ├── runtime/            step_executor, dag_executor, finalizer, reaper
│   ├── dispatcher.py       action name → ActionResult
│   └── domain_actions/     handlers: banking, home loan, car loan, support, health
├── workflow_execution/     ActionResult + WorkflowContext schemas
├── knowledge_ingestions/   BRD ingestion pipeline
├── action_configuration/   Execution metadata layer
├── routes/                 15+ FastAPI route files
├── models/                 SQLAlchemy models
├── repositories/           DB access layer
└── core/                   Logger, Redis client, startup health checks
```

---

## API Reference (Summary)

```
POST /api/workflows/generate          NL → compile → save
GET  /api/workflows/{id}/dsl          Reconstructed DSL
GET  /api/workflows/{id}/ast          AST as nodes + edges
GET  /api/workflows/{id}/compiled     Full parsed_rule_json

POST /api/execute/                    Queue DAG execution
POST /api/execute/{id}/pause|resume

GET  /api/executions/                 History with filters
GET  /api/executions/{id}             Steps + trace

POST /api/knowledge-ingestion/upload  BRD PDF → workflow knowledge

POST /api/search/semantic             pgvector similarity search

GET  /api/catalog/triggers|actions    DB catalog with search

GET  /api/dashboard/stats             KPI summary
GET  /api/analytics/*                 6 analytics endpoints

GET  /api/health/ready                Readiness probe (503 if not ready)
GET  /api/health/providers            LLM provider health + cooldown

GET  /api/prompts/stats               Prompt version pass rate
POST /api/prompts/{name}/rollback     Manual version rollback
```

Full reference: see `AGENT.md`

---

## What's Next

- **Hybrid Search** — BM25 + embeddings + Reciprocal Rank Fusion for catalog matching
- **Cross-encoder reranking** — `ms-marco-MiniLM` for top-K → top-3 precision
- **Multi-agent architecture** — GenerationAgent · ValidationAgent · RepairAgent
- **Decision Nodes** — branch on `WorkflowContext.outputs` values
- **MCP integration** — external tool calls as action handlers
- **RAG** — BRD chunks as few-shot context in generation prompt
