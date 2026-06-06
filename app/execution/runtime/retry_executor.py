from app.execution.dispatcher import execute_action
from app.models.workflow import Workflow

from app.execution.runtime.step_execution_service import (
    mark_step_running,
    mark_step_completed,
    mark_step_failed,
)

from app.execution.runtime.workflow_execution_service import (
    mark_workflow_failed,
)
from app.execution.runtime.workflow_finalizer import finalize_workflow_execution
from app.execution.retry_handler import handle_retry
from app.core.logger import logger


def execute_retry(db, workflow_execution, step_execution):
    try:
        logger.info(
            "retry_execution_started",
            extra={
                "extra_data": {
                    "workflow_execution_id": workflow_execution.id,
                    "step_execution_id": step_execution.id,
                    "step_name": step_execution.step_name,
                }
            },
        )

        # Refresh to get latest DB state
        db.refresh(workflow_execution)
        db.refresh(step_execution)

        if step_execution.status != "RETRY_SCHEDULED":
            logger.info(
                "retry_skipped_step_not_scheduled",
                extra={
                    "extra_data": {
                        "step_execution_id": step_execution.id,
                        "status": step_execution.status,
                    }
                },
            )
            return

        # Move step back to RUNNING
        mark_step_running(db=db, step_execution=step_execution)

        workflow = (
            db.query(Workflow)
            .filter(Workflow.id == workflow_execution.workflow_id)
            .first()
        )

        if not workflow:
            mark_step_failed(
                db=db,
                step_execution=step_execution,
                error="workflow_definition_not_found_on_retry",
            )
            mark_workflow_failed(
                db=db,
                workflow_execution=workflow_execution,
                error="workflow_definition_not_found_on_retry",
            )
            return

        dag = workflow.parsed_rule_json or {}
        # Find the step definition in the DAG by step_name
        steps = dag.get("steps", [])
        step_def = next(
            (s for s in steps if s.get("action") == step_execution.step_name),
            None,
        )

        action = step_execution.step_name
        config = step_def.get("config", {}) if step_def else {}

        result = execute_action(
            action_name=action,
            payload=step_execution.input_payload or {},
            config=config,
        )

        success = result.get("success") is True or result.get("status") == "success"

        if success:
            mark_step_completed(
                db=db,
                step_execution=step_execution,
                output_payload=result,
            )

            # Finalize workflow — other steps may still be pending
            finalize_workflow_execution(db=db, workflow_execution=workflow_execution)

            logger.info(
                "retry_execution_completed",
                extra={
                    "extra_data": {
                        "workflow_execution_id": workflow_execution.id,
                        "step_execution_id": step_execution.id,
                    }
                },
            )
            return

        # Retry failed again — re-enter retry/DLQ decision
        mark_step_failed(db=db, step_execution=step_execution, error=str(result))

        handle_retry(db=db, step_execution=step_execution, error=str(result))

    except Exception as e:
        logger.exception(
            "retry_execution_failed",
            extra={
                "extra_data": {
                    "workflow_execution_id": workflow_execution.id,
                    "step_execution_id": step_execution.id,
                    "error": str(e),
                }
            },
        )

        try:
            if step_execution.status not in ("FAILED", "DLQ", "COMPLETED"):
                mark_step_failed(db=db, step_execution=step_execution, error=str(e))
                handle_retry(db=db, step_execution=step_execution, error=str(e))

            if workflow_execution.status not in ("FAILED", "COMPLETED"):
                mark_workflow_failed(
                    db=db,
                    workflow_execution=workflow_execution,
                    error=str(e),
                )

        except Exception as state_error:
            logger.error(
                "retry_execution_state_update_failed",
                extra={
                    "extra_data": {
                        "workflow_execution_id": workflow_execution.id,
                        "step_execution_id": step_execution.id,
                        "error": str(state_error),
                    }
                },
            )
