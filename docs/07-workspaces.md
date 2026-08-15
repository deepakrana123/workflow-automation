# Workspaces & Integrations

## Overview

Workspaces provide multi-tenant isolation. Each workspace can have its own set of external integrations (HTTP endpoints, APIs) that action configurations reference for HTTP-type execution.

## Workspace Integration

A `WorkspaceIntegration` represents a connection to an external banking system:

| Field | Description |
|-------|-------------|
| `name` | Human-readable identifier |
| `provider_type` | Protocol: http, soap, grpc, kafka, mcp |
| `base_url` | Base endpoint URL |
| `authentication_type` | api_key, bearer, oauth2, basic |
| `credentials` | JSONB with auth tokens/keys |

## Authentication Types

| Type | Credentials Shape | Header Produced |
|------|-------------------|-----------------|
| `bearer` | `{"token": "..."}` | `Authorization: Bearer <token>` |
| `api_key` | `{"header": "X-API-Key", "key": "..."}` | `<header>: <key>` |
| `basic` | `{"username": "...", "password": "..."}` | `Authorization: Basic <b64>` |
| `oauth2` | `{"access_token": "..."}` | `Authorization: Bearer <token>` |

## API Endpoints

```
GET    /api/workspaces/{workspace_id}/integrations
POST   /api/workspaces/{workspace_id}/integrations
GET    /api/workspace-integrations/{id}
PUT    /api/workspace-integrations/{id}
DELETE /api/workspace-integrations/{id}
```

## Usage in Action Configurations

When `execution_type = "http"`, the `ActionConfiguration` references a `workspace_integration_id`. At execution time, the `HttpExecutor`:
1. Loads the `WorkspaceIntegration` (base_url, auth)
2. Appends `configuration["endpoint"]` to `base_url`
3. Applies authentication headers
4. Renders `body_template` with workflow context variables
5. Makes the HTTP request
6. Maps response via `response_mapping`

## Key Files

| File | Role |
|------|------|
| `app/workspace_integrations/models.py` | SQLAlchemy model |
| `app/workspace_integrations/repository.py` | Database access |
| `app/workspace_integrations/integrations.py` | Service layer (CRUD + validation) |
| `app/routes/workspace_integrations.py` | REST API |
