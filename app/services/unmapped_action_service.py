"""
app/services/unmapped_action_service.py

UnmappedActionService — lets workspace owners manually resolve BRD actions
that the automatic embedding mapper could not match to the catalog.

Design principle:
  WorkflowActionMapping IS the workspace's action. ActionDefinition is the
  GLOBAL catalog. These are two separate concepts. A workspace owner who
  defines their own action does NOT touch the global catalog — their action
  lives on the mapping row only. This keeps the global catalog clean and
  controlled.

  The embedding for a manually-resolved action is stored on
  WorkflowActionMapping.embedding — not on ActionDefinition. This lets
  WorkspaceCatalogMatcher find the action via vector similarity using the
  workspace-specific name and context.

Resolution modes:

  Mode A — map to existing ActionDefinition (action_definition_id provided):
    The mapping row points to an existing catalog entry.
    All snapshot fields are copied from ActionDefinition.
    The ActionDefinition embedding is also copied to mapping.embedding.
    No new catalog entry is created.

  Mode B — workspace-local action (action_definition_id=None):
    The user provides action_name, display_name, execution_template, etc.
    These values are stored directly on the mapping row.
    matched_action_definition_id stays NULL — no global catalog entry created.
    An embedding is generated from action_name + display_name and stored on
    mapping.embedding for vector search.
    status → MAPPED.

After either mode the action is immediately available for:
  - WorkspaceCatalogMatcher (FTS on action_name + display_name + aliases)
  - config_resolver (resolves by action_name through WorkflowActionMapping)
  - Runtime execution (execution_template on the mapping row)
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.knowledge_ingestions.workflow_repository import WorkflowRepository
from app.models.workflow_action_mapping import WorkflowActionMapping, MappingStatus
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.action_definitions import ActionDefinition
from app.core.logger import logger


class UnmappedActionService:

    def __init__(self, db: Session):
        self.db   = db
        self.repo = WorkflowRepository(db)

    # ── List ──────────────────────────────────────────────────────────────────

    def list_unmapped(self, workspace_id: int) -> list[dict]:
        """
        Return all UNMAPPED action mapping rows for a workspace.

        Each row includes the original BRD extract, retrieval diagnostics
        (query_text, top_candidates), and source BRD info so the user
        can make an informed resolution decision.
        """
        rows = self.repo.get_unmapped_actions_for_workspace(workspace_id)
        return [self._serialize(m) for m in rows]

    # ── Resolve ───────────────────────────────────────────────────────────────

    def resolve(
        self,
        mapping_id: int,
        workspace_id: int,
        action_definition_id: int | None = None,
        action_name: str | None = None,
        display_name: str | None = None,
        catalog_description: str | None = None,
        aliases: list[str] | None = None,
        workflow_type: str | None = None,
        input_schema: dict | None = None,
        output_schema: dict | None = None,
        execution_template: dict | None = None,
    ) -> dict:
        """
        Resolve an unmapped action.

        Mode A — existing catalog entry:
          Provide action_definition_id.
          Snapshot + embedding copied from ActionDefinition.

        Mode B — workspace-local action:
          Leave action_definition_id=None. Provide action_name (required).
          Values stored directly on the mapping row.
          Embedding generated and stored on mapping.embedding.
          ActionDefinition is NEVER created or modified.

        Returns the serialized resolved mapping.
        """
        mapping = self._load_owned_mapping(mapping_id, workspace_id)

        if action_definition_id is not None:
            self._resolve_mode_a(mapping, action_definition_id)
        else:
            if not action_name or not action_name.strip():
                raise ValueError(
                    "action_name is required when not mapping to an existing "
                    "catalog action (action_definition_id not provided)"
                )
            self._resolve_mode_b(
                mapping=mapping,
                action_name=action_name.strip(),
                display_name=display_name,
                catalog_description=catalog_description,
                aliases=aliases or [],
                workflow_type=workflow_type or "finance",
                input_schema=input_schema,
                output_schema=output_schema,
                execution_template=execution_template,
            )

        mapping.status = MappingStatus.MAPPED
        self.db.commit()
        self.db.refresh(mapping)

        mode = "catalog" if action_definition_id is not None else "workspace_local"
        logger.info(
            "unmapped_action_resolved",
            extra={"extra_data": {
                "mapping_id":           mapping_id,
                "workspace_id":         workspace_id,
                "resolution_mode":      mode,
                "action_definition_id": mapping.matched_action_definition_id,
                "action_name":          mapping.action_name,
            }},
        )

        return self._serialize(mapping)

    # ── Catalog suggestions ───────────────────────────────────────────────────

    def suggest_catalog_matches(
        self,
        mapping_id: int,
        workspace_id: int,
        limit: int = 10,
    ) -> list[dict]:
        """
        Re-run FTS search against ActionDefinition for an unmapped action.

        Returns up to `limit` candidates ordered by FTS relevance.
        The returned action_definition_id can be passed to resolve() Mode A.
        """
        mapping = self._load_owned_mapping(mapping_id, workspace_id)
        query   = f"{mapping.extract_name} {mapping.description or ''}".strip()
        results = self.repo.search_actions_by_postgress(query, limit=limit)

        return [
            {
                "action_definition_id": ad.id,
                "name":                 ad.name,
                "display_name":         ad.display_name,
                "description":          ad.description,
                "workflow_type":        ad.workflow_type,
                "rank":                 float(rank),
            }
            for ad, rank in results
        ]

    # ── Private helpers ───────────────────────────────────────────────────────

    def _load_owned_mapping(
        self,
        mapping_id: int,
        workspace_id: int,
    ) -> WorkflowActionMapping:
        """Load and verify workspace ownership."""
        mapping = (
            self.db.query(WorkflowActionMapping)
            .join(
                WorkflowKnowledge,
                WorkflowKnowledge.id == WorkflowActionMapping.workflow_knowledge_id,
            )
            .filter(
                WorkflowActionMapping.id == mapping_id,
                WorkflowKnowledge.workspace_id == workspace_id,
            )
            .first()
        )
        if mapping is None:
            raise ValueError(
                f"Unmapped action {mapping_id} not found in workspace {workspace_id}"
            )
        return mapping

    def _resolve_mode_a(
        self,
        mapping: WorkflowActionMapping,
        action_definition_id: int,
    ) -> None:
        """
        Mode A: point mapping to an existing ActionDefinition.
        Copies all snapshot fields and the embedding.
        """
        ad = (
            self.db.query(ActionDefinition)
            .filter(ActionDefinition.id == action_definition_id)
            .first()
        )
        if ad is None:
            raise ValueError(
                f"ActionDefinition {action_definition_id} not found"
            )
        mapping.matched_action_definition_id = ad.id
        mapping.action_name                  = ad.name
        mapping.display_name                 = ad.display_name
        mapping.catalog_description          = ad.description
        mapping.aliases                      = ad.aliases
        mapping.workflow_type                = ad.workflow_type
        mapping.input_schema                 = ad.input_schema
        mapping.output_schema                = ad.output_schema
        mapping.execution_template           = ad.execution_template
        mapping.similarity_score             = 1.0
        mapping.confidence                   = 1.0
        # Copy the catalog embedding so workspace vector search works
        if ad.embedding is not None:
            mapping.embedding = ad.embedding

    def _resolve_mode_b(
        self,
        mapping: WorkflowActionMapping,
        action_name: str,
        display_name: str | None,
        catalog_description: str | None,
        aliases: list[str],
        workflow_type: str,
        input_schema: dict | None,
        output_schema: dict | None,
        execution_template: dict | None,
    ) -> None:
        """
        Mode B: store user-provided values directly on the mapping row.

        ActionDefinition is never created or modified.
        matched_action_definition_id stays NULL.
        An embedding is generated from action_name + display_name and stored
        on mapping.embedding so vector search can find this action.
        """
        resolved_display = display_name or action_name.replace("_", " ").title()

        mapping.matched_action_definition_id = None
        mapping.action_name                  = action_name
        mapping.display_name                 = resolved_display
        mapping.catalog_description          = catalog_description
        mapping.aliases                      = aliases or []
        mapping.workflow_type                = workflow_type
        mapping.input_schema                 = input_schema
        mapping.output_schema                = output_schema
        mapping.execution_template           = execution_template
        mapping.similarity_score             = 1.0
        mapping.confidence                   = 1.0

        # Generate embedding from the user-provided name and display name
        # so this action is discoverable by vector similarity in future
        # BRD ingestions and in WorkspaceCatalogMatcher.
        self._embed_mapping(mapping, action_name, resolved_display, aliases)

    def _embed_mapping(
        self,
        mapping: WorkflowActionMapping,
        action_name: str,
        display_name: str,
        aliases: list[str],
    ) -> None:
        """
        Generate and store an embedding on the mapping row.

        Text used: "action_name_words display_name alias1 alias2"
        — same strategy as EmbeddingService.build_action_text().

        Best-effort: if the model is unavailable the action is still
        resolved and usable via FTS. Only vector search will miss it.
        """
        try:
            from app.semantic.embedding_service import EmbeddingService
            svc        = EmbeddingService()
            alias_str  = " ".join(aliases or [])
            text       = " ".join(
                p for p in [
                    action_name.replace("_", " "),
                    display_name,
                    alias_str,
                ] if p
            ).strip()
            emb = svc.generate_embedding(text)
            mapping.embedding = emb
            self.db.flush()
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "unmapped_action_embedding_failed",
                extra={"extra_data": {
                    "action_name": action_name,
                    "error":       str(exc),
                }},
            )

    # ── Serializer ────────────────────────────────────────────────────────────

    def _serialize(self, m: WorkflowActionMapping) -> dict:
        wk = m.workflow if m.workflow else (
            self.db.query(WorkflowKnowledge)
            .filter(WorkflowKnowledge.id == m.workflow_knowledge_id)
            .first()
        )

        return {
            "mapping_id":             m.id,
            "workflow_knowledge_id":  m.workflow_knowledge_id,
            "source_document":        wk.source_document if wk else None,
            "workflow_name":          wk.workflow_name   if wk else None,

            # What the BRD said
            "extract_name":           m.extract_name,
            "description":            m.description,

            # Current state
            "status":                 m.status.value if m.status else "PENDING",
            "action_definition_id":   m.matched_action_definition_id,

            # User-provided or catalog-copied values
            "action_name":            m.action_name,
            "display_name":           m.display_name,
            "catalog_description":    m.catalog_description,
            "aliases":                m.aliases,
            "workflow_type":          m.workflow_type,
            "execution_template":     m.execution_template,
            "has_embedding":          m.embedding is not None,

            # Retrieval diagnostics (for the user to understand why it was unmapped)
            "query_text":             m.query_text,
            "similarity_score":       m.similarity_score,
            "confidence":             m.confidence,
            "top_candidates":         m.top_candidates or [],
        }
