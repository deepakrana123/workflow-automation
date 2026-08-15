# Security

## Authentication & Authorization

Currently MFlows does not enforce authentication at the API layer. This is acceptable for internal deployment but must be addressed before any external-facing deployment.

### Recommendations for Production

1. **API Gateway** — Deploy behind an API gateway (AWS ALB, Kong, Traefik) that handles JWT validation
2. **Service-to-service auth** — Workers communicate via Redis; no inter-service HTTP calls requiring auth
3. **Database** — PostgreSQL credentials via environment variables; never committed to source

## Secrets Management

| Secret | Storage | Access |
|--------|---------|--------|
| `DATABASE_URL` | `.env` file / environment variable | App + Workers |
| `REDIS_URL` | `.env` file / environment variable | App + Workers |
| `GEMINI_API_KEY` | `.env` file / environment variable | App (NLP pipeline only) |
| Workspace Integration credentials | `workspace_integrations.credentials` (JSONB) | HttpExecutor at runtime |

### Best Practices

- Never log credential values — reference by key name only
- Workspace integration credentials should be encrypted at rest (Supabase column-level encryption recommended)
- Rotate API keys periodically; the system supports credential updates via PUT endpoint without downtime

## Input Validation

- All API inputs validated via Pydantic schemas
- File uploads restricted to PDF content type only
- LLM output is never executed directly — always compiled + validated
- SQL injection prevented by SQLAlchemy parameterized queries
- No raw SQL with user-supplied interpolation

## CORS

Currently configured with wildcard `"*"` for development. Before production:

```python
allow_origins=["https://your-banking-portal.example.com"]
```

## Redis Security

- Redis is internal-only (not exposed to public network)
- No Redis AUTH configured by default in docker-compose
- Production: Enable Redis AUTH + TLS

## Rate Limiting

No built-in rate limiting. Recommended:
- Apply at API gateway level
- Particularly for `/api/workflows/generate` (LLM calls) and `/api/execute/` (execution dispatch)

## Audit Trail

All workflow executions produce audit records:
- `audit_log` table — general action audit
- `trace_events` table — full distributed trace
- `generation_logs` table — LLM call metrics
- `step_retry_history` table — retry decisions

## Data Isolation

- Workspace-level isolation via `workspace_id` foreign keys
- No cross-workspace data leakage in queries
- Action configurations are scoped to (workflow_knowledge_id, action_definition_id)
