# Action Configurations

## Overview

Action Configurations define HOW a specific action is executed within a specific workflow context. They bridge the gap between the banking action catalog (WHAT to do) and the execution implementation (HOW to do it).

## Concepts

- **ActionDefinition** (catalog) → defines the action's identity, description, and default execution template
- **ActionConfiguration** (per-workflow) → overrides execution details for a specific workflow

## Configuration Structure

```json
{
  "workflow_knowledge_id": 42,
  "action_definition_id": 15,
  "execution_type": "python",
  "configuration": {
    "handler": "send_payment_reminder"
  },
  "version": 1,
  "active": true
}
```

### Python Execution
```json
{
  "execution_type": "python",
  "configuration": {
    "handler": "process_neft"
  }
}
```

### HTTP Execution
```json
{
  "execution_type": "http",
  "workspace_integration_id": 3,
  "configuration": {
    "method": "POST",
    "endpoint": "/payments/neft",
    "headers": {"Content-Type": "application/json"},
    "body_template": {"amount": "{{amount}}", "beneficiary": "{{account_id}}"},
    "response_mapping": {"transaction_id": "$.id"},
    "timeout": 30
  }
}
```

## Versioning

Each update creates a new version (version N+1) and deactivates the previous active version. Only one version can be active per (workflow_knowledge_id, action_definition_id) pair.

## Resolution at Runtime

When a step executes, `config_resolver.resolve_action_configuration()`:
1. Looks up `ActionDefinition` by action name
2. If `workflow_knowledge_id` available: exact match by (workflow, action_def)
3. Fallback: latest active config by action_definition_id only
4. Returns `(ActionConfiguration, execution_type)` or `(None, "python")`

## API Endpoints

```
GET    /api/workflows/{workflow_knowledge_id}/action-configurations
GET    /api/action-configurations/{id}
PUT    /api/action-configurations/{id}        — creates new version
PATCH  /api/action-configurations/{id}/activate
PATCH  /api/action-configurations/{id}/deactivate
```

## Key Files

| File | Role |
|------|------|
| `app/action_configuration/management_service.py` | CRUD + versioning |
| `app/action_configuration/action_configuration_service.py` | Default config seeding |
| `app/repositories/action_configuration_repository.py` | Database access |
| `app/execution/runtime/config_resolver.py` | Runtime resolution |
