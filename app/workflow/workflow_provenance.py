"""
app/workflow/workflow_provenance.py

WorkflowProvenanceService — answers "where did each step come from?"

Provenance is derived (not stored): it joins a compiled workflow's steps back
to the BRD-extraction mappings that justified them. For each step we surface
the source term, the source clause, and the mapping confidence, so a reviewer
(or a regulator) can trace an executable step back to the requirement text.

Two grounding levels:
  - "brd"        : the step's action matched a WorkflowActionMapping extracted
                   from an ingested BRD (rich provenance + confidence).
  - "generated"  : no BRD mapping (e.g. NL-only generation) — the source is the
                   original natural-language request, no confidence score.

Nothing new is persisted; this is a projection over existing data, so it is
always consistent with the current mappings.
"""

from sqlalchemy.orm import Session

from app.repositories import workflow as workflow_repo
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workflow_action_mapping import WorkflowActionMapping
from app.models.action_definitions import ActionDefinition

SOURCE_BRD = "brd"
SOURCE_GENERATED = "generated"


def build_provenance(
    workflow_id: int,
    steps: list[dict],
    action_to_mapping: dict[str, dict],
    raw_input: str | None,
    source_document: str | None,
) -> dict:
    """Pure builder — assemble the provenance projection from resolved lookups.

    Args:
        workflow_id: the workflow being explained.
        steps: compiled DAG steps ({id, action, ...}).
        action_to_mapping: {action_name: {term, clause, confidence, similarity, status}}.
        raw_input: the original NL request (fallback source for ungrounded steps).
        source_document: the BRD filename, if the workflow came from ingestion.
    """
    step_provenance = []
    confidences: list[float] = []

    for step in steps:
        action = step.get("action", "")
        mapping = action_to_mapping.get(action)

        if mapping:
            confidence = mapping.get("confidence")
            if confidence is not None:
                confidences.append(confidence)
            step_provenance.append({
                "id": step.get("id"),
                "action": action,
                "source_type": SOURCE_BRD,
                "source_term": mapping.get("term"),
                "source_clause": mapping.get("clause"),
                "confidence": confidence,
                "similarity": mapping.get("similarity"),
            })
        else:
            step_provenance.append({
                "id": step.get("id"),
                "action": action,
                "source_type": SOURCE_GENERATED,
                "source_term": None,
                "source_clause": raw_input,
                "confidence": None,
                "similarity": None,
            })

    grounded = any(s["source_type"] == SOURCE_BRD for s in step_provenance)
    avg_conf = round(sum(confidences) / len(confidences), 4) if confidences else None

    return {
        "workflow_id": workflow_id,
        "source_document": source_document,
        "grounded": grounded,
        "average_confidence": avg_conf,
        "steps": step_provenance,
    }


class WorkflowProvenanceService:
    """Builds a workflow's provenance by joining steps to extraction mappings."""

    def for_workflow(self, db: Session, workflow_id: int) -> dict | None:
        workflow = workflow_repo.get_by_id(db, workflow_id)
        if workflow is None:
            return None

        compiled = workflow.parsed_rule_json or {}
        steps = compiled.get("steps", []) or []

        # Resolve the BRD knowledge for this workflow the same way the runtime
        # does — by matching workflow name (latest ingestion wins).
        knowledge = (
            db.query(WorkflowKnowledge)
            .filter(WorkflowKnowledge.workflow_name == workflow.name)
            .order_by(WorkflowKnowledge.id.desc())
            .first()
        )

        action_to_mapping: dict[str, dict] = {}
        source_document = None

        if knowledge is not None:
            source_document = knowledge.source_document
            action_names = {s.get("action") for s in steps if s.get("action")}

            if action_names:
                defs = (
                    db.query(ActionDefinition.id, ActionDefinition.name)
                    .filter(ActionDefinition.name.in_(action_names))
                    .all()
                )
                name_by_id = {d.id: d.name for d in defs}

                if name_by_id:
                    mappings = (
                        db.query(WorkflowActionMapping)
                        .filter(
                            WorkflowActionMapping.workflow_knowledge_id == knowledge.id,
                            WorkflowActionMapping.matched_action_definition_id.in_(
                                list(name_by_id.keys())
                            ),
                        )
                        .all()
                    )
                    for m in mappings:
                        name = name_by_id.get(m.matched_action_definition_id)
                        if not name:
                            continue
                        action_to_mapping[name] = {
                            "term": m.extract_name,
                            "clause": m.description,
                            "confidence": m.confidence,
                            "similarity": m.similarity_score,
                            "status": getattr(m.status, "value", m.status),
                        }

        return build_provenance(
            workflow_id=workflow_id,
            steps=steps,
            action_to_mapping=action_to_mapping,
            raw_input=workflow.raw_input,
            source_document=source_document,
        )
