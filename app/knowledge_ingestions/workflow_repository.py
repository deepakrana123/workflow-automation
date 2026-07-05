from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workflow_trigger_mapping import WorkflowTriggerMapping
from app.models.workflow_action_mapping import WorkflowActionMapping
from app.models.workflow_business_rule import WorkflowBusinessRule
from app.models.workflow_actor import WorkflowActor
from app.models.workflow_external_system import WorkflowExternalSystem
from app.knowledge_ingestions.schemas import WorkflowExtraction
from sqlalchemy.orm import Session
from app.knowledge_ingestions.exceptions import RepositoryError
class WorkflowRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, workflow: WorkflowExtraction):
        try:
            knowledge = WorkflowKnowledge(
                workflow_name=workflow.workflow_name, summary=workflow.summary
            )

            self.db.add(knowledge)
            self.db.flush()

            for trigger in workflow.triggers:
                self.db.add(
                    WorkflowTriggerMapping(
                        workflow_knowledge_id=knowledge.id,
                        extracted_name=trigger.name,
                        description=trigger.description,
                    )
                )

            for action in workflow.action_references:
                self.db.add(
                    WorkflowActionMapping(
                        workflow_knowledge_id=knowledge.id,
                        extract_name=action.name,
                        description=action.description,
                    )
                )

            for rule in workflow.business_rules:
                self.db.add(
                    WorkflowBusinessRule(
                        workflow_knowledge_id=knowledge.id,
                        rule=rule.rule,
                    )
                )

            for actor in workflow.actors:
                self.db.add(
                    WorkflowActor(
                        workflow_knowledge_id=knowledge.id,
                        name=actor.name,
                        role=actor.role,
                    )
                )

            for system in workflow.external_systems:
                self.db.add(
                    WorkflowExternalSystem(
                        workflow_knowledge_id=knowledge.id,
                        name=system.name,
                        description=system.description,
                    )
                )
            self.db.commit()
            return knowledge
        except Exception as e:
                self.db.rollback()
                raise RepositoryError(
                    f"Failed to persist workflow: {e}"
                ) from e
