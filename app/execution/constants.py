"""
app/execution/constants.py

Redis queue names and event lifecycle status constants for the
worker/consumer layer.

For workflow and step state machine constants, see:
    app/execution/runtime/constants.py
"""

# ── Event processing statuses ─────────────────────────────────────────────────
EVENT_RECEIVED = "RECEIVED"
EVENT_PROCESSING = "PROCESSING"
EVENT_COMPLETED = "COMPLETED"
EVENT_FAILED = "FAILED"
EVENT_RETRY_SCHEDULED = "RETRY_SCHEDULED"
EVENT_DLQ = "DLQ"

# ── Redis queue names ─────────────────────────────────────────────────────────
REDIS_EVENT_QUEUE = "workflow_events"
REDIS_RETRY_QUEUE = "workflow_retry"
REDIS_DLQ = "workflow_dlq"
