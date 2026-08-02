"""
app/services/workflow_dispatch_service.py

Orchestrates workflow execution dispatch: create run, create execution,
queue to Redis. Owns the transaction boundary and duplicate-guard logic.
"""

import json
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.workflow import Workflow
from app.models.workflow_run import WorkflowRun
from app.models.workflow_execution import WorkflowExecution
from app.execution.runtime.workflow_execution_service import (
    mark_workflow_running,
    mark_workflow_paused,
)
from app.core.redis_client import redis_client
from app.core.logger import logger
from app.execution.constants import REDIS_EVENT_QUEUE


@dataclass
class DispatchResult:
    success: bool
    workflow_run_id: int | None = None
    workflow_execution_id: int | None = None
    message: str | None = None


class WorkflowDispatchService:

    def __init__(self, db: Session):
        self.db = db

    def dispatch(
        self,
        workflow_id: int,
        entity_id: str,
        event_type: str | None = None,
    ) -> DispatchResult:
        """
        Queue a workflow for execution.

        Guards against duplicate active executions via DB check + Redis lock.
        Creates WorkflowRun + WorkflowExecution, pushes event to Redis queue.
        """
        workflow = (
            self.db.query(Workflow)
            .filter(Workflow.id == workflow_id)
            .first()
        )
        if not workflow:
            raise ValueError("workflow not found")

        # Duplicate execution guard
        existing = (
            self.db.query(WorkflowExecution)
            .filter(
                WorkflowExecution.workflow_id == workflow_id,
                WorkflowExecution.status.in_(["PENDING", "RUNNING"]),
            )
            .first()
        )

        lock_key = f"workflow_lock:{workflow_id}"
        lock_acquired = redis_client.set(lock_key, "running", nx=True, ex=3600)

        if existing or not lock_acquired:
            return DispatchResult(
                success=False,
                workflow_execution_id=existing.id if existing else None,
                message="workflow already has an active execution",
            )

        try:
            workflow_run = WorkflowRun(
                workflow_id=workflow.id,
                entity_id=entity_id,
                event_type=event_type,
                status="QUEUED",
            )
            self.db.add(workflow_run)
            self.db.flush()

            workflow_execution = WorkflowExecution(
                workflow_id=workflow.id,
                workflow_run_id=workflow_run.id,
                entity_id=entity_id,
                status="PENDING",
            )
            self.db.add(workflow_execution)
            self.db.commit()
            self.db.refresh(workflow_run)
            self.db.refresh(workflow_execution)

            # Queue for async processing
            workflow_event = {"workflow_execution_id": workflow_execution.id}
            redis_client.lpush(REDIS_EVENT_QUEUE, json.dumps(workflow_event))

            logger.info(
                "workflow_execution_queued",
                extra={"extra_data": {
                    "workflow_run_id": workflow_run.id,
                    "workflow_execution_id": workflow_execution.id,
                    "workflow_id": workflow.id,
                }},
            )

            return DispatchResult(
                success=True,
                workflow_run_id=workflow_run.id,
                workflow_execution_id=workflow_execution.id,
            )

        except IntegrityError:
            self.db.rollback()
            return DispatchResult(success=False, message="duplicate execution ignored")

    def pause(self, workflow_execution_id: int) -> dict:
        """Pause a running workflow execution."""
        execution = (
            self.db.query(WorkflowExecution)
            .filter(WorkflowExecution.id == workflow_execution_id)
            .first()
        )
        if not execution:
            raise ValueError("workflow execution not found")
        if execution.status != "RUNNING":
            raise ValueError(
                f"cannot pause execution in status '{execution.status}' — must be RUNNING"
            )

        mark_workflow_paused(db=self.db, workflow_execution=execution)
        return {
            "success": True,
            "workflow_execution_id": execution.id,
            "status": execution.status,
        }

    def resume(self, workflow_execution_id: int) -> dict:
        """Resume a paused workflow execution."""
        execution = (
            self.db.query(WorkflowExecution)
            .filter(WorkflowExecution.id == workflow_execution_id)
            .first()
        )
        if not execution:
            raise ValueError("workflow execution not found")
        if execution.status != "PAUSED":
            raise ValueError(
                f"cannot resume execution in status '{execution.status}' — must be PAUSED"
            )

        mark_workflow_running(db=self.db, workflow_execution=execution)

        workflow_event = {"workflow_execution_id": execution.id}
        redis_client.lpush(REDIS_EVENT_QUEUE, json.dumps(workflow_event))

        logger.info(
            "workflow_execution_resumed",
            extra={"extra_data": {"workflow_execution_id": execution.id}},
        )

        return {
            "success": True,
            "workflow_execution_id": execution.id,
            "status": execution.status,
        }
