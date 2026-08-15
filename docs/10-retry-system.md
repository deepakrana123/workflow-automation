# Retry System

## Overview

MFlows uses exponential backoff retry with a dead-letter queue for permanently failed steps.

## Retry Decision Flow

```
Step fails (ActionResult.success = False)
    ↓
handle_retry(db, step_execution, error, skip_retry)
    ↓
┌─────────────────────────────────────┐
│  skip_retry=True?                   │──→ DLQ immediately
│  (unrecoverable: unknown action,    │
│   config not found, handler missing)│
└────────────────┬────────────────────┘
                 │ No
                 ▼
┌─────────────────────────────────────┐
│  attempts <= MAX_RETRIES (5)?       │──→ No → DLQ
└────────────────┬────────────────────┘
                 │ Yes
                 ▼
         Schedule Retry
         ├── Mark step RETRY_SCHEDULED
         ├── Calculate delay: 30s × 2^(attempt-1)
         └── Redis ZADD workflow_retry (score = now + delay)
```

## Retry Policy

```python
MAX_RETRIES = 5
BASE_DELAY_SECONDS = 30

def calculate_delay(attempts):
    return BASE_DELAY_SECONDS * (2 ** (attempts - 1))
```

| Attempt | Delay |
|---------|-------|
| 1 | 30s |
| 2 | 60s |
| 3 | 120s |
| 4 | 240s |
| 5 | 480s |

## Non-Retryable Errors

These errors set `skip_retry=True` in ActionResult metadata:
- `ConfigurationNotFoundError` — action has no config
- `ExecutorNotFoundError` — unknown execution_type
- `HandlerNotFoundError` — Python handler not registered
- Any action returning `metadata={"skip_retry": True}`

## Dead Letter Queue (DLQ)

When retries are exhausted:
1. Step status → `DLQ`
2. Redis LPUSH to `workflow_dlq`
3. `finalize_workflow_execution()` marks workflow as FAILED

DLQ items are visible via the traces API and dashboard for manual investigation.

## Retry History

Every retry attempt is recorded in `step_retry_history` table:
- `attempt_number`, `trigger` (retry/dlq/timeout_recovery/manual_resume)
- `status_at_attempt`, `error`, `duration_ms`
- `retry_scheduled_at`, `retry_executed_at`

## Key Files

| File | Role |
|------|------|
| `app/execution/retry_handler.py` | Retry vs DLQ decision |
| `app/execution/retry_policy.py` | should_retry() + calculate_delay() |
| `app/execution/retry.py` | Redis queue operations |
| `app/execution/state_manager.py` | Low-level step status mutations |
| `app/workers/retry_worker.py` | Processes due retries |
| `app/repositories/step_retry_history_repo.py` | Retry audit trail |
