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
    except Exception as exc:  # noqa: BLE001
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
    workspace_id: int | None = None,
):
    steps = dag.get("steps", [])
    steps_by_id = {s["id"]: s for s in steps}

    progress      = load_execution_progress(db, workflow_execution.id)
    completed_steps = progress["completed"]
    failed_steps    = progress["failed"]
    waiting_steps   = progress["waiting"]
    skipped_steps   = progress.get("skipped", set())

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
                        workspace_id=workspace_id,
                    ),
                }
            ]
        else:
            results = execute_parallel_steps(
                workflow_execution_id=workflow_execution.id,
                ready_steps=ready_steps,
                payload=payload,
                workspace_id=workspace_id,
            )

        workflow_failed  = False
        workflow_waiting = False

        for item in results:
            step_id = item["step_id"]
            result  = item["result"]

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

            if result.get("blocked"):
                waiting_steps.add(step_id)
                workflow_waiting = True
                logger.info(
                    "dag_step_rule_blocked",
                    extra={"extra_data": {
                        "workflow_execution_id": workflow_execution.id,
                        "step_id": step_id,
                        "rule_evaluation": result.get("rule_evaluation"),
                    }},
                )
                continue

            if result["success"]:
                completed_steps.add(step_id)
                outputs = _extract_outputs(result.get("result"))
                context.update_step(step_id, outputs)

                # ── Cross-workflow dispatch on success ────────────────────
                _handle_chain_dispatch(
                    db=db,
                    step_definition=steps_by_id.get(step_id, {}),
                    outputs=outputs,
                    workflow_execution=workflow_execution,
                    dispatch_type="success",
                )

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

                # ── Cross-workflow dispatch on failure ────────────────────
                _handle_chain_dispatch(
                    db=db,
                    step_definition=steps_by_id.get(step_id, {}),
                    outputs={},
                    workflow_execution=workflow_execution,
                    dispatch_type="failure",
                )

                logger.warning(
                    "dag_step_failed",
                    extra={"extra_data": {
                        "workflow_execution_id": workflow_execution.id,
                        "step_id": step_id,
                    }},
                )

        if workflow_failed or workflow_waiting:
            break

    return context


# ── Cross-workflow chain dispatch ─────────────────────────────────────────────

def _handle_chain_dispatch(
    db,
    step_definition: dict,
    outputs: dict,
    workflow_execution,
    dispatch_type: str,  # "success" | "failure"
) -> None:
    """
    Read on_success_dispatch / on_failure_dispatch / on_condition_dispatch
    from a step's config and fire the target workflow if conditions are met.

    Config format (set when user accepts a chain suggestion):
      {
        "on_success_dispatch":   {"workflow_id": 5},
        "on_failure_dispatch":   {"workflow_id": 7},
        "on_condition_dispatch": {
            "field": "credit_score", "op": "lt", "value": 650,
            "workflow_id": 8
        }
      }

    Never raises — chain dispatch failure must not abort the current workflow.
    """
    config = step_definition.get("config") or {}
    entity_id = str(getattr(workflow_execution, "entity_id", "") or "")

    # ── Unconditional success/failure dispatch ────────────────────────────────
    key = "on_success_dispatch" if dispatch_type == "success" else "on_failure_dispatch"
    spec = config.get(key)
    if spec and spec.get("workflow_id"):
        _fire_workflow(db, spec["workflow_id"], entity_id, dispatch_type)

    # ── Conditional dispatch (evaluated on success only) ─────────────────────
    if dispatch_type == "success":
        cond = config.get("on_condition_dispatch")
        if cond and cond.get("workflow_id"):
            if _evaluate_condition(cond, outputs):
                _fire_workflow(
                    db, cond["workflow_id"], entity_id, "condition_met"
                )


def _evaluate_condition(cond: dict, outputs: dict) -> bool:
    """
    Evaluate a simple field/op/value condition against step outputs.

    Supported ops: eq, ne, lt, lte, gt, gte, in, not_in
    """
    field = cond.get("field")
    op    = cond.get("op")
    value = cond.get("value")

    if not field or not op:
        return False

    actual = outputs.get(field)
    if actual is None:
        return False

    try:
        if op == "eq":      return actual == value
        if op == "ne":      return actual != value
        if op == "lt":      return float(actual) < float(value)
        if op == "lte":     return float(actual) <= float(value)
        if op == "gt":      return float(actual) > float(value)
        if op == "gte":     return float(actual) >= float(value)
        if op == "in":      return actual in (value or [])
        if op == "not_in":  return actual not in (value or [])
    except (TypeError, ValueError):
        pass

    return False


def _fire_workflow(
    db,
    workflow_id: int,
    entity_id: str,
    event_type: str,
) -> None:
    """Dispatch a chained workflow. Best-effort — logs but never raises."""
    try:
        from app.services.workflow_dispatch_service import WorkflowDispatchService
        result = WorkflowDispatchService(db).dispatch(
            workflow_id=workflow_id,
            entity_id=entity_id,
            event_type=f"chain_{event_type}",
        )
        logger.info(
            "chain_dispatch_fired",
            extra={"extra_data": {
                "target_workflow_id": workflow_id,
                "event_type":         event_type,
                "success":            result.success,
                "message":            result.message,
            }},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "chain_dispatch_failed",
            extra={"extra_data": {
                "target_workflow_id": workflow_id,
                "error":              str(exc),
            }},
        )
