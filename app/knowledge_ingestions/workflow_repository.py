from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workflow_trigger_mapping import WorkflowTriggerMapping
from app.models.workflow_action_mapping import WorkflowActionMapping
from app.models.workflow_business_rule import WorkflowBusinessRule
from app.models.workflow_actor import WorkflowActor
from app.models.workflow_external_system import WorkflowExternalSystem
from app.knowledge_ingestions.schemas import WorkflowExtraction
from sqlalchemy.orm import Session
from app.knowledge_ingestions.exceptions import RepositoryError
from app.models.action_definitions import ActionDefinition
from app.models.trigger_definitions import TriggerDefinition


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
            raise RepositoryError(f"Failed to persist workflow: {e}") from e

    def get_unmapped_actions(self):
        return (
            self.db.query(WorkflowActionMapping)
            .filter(WorkflowActionMapping.matched_action_definition_id.is_(None))
            .all()
        )

    def get_unmapped_triggers(self):
        return (
            self.db.query(WorkflowTriggerMapping)
            .filter(WorkflowTriggerMapping.matched_trigger_definition_id.is_(None))
            .all()
        )

    def find_best_action(self, embedding):
        distance = ActionDefinition.embedding.cosine_distance(embedding)
        return (
            self.db.query(ActionDefinition, distance.label("distance"))
            .filter(ActionDefinition.active.is_(True))
            .order_by(distance)
            .first()
        )

    def find_best_trigger(self, embedding):
        distance = TriggerDefinition.embedding.cosine_distance(embedding)
        return (
            self.db.query(TriggerDefinition, distance.label("distance"))
            .filter(TriggerDefinition.active.is_(True))
            .order_by(distance)
            .first()
        )

    def update_action_mapping(
        self,
        mapping_id: int,
        action_definitation_id: int,
        similarity_score: float,
        confidence: float,
    ):
        mapping = (
            self.db.query(WorkflowActionMapping)
            .filter(WorkflowActionMapping.id == mapping_id)
            .first()
        )
        print(mapping)
        if mapping is None:
            return

        mapping.matched_action_definition_id = action_definitation_id
        mapping.similarity_score = similarity_score
        mapping.confidence = confidence
        self.db.commit()

    def update_trigger_mapping(
        self,
        mapping_id: int,
        trigger_definitation_id: int,
        similarity_score: float,
        confidence: float,
    ):
        mapping = (
            self.db.query(WorkflowTriggerMapping)
            .filter(WorkflowTriggerMapping.id == mapping_id)
            .first()
        )

        if mapping is None:
            return

        mapping.matched_trigger_definition_id = (trigger_definitation_id,)
        mapping.similarity_score = similarity_score
        mapping.confidence = confidence
        self.db.commit()

    def get_workflow_actions(self, workflow_knowledge_id: int):
        return (
            self.db.query(WorkflowActionMapping)
            .filter(
                WorkflowActionMapping.workflow_knowledge_id == workflow_knowledge_id
            )
            .all()
        )
