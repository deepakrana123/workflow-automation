"""
app/runtime/audit.py

RuntimeAuditService — records structured runtime events to the audit_logs table.

Event types match the spec:
  WORKFLOW_ACCESSED, RETRIEVAL_STARTED, RETRIEVAL_COMPLETED, CANDIDATE_SELECTED,
  AUTHORIZATION_DENIED, RULE_EVALUATED, RULE_FAILED, ACTION_EXECUTED,
  ACTION_FAILED, STEP_COMPLETED, WORKFLOW_COMPLETED

The AuditLog model already has user_id, workspace_id, workflow_id columns.
This service just provides a typed interface on top of audit_repo.create().

Sensitive payloads (credentials, full request bodies) are never stored.
"""

from __future__ import annotations

import json
from typing import Optional

from sqlalchemy.orm import Session

from app.repositories.audit_repo import create as _create
from app.core.logger import logger

# ── Runtime event type constants ──────────────────────────────────────────────
RUNTIME_WORKFLOW_ACCESSED    = "runtime_workflow_accessed"
RUNTIME_RETRIEVAL_STARTED    = "runtime_retrieval_started"
RUNTIME_RETRIEVAL_COMPLETED  = "runtime_retrieval_completed"
RUNTIME_CANDIDATE_SELECTED   = "runtime_candidate_selected"
RUNTIME_AUTHZ_DENIED         = "runtime_authorization_denied"
RUNTIME_RULE_EVALUATED       = "runtime_rule_evaluated"
RUNTIME_RULE_FAILED          = "runtime_rule_failed"
RUNTIME_ACTION_EXECUTED      = "runtime_action_executed"
RUNTIME_ACTION_FAILED        = "runtime_action_failed"
RUNTIME_STEP_COMPLETED       = "runtime_step_completed"
RUNTIME_WORKFLOW_COMPLETED   = "runtime_workflow_completed"
RUNTIME_GLOBAL_SEARCH        = "runtime_global_search"


def _safe_json(obj) -> str | None:
    if obj is None:
        return None
    try:
        return json.dumps(obj, default=str)
    except Exception:
        return str(obj)


class RuntimeAuditService:
    """Thin typed wrapper over audit_repo.create for runtime events."""

    def __init__(self, db: Session):
        self._db = db

    def workflow_accessed(
        self,
        user_id: str,
        workspace_id: int,
        workflow_id: int | None,
    ) -> None:
        self._write(
            event_type=RUNTIME_WORKFLOW_ACCESSED,
            status="success",
            action="runtime:workflow_accessed",
            user_id=user_id,
            workspace_id=workspace_id,
            workflow_id=workflow_id,
        )

    def retrieval_started(
        self,
        user_id: str,
        workspace_id: int,
        query: str,
        workflow_id: int | None = None,
    ) -> None:
        self._write(
            event_type=RUNTIME_RETRIEVAL_STARTED,
            status="started",
            action="runtime:retrieval_started",
            user_id=user_id,
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            request_payload=_safe_json({"query": query[:200]}),
        )

    def retrieval_completed(
        self,
        user_id: str,
        workspace_id: int,
        query: str,
        total_retrieved: int,
        total_authorized: int,
        selected_action_name: str | None = None,
        workflow_id: int | None = None,
    ) -> None:
        self._write(
            event_type=RUNTIME_RETRIEVAL_COMPLETED,
            status="success",
            action="runtime:retrieval_completed",
            user_id=user_id,
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            response_payload=_safe_json({
                "total_retrieved":   total_retrieved,
                "total_authorized":  total_authorized,
                "selected_action":   selected_action_name,
            }),
        )

    def authorization_denied(
        self,
        user_id: str,
        workspace_id: int,
        action_id: int | None,
        reason: str,
        workflow_id: int | None = None,
    ) -> None:
        self._write(
            event_type=RUNTIME_AUTHZ_DENIED,
            status="denied",
            action="runtime:authorization_denied",
            user_id=user_id,
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            request_payload=_safe_json({"action_id": action_id, "reason": reason}),
        )

    def rule_evaluated(
        self,
        user_id: str,
        workspace_id: int,
        allowed: bool,
        failed_count: int,
        workflow_id: int | None = None,
    ) -> None:
        event = RUNTIME_RULE_FAILED if not allowed else RUNTIME_RULE_EVALUATED
        self._write(
            event_type=event,
            status="denied" if not allowed else "success",
            action="runtime:rule_evaluated",
            user_id=user_id,
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            response_payload=_safe_json({"allowed": allowed, "failed_count": failed_count}),
        )

    def action_executed(
        self,
        user_id: str,
        workspace_id: int,
        action_name: str,
        success: bool,
        workflow_id: int | None = None,
        execution_id: int | None = None,
    ) -> None:
        event = RUNTIME_ACTION_EXECUTED if success else RUNTIME_ACTION_FAILED
        self._write(
            event_type=event,
            status="success" if success else "failed",
            action="runtime:action_executed",
            user_id=user_id,
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            request_payload=_safe_json({
                "action_name":   action_name,
                "execution_id":  execution_id,
            }),
        )

    def global_search(
        self,
        user_id: str,
        workspace_id: int,
        query: str,
        result_count: int,
    ) -> None:
        self._write(
            event_type=RUNTIME_GLOBAL_SEARCH,
            status="success",
            action="runtime:global_search",
            user_id=user_id,
            workspace_id=workspace_id,
            request_payload=_safe_json({"query": query[:200], "result_count": result_count}),
        )

    # ── Private ────────────────────────────────────────────────────────────────

    def _write(
        self,
        event_type: str,
        status: str,
        action: str,
        user_id: str | None = None,
        workspace_id: int | None = None,
        workflow_id: int | None = None,
        request_payload: str | None = None,
        response_payload: str | None = None,
    ) -> None:
        try:
            _create(
                db=self._db,
                workflow_id=workflow_id,
                action=action,
                status=status,
                event_type=event_type,
                request_payload=request_payload,
                response_payload=response_payload,
                user_id=user_id,
                workspace_id=workspace_id,
            )
        except Exception as exc:
            logger.warning(
                "runtime_audit_write_failed",
                extra={"extra_data": {"event_type": event_type, "error": str(exc)}},
            )
