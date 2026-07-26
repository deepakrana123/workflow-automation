"""
app/execution/runtime/retry_executor.py

Handles re-execution of steps that were scheduled for retry via Redis.

Uses the same dispatch path as step_executor:
  ActionConfiguration → ExecutorRegistry → Executor.execute()

This ensures retry behaviour is identical to first-attempt behaviour.
"""

from app.models.workflow import Workflow
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.action_definitions import ActionDefinition
from app.repositories.action_configuration_repository import ActionConfigurationRepository
from app.execution.executors.registry import ExecutorRegistry
from app.workflow_execution.schemas.action_result import ActionResult

from app.execution.runtime.step_execution_service import (
    mark_step_running,
    mark_step_completed,
    mark_step_failed,
)
from app.execution.runtime.workflow_execution_service import mark_workflow_failed
from app.execution.runtime.workflow_finalizer import finalize_workflow_execution
from app.execution.retry_handler import handle_retry
from app.core.logger import logger


def _load_action_configuration(db, action_name: str, workflow_knowledge_id: int | None):
    """
    Mirror of step_executor._load_action_configuration.
    Returns (ActionConfiguration | None, execution_type: str).
    """
    try:
        action_def = (
            db.query(ActionDefinition)
            .filter(
                ActionDefinition.name == action_name,
                ActionDefinition.active.is_(True),
            )
            .first()
        )
        if action_def is None:
            return None, "python"

        repo = ActionConfigurationRepository(db)

        if workflow_knowledge_id is not None:
            config = repo.get_active_configuration(
                workflow_knowledge_id=workflow_knowledge_id,
                action_definition_id=action_def.id,
            )
        else:
            config = repo.get_by_action_definition(
                action_definition_id=action_def.id,
            )

        if config is None:
            return None, "python"

        return config, config.execution_type or "python"

    except Exception as e:
        logger.warning(
            "retry_executor_config_lookup_failed",
            extra={"extra_data": {"action_name": action_name, "error": str(e)}},
        )
        return None, "python"


def execute_retry(db, workflow_execution, step_execution):
    try:
        logger.info(
            "retry_execution_started",
            extra={"extra_data": {
                "workflow_execution_id": workflow_execution.id,
                "step_execution_id":     step_execution.id,
                "step_name":             step_execution.step_name,
            }},
        )

        db.refresh(workflow_execution)
        db.refresh(step_execution)

        if step_execution.status != "RETRY_SCHEDULED":
            logger.info(
                "retry_skipped_step_not_scheduled",
                extra={"extra_data": {
                    "step_execution_id": step_execution.id,
                    "status":            step_execution.status,
                }},
            )
            return

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

        # Resolve workflow_knowledge_id for ActionConfiguration lookup
        workflow_knowledge = (
            db.query(WorkflowKnowledge)
            .filter(WorkflowKnowledge.workflow_name == workflow.name)
            .order_by(WorkflowKnowledge.id.desc())
            .first()
        )
        workflow_knowledge_id = workflow_knowledge.id if workflow_knowledge else None

        action = step_execution.step_name

        action_config, execution_type = _load_action_configuration(
            db=db,
            action_name=action,
            workflow_knowledge_id=workflow_knowledge_id,
        )

        if action_config is None:
            error = (
                f"No ActionConfiguration found for action '{action}' on retry "
                f"(workflow_knowledge_id={workflow_knowledge_id})"
            )
            logger.error(
                "retry_executor_no_action_configuration",
                extra={"extra_data": {
                    "action":                action,
                    "workflow_knowledge_id": workflow_knowledge_id,
                }},
            )
            mark_step_failed(db=db, step_execution=step_execution, error=error)
            handle_retry(
                db=db,
                step_execution=step_execution,
                error=error,
                workflow_execution=workflow_execution,
                skip_retry=True,
            )
            return

        executor = ExecutorRegistry.get_executor(execution_type)
        result: ActionResult = executor.execute(
            configuration=action_config,
            context=step_execution.input_payload or {},
        )

        if result.success:
            mark_step_completed(
                db=db,
                step_execution=step_execution,
                output_payload=result.model_dump(),
            )
            finalize_workflow_execution(db=db, workflow_execution=workflow_execution)

            logger.info(
                "retry_execution_completed",
                extra={"extra_data": {
                    "workflow_execution_id": workflow_execution.id,
                    "step_execution_id":     step_execution.id,
                }},
            )
            return

        # Retry failed again — re-enter retry/DLQ decision
        step_error = result.error or str(result.outputs)
        mark_step_failed(db=db, step_execution=step_execution, error=step_error)
        handle_retry(
            db=db,
            step_execution=step_execution,
            error=step_error,
            workflow_execution=workflow_execution,
            skip_retry=result.metadata.get("skip_retry", False),
        )

    except Exception as e:
        logger.exception(
            "retry_execution_failed",
            extra={"extra_data": {
                "workflow_execution_id": workflow_execution.id,
                "step_execution_id":     step_execution.id,
                "error":                 str(e),
            }},
        )

        try:
            if step_execution.status not in ("FAILED", "DLQ", "COMPLETED"):
                mark_step_failed(db=db, step_execution=step_execution, error=str(e))
                handle_retry(
                    db=db,
                    step_execution=step_execution,
                    error=str(e),
                    workflow_execution=workflow_execution,
                )

            if workflow_execution.status not in ("FAILED", "COMPLETED"):
                mark_workflow_failed(
                    db=db,
                    workflow_execution=workflow_execution,
                    error=str(e),
                )

        except Exception as state_error:
            logger.error(
                "retry_execution_state_update_failed",
                extra={"extra_data": {
                    "workflow_execution_id": workflow_execution.id,
                    "step_execution_id":     step_execution.id,
                    "error":                 str(state_error),
                }},
            )
