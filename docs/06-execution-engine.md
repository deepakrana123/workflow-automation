# Execution Engine

## Overview

The execution engine runs compiled workflow DAGs deterministically. It handles dependency ordering, parallel fan-out, action dispatch, retry, DLQ, and distributed tracing.

## Execution Flow

```
POST /api/execute/ {workflow_id, entity_id}
    ↓
WorkflowDispatchService
    ├── Duplicate guard (DB + Redis lock)
    ├── Create WorkflowRun + WorkflowExecution
    └── Redis LPUSH → workflow_events queue
            ↓
Consumer Worker (BRPOP)
    ↓
runtime_processor(db, workflow_execution_id)
    ├── Load WorkflowExecution
    ├── Mark RUNNING
    ├── Load Workflow → parsed_rule_json (the DAG)
    ├── Resolve workflow_knowledge_id
    └── run_dag_execution(...)
            ↓
DAG Executor (loop)
    ├── get_ready_steps() — steps with all deps satisfied
    ├── If 1 step → sequential execute_workflow_step()
    ├── If N steps → parallel ThreadPoolExecutor
    ├── Accumulate outputs in WorkflowContext
    └── Break on failure
            ↓
finalize_workflow_execution()
    ├── All COMPLETED → mark_workflow_completed
    ├── Any DLQ → mark_workflow_failed
    ├── Any FAILED → mark_workflow_failed
    └── Any RETRY_SCHEDULED → defer (worker will retry)
```

## Step Execution

`execute_workflow_step()` uses checkpoint labels for precise error diagnosis:

1. `create_step_execution` — persist step record
2. `mark_step_running` — update status
3. `record_step_started` — emit trace event
4. `inject_trace_into_payload` — add trace context to action payload
5. `load_action_configuration` — resolve config via config_resolver
6. `executor_dispatch` — call appropriate executor
7. `mark_step_completed` or `mark_step_failed` + `handle_retry`

## Executor Registry

Maps `execution_type` → executor implementation:

| Type | Executor | Description |
|------|----------|-------------|
| `python` | `PythonExecutor` | Calls internal Python handler functions |
| `http` | `HttpExecutor` | Makes HTTP request to external system via WorkspaceIntegration |

### PythonExecutor
Resolves `configuration["handler"]` → looks up in `ACTION_HANDLER_MAP` → calls handler → returns `ActionResult`.

### HttpExecutor
Builds URL from `WorkspaceIntegration.base_url` + `configuration["endpoint"]`. Applies auth headers. Renders body template with `{{variable}}` placeholders. Maps response via `response_mapping`.

## ActionResult Contract

Every executor must return:
```python
ActionResult(
    success: bool,
    outputs: dict = {},       # Merged into WorkflowContext
    message: str | None,
    error: str | None,
    metadata: dict = {},      # skip_retry, provider, latency
)
```

## Parallel Execution

When `get_ready_steps()` returns multiple steps (independent branches), they execute in parallel using `ThreadPoolExecutor`. Each thread gets its own DB session.

## Key Files

| File | Role |
|------|------|
| `app/services/workflow_dispatch_service.py` | Queue workflow for execution |
| `app/execution/runtime_processor.py` | Main orchestration entry point |
| `app/execution/runtime/dag_executor.py` | DAG traversal loop |
| `app/execution/runtime/step_executor.py` | Single step execution |
| `app/execution/runtime/config_resolver.py` | ActionConfiguration lookup |
| `app/execution/executors/registry.py` | Executor type routing |
| `app/execution/executors/python_executor.py` | Internal handler dispatch |
| `app/execution/executors/http_executor.py` | External HTTP calls |
