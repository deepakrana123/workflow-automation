from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workflow_trigger_mapping import WorkflowTriggerMapping
from app.models.workflow_action_mapping import WorkflowActionMapping
from app.models.workflow_business_rule import WorkflowBusinessRule
from app.models.workflow_actor import WorkflowActor
from app.models.workflow_external_system import WorkflowExternalSystem
from app.knowledge_ingestions.schemas import WorkflowExtraction
from sqlalchemy.orm import Session
from app.models.action_definitions import ActionDefinition
from app.models.trigger_definitions import TriggerDefinition
from sqlalchemy import func


class WorkflowRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(
        self,
        workflow: WorkflowExtraction,
        workspace_id: int | None = None,
        source_document: str | None = None,
    ):
        knowledge = WorkflowKnowledge(
            workflow_name=workflow.workflow_name,
            summary=workflow.summary,
            workspace_id=workspace_id,
            source_document=source_document,
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
        self.db.flush()
        return knowledge

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

    def search_actions_by_embedding(
        self, embedding, limit: int = 20
    ) -> list[tuple[ActionDefinition, float]]:
        distance = ActionDefinition.embedding.cosine_distance(embedding)
        return (
            self.db.query(ActionDefinition, distance.label("distance"))
            .filter(ActionDefinition.active.is_(True))
            .order_by(distance)
            .limit(limit)
            .all()
        )

    def search_triggers_by_embedding(
        self, embedding, limit: int = 20
    ) -> list[tuple[TriggerDefinition, float]]:
        distance = TriggerDefinition.embedding.cosine_distance(embedding)
        return (
            self.db.query(TriggerDefinition, distance.label("distance"))
            .filter(TriggerDefinition.active.is_(True))
            .order_by(distance)
            .limit(limit)
            .all()
        )

    def update_action_mapping(
        self,
        mapping_id: int,
        action_definition_id: int,
        similarity_score: float,
        confidence: float,
    ) -> None:
        mapping = (
            self.db.query(WorkflowActionMapping)
            .filter(WorkflowActionMapping.id == mapping_id)
            .first()
        )
        if mapping is None:
            return
        mapping.matched_action_definition_id = action_definition_id
        mapping.similarity_score = similarity_score
        mapping.confidence = confidence
        self.db.flush()

    def update_trigger_mapping(
        self,
        mapping_id: int,
        trigger_definition_id: int,
        similarity_score: float,
        confidence: float,
    ) -> None:
        mapping = (
            self.db.query(WorkflowTriggerMapping)
            .filter(WorkflowTriggerMapping.id == mapping_id)
            .first()
        )
        if mapping is None:
            return
        mapping.matched_trigger_definition_id = trigger_definition_id
        mapping.similarity_score = similarity_score
        mapping.confidence = confidence
        self.db.flush()

    def get_workflow_actions(self, workflow_knowledge_id: int):
        return (
            self.db.query(WorkflowActionMapping)
            .filter(
                WorkflowActionMapping.workflow_knowledge_id == workflow_knowledge_id
            )
            .all()
        )

    def search_actions_by_postgress(self, query: str, limit: int = 20):
        vector = func.to_tsvector(
            "english",
            func.concat(
                ActionDefinition.name,
                " ",
                func.coalesce(ActionDefinition.description, " "),
            ),
        )
        query = func.plainto_tsquery("english", query)
        rank = func.ts_rank(vector, query)
        return (
            self.db.query(ActionDefinition, rank.label("rank"))
            .filter(vector.op("@@")(query))
            .order_by(rank.desc())
            .limit(limit)
            .all()
        )

    def search_triggers_by_postgress(self, query: str, limit: int = 20):
        vector = func.to_tsvector(
            "english",
            func.concat(
                TriggerDefinition.name,
                " ",
                func.coalesce(TriggerDefinition.description, " "),
            ),
        )
        query = func.plainto_tsquery("english", query)
        rank = func.ts_rank(vector, query)
        return (
            self.db.query(TriggerDefinition, rank.label("rank"))
            .filter(vector.op("@@")(query))
            .order_by(rank.desc())
            .limit(limit)
            .all()
        )

    def get_all_active_actions(self):
        return (
            self.db.query(ActionDefinition)
            .filter(ActionDefinition.active.is_(True))
            .all()
        )

    def get_all_active_triggers(self):
        return (
            self.db.query(TriggerDefinition)
            .filter(TriggerDefinition.active.is_(True))
            .all()
        )
