from app.execution.runtime.dag_scheduler import get_ready_steps
from app.execution.runtime.step_executor import execute_workflow_step
from app.execution.runtime.parallel_step_executor import execute_parallel_steps
from app.workflow_execution.schemas.workflow_context import WorkflowContext
from app.core.logger import logger


def run_dag_execution(
    db,
    workflow_execution,
    dag,
    payload,
):
    steps = dag.get("steps", [])

    completed_steps = set()
    failed_steps = set()

    # WorkflowContext accumulates outputs from every completed step.
    # Future Decision Nodes will read from context.outputs to branch.
    context = WorkflowContext()

    while True:
        ready_steps = get_ready_steps(
            dag_steps=steps,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
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
                    ),
                }
            ]

        # Parallel path — each branch gets the same context instance
        else:
            results = execute_parallel_steps(
                workflow_execution_id=workflow_execution.id,
                ready_steps=ready_steps,
                payload=payload,
            )

        workflow_failed = False

        for item in results:
            step_id = item["step_id"]
            result  = item["result"]

            if result["success"]:
                completed_steps.add(step_id)

                # Merge step outputs into shared WorkflowContext
                action_result = result.get("result")
                if action_result and hasattr(action_result, "outputs"):
                    context.update(action_result.outputs)
                elif isinstance(action_result, dict):
                    # Legacy dict result — merge everything except control keys
                    outputs = {
                        k: v for k, v in action_result.items()
                        if k not in ("success", "status", "skip_retry", "message", "error")
                    }
                    context.update(outputs)

            else:
                failed_steps.add(step_id)
                workflow_failed = True

                logger.warning(
                    "dag_step_failed",
                    extra={
                        "extra_data": {
                            "workflow_execution_id": workflow_execution.id,
                            "step_id": step_id,
                        }
                    },
                )

        if workflow_failed:
            break

    return context
