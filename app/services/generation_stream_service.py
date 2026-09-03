"""
app/services/generation_stream_service.py

WorkspaceGenerationStreamService — bridges the synchronous generation
pipeline to an async Server-Sent Events stream.

Why the thread + queue pattern (see architecture decision in the audit):
  - NLPWorkflowService.generate() is synchronous (blocking HTTP calls to LLM).
  - FastAPI endpoints are async.
  - asyncio.to_thread() only gives you the final return value — you cannot get
    intermediate progress events from it.
  - A thread writes events into a thread-safe queue.Queue as they happen.
  - An async generator reads from the queue and yields SSE-formatted strings.
  - A sentinel object (DONE / ERROR) signals end-of-stream.
  - queue.get(timeout=5) doubles as a heartbeat mechanism — if nothing arrives
    in 5 seconds, a heartbeat event is sent to keep the connection alive.

The SSE format per event:
  data: {"event": "<name>", "seq": <int>, "ts": <unix_ms>, "data": {...}}\n\n

The frontend connects via fetch() + ReadableStream (not EventSource, because
EventSource only supports GET and cannot send JSON bodies or auth headers).
"""

from __future__ import annotations

import asyncio
import json
import queue
import threading
import time
from typing import AsyncGenerator

from sqlalchemy.orm import Session

from app.core.config import GENERATION_BUDGET_SECONDS
from app.core.logger import logger


# Sentinel objects — never confused with real event payloads
_DONE  = object()
_ERROR = object()

# How long to wait on the queue before emitting a heartbeat (seconds)
_HEARTBEAT_INTERVAL = 5


class WorkspaceGenerationStreamService:
    """
    Streams workspace workflow generation progress as SSE events.

    Usage (in a FastAPI route):

        from fastapi.responses import StreamingResponse

        @router.post("/{workspace_id}/generate/stream")
        async def generate_stream(workspace_id: int, body: ..., db = Depends(get_db)):
            svc = WorkspaceGenerationStreamService()
            return StreamingResponse(
                svc.stream(db, workspace_id, body),
                media_type="text/event-stream",
                headers={
                    "Cache-Control":     "no-cache",
                    "X-Accel-Buffering": "no",   # disable nginx buffering
                },
            )
    """

    async def stream(
        self,
        db: Session,
        workspace_id: int,
        name: str,
        user_request: str,
        domain: str,
        selected_action_ids: list[int] | None = None,
        budget_seconds: float | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Async generator that yields SSE-formatted strings.

        Starts the synchronous generation pipeline in a background thread.
        The pipeline pushes events into a thread-safe queue via its
        progress_callback. This generator pulls from the queue and yields
        SSE strings. Heartbeats are sent every 5 seconds while waiting.
        """
        budget = budget_seconds if budget_seconds is not None else GENERATION_BUDGET_SECONDS
        event_queue: queue.Queue = queue.Queue()
        seq = 0
        stream_start = time.time()

        def _format_event(event: str, data: dict) -> str:
            """Format one SSE message."""
            nonlocal seq
            seq += 1
            payload = {
                "event": event,
                "seq":   seq,
                "ts":    int(time.time() * 1000),
                "data":  data,
            }
            return f"data: {json.dumps(payload)}\n\n"

        def _callback(event: str, data: dict) -> None:
            """Called by the generation pipeline on the worker thread."""
            event_queue.put((event, data))

        def _run_generation() -> None:
            """The generation pipeline runs entirely on this thread."""
            # Each streaming request gets its own DB session — the caller's
            # session is not thread-safe. We open a new session here and close
            # it when the thread exits.
            from app.db.session import SessionLocal
            from app.services.nl_workflow_service import (
                generate_workspace_workflow_service,
            )

            thread_db = SessionLocal()
            try:
                generate_workspace_workflow_service(
                    db=thread_db,
                    workspace_id=workspace_id,
                    name=name,
                    user_request=user_request,
                    domain=domain,
                    selected_action_ids=selected_action_ids,
                    progress_callback=_callback,
                    budget_seconds=budget,
                )
            except ValueError as exc:
                # Known business errors — suitability rejected, budget exceeded, etc.
                code = "budget_exceeded" if "budget_exceeded" in str(exc) else "generation_failed"
                retryable = "budget_exceeded" in str(exc)
                event_queue.put((_ERROR, {
                    "code":      code,
                    "message":   str(exc),
                    "retryable": retryable,
                }))
            except Exception as exc:
                logger.exception(
                    "generation_stream_worker_error",
                    extra={"extra_data": {
                        "workspace_id": workspace_id,
                        "error":        str(exc),
                    }},
                )
                event_queue.put((_ERROR, {
                    "code":      "internal_error",
                    "message":   "Generation failed unexpectedly.",
                    "retryable": True,
                }))
            finally:
                thread_db.close()
                event_queue.put(_DONE)

        # Start the worker thread — daemon=True so it does not block server shutdown
        thread = threading.Thread(target=_run_generation, daemon=True)
        thread.start()

        # Drain the queue and yield SSE events
        while True:
            try:
                item = event_queue.get(timeout=_HEARTBEAT_INTERVAL)

                if item is _DONE:
                    elapsed_ms = int((time.time() - stream_start) * 1000)
                    yield _format_event("stream_closed", {"elapsed_ms": elapsed_ms})
                    break

                if item is _ERROR:
                    # _ERROR sentinel is never put directly — the tuple form is
                    # (sentinel, data). But we guard both forms.
                    break

                event_name, data = item

                # The ERROR tuple — sent from the worker on exception
                if event_name is _ERROR:
                    yield _format_event("error", data)
                    break

                yield _format_event(event_name, data)

            except queue.Empty:
                # Nothing arrived in _HEARTBEAT_INTERVAL seconds — send heartbeat
                elapsed_ms = int((time.time() - stream_start) * 1000)
                yield _format_event("heartbeat", {"elapsed_ms": elapsed_ms})

                # Safety: if thread died without sending DONE, stop the generator
                if not thread.is_alive() and event_queue.empty():
                    yield _format_event("stream_closed", {
                        "elapsed_ms": elapsed_ms,
                        "note":       "worker_thread_exited",
                    })
                    break
