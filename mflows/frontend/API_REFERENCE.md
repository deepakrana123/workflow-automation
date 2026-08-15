# MFlows Frontend — API Reference

Base URL: `http://localhost:8000/api`

All endpoints return JSON. No auth required (dev mode).

---

## Dashboard

### GET `/dashboard/stats`
```
Response:
{
  "total_workflows": 42,
  "active_workflows": 38,
  "executions_today": 156,
  "total_executions": 2340,
  "completed_executions": 2100,
  "failed_executions": 180,
  "success_rate": 0.897,
  "queue_depth": 3,
  "retry_count": 45
}
```

### GET `/dashboard/execution-trend?days=7`
```
Response:
[
  {"date": "2026-07-28", "total": 34, "success": 30, "failed": 4},
  {"date": "2026-07-29", "total": 41, "success": 38, "failed": 3}
]
```

### GET `/dashboard/workflow-usage`
```
Response:
[
  {"name": "loan_collection_flow", "executions": 156},
  {"name": "kyc_verification", "executions": 89}
]
```

---

## Workflows

### GET `/workflows?domain=finance`
```
Response:
[
  {
    "id": 1,
    "name": "loan_collection_flow",
    "domain": "finance",
    "status": "active",
    "raw_input": "when payment is missed send reminder then escalate",
    "parsed_rule_json": {...},
    "created_at": "2026-07-15T10:30:00Z",
    "updated_at": "2026-07-15T10:30:00Z"
  }
]
```

### GET `/workflows/:id`
```
Response: same as above (single object)
```

### POST `/workflows/generate`
```
Request:
{
  "user_request": "when payment is missed send reminder then escalate to collections",
  "name": "loan_collection_flow",
  "domain": "finance"
}

Response:
{
  "workflow_id": 42,
  "name": "loan_collection_flow",
  "domain": "finance",
  "dsl": "@1: payment_missed -> send_payment_reminder\n@2 @depends(@1): payment_missed -> escalate_case",
  "execution_plan": {},
  "parsed_rule_json": {
    "version": "v2",
    "trigger": {"event_type": "payment_missed"},
    "steps": [
      {"id": "1", "action": "send_payment_reminder", "depends_on": []},
      {"id": "2", "action": "escalate_case", "depends_on": ["1"]}
    ]
  }
}

Errors:
  400: {"detail": "Invalid domain 'xyz'. Allowed: ['finance']"}
  400: {"detail": "trigger_not_found"}
  502: {"detail": "LLM generation failed"}
```

---

## Execute

### POST `/execute/`
```
Request:
{
  "workflow_id": 42,
  "entity_id": "LOAN-2024-001"
}

Response (success):
{
  "success": true,
  "queued": true,
  "workflow_run_id": 101,
  "workflow_execution_id": 205
}

Response (duplicate):
{
  "success": false,
  "message": "workflow already has an active execution",
  "workflow_execution_id": 200
}
```

### POST `/execute/:workflow_execution_id/pause`
```
Response:
{
  "success": true,
  "workflow_execution_id": 205,
  "status": "PAUSED"
}

Errors:
  404: {"detail": "workflow execution not found"}
  409: {"detail": "cannot pause execution in status 'COMPLETED' — must be RUNNING"}
```

### POST `/execute/:workflow_execution_id/resume`
```
Response:
{
  "success": true,
  "workflow_execution_id": 205,
  "status": "RUNNING"
}

Errors:
  404: {"detail": "workflow execution not found"}
  409: {"detail": "cannot resume execution in status 'RUNNING' — must be PAUSED"}
```

---

## Executions

### GET `/executions?page=1&page_size=20&status=failed&workflow_id=42`
```
Query params: page, page_size, workflow_id, status, start_date, end_date

Response:
{
  "data": [
    {
      "id": "205",
      "workflow_id": "42",
      "workflow_name": "loan_collection_flow",
      "status": "completed",
      "start_time": "2026-07-29T14:00:00Z",
      "end_time": "2026-07-29T14:00:05Z",
      "duration_ms": 5230,
      "retry_count": 0,
      "error": null,
      "trace_id": "trc_abc123",
      "steps": []
    }
  ],
  "total": 156,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

### GET `/executions/:id`
```
Response:
{
  "id": "205",
  "workflow_id": "42",
  "workflow_name": "loan_collection_flow",
  "status": "completed",
  "start_time": "2026-07-29T14:00:00Z",
  "end_time": "2026-07-29T14:00:05Z",
  "duration_ms": 5230,
  "retry_count": 0,
  "error": null,
  "trace_id": "trc_abc123",
  "steps": [
    {
      "id": "1",
      "name": "send_payment_reminder",
      "status": "completed",
      "start_time": "2026-07-29T14:00:01Z",
      "end_time": "2026-07-29T14:00:02Z",
      "duration_ms": 1200,
      "input": {"entity_id": "LOAN-2024-001"},
      "output": {"success": true, "outputs": {"reminder_sent": true}},
      "error": null,
      "retry_count": 0
    }
  ]
}
```

---

## Catalog

### GET `/catalog/triggers?page=1&page_size=50&search=payment&workflow_type=finance&active=true`
```
Response:
{
  "data": [
    {
      "id": 1,
      "name": "payment_missed",
      "display_name": "Payment Missed",
      "description": "A scheduled payment was not received by the due date.",
      "workflow_type": "finance",
      "aliases": ["payment overdue", "emi missed", "installment missed"],
      "active": true
    }
  ],
  "total": 33,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

### GET `/catalog/triggers/:id`
```
Response: single trigger object (same shape as above)
```

### GET `/catalog/actions?page=1&page_size=50&search=kyc&workflow_type=finance&active=true`
```
Response:
{
  "data": [
    {
      "id": 6,
      "name": "initiate_kyc",
      "display_name": "Initiate KYC",
      "description": "Start the Know Your Customer verification process.",
      "workflow_type": "finance",
      "aliases": ["start kyc", "begin kyc", "kyc initiation"],
      "active": true
    }
  ],
  "total": 500,
  "page": 1,
  "page_size": 50,
  "total_pages": 10
}
```

### GET `/catalog/actions/:id`
```
Response: single action object (same shape as above)
```

---

## Search

### POST `/search/semantic`
```
Request:
{
  "query": "freeze customer account",
  "top_k": 10
}

Response:
{
  "trigger_matches": [
    {
      "name": "account_locked",
      "display_name": "Account Locked",
      "distance_score": 0.15,
      "similarity_score": 0.85,
      "type": "trigger"
    }
  ],
  "action_matches": [
    {
      "name": "freeze_account",
      "display_name": "Freeze Account",
      "distance_score": 0.05,
      "similarity_score": 0.95,
      "type": "action"
    }
  ]
}
```

---

## Knowledge Ingestion

### POST `/knowledge-ingestion/upload`
```
Request:
  Content-Type: multipart/form-data
  Body: file=<PDF file>

Response (success):
{
  "id": 5,
  "workflow_name": "Loan Origination Process",
  "summary": "End-to-end loan origination workflow from application to disbursement",
  "triggers": [
    {"name": "Customer submits loan application", "description": "..."}
  ],
  "action_references": [
    {"name": "Validate KYC", "description": "...", "matched_action_definition_id": 6}
  ],
  "business_rules": [
    {"rule": "Reject if mandatory documents are missing."}
  ],
  "actors": [
    {"name": "Credit Officer", "role": "Approver"}
  ],
  "external_systems": [
    {"name": "CIBIL", "description": "Credit bureau for score check"}
  ]
}

Errors:
  400: {"detail": "Invalid file type 'text/plain'. Only PDF is accepted."}
  400: {"detail": "Uploaded file is empty."}
```

---

## Action Configurations

### GET `/workflows/:workflow_knowledge_id/action-configurations`
```
Response:
[
  {
    "id": 10,
    "workflow_knowledge_id": 5,
    "action_definition_id": 6,
    "workspace_integration_id": null,
    "execution_type": "python",
    "configuration": {"handler": "initiate_kyc"},
    "version": 1,
    "active": true,
    "created_at": "2026-07-20T12:00:00Z"
  }
]
```

### GET `/action-configurations/:id`
```
Response: single configuration object
```

### PUT `/action-configurations/:id`
```
Request:
{
  "execution_type": "http",
  "workspace_integration_id": 3,
  "configuration": {
    "method": "POST",
    "endpoint": "/kyc/initiate",
    "headers": {"Content-Type": "application/json"},
    "body_template": {"customer_id": "{{entity_id}}"},
    "response_mapping": {"kyc_id": "$.id"},
    "timeout": 30
  }
}

Response: new version object (version incremented, active=true)

Errors:
  400: {"detail": "execution_type='http' requires workspace_integration_id"}
  400: {"detail": "configuration missing required keys for execution_type='http': ['endpoint', 'method']"}
```

### PATCH `/action-configurations/:id/activate`
```
Response: configuration object with active=true
```

### PATCH `/action-configurations/:id/deactivate`
```
Response: configuration object with active=false
```

---

## Workspace Integrations

### GET `/workspaces/:workspace_id/integrations?active_only=true`
```
Response:
[
  {
    "id": 3,
    "workspace_id": 1,
    "name": "Core Banking API",
    "provider_type": "http",
    "base_url": "https://cbs.internal.bank/api/v2",
    "authentication_type": "bearer",
    "credentials": {"token": "***"},
    "description": "Internal CBS integration",
    "active": true,
    "created_at": "2026-07-10T08:00:00Z"
  }
]
```

### POST `/workspaces/:workspace_id/integrations`
```
Request:
{
  "name": "Payment Gateway",
  "provider_type": "http",
  "base_url": "https://payments.bank.internal/api",
  "authentication_type": "api_key",
  "credentials": {"header": "X-API-Key", "key": "sk_live_abc123"},
  "description": "Internal payment processing"
}

Response: created integration object

Errors:
  400: {"detail": "A workspace integration named 'Payment Gateway' already exists in workspace 1"}
  400: {"detail": "Workspace 1 not found or inactive"}
```

### GET `/workspace-integrations/:id`
```
Response: single integration object
```

### PUT `/workspace-integrations/:id`
```
Request: partial update (only include fields to change)
{
  "base_url": "https://payments-v2.bank.internal/api",
  "credentials": {"header": "X-API-Key", "key": "sk_live_new_key"}
}

Response: updated integration object
```

### DELETE `/workspace-integrations/:id`
```
Response: 200 (no body)
```

---

## Traces

### GET `/traces?execution_id=205&status=failed&page=1&page_size=50`
```
Response:
{
  "data": [
    {
      "id": "1001",
      "trace_id": "trc_abc123",
      "span_id": "spn_def456",
      "parent_span_id": "trc_abc123",
      "workflow_id": "205",
      "execution_id": "205",
      "step_id": "1",
      "event_type": "STEP_COMPLETED",
      "event_source": "step_executor",
      "status": "success",
      "message": "Step 'send_payment_reminder' completed",
      "latency_ms": 0,
      "input": null,
      "output": {"result": {...}},
      "metadata": {"event_type": "STEP_COMPLETED", "trace_id": "trc_abc123"},
      "timing": {"queue_time_ms": 0, "processing_time_ms": 0, "total_time_ms": 0},
      "retry_history": [],
      "created_at": "2026-07-29T14:00:02Z"
    }
  ],
  "total": 12,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

### GET `/traces/:trace_id`
```
Response: single trace event object (or first match if trace_id string)
```

---

## Analytics

### GET `/analytics/workflow-creation?start_date=2026-07-01&end_date=2026-07-31&domain=finance`
```
Response:
[
  {"date": "2026-07-01", "value": 3},
  {"date": "2026-07-02", "value": 5}
]
```

### GET `/analytics/execution-volume?start_date=2026-07-01`
```
Response:
[
  {"date": "2026-07-01", "value": 45},
  {"date": "2026-07-02", "value": 52}
]
```

### GET `/analytics/failures?start_date=2026-07-01`
```
Response:
[
  {"date": "2026-07-01", "total": 45, "failures": 3, "rate": 0.067},
  {"date": "2026-07-02", "total": 52, "failures": 5, "rate": 0.096}
]
```

### GET `/analytics/retries?start_date=2026-07-01`
```
Response:
[
  {"date": "2026-07-01", "retries": 12, "avg_retry_count": 1.5},
  {"date": "2026-07-02", "retries": 8, "avg_retry_count": 1.2}
]
```

### GET `/analytics/trigger-frequency`
```
Response:
[
  {"name": "Payment Missed", "count": 0},
  {"name": "Loan Requested", "count": 0}
]
```

### GET `/analytics/action-frequency`
```
Response:
[
  {"name": "Send Payment Reminder", "count": 0},
  {"name": "Escalate Case", "count": 0}
]
```

---

## Prompts

### GET `/prompts`
```
Response:
[
  {
    "prompt_name": "workflow_generation",
    "available_versions": ["v1"],
    "active_version": "v1",
    "previous_version": null
  }
]
```

### GET `/prompts/stats`
```
Response:
[
  {
    "prompt_name": "workflow_generation",
    "prompt_version": "v1",
    "total": 340,
    "passed": 312,
    "pass_rate": 0.918,
    "avg_attempts": 1.3,
    "avg_latency_ms": 2450
  }
]
```

### GET `/prompts/:prompt_name/state`
```
Response:
{
  "prompt_name": "workflow_generation",
  "active_version": "v1",
  "previous_version": null,
  "consecutive_failures": 0,
  "updated_at": 1722300000.0
}
```

### POST `/prompts/:prompt_name/activate`
```
Request:
{"version": "v2"}

Response:
{
  "success": true,
  "prompt_name": "workflow_generation",
  "active_version": "v2"
}

Errors:
  404: {"detail": "Prompt 'xyz' not found"}
  400: {"detail": "Version 'v3' not found. Available: ['v1', 'v2']"}
```

### POST `/prompts/:prompt_name/rollback`
```
Response:
{
  "success": true,
  "prompt_name": "workflow_generation",
  "rolled_back_to": "v1"
}

Errors:
  400: {"detail": "No previous version to roll back to for prompt 'workflow_generation'."}
```

### GET `/prompts/:prompt_name/failures?limit=10`
```
Response:
[
  {
    "id": 45,
    "prompt_version": "v1",
    "failure_reason": "schema_fail",
    "attempt_number": 3,
    "created_at": "2026-07-29T14:00:00Z"
  }
]
```

---

## Health

### GET `/health/ready`
```
Response (healthy):
{
  "status": "ok",
  "checks": {
    "database": {"status": "ok"},
    "redis": {"status": "ok"},
    "embedding_model": {"status": "ok"}
  }
}

Response (degraded — returns 503):
{
  "status": "degraded",
  "checks": {
    "database": {"status": "error", "error": "connection refused"},
    "redis": {"status": "ok"},
    "embedding_model": {"status": "ok"}
  }
}
```

---

## Common Patterns

### Pagination
All list endpoints that support pagination return:
```
{
  "data": [...],
  "total": 156,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

### Error Format
All errors return:
```
{
  "detail": "Human-readable error message"
}
```

### Status Values

**Workflow Execution:**
- `PENDING` → `RUNNING` → `COMPLETED`
- `RUNNING` → `FAILED`
- `RUNNING` → `PAUSED` → `RUNNING` (resume)
- `RUNNING` → `WAITING_APPROVAL`

**Step Execution:**
- `PENDING` → `RUNNING` → `COMPLETED`
- `RUNNING` → `FAILED` → `RETRY_SCHEDULED` → `RUNNING`
- `FAILED` → `DLQ`
- `WAITING`, `SKIPPED`, `BLOCKED`

### Status Color Mapping (for frontend)
```
completed  → green
running    → blue
pending    → gray
failed     → red
dlq        → dark red
retry_scheduled → amber
paused     → purple
waiting    → yellow
```
