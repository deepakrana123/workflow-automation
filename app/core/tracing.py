"""
app/core/tracing.py

Production-grade distributed tracing foundation.

Provides:
- ULID-based ID generation for trace_id, span_id, provider request IDs
- build_log_context() — standardized structured log context
- build_trace_headers() — outbound HTTP header preparation for downstream propagation
- inject_trace_into_payload() — attaches trace context to action payloads

Design:
- No OpenTelemetry dependency yet — clean foundation for future OTel integration
- All IDs are prefixed for readability: wf_ / sp_ / req_
- Backward compatible — all fields are optional in log context
"""

import ulid


def generate_trace_id() -> str:
    return f"wf_{str(ulid.new())}"


def generate_span_id() -> str:
    return f"sp_{str(ulid.new())}"


def generate_provider_request_id() -> str:
    return f"req_{str(ulid.new())}"


# ─────────────────────────────────────────────
# STRUCTURED LOG CONTEXT
# ─────────────────────────────────────────────


def build_log_context(
    workflow_execution=None,
    execution_step=None,
    trace_id: str = None,
    span_id: str = None,
    extra: dict = None,
) -> dict:
    """
    Build a standardized structured log context dict.

    Usage:
        logger.info("step_started", extra={
            "extra_data": build_log_context(
                workflow_execution=wf_exec,
                execution_step=step,
                extra={"action": "send_reminder"}
            )
        })

    Returns a flat dict suitable for JSON logging:
        {
            "trace_id": "wf_...",
            "span_id": "sp_...",
            "workflow_execution_id": 42,
            "workflow_run_id": 10,
            "step_execution_id": 7,
            "step_name": "send_reminder",
            "attempt": 1,
            ...extra fields
        }
    """
    ctx = {}

    # Resolve trace_id — prefer explicit arg, then from workflow_execution
    resolved_trace_id = trace_id
    if not resolved_trace_id and workflow_execution is not None:
        resolved_trace_id = getattr(workflow_execution, "trace_id", None)
    if resolved_trace_id:
        ctx["trace_id"] = resolved_trace_id

    # Resolve span_id — prefer explicit arg, then from execution_step
    resolved_span_id = span_id
    if not resolved_span_id and execution_step is not None:
        resolved_span_id = getattr(execution_step, "span_id", None)
    if resolved_span_id:
        ctx["span_id"] = resolved_span_id

    # Workflow execution fields
    if workflow_execution is not None:
        ctx["workflow_execution_id"] = getattr(workflow_execution, "id", None)
        ctx["workflow_run_id"] = getattr(workflow_execution, "workflow_run_id", None)
        ctx["workflow_id"] = getattr(workflow_execution, "workflow_id", None)
        ctx["workflow_status"] = getattr(workflow_execution, "status", None)

    # Step execution fields
    if execution_step is not None:
        ctx["step_execution_id"] = getattr(execution_step, "id", None)
        ctx["step_name"] = getattr(execution_step, "step_name", None)
        ctx["step_id"] = getattr(execution_step, "step_id", None)
        ctx["attempt"] = getattr(execution_step, "attempts", None)
        ctx["parent_span_id"] = getattr(execution_step, "parent_span_id", None)
        ctx["provider_request_id"] = getattr(
            execution_step, "provider_request_id", None
        )

    # Merge extra fields — extra takes lowest priority (ctx wins on conflict)
    if extra:
        for k, v in extra.items():
            if k not in ctx:
                ctx[k] = v

    # Remove None values for clean logs
    return {k: v for k, v in ctx.items() if v is not None}


# ─────────────────────────────────────────────
# DOWNSTREAM PROPAGATION
# ─────────────────────────────────────────────


def build_trace_headers(
    trace_id: str,
    span_id: str,
    parent_span_id: str = None,
    provider_request_id: str = None,
) -> dict:
    """
    Build standardized HTTP headers for downstream API call propagation.

    These headers follow the W3C traceparent convention naming pattern.
    Ready to be passed to requests.post(headers=...) when real HTTP clients are added.

    Usage:
        headers = build_trace_headers(
            trace_id=workflow_execution.trace_id,
            span_id=step_execution.span_id,
            parent_span_id=step_execution.parent_span_id,
        )
        # Future: requests.post(url, headers=headers, json=payload)

    Returns:
        {
            "X-Trace-Id": "wf_...",
            "X-Span-Id": "sp_...",
            "X-Parent-Span-Id": "wf_...",   # optional
            "X-Request-Id": "req_...",       # optional
        }
    """
    headers = {
        "X-Trace-Id": trace_id,
        "X-Span-Id": span_id,
    }

    if parent_span_id:
        headers["X-Parent-Span-Id"] = parent_span_id

    if provider_request_id:
        headers["X-Request-Id"] = provider_request_id

    return headers


def inject_trace_into_payload(
    payload: dict,
    workflow_execution,
    execution_step=None,
) -> dict:
    """
    Inject trace context into the action payload dict.
    All values are explicitly cast to plain Python primitives (str/int)
    so psycopg2 can safely serialize them into JSONB columns.

    Uses json round-trip as final safety net to catch any non-serializable
    SQLAlchemy instrumented attributes or ULID objects.
    """
    import json

    def _safe_str(val) -> str | None:
        if val is None:
            return None
        s = str(val)
        # Reject SQLAlchemy instrumented attribute repr strings
        if s.startswith("<") or "InstrumentedAttribute" in s:
            return None
        return s if s else None

    def _safe_int(val) -> int | None:
        if val is None:
            return None
        try:
            return int(val)
        except (TypeError, ValueError):
            return None

    trace_context = {}

    tid = _safe_str(getattr(workflow_execution, "trace_id", None))
    wid = _safe_int(getattr(workflow_execution, "id", None))

    if tid:
        trace_context["trace_id"] = tid
    if wid:
        trace_context["workflow_execution_id"] = wid

    if execution_step is not None:
        sid = _safe_str(getattr(execution_step, "span_id", None))
        psid = _safe_str(getattr(execution_step, "parent_span_id", None))
        esid = _safe_int(getattr(execution_step, "id", None))

        if sid:
            trace_context["span_id"] = sid
        if psid:
            trace_context["parent_span_id"] = psid
        if esid:
            trace_context["step_execution_id"] = esid

    # Final safety net — json round-trip forces all values to plain primitives
    # This catches any remaining SQLAlchemy proxy objects or non-serializable types
    try:
        trace_context = json.loads(json.dumps(trace_context, default=str))
    except Exception:
        trace_context = {}

    enriched = dict(payload)
    enriched["_trace"] = trace_context
    return enriched
