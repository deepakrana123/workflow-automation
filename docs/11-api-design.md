# API Design

## Base URL

All endpoints are prefixed with `/api`.

## Route Modules

| Prefix | Module | Purpose |
|--------|--------|---------|
| `/api/workflows` | `routes/workflows.py` | Generate and list workflows |
| `/api/execute` | `routes/execute.py` | Dispatch, pause, resume executions |
| `/api/executions` | `routes/executions.py` | Execution history and step details |
| `/api/catalog` | `routes/catalog.py` | Browse triggers and actions catalog |
| `/api/search` | `routes/search.py` | Semantic search across catalog |
| `/api/traces` | `routes/traces.py` | Distributed trace viewer |
| `/api/dashboard` | `routes/dashboard.py` | KPI stats for dashboard |
| `/api/analytics` | `routes/analytics.py` | Time-series analytics charts |
| `/api/prompts` | `routes/prompts.py` | Prompt version management |
| `/api/knowledge-ingestion` | `routes/knowledge_ingestion.py` | BRD upload and extraction |
| `/api/workspaces/{id}/integrations` | `routes/workspace_integrations.py` | Manage external integrations |
| `/api/action-configurations` | `routes/action_configurations.py` | Manage action configs |
| `/api/health` | `routes/health.py` | Health and readiness checks |
| `/api/settings` | `routes/settings.py` | Runtime settings |

## Key Endpoints

### Generate Workflow (NL → DAG)
```
POST /api/workflows/generate
{
  "user_request": "when payment is missed send reminder then escalate",
  "name": "payment_followup",
  "domain": "finance"
}
→ {workflow_id, name, domain, dsl, parsed_rule_json}
```

### Execute Workflow
```
POST /api/execute/
{
  "workflow_id": 1,
  "entity_id": "LOAN-12345"
}
→ {success, queued, workflow_run_id, workflow_execution_id}
```

### Upload BRD
```
POST /api/knowledge-ingestion/upload
Content-Type: multipart/form-data
file: <PDF>
→ {workflow_knowledge_id, workflow_name, triggers, actions}
```

### Prompt Version Management
```
GET  /api/prompts                          → list all prompts with versions
POST /api/prompts/{name}/activate          → promote a version
POST /api/prompts/{name}/rollback          → rollback to previous
GET  /api/prompts/stats                    → performance by version
```

## Error Handling

All routes return structured errors:
```json
{
  "detail": "Human-readable error message"
}
```

HTTP status codes follow standard conventions:
- 400 — validation failure, invalid domain, bad input
- 404 — entity not found
- 409 — conflict (e.g., pause on non-RUNNING execution)
- 502 — LLM provider failure
