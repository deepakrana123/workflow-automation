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

        # for rule in workflow.business_rules:
        #     self.db.add(
        #         WorkflowBusinessRule(
        #             workflow_knowledge_id=knowledge.id,
        #             rule=rule.rule,
        #         )
        #     )
        
        for rule in workflow.business_rules:
            self.db.add(
                WorkflowBusinessRule(
                    workflow_knowledge_id=knowledge.id,
                    rule=rule.rule,
                    condition=rule.condition,
                    outcome=rule.outcome,
                    responsible_role=rule.responsible_role,
                    threshold=rule.threshold,
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

    def get_unmapped_actions(self, workspace_id: int | None = None):
        """Return action mappings in PENDING or UNMAPPED status.

        When workspace_id is provided (the normal case), results are scoped to
        that workspace via a join through WorkflowKnowledge.  Passing None
        returns all rows across all workspaces — only used in tests or
        single-tenant admin tooling.
        """
        q = (
            self.db.query(WorkflowActionMapping)
            .filter(
                WorkflowActionMapping.status.in_(
                    [MappingStatus.PENDING, MappingStatus.UNMAPPED]
                )
            )
        )
        if workspace_id is not None:
            q = q.join(
                WorkflowKnowledge,
                WorkflowKnowledge.id == WorkflowActionMapping.workflow_knowledge_id,
            ).filter(WorkflowKnowledge.workspace_id == workspace_id)
        return q.all()

    def get_unmapped_triggers(self, workspace_id: int | None = None):
        """Return trigger mappings in PENDING or UNMAPPED status.

        Scoped to workspace_id when provided — prevents one workspace's
        PENDING rows from being processed during another workspace's ingestion.
        """
        q = (
            self.db.query(WorkflowTriggerMapping)
            .filter(
                WorkflowTriggerMapping.status.in_(
                    [MappingStatus.PENDING, MappingStatus.UNMAPPED]
                )
            )
        )
        if workspace_id is not None:
            q = q.join(
                WorkflowKnowledge,
                WorkflowKnowledge.id == WorkflowTriggerMapping.workflow_knowledge_id,
            ).filter(WorkflowKnowledge.workspace_id == workspace_id)
        return q.all()

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
        failure_reason: str | None = None,
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

    def mark_trigger_unmapped(
        self,
        mapping_id: int,
        query_text: str | None = None,
        top_candidates: list | None = None,
    ) -> None:
        """Mark a trigger as UNMAPPED with retrieval diagnostics."""
        mapping = (
            self.db.query(WorkflowTriggerMapping)
            .filter(WorkflowTriggerMapping.id == mapping_id)
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
        query_text: str | None = None,
        top_candidates: list | None = None,
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
        if query_text is not None:
            mapping.query_text = query_text
        if top_candidates is not None:
            mapping.top_candidates = top_candidates
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
        Resolve a runtime-ready ActionDefinition for a given action name
        scoped to a workspace.

        Resolution order:
          1. Query WorkflowActionMapping by action_name (snapshot column) +
             workspace_id. This covers both:
             - Mode A: row has matched_action_definition_id → join to
               ActionDefinition to get its execution_template if the snapshot
               has none.
             - Mode B (workspace-local): matched_action_definition_id is NULL
               but the snapshot columns (execution_template, input_schema, etc.)
               are fully populated on the mapping row itself.
          2. If the mapping row carries a complete execution_template in its
             snapshot, build and return a synthetic ActionDefinition from the
             snapshot so no additional DB round-trip is needed.
          3. Fall through to the real ActionDefinition row (Mode A) when the
             mapping snapshot has no execution_template of its own.

        Returns an ActionDefinition-compatible object, or None if not found.
        """
        from app.models.action_definitions import ActionDefinition

        mapping = (
            self.db.query(WorkflowActionMapping)
            .join(
                WorkflowKnowledge,
                WorkflowKnowledge.id == WorkflowActionMapping.workflow_knowledge_id,
            )
            .filter(
                WorkflowKnowledge.workspace_id == workspace_id,
                WorkflowActionMapping.action_name == action_name,
                WorkflowActionMapping.status == MappingStatus.MAPPED,
            )
            .first()
        )

        if mapping is None:
            return None

        # If the mapping snapshot has an execution_template, synthesize an
        # ActionDefinition from the snapshot — avoids another DB query and
        # correctly handles Mode B workspace-local actions.
        if mapping.execution_template:
            synthetic = ActionDefinition()
            synthetic.id                = mapping.matched_action_definition_id or 0
            synthetic.name              = mapping.action_name
            synthetic.display_name      = mapping.display_name or mapping.action_name
            synthetic.description       = mapping.catalog_description
            synthetic.workflow_type     = mapping.workflow_type or "finance"
            synthetic.aliases           = mapping.aliases or []
            synthetic.input_schema      = mapping.input_schema
            synthetic.output_schema     = mapping.output_schema
            synthetic.execution_template = mapping.execution_template
            synthetic.active            = True
            return synthetic

        # Mode A fallback: mapping points to a real ActionDefinition whose
        # execution_template lives on the catalog row.
        if mapping.matched_action_definition_id is not None:
            return (
                self.db.query(ActionDefinition)
                .filter(
                    ActionDefinition.id == mapping.matched_action_definition_id,
                    ActionDefinition.active.is_(True),
                )
                .first()
            )

        return None


    def search_actions_by_postgress(self, query: str, limit: int = 20):
        """Full-text search over action_definitions.

        Strategy: AND-first (websearch_to_tsquery) for precision.
        If zero rows match — which happens when any one token from a long BRD
        phrase is absent from the catalog entry — re-run with OR semantics so
        partial matches still surface for RRF to consider.
        """
        from sqlalchemy import text as sa_text

        _SQL_BASE = """
            SELECT ad.id,
                   ts_rank(
                       to_tsvector('english',
                           replace(ad.name, '_', ' ') || ' ' ||
                           coalesce(ad.display_name, ' ')  || ' ' ||
                           coalesce(ad.description, ' ')
                       ) || jsonb_to_tsvector('english',
                           coalesce(ad.aliases, '[]'::jsonb), '["string"]'),
                       {ts_query_expr}
                   ) AS rank
            FROM action_definitions ad
            WHERE ad.active = true
              AND (
                  to_tsvector('english',
                      replace(ad.name, '_', ' ') || ' ' ||
                      coalesce(ad.display_name, ' ')  || ' ' ||
                      coalesce(ad.description, ' ')
                  ) || jsonb_to_tsvector('english',
                      coalesce(ad.aliases, '[]'::jsonb), '["string"]')
              ) @@ {ts_query_expr}
            ORDER BY rank DESC
            LIMIT :limit
        """

        and_sql = sa_text(
            _SQL_BASE.format(ts_query_expr="websearch_to_tsquery('english', :q)")
        )
        rows = self.db.execute(and_sql, {"q": query, "limit": limit}).fetchall()

        if not rows:
            # OR-fallback: replace & with | in plainto_tsquery output
            or_sql = sa_text(
                _SQL_BASE.format(
                    ts_query_expr=(
                        "cast(regexp_replace("
                        "  cast(plainto_tsquery('english', :q) as text),"
                        "  '&', '|', 'g'"
                        ") as tsquery)"
                    )
                )
            )
            rows = self.db.execute(or_sql, {"q": query, "limit": limit}).fetchall()

        if not rows:
            return []

        id_to_rank = {r[0]: float(r[1]) for r in rows}
        matched_ids = list(id_to_rank.keys())
        actions = (
            self.db.query(ActionDefinition)
            .filter(ActionDefinition.id.in_(matched_ids))
            .all()
        )
        actions.sort(key=lambda a: id_to_rank.get(a.id, 0.0), reverse=True)
        return [(a, id_to_rank[a.id]) for a in actions]

   
    def search_triggers_by_postgress(self, query: str, limit: int = 20):
        """Full-text search over triggers using AND-first / OR-fallback.

        Mirrors search_actions_by_postgress — ensures partial-match triggers
        are still returned when the BRD phrase doesn't exactly echo the catalog
        trigger name or description.
        """
        from sqlalchemy import text as sa_text

        _SQL_BASE = """
            SELECT td.id,
                   ts_rank(
                       to_tsvector('english',
                           replace(td.name, '_', ' ') || ' ' ||
                           coalesce(td.display_name, ' ')  || ' ' ||
                           coalesce(td.description, ' ')
                       ) || jsonb_to_tsvector('english',
                           coalesce(td.aliases, '[]'::jsonb), '["string"]'),
                       {ts_query_expr}
                   ) AS rank
            FROM trigger_definitions td
            WHERE td.active = true
              AND (
                  to_tsvector('english',
                      replace(td.name, '_', ' ') || ' ' ||
                      coalesce(td.display_name, ' ')  || ' ' ||
                      coalesce(td.description, ' ')
                  ) || jsonb_to_tsvector('english',
                      coalesce(td.aliases, '[]'::jsonb), '["string"]')
              ) @@ {ts_query_expr}
            ORDER BY rank DESC
            LIMIT :limit
        """

        and_sql = sa_text(
            _SQL_BASE.format(ts_query_expr="websearch_to_tsquery('english', :q)")
        )
        rows = self.db.execute(and_sql, {"q": query, "limit": limit}).fetchall()

        if not rows:
            or_sql = sa_text(
                _SQL_BASE.format(
                    ts_query_expr=(
                        "cast(regexp_replace("
                        "  cast(plainto_tsquery('english', :q) as text),"
                        "  '&', '|', 'g'"
                        ") as tsquery)"
                    )
                )
            )
            rows = self.db.execute(or_sql, {"q": query, "limit": limit}).fetchall()

        if not rows:
            return []

        id_to_rank = {r[0]: float(r[1]) for r in rows}
        matched_ids = list(id_to_rank.keys())
        triggers = (
            self.db.query(TriggerDefinition)
            .filter(TriggerDefinition.id.in_(matched_ids))
            .all()
        )
        triggers.sort(key=lambda t: id_to_rank.get(t.id, 0.0), reverse=True)
        return [(t, id_to_rank[t.id]) for t in triggers]

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
    
    def search_business_rules(self, workspace_id: int, query: str, limit: int = 20):
        query = query.strip()

        if not query:
            return []
        

        text_vector = func.to_tsvector(
            "english",
            func.concat_ws(
                " ",
                WorkflowBusinessRule.rule,
                WorkflowBusinessRule.condition,
                WorkflowBusinessRule.outcome,
                WorkflowBusinessRule.responsible_role,
                WorkflowBusinessRule.threshold
            ),
        )

        ts_query = func.websearch_to_tsquery("english",query)
        rank = func.ts_rank(text_vector , ts_query)

        return (
            self.db.query(
                WorkflowBusinessRule,
                WorkflowKnowledge.workflow_name,
                WorkflowKnowledge.source_document,
                rank.label("rank"),
            ).join(
                WorkflowKnowledge,
                WorkflowKnowledge.id == WorkflowBusinessRule.workflow_knowledge_id,
            ).filter(
                WorkflowKnowledge.workspace_id == workspace_id,
                text_vector.op("@@")(ts_query)
            ).order_by(rank.desc()).limit(max(1,min(limit,100)))
            .all()
            
        )
