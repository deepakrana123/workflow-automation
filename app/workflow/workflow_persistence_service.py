"""
app/workflow/workflow_persistence_service.py

Saves a compiled workflow to the database.

Responsibilities:
- Takes the output of WorkflowCompilerService.compile()
- Validates domain
- Persists to workflows table via repository
- Returns structured save result

Does NOT know about NLP, LLM, or prompt logic.
"""

from sqlalchemy.orm import Session

from app.repositories import workflow as workflow_repo
from app.core.logger import logger


ALLOWED_DOMAINS = {
    "support",
    "health",
    "loan",
    "payments",
    "hr",
    "logistics",
    "ecommerce",
}


class WorkflowPersistenceService:

    def save(
        self,
        db: Session,
        name: str,
        domain: str,
        user_request: str,
        compile_result: dict,
    ) -> dict:
        """
        Persist a compiled workflow to the DB.

        Args:
            db           : SQLAlchemy session
            name         : workflow name (from user input)
            domain       : domain string — must be in ALLOWED_DOMAINS
            user_request : original NL input stored as raw_input
            compile_result: output from WorkflowCompilerService.compile()
                           expects keys: "dsl", "compiled"
                           compiled = {"version":"v2", "trigger":{...}, "steps":[...]}

        Returns:
            {
                "workflow_id": int,
                "name": str,
                "domain": str,
                "dsl": str,
                "parsed_rule_json": dict,
            }

        Raises:
            ValueError: if domain is invalid
        """
        if domain not in ALLOWED_DOMAINS:
            logger.warning(
                "workflow_persistence_invalid_domain",
                extra={"extra_data": {"domain": domain}},
            )
            raise ValueError(
                f"Invalid domain '{domain}'. Allowed: {sorted(ALLOWED_DOMAINS)}"
            )

        dsl: str = compile_result["dsl"]
        compiled: dict = compile_result["compiled"]

        # compiled already has version, trigger, steps — this is parsed_rule_json
        parsed_rule_json = compiled

        saved = workflow_repo.create(
            db=db,
            name=name,
            domain=domain,
            raw_input=user_request,
            parsed_rule_json=parsed_rule_json,
        )
        db.commit()
        db.refresh(saved)

        logger.info(
            "workflow_persisted",
            extra={
                "extra_data": {
                    "workflow_id": saved.id,
                    "name": saved.name,
                    "domain": saved.domain,
                    "step_count": len(compiled.get("steps", [])),
                }
            },
        )

        return {
            "workflow_id": saved.id,
            "name": saved.name,
            "domain": saved.domain,
            "dsl": dsl,
            "parsed_rule_json": parsed_rule_json,
        }
