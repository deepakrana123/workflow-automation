from app.execution.runtime.dag_scheduler import get_ready_steps
from app.execution.runtime.step_executor import execute_workflow_step
from app.execution.runtime.parallel_step_executor import execute_parallel_steps
from app.execution.runtime.step_execution_service import (
    load_execution_progress,
    create_step_execution,
    mark_step_skipped,
)
from app.execution.rules.routing import (
    resolve_activated_children,
    resolve_skipped_steps,
)
from app.workflow_execution.schemas.workflow_context import WorkflowContext
from app.core.logger import logger


def _extract_outputs(action_result) -> dict:
    """Pull the real outputs dict out of a step result (dump or ActionResult)."""
    if isinstance(action_result, dict):
        return action_result.get("outputs", {}) or {}
    if action_result is not None and hasattr(action_result, "outputs"):
        return action_result.outputs or {}
    return {}


def _record_skipped(db, workflow_execution, step_def, step_id):
    """Persist a SKIPPED step row so it is auditable and finalizer-visible."""
    try:
        se = create_step_execution(
            db=db,
            workflow_execution_id=workflow_execution.id,
            step_name=(step_def or {}).get("action") or step_id,
            step_id=step_id,
        )
        mark_step_skipped(db=db, step_execution=se)
    except Exception as exc:  # noqa: BLE001 - skip recording must not break the DAG
        logger.warning(
            "dag_skip_record_failed",
            extra={"extra_data": {
                "workflow_execution_id": workflow_execution.id,
                "step_id": step_id,
                "error": str(exc),
            }},
        )


def run_dag_execution(
    db,
    workflow_execution,
    dag,
    payload,
    workflow_knowledge_id: int | None = None,
):
    steps = dag.get("steps", [])
    steps_by_id = {s["id"]: s for s in steps}

    # Rehydrate progress from persisted step rows so a resumed execution
    # (after pause / human approval) continues from where it stopped and
    # never re-runs completed steps (exactly-once).
    progress = load_execution_progress(db, workflow_execution.id)
    completed_steps = progress["completed"]
    failed_steps    = progress["failed"]
    waiting_steps   = progress["waiting"]
    skipped_steps   = progress.get("skipped", set())

    # WorkflowContext accumulates outputs — seeded from rehydrated per-step
    # outputs so rule routing can read a parent's output after a resume.
    context = WorkflowContext()
    context.outputs.update(progress["outputs"])
    for sid, outs in progress.get("step_outputs", {}).items():
        context.update_step(sid, outs)

    while True:
        ready_steps = get_ready_steps(
            dag_steps=steps,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            waiting_steps=waiting_steps,
            skipped_steps=skipped_steps,
        )

        if not ready_steps:
            break

        # Sequential path
        if len(ready_steps) == 1:
            step = ready_steps[0]
            results = [
                {
                    "step_id": step["id"],
                    "result": execute_workflow_step(
                        db=db,
                        workflow_execution=workflow_execution,
                        step_definition=step,
                        payload=payload,
                        workflow_knowledge_id=workflow_knowledge_id,
                    ),
                }
            ]

        # Parallel path
        else:
            results = execute_parallel_steps(
                workflow_execution_id=workflow_execution.id,
                ready_steps=ready_steps,
                payload=payload,
                workflow_knowledge_id=workflow_knowledge_id,
            )

        workflow_failed  = False
        workflow_waiting = False

        for item in results:
            step_id = item["step_id"]
            result  = item["result"]

            # A human_task step suspends the DAG: neither completed nor failed.
            if result.get("waiting"):
                waiting_steps.add(step_id)
                workflow_waiting = True
                logger.info(
                    "dag_step_waiting",
                    extra={"extra_data": {
                        "workflow_execution_id": workflow_execution.id,
                        "step_id": step_id,
                    }},
                )
                continue

            if result["success"]:
                completed_steps.add(step_id)
                outputs = _extract_outputs(result.get("result"))
                context.update_step(step_id, outputs)

                # ── Rule engine: parent decides children ────────────────────
                # Only steps carrying a `routing` spec trigger branching; all
                # other (linear) steps behave exactly as before.
                routing = steps_by_id.get(step_id, {}).get("routing")
                if routing:
                    activated = resolve_activated_children(routing, outputs)
                    newly_skipped = resolve_skipped_steps(steps, step_id, activated)
                    newly_skipped -= completed_steps
                    newly_skipped -= failed_steps
                    for sid in newly_skipped:
                        if sid not in skipped_steps:
                            _record_skipped(db, workflow_execution, steps_by_id.get(sid), sid)
                            skipped_steps.add(sid)
                    logger.info(
                        "dag_routing_applied",
                        extra={"extra_data": {
                            "workflow_execution_id": workflow_execution.id,
                            "decision_step": step_id,
                            "activated": activated,
                            "skipped": sorted(newly_skipped),
                        }},
                    )

            else:
                failed_steps.add(step_id)
                workflow_failed = True
                logger.warning(
                    "dag_step_failed",
                    extra={"extra_data": {
                        "workflow_execution_id": workflow_execution.id,
                        "step_id": step_id,
                    }},
                )

        # Stop the DAG on failure OR when awaiting human approval. The finalizer
        # inspects persisted step statuses (COMPLETED/SKIPPED/FAILED/WAITING).
        if workflow_failed or workflow_waiting:
            break

    return context
