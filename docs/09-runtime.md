# Runtime Architecture

## Workers

MFlows uses three background workers for event-driven execution:

### Consumer Worker (`app/workers/consumer.py`)
- Listens on Redis queue `workflow_events` via `BRPOP`
- Uses `ThreadPoolExecutor(max_workers=5)` for concurrent processing
- Each event contains `{"workflow_execution_id": <id>}`
- Calls `runtime_processor()` with a fresh DB session

### Retry Worker (`app/workers/retry_worker.py`)
- Polls Redis sorted set `workflow_retry` every 5 seconds
- Claims due items atomically via pipeline (`ZRANGEBYSCORE` + `ZREM`)
- Calls `execute_retry()` for each due step
- Records trace events and retry history

### Reaper Worker (`app/workers/reaper_worker.py`)
- Scans for `WorkflowExecution` stuck in RUNNING > 60 seconds
- Resets to PENDING and increments `attempts`
- After 3 recovery attempts → moves to DLQ
- Marks stuck child steps as FAILED
- Re-queues execution to `workflow_events`

## State Machines

### Workflow States
```
PENDING → RUNNING → COMPLETED
                  → FAILED
                  → PAUSED → RUNNING (resume)
                  → WAITING_APPROVAL
```

### Step States
```
PENDING → RUNNING → COMPLETED
                  → FAILED → RETRY_SCHEDULED → RUNNING (retry)
                           → DLQ (exhausted)
                  → WAITING
                  → SKIPPED
                  → BLOCKED
```

## Distributed Tracing

Every workflow execution gets a `trace_id` at creation. Every step gets a `span_id`. Trace events are written to `trace_events` table throughout execution:

- `WORKFLOW_STARTED` / `WORKFLOW_COMPLETED` / `WORKFLOW_FAILED`
- `STEP_STARTED` / `STEP_COMPLETED` / `STEP_FAILED`
- `ACTION_DISPATCHED` / `ACTION_SUCCESS` / `ACTION_FAILED`
- `RETRY_SCHEDULED` / `RETRY_STARTED` / `RETRY_COMPLETED`
- `REAPER_RECOVERED`

## Concurrency Model

- Sequential steps: single-threaded within the consumer worker thread
- Parallel steps: `ThreadPoolExecutor` — each thread gets its own `SessionLocal()` DB session
- Redis ensures at-most-once processing (lock + BRPOP)
- Reaper ensures at-least-once completion (timeout recovery)

## Key Configuration

| Constant | Value | Location |
|----------|-------|----------|
| MAX_RETRIES | 5 | `app/core/config.py` |
| BASE_DELAY_SECONDS | 30 | `app/core/config.py` |
| PROCESSING_TIMEOUT_SECONDS | 60 | `app/core/config.py` |
| MAX_RECOVERY_ATTEMPTS (reaper) | 3 | `app/workers/reaper_worker.py` |
| Consumer MAX_WORKERS | 5 | `app/workers/consumer.py` |
