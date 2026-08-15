"""
app/workflow/workspace_synthesis.py

WorkspaceSynthesisService — aggregates the knowledge extracted from ALL BRDs
in a workspace into a single, deduplicated, provenance-rich view.

This is the deterministic foundation of "one workflow from multiple BRDs":

  N BRDs (each a WorkflowKnowledge with flat, unordered extracted actions)
        │
        ▼  union + dedup by canonical ActionDefinition
  workspace action set  (each action: which BRDs contributed it, clauses, confidence)
        │
        ▼  conflict / review flags (unresolved + low-confidence)
  synthesis view

Sequencing these actions into an executable DAG is a later phase that reuses
the generation/compiler pipeline; this layer produces the trustworthy,
attributable knowledge that the sequencing step consumes.

No LLM, no new persistence — a projection over existing mappings.
"""

from sqlalchemy.orm import Session

from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workflow_action_mapping import WorkflowActionMapping
from app.models.workflow_trigger_mapping import WorkflowTriggerMapping
from app.models.workflow_business_rule import WorkflowBusinessRule
from app.workflow.rule_conflicts import detect_rule_conflicts

# Below this mapping confidence, an action is flagged for human review.
LOW_CONFIDENCE_THRESHOLD = 0.5


def build_workspace_synthesis(
    knowledge_items: list[dict],
    low_confidence_threshold: float = LOW_CONFIDENCE_THRESHOLD,
) -> dict:
    """Pure builder — aggregate per-BRD extractions into one workspace view.

    Args:
        knowledge_items: one dict per BRD:
            {
              "workflow_knowledge_id": int,
              "workflow_name": str,
              "source_document": str | None,
              "actions": [ {canonical_id, canonical_name, display_name,
                            term, clause, confidence, similarity, status} ],
              "triggers": [ {canonical_id, canonical_name, term, clause} ],
              "business_rules": [ "rule text", ... ],
            }
    """
    documents = []
    # canonical_id -> aggregated action
    actions_by_canonical: dict[int, dict] = {}
    unresolved_actions: list[dict] = []
    triggers_by_canonical: dict[int, dict] = {}
    business_rules: list[dict] = []
    review_flags: list[dict] = []

    for item in knowledge_items:
        doc = item.get("source_document")
        wk_id = item.get("workflow_knowledge_id")
        documents.append({
            "workflow_knowledge_id": wk_id,
            "workflow_name": item.get("workflow_name"),
            "source_document": doc,
        })

        for action in item.get("actions", []):
            source = {
                "workflow_knowledge_id": wk_id,
                "source_document": doc,
                "term": action.get("term"),
                "clause": action.get("clause"),
                "confidence": action.get("confidence"),
                "similarity": action.get("similarity"),
            }
            canonical_id = action.get("canonical_id")

            if canonical_id is None:
                # Not mapped to a catalog action — needs review / new action.
                unresolved_actions.append({
                    "term": action.get("term"),
                    "clause": action.get("clause"),
                    "source_document": doc,
                    "workflow_knowledge_id": wk_id,
                })
                continue

            agg = actions_by_canonical.get(canonical_id)
            if agg is None:
                agg = {
                    "canonical_id": canonical_id,
                    "action": action.get("canonical_name"),
                    "display_name": action.get("display_name") or action.get("canonical_name"),
                    "sources": [],
                }
                actions_by_canonical[canonical_id] = agg
            agg["sources"].append(source)

        for trigger in item.get("triggers", []):
            canonical_id = trigger.get("canonical_id")
            if canonical_id is None:
                continue
            agg = triggers_by_canonical.get(canonical_id)
            if agg is None:
                agg = {
                    "canonical_id": canonical_id,
                    "trigger": trigger.get("canonical_name"),
                    "sources": [],
                }
                triggers_by_canonical[canonical_id] = agg
            agg["sources"].append({
                "workflow_knowledge_id": wk_id,
                "source_document": doc,
                "term": trigger.get("term"),
                "clause": trigger.get("clause"),
            })

        for rule in item.get("business_rules", []):
            business_rules.append({"rule": rule, "source_document": doc})

    # Finalize actions: confidence stats + contributed_by count.
    actions = []
    for agg in actions_by_canonical.values():
        confidences = [s["confidence"] for s in agg["sources"] if s.get("confidence") is not None]
        min_conf = min(confidences) if confidences else None
        agg["contributed_by"] = len({s["workflow_knowledge_id"] for s in agg["sources"]})
        agg["min_confidence"] = round(min_conf, 4) if min_conf is not None else None
        actions.append(agg)

        if min_conf is not None and min_conf < low_confidence_threshold:
            review_flags.append({
                "type": "low_confidence",
                "action": agg["action"],
                "min_confidence": agg["min_confidence"],
            })

    for ua in unresolved_actions:
        review_flags.append({
            "type": "unresolved_action",
            "term": ua["term"],
            "source_document": ua["source_document"],
        })

    # Cross-BRD conflicting thresholds (e.g. approval above ₹5L vs ₹10L).
    conflicts = detect_rule_conflicts(business_rules)
    for c in conflicts:
        review_flags.append({
            "type": "rule_conflict",
            "subject": c["subject"],
            "rules": c["rules"],
        })

    return {
        "brd_count": len(documents),
        "documents": documents,
        "actions": actions,
        "unresolved_actions": unresolved_actions,
        "triggers": list(triggers_by_canonical.values()),
        "business_rules": business_rules,
        "conflicts": conflicts,
        "review_flags": review_flags,
    }


class WorkspaceSynthesisService:
    """Builds the aggregated knowledge view for a workspace."""

    def for_workspace(self, db: Session, workspace_id: int) -> dict:
        knowledge_rows = (
            db.query(WorkflowKnowledge)
            .filter(WorkflowKnowledge.workspace_id == workspace_id)
            .order_by(WorkflowKnowledge.id.asc())
            .all()
        )

        knowledge_items = []
        for wk in knowledge_rows:
            action_mappings = (
                db.query(WorkflowActionMapping)
                .filter(WorkflowActionMapping.workflow_knowledge_id == wk.id)
                .all()
            )
            actions = []
            for m in action_mappings:
                ad = m.action_definition  # relationship; None if unmapped
                actions.append({
                    "canonical_id": m.matched_action_definition_id,
                    "canonical_name": ad.name if ad else None,
                    "display_name": ad.display_name if ad else None,
                    "term": m.extract_name,
                    "clause": m.description,
                    "confidence": m.confidence,
                    "similarity": m.similarity_score,
                    "status": getattr(m.status, "value", m.status),
                })

            trigger_mappings = (
                db.query(WorkflowTriggerMapping)
                .filter(WorkflowTriggerMapping.workflow_knowledge_id == wk.id)
                .all()
            )
            triggers = []
            for t in trigger_mappings:
                td = t.trigger_definition
                triggers.append({
                    "canonical_id": t.matched_trigger_definition_id,
                    "canonical_name": td.name if td else None,
                    "term": t.extracted_name,
                    "clause": t.description,
                })

            rules = (
                db.query(WorkflowBusinessRule.rule)
                .filter(WorkflowBusinessRule.workflow_knowledge_id == wk.id)
                .all()
            )

            knowledge_items.append({
                "workflow_knowledge_id": wk.id,
                "workflow_name": wk.workflow_name,
                "source_document": wk.source_document,
                "actions": actions,
                "triggers": triggers,
                "business_rules": [r.rule for r in rules],
            })

        result = build_workspace_synthesis(knowledge_items)
        result["workspace_id"] = workspace_id
        return result
