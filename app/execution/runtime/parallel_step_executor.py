from concurrent.futures import ThreadPoolExecutor, as_completed

from app.db.session import SessionLocal
from app.models.workflow_execution import WorkflowExecution
from app.execution.runtime.step_executor import execute_workflow_step


def execute_single_step(
    workflow_execution_id: int,
    step_definition: dict,
    payload: dict,
    workflow_knowledge_id: int | None = None,
):
    db = SessionLocal()
    try:
        workflow_execution = (
            db.query(WorkflowExecution)
            .filter(WorkflowExecution.id == workflow_execution_id)
            .first()
        )

        if not workflow_execution:
            return {
                "step_id": step_definition["id"],
                "result": {"success": False, "error": "workflow_execution_not_found"},
            }

        db.refresh(workflow_execution)

        result = execute_workflow_step(
            db=db,
            workflow_execution=workflow_execution,
            step_definition=step_definition,
            payload=payload,
            workflow_knowledge_id=workflow_knowledge_id,
        )

        return {"step_id": step_definition["id"], "result": result}

    finally:
        db.close()


def execute_parallel_steps(
    workflow_execution_id: int,
    ready_steps: list,
    payload: dict,
    workflow_knowledge_id: int | None = None,
):
    results = []
    with ThreadPoolExecutor(max_workers=len(ready_steps)) as executor:
        futures = [
            executor.submit(
                execute_single_step,
                workflow_execution_id,
                step,
                payload,
                workflow_knowledge_id,
            )
            for step in ready_steps
        ]

        for future in as_completed(futures):
            results.append(future.result())

    return results
