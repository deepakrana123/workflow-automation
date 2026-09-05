from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workflow_trigger_mapping import WorkflowTriggerMapping
from app.models.workflow_action_mapping import WorkflowActionMapping, MappingStatus
from app.models.workflow_business_rule import WorkflowBusinessRule
from app.models.workflow_actor import WorkflowActor
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
                    applicable_rules=(
                        trigger.applicable_rules if trigger.applicable_rules else None
                    ),
                    responsible_actors=(
                        trigger.responsible_actors if trigger.responsible_actors else None
                    ),
                )
            )

        for action in workflow.action_references:
            self.db.add(
                WorkflowActionMapping(
                    workflow_knowledge_id=knowledge.id,
                    extract_name=action.name,
                    description=action.description,
                    applicable_rules=(
                        action.applicable_rules if action.applicable_rules else None
                    ),
                    responsible_actors=(
                        action.responsible_actors if action.responsible_actors else None
                    ),
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

    def mark_action_unmapped(
        self,
        mapping_id: int,
        query_text: str | None = None,
        top_candidates: list | None = None,
    ) -> None:
        """Mark an action as UNMAPPED with optional retrieval diagnostics."""
        mapping = (
            self.db.query(WorkflowActionMapping)
            .filter(WorkflowActionMapping.id == mapping_id)
            .first()
        )
        if mapping is None:
            return
        mapping.status = MappingStatus.UNMAPPED
        if query_text is not None:
            mapping.query_text = query_text
        if top_candidates is not None:
            mapping.top_candidates = top_candidates
        self.db.flush()

    def get_unmapped_actions_for_workspace(
        self,
        workspace_id: int,
    ) -> list[WorkflowActionMapping]:
        """
        Return all UNMAPPED action mapping rows for a workspace.

        Used by the workspace diagnostics / manual resolution UI to show
        the user which BRD actions could not be automatically matched to
        the catalog.
        """
        return (
            self.db.query(WorkflowActionMapping)
            .join(
                WorkflowKnowledge,
                WorkflowKnowledge.id == WorkflowActionMapping.workflow_knowledge_id,
            )
            .filter(
                WorkflowKnowledge.workspace_id == workspace_id,
                WorkflowActionMapping.status == MappingStatus.UNMAPPED,
            )
            .order_by(WorkflowActionMapping.id.asc())
            .all()
        )

    def update_action_mapping(
        self,
        mapping_id: int,
        action_definition_id: int,
        similarity_score: float,
        confidence: float,
        query_text: str | None = None,
        top_candidates: list | None = None,
        # ── snapshot fields copied from ActionDefinition at mapping time ──
        action_name: str | None = None,
        display_name: str | None = None,
        catalog_description: str | None = None,
        aliases: list | None = None,
        workflow_type: str | None = None,
        input_schema: dict | None = None,
        output_schema: dict | None = None,
        execution_template: dict | None = None,
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
        mapping.status = MappingStatus.MAPPED
        if query_text is not None:
            mapping.query_text = query_text
        if top_candidates is not None:
            mapping.top_candidates = top_candidates
        # Write snapshot — runtime reads these, never ActionDefinition
        if action_name is not None:
            mapping.action_name = action_name
        if display_name is not None:
            mapping.display_name = display_name
        if catalog_description is not None:
            mapping.catalog_description = catalog_description
        if aliases is not None:
            mapping.aliases = aliases
        if workflow_type is not None:
            mapping.workflow_type = workflow_type
        if input_schema is not None:
            mapping.input_schema = input_schema
        if output_schema is not None:
            mapping.output_schema = output_schema
        if execution_template is not None:
            mapping.execution_template = execution_template
        self.db.flush()

    def update_trigger_mapping(
        self,
        mapping_id: int,
        trigger_definition_id: int,
        similarity_score: float,
        confidence: float,
        # ── snapshot fields copied from TriggerDefinition at mapping time ──
        trigger_name: str | None = None,
        display_name: str | None = None,
        catalog_description: str | None = None,
        aliases: list | None = None,
        workflow_type: str | None = None,
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
        mapping.status = MappingStatus.MAPPED
        # Write snapshot — generation reads these, never TriggerDefinition
        if trigger_name is not None:
            mapping.trigger_name = trigger_name
        if display_name is not None:
            mapping.display_name = display_name
        if catalog_description is not None:
            mapping.catalog_description = catalog_description
        if aliases is not None:
            mapping.aliases = aliases
        if workflow_type is not None:
            mapping.workflow_type = workflow_type
        self.db.flush()

    def get_workflow_actions(self, workflow_knowledge_id: int):
        return (
            self.db.query(WorkflowActionMapping)
            .filter(
                WorkflowActionMapping.workflow_knowledge_id == workflow_knowledge_id
            )
            .all()
        )

    def get_action_definition_for_action(
        self,
        workspace_id: int,
        action_name: str,
    ):
        """
        Resolve an ActionDefinition for a given action name scoped to a workspace.

        Looks up the action_definitions row whose name matches ``action_name``
        via WorkflowActionMapping → WorkflowKnowledge (workspace filter).

        Returns the ActionDefinition ORM object, or None if not found.
        This is the runtime resolution path replacing ActionConfiguration.
        """
        from app.models.action_definitions import ActionDefinition

        return (
            self.db.query(ActionDefinition)
            .join(
                WorkflowActionMapping,
                WorkflowActionMapping.matched_action_definition_id == ActionDefinition.id,
            )
            .join(
                WorkflowKnowledge,
                WorkflowKnowledge.id == WorkflowActionMapping.workflow_knowledge_id,
            )
            .filter(
                WorkflowKnowledge.workspace_id == workspace_id,
                ActionDefinition.name == action_name,
                ActionDefinition.active.is_(True),
            )
            .first()
        )

    # def search_actions_by_postgress(self, query: str, limit: int = 20):
    #     vector = func.to_tsvector(
    #         "english",
    #         func.concat(
    #             ActionDefinition.name,
    #             " ",
    #             # ActionDefinition.display_name
    #             # func.coalesce(ActionDefinition.description, " "),
    #             func.coalesce(ActionDefinition.display_name, " "),
    #             " ",
    #             func.coalesce(ActionDefinition.aliases.cast(String), " "),

    #         ),
    #     )
    #     query = func.plainto_tsquery("english", query)
    #     rank = func.ts_rank(vector, query)
    #     return (
    #         self.db.query(ActionDefinition, rank.label("rank"))
    #         .filter(vector.op("@@")(query))
    #         .order_by(rank.desc())
    #         .limit(limit)
    #         .all()
    #     )

    # def search_actions_by_postgress(self, query: str, limit: int = 20):
    #     text_vector = func.to_tsvector(
    #         "english",
    #         func.concat(
    #             func.replace(ActionDefinition.name, "_", " "),
    #             " ",
    #             func.coalesce(ActionDefinition.display_name, " "),
    #             " ",
    #             func.coalesce(ActionDefinition.description, " ")
    #         ),
    #     )
    #     alias_vector = func.jsonb_to_tsvector(
    #         "english",
    #         func.coalesce(ActionDefinition.aliases, "[]"),
    #         '["string"]',
    #     )
    #     vector = text_vector.op("||")(alias_vector)
    #     ts_query = func.plainto_tsquery("english", query)
    #     rank = func.ts_rank(vector, ts_query)
    #     return (
    #         self.db.query(ActionDefinition, rank.label("rank"))
    #         .filter(vector.op("@@")(ts_query))
    #         .order_by(rank.desc())
    #         .limit(limit)
    #         .all()
    #     )

    def search_actions_by_postgress(self, query: str, limit: int = 20):
        """Full-text search over actions using websearch_to_tsquery.

        websearch_to_tsquery handles long descriptive BRD queries naturally:
        - multiple words → AND by default (all tokens must appear)
        - no strict ordering required (unlike phraseto_tsquery)
        - supports quoted phrases, OR, - negation without SQL errors

        This gives the best recall for queries like:
        "Apply the applicable interest rate to the loan account"
        → tokens 'apply', 'interest', 'rate', 'loan', 'account' all searched
        → apply_interest matches on 'apply' + 'interest' in name + description
        """
        text_vector = func.to_tsvector(
            "english",
            func.concat(
                func.replace(ActionDefinition.name, "_", " "),
                " ",
                func.coalesce(ActionDefinition.display_name, " "),
                " ",
                func.coalesce(ActionDefinition.description, " "),
            ),
        )

        alias_vector = func.jsonb_to_tsvector(
            "english",
            func.coalesce(ActionDefinition.aliases, "[]"),
            '["string"]',
        )

        vector = text_vector.op("||")(alias_vector)

        ts_query = func.websearch_to_tsquery("english", query)

        rank = func.ts_rank(vector, ts_query)

        return (
            self.db.query(ActionDefinition, rank.label("rank"))
            .filter(vector.op("@@")(ts_query))
            .order_by(rank.desc())
            .limit(limit)
            .all()
        )

    # def search_triggers_by_postgress(self, query: str, limit: int = 20):
    #     text_vector = func.to_tsvector(
    #         "english",
    #         func.concat(
    #             func.replace(TriggerDefinition.name, "_", " "),
    #             " ",
    #             func.coalesce(TriggerDefinition.display_name, " "),
    #             " ",
    #             func.coalesce(TriggerDefinition.description, " "),
    #         ),
    #     )
    #     alias_vector = func.jsonb_to_tsvector(
    #         "english",
    #         func.coalesce(TriggerDefinition.aliases, "[]"),
    #         '["string"]',
    #     )
    #     vector = text_vector.op("||")(alias_vector)
    #     query = func.plainto_tsquery("english", query)
#     rank = func.ts_rank(vector, query)
    #     return (
    #         self.db.query(TriggerDefinition, rank.label("rank"))
    #         .filter(vector.op("@@")(query))
    #         .order_by(rank.desc())
    #         .limit(limit)
    #         .all()
    #     )

    def search_triggers_by_postgress(self, query: str, limit: int = 20):
        """Full-text search over triggers using websearch_to_tsquery.

        Mirrors search_actions_by_postgress — flexible AND-by-default matching
        handles multi-word trigger queries without requiring exact phrase order.
        """
        text_vector = func.to_tsvector(
            "english",
            func.concat(
                func.replace(TriggerDefinition.name, "_", " "),
                " ",
                func.coalesce(TriggerDefinition.display_name, " "),
                " ",
                func.coalesce(TriggerDefinition.description, " "),
            ),
        )

        alias_vector = func.jsonb_to_tsvector(
            "english",
            func.coalesce(TriggerDefinition.aliases, "[]"),
            '["string"]',
        )

        vector = text_vector.op("||")(alias_vector)

        ts_query = func.websearch_to_tsquery("english", query)

        rank = func.ts_rank(vector, ts_query)

        return (
            self.db.query(TriggerDefinition, rank.label("rank"))
            .filter(vector.op("@@")(ts_query))
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
