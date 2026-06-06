from sqlalchemy.orm import Session
from app.schemas.workflow import WorkflowCreate
from app.repositories import workflow
from app.core.logger import logger
from app.parsers.dag_orchestrator import parse_dag_workflow
from app.parsers.dsl_normalizer import normalize_multiline_dsl

ALLOWED_DOMAINS = {
    "support",
    "health",
    "loan",
    "payments",
    "hr",
    "logistics",
    "ecommerce",
}


def create_workflow_service(payload: WorkflowCreate, db: Session):
    if payload.domain not in ALLOWED_DOMAINS:
        logger.warning(
            "workflow_invalid_domain",
            extra={"extra_data": {"domain": payload.domain}},
        )
        raise ValueError("Invalid domain")

    parse = normalize_multiline_dsl(payload.raw_input)
    parse_result = parse_dag_workflow(parse)

    if not parse_result["validation"]["is_valid"]:
        logger.warning(
            "workflow_parse_invalid",
            extra={
                "extra_data": {
                    "errors": parse_result["validation"]["errors"],
                    "raw_input": payload.raw_input[:100],
                }
            },
        )
        raise ValueError("Workflow text is invalid")

    parsed_rule_json = {
        "version": "v2",
        "steps": parse_result["steps"],
    }

    result = workflow.create(
        db=db,
        name=payload.name,
        domain=payload.domain,
        raw_input=payload.raw_input,
        parsed_rule_json=parsed_rule_json,
    )

    db.commit()
    db.refresh(result)

    logger.info(
        "workflow_created",
        extra={
            "extra_data": {
                "workflow_id": result.id,
                "name": result.name,
                "domain": result.domain,
                "workflow_version": "v2",
                "step_count": len(parse_result["steps"]),
            }
        },
    )

    return result


def get_workflow_service(workflow_id: int, db: Session):
    result = workflow.get_by_id(db, workflow_id)
    if not result:
        logger.warning(
            "workflow_not_found",
            extra={"extra_data": {"workflow_id": workflow_id}},
        )
        raise ValueError("Workflow not found")
    return result


def list_workflow_service(domain: str | None, db: Session):
    return workflow.list_by_domain(db, domain)


def debug_parse_service(raw_text: str):
    logger.info(
        "debug_parse_called",
        extra={"extra_data": {"raw_text_preview": raw_text[:100]}},
    )
    parse = normalize_multiline_dsl(raw_text)
    return parse_dag_workflow(parse)
