"""
app/workflow/workspace_context.py

WorkspaceContextService — read-only projections that let a user understand what
MFlows has learned about a workspace BEFORE any workflow is generated.

Everything here is DERIVED, not stored: it projects over the existing
WorkflowKnowledge / mapping / business-rule tables (and reuses the deterministic
WorkspaceSynthesisService for the deduplicated cross-BRD view). No new tables,
no LLM, no mutation.

Four views:
  - overview        : workspace header + headline counts
  - documents       : per-BRD card (counts + derived extraction/mapping status)
  - business_rules  : the rules MFlows extracted, with their source BRD
  - actions         : workspace-scoped actions (deduped) + unresolved terms

The pure builders (`build_overview`, `build_document_view`) take plain dicts so
they are unit-testable without a DB, mirroring `build_workspace_synthesis`.
"""

from collections import Counter

from sqlalchemy.orm import Session

from app.models.action_definitions import ActionDefinition
from app.models.workflow import Workflow
from app.models.workflow_action_mapping import WorkflowActionMapping
from app.models.workflow_business_rule import WorkflowBusinessRule
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workflow_trigger_mapping import WorkflowTriggerMapping
from app.models.workspace import Workspace
from app.workflow.workspace_synthesis import WorkspaceSynthesisService


# ── Pure builders (no DB) ─────────────────────────────────────────────────────

def build_overview(
    workspace: dict,
    synthesis: dict,
    domain: str | None = None,
    workflow_count: int = 0,
    generated_file_count: int = 0,
) -> dict:
    """Project the workspace header + headline counts.

    Args:
        workspace: {id, name, display_name, organization_name, description, active}
        synthesis: output of build_workspace_synthesis / WorkspaceSynthesisService
        domain: best-effort banking domain (derived from mapped actions)
        workflow_count / generated_file_count: wired once workflows carry a
            workspace_id (see project plan step 5); 0 until then.
    """
    return {
        "workspace_id": workspace.get("id"),
        "name": workspace.get("name"),
        "display_name": workspace.get("display_name"),
        "organization_name": workspace.get("organization_name"),
        "domain": domain,
        "summary": workspace.get("description"),
        "status": "active" if workspace.get("active", True) else "inactive",
        "brd_count": synthesis.get("brd_count", 0),
        "action_count": len(synthesis.get("actions", []) or []),
        "unresolved_action_count": len(synthesis.get("unresolved_actions", []) or []),
        "trigger_count": len(synthesis.get("triggers", []) or []),
        "business_rule_count": len(synthesis.get("business_rules", []) or []),
        "workflow_count": workflow_count,
        "generated_file_count": generated_file_count,
        "review_flag_count": len(synthesis.get("review_flags", []) or []),
    }


def build_workspace_prompt_vars(
    display_name: str,
    description: str | None,
    actors: list[str],
    rules: list[str],
) -> dict:
    """Pure builder for the workspace (v2) generation template variables.

    Produces {"workspace_summary", "business_rules"} strings. Kept here (a
    dependency-light module) so it is unit-testable without the LLM stack.
    """
    summary_parts: list[str] = []
    if description:
        summary_parts.append(description.strip())
    summary_parts.append(f"Workspace: {display_name}.")
    if actors:
        summary_parts.append("Relevant actors: " + ", ".join(actors) + ".")
    workspace_summary = " ".join(summary_parts)

    if rules:
        business_rules = "\n".join(f"{i + 1}. {r}" for i, r in enumerate(rules))
    else:
        business_rules = "None specified."

    return {
        "workspace_summary": workspace_summary,
        "business_rules": business_rules,
    }


def build_document_view(items: list[dict]) -> list[dict]:
    """Project one card per BRD with derived extraction/mapping status.

    Args:
        items: one dict per BRD:
            {
              workflow_knowledge_id, workflow_name, source_document, created_at,
              action_total, action_mapped, trigger_total, rule_total
            }

    Derived (no such columns exist):
      - extraction_status: "extracted" if anything was pulled out, else "pending"
      - mapping_status: none | unmapped | partial | mapped (over actions)
    """
    docs = []
    for it in items:
        action_total = it.get("action_total", 0) or 0
        action_mapped = it.get("action_mapped", 0) or 0
        trigger_total = it.get("trigger_total", 0) or 0
        rule_total = it.get("rule_total", 0) or 0

        extracted = (action_total + trigger_total + rule_total) > 0

        if action_total == 0:
            mapping_status = "none"
        elif action_mapped == 0:
            mapping_status = "unmapped"
        elif action_mapped >= action_total:
            mapping_status = "mapped"
        else:
            mapping_status = "partial"

        docs.append({
            "workflow_knowledge_id": it.get("workflow_knowledge_id"),
            "name": it.get("source_document") or it.get("workflow_name"),
            "workflow_name": it.get("workflow_name"),
            "source_document": it.get("source_document"),
            "status": "extracted" if extracted else "empty",
            "extraction_status": "extracted" if extracted else "pending",
            "mapping_status": mapping_status,
            "action_count": action_total,
            "mapped_action_count": action_mapped,
            "trigger_count": trigger_total,
            "business_rule_count": rule_total,
            "uploaded_at": it.get("created_at"),
        })
    return docs


# ── Service (DB-backed, thin) ─────────────────────────────────────────────────

class WorkspaceContextService:
    """Read-only workspace context projections. Reuses WorkspaceSynthesisService."""

    def __init__(self, synthesis_service: WorkspaceSynthesisService | None = None):
        self._synthesis = synthesis_service or WorkspaceSynthesisService()

    # -- public views ----------------------------------------------------------

    def overview(self, db: Session, workspace_id: int) -> dict:
        workspace = self._get_workspace(db, workspace_id)
        synthesis = self._synthesis.for_workspace(db, workspace_id)
        domain = self._derive_domain(db, workspace_id)
        workflow_count = (
            db.query(Workflow)
            .filter(Workflow.workspace_id == workspace_id)
            .count()
        )
        return build_overview(
            workspace=self._workspace_dict(workspace),
            synthesis=synthesis,
            domain=domain,
            workflow_count=workflow_count,
            # Generated files are not linked to a workspace yet.
            generated_file_count=0,
        )

    def documents(self, db: Session, workspace_id: int) -> dict:
        knowledge_rows = self._knowledge_rows(db, workspace_id)
        items = []
        for wk in knowledge_rows:
            action_total = (
                db.query(WorkflowActionMapping)
                .filter(WorkflowActionMapping.workflow_knowledge_id == wk.id)
                .count()
            )
            action_mapped = (
                db.query(WorkflowActionMapping)
                .filter(
                    WorkflowActionMapping.workflow_knowledge_id == wk.id,
                    WorkflowActionMapping.matched_action_definition_id.isnot(None),
                )
                .count()
            )
            trigger_total = (
                db.query(WorkflowTriggerMapping)
                .filter(WorkflowTriggerMapping.workflow_knowledge_id == wk.id)
                .count()
            )
            rule_total = (
                db.query(WorkflowBusinessRule)
                .filter(WorkflowBusinessRule.workflow_knowledge_id == wk.id)
                .count()
            )
            items.append({
                "workflow_knowledge_id": wk.id,
                "workflow_name": wk.workflow_name,
                "source_document": wk.source_document,
                "created_at": wk.created_at,
                "action_total": action_total,
                "action_mapped": action_mapped,
                "trigger_total": trigger_total,
                "rule_total": rule_total,
            })

        return {
            "workspace_id": workspace_id,
            "documents": build_document_view(items),
        }

    def business_rules(self, db: Session, workspace_id: int) -> dict:
        synthesis = self._synthesis.for_workspace(db, workspace_id)
        return {
            "workspace_id": workspace_id,
            "business_rules": synthesis.get("business_rules", []),
            "conflicts": synthesis.get("conflicts", []),
        }

    def actions(self, db: Session, workspace_id: int) -> dict:
        """Workspace-scoped actions only — the candidate set for generation.

        This is the deduplicated, catalog-mapped action set derived from the
        workspace's BRDs. It deliberately does NOT include the global catalog.
        """
        synthesis = self._synthesis.for_workspace(db, workspace_id)
        return {
            "workspace_id": workspace_id,
            "actions": synthesis.get("actions", []),
            "unresolved_actions": synthesis.get("unresolved_actions", []),
            "triggers": synthesis.get("triggers", []),
        }

    # -- helpers ---------------------------------------------------------------

    def _get_workspace(self, db: Session, workspace_id: int) -> Workspace | None:
        return db.query(Workspace).filter(Workspace.id == workspace_id).first()

    def _knowledge_rows(self, db: Session, workspace_id: int) -> list[WorkflowKnowledge]:
        return (
            db.query(WorkflowKnowledge)
            .filter(WorkflowKnowledge.workspace_id == workspace_id)
            .order_by(WorkflowKnowledge.id.asc())
            .all()
        )

    def _derive_domain(self, db: Session, workspace_id: int) -> str | None:
        """Best-effort domain: most common workflow_type of mapped actions.

        Workspaces have no domain column; this is a derived hint, not stored.
        """
        rows = (
            db.query(ActionDefinition.workflow_type)
            .join(
                WorkflowActionMapping,
                WorkflowActionMapping.matched_action_definition_id == ActionDefinition.id,
            )
            .join(
                WorkflowKnowledge,
                WorkflowKnowledge.id == WorkflowActionMapping.workflow_knowledge_id,
            )
            .filter(WorkflowKnowledge.workspace_id == workspace_id)
            .all()
        )
        types = [r[0] for r in rows if r[0]]
        if not types:
            return None
        return Counter(types).most_common(1)[0][0]

    @staticmethod
    def _workspace_dict(workspace: Workspace) -> dict:
        return {
            "id": workspace.id,
            "name": workspace.name,
            "display_name": workspace.display_name,
            "organization_name": workspace.organization_name,
            "description": workspace.description,
            "active": workspace.active,
        }
