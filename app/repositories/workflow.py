from sqlalchemy.orm import Session
from app.models.workflow import Workflow
from app.core.logger import logger


def create(db: Session, name: str, domain: str, raw_input: str, parsed_rule_json=None):
    workflow = Workflow(
        name=name, domain=domain, raw_input=raw_input, parsed_rule_json=parsed_rule_json
    )
    db.add(workflow)
    db.flush()
    logger.debug(
        "workflow_repo_flushed",
        extra={"extra_data": {"workflow_id": workflow.id, "name": name}},
    )
    return workflow


def get_by_id(db: Session, workflow_id: int):
    result = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not result:
        logger.warning(
            "workflow_repo_not_found",
            extra={"extra_data": {"workflow_id": workflow_id}},
        )
    return result


def list_by_domain(db: Session, domain: str):
    query = db.query(Workflow)
    if domain:
        query = query.filter(Workflow.domain == domain)
    return query.all()


def delete(db: Session, workflow: Workflow):
    logger.info(
        "workflow_repo_deleted",
        extra={"extra_data": {"workflow_id": workflow.id}},
    )
    db.delete(workflow)
