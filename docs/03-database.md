# Database Schema

## Overview

PostgreSQL (hosted on Supabase) with pgvector extension for embedding-based semantic search.

## Core Tables

### workflows
The compiled workflow definition — the DAG that the runtime executes.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | |
| name | String | Workflow name |
| domain | String | Banking vertical (e.g., "finance") |
| raw_input | String | Original NL request or BRD reference |
| parsed_rule_json | JSONB | Compiled DAG: `{version, trigger, steps}` |
| status | String(50) | "active" / "inactive" |
| priority | Integer | Execution priority (default 1) |
| created_at | DateTime | |
| updated_at | DateTime | |

### workflow_executions
Runtime execution state — one row per execution attempt.

| Column | Type | Description |
|--------|------|-------------|
| id | BigInteger PK | |
| workflow_id | BigInteger FK | References workflows.id |
| workflow_run_id | BigInteger FK | References workflow_runs.id |
| entity_id | String(255) | Business entity (loan_id, account_id) |
| status | String(50) | PENDING → RUNNING → COMPLETED/FAILED |
| attempts | Integer | Reaper recovery count |
| last_error | Text | Most recent error message |
| trace_id | String(100) | Distributed trace identifier |
| correlation_id | String(100) | External correlation ID |
| started_at / completed_at / created_at / updated_at | DateTime | |

### execution_steps
Per-step runtime state within a workflow execution.

| Column | Type | Description |
|--------|------|-------------|
| id | BigInteger PK | |
| workflow_execution_id | BigInteger FK | |
| step_id | String | Logical step identifier from DAG |
| step_name | String(255) | Action name being executed |
| status | String(50) | PENDING → RUNNING → COMPLETED/FAILED/DLQ |
| attempts | Integer | Retry attempt count |
| span_id / parent_span_id | String(100) | Distributed tracing |
| input_payload / output_payload | JSONB | Step I/O |
| last_error | Text | |

### trigger_definitions
Banking event catalog — semantic searchable.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | |
| name | String UNIQUE | snake_case identifier |
| display_name | String | Human-readable name |
| description | Text | Business description |
| workflow_type | String | Domain category |
| aliases | JSONB | Keyword synonyms for search |
| embedding | Vector(384) | pgvector embedding |
| active | Boolean | |

### action_definitions
Banking action catalog — semantic searchable. Same structure as trigger_definitions plus:

| Column | Type | Description |
|--------|------|-------------|
| handler_name | String | Maps to Python handler in dispatcher |
| input_schema / output_schema | JSONB | Contract definitions |
| execution_template | JSONB | Default execution config |

### action_configurations
Per-workflow execution override for each action.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | |
| workflow_knowledge_id | Integer FK | |
| action_definition_id | Integer FK | |
| workspace_integration_id | Integer FK (nullable) | For HTTP execution |
| execution_type | String | "python" or "http" |
| configuration | JSONB | Handler config or HTTP endpoint details |
| version | Integer | Version number |
| active | Boolean | Only one active per (workflow, action) pair |

### workspace_integrations
External system connections for HTTP-type actions.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer PK | |
| workspace_id | Integer FK | |
| name | String | Integration name |
| provider_type | String | http, soap, grpc, kafka, mcp |
| base_url | String | Base endpoint URL |
| authentication_type | String | api_key, bearer, oauth2, basic |
| credentials | JSONB | Auth credentials (encrypted at rest) |

## Migrations

Managed by Alembic. Migration files are in `alembic/versions/`. Never modify migration files after they've been applied to a shared database.
