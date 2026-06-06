from app.models.workflow_run import WorkflowRun


def create(db, workflow_id: int, event_type: str, entity_id: str) -> WorkflowRun:
    row = WorkflowRun(
        workflow_id=workflow_id,
        event_type=event_type,
        entity_id=entity_id,
        status="QUEUED",
    )
    db.add(row)
    db.flush()
    return row
