# System Overview

## What is MFlows?

MFlows is an AI-powered Banking Workflow Automation Platform. It converts natural language instructions or Business Requirement Documents (BRDs) into executable, deterministic workflow DAGs — specifically designed for retail banking, corporate banking, lending, credit operations, compliance, and fraud operations.

## Core Capabilities

- **Natural Language → Workflow**: A banker writes "when payment is missed, send reminder then escalate" and MFlows generates, validates, compiles, and persists an executable workflow.
- **BRD Document Ingestion**: Upload a PDF, the system extracts workflow knowledge (triggers, actions, business rules) using LLM + OCR, maps them to a banking action catalog via vector embeddings.
- **Deterministic Execution**: Compiled workflows run as DAGs with dependency-ordered steps, parallel fan-out, retry with exponential backoff, dead-letter queue, and automatic timeout recovery.
- **Banking Action Catalog**: 500+ pre-built banking actions (KYC, AML, loan origination, payments, collections, cards, trade finance, treasury) with semantic search for matching.

## Architecture Summary

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                    │
│   /workflows  /execute  /catalog  /traces  /analytics   │
└────────────────────────────┬────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
┌──────────────────┐ ┌────────────┐ ┌─────────────────┐
│  NLP Pipeline    │ │  BRD       │ │  Execution      │
│  (NL → DAG)     │ │  Ingestion │ │  Engine         │
└────────┬─────────┘ └─────┬──────┘ └────────┬────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌──────────────────────────────────────────────────────────┐
│              PostgreSQL (Supabase) + Redis                │
└──────────────────────────────────────────────────────────┘
```

## Technology Stack

| Component | Technology |
|-----------|-----------|
| API Framework | FastAPI (Python 3.12) |
| Database | PostgreSQL via Supabase |
| Vector Store | pgvector (384-dim embeddings) |
| Queue | Redis (event queue + retry sorted set) |
| LLM Providers | Gemini (primary), Ollama (local) |
| Embedding Model | BAAI/bge-small-en-v1.5 (catalog), all-MiniLM-L6-v2 (BRD mapping) |
| Containerization | Docker + Docker Compose |

## Services (Docker Compose)

| Service | Role |
|---------|------|
| `api` | FastAPI application server |
| `worker` | Redis consumer — processes workflow execution events |
| `retry_worker` | Polls Redis sorted set for due retries |
| `reaper_worker` | Recovers stuck RUNNING executions |
| `redis` | Event queue and retry scheduling |

## Key Invariants

1. Raw LLM output is never executed — always passes through compile + validate.
2. LLM calls exist only in `app/nlp/`. The execution engine is ML-free.
3. The execution engine is deterministic — same `parsed_rule_json` produces same step order.
4. Every action returns `ActionResult`. The runtime reads nothing else.
5. Prompt templates are files, never hardcoded in Python.
