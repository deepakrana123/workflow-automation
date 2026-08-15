"""
app/workflow/workspace_diagnostics.py

WorkspaceDiagnosticsService — per-action pipeline trace for observability.

For every extracted action in every BRD in a workspace, returns:
  - original extracted text
  - query text sent to retrieval
  - mapping status (MAPPED / UNMAPPED / PENDING)
  - matched catalog action (if any)
  - similarity_score (rrf_score of winner)
  - confidence (sigmoid(cross_encoder_score) of winner)
  - top_candidates (full top-K with per-source ranks and scores)
  - diagnostic_classification

Diagnostic classifications (derived, never invented):
  MAPPED           — accepted above threshold
  RETRIEVAL_MISS   — no candidates returned at all
  MAPPING_REJECTED — candidates returned but none above threshold
  PENDING          — mapping was never attempted (legacy rows)

No new data is collected here — this is a pure projection over stored columns.
"""

from sqlalchemy.orm import Session

from app.models.workflow_action_mapping import WorkflowActionMapping, MappingStatus
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.action_definitions import ActionDefinition


def _classify(mapping: WorkflowActionMapping) -> str:
    if mapping.status == MappingStatus.MAPPED:
        return "MAPPED"
    if mapping.status == MappingStatus.PENDING:
        return "PENDING"
    # UNMAPPED — distinguish retrieval miss from mapping rejected
    top = mapping.top_candidates or []
    if not top:
        return "RETRIEVAL_MISS"
    return "MAPPING_REJECTED"


class WorkspaceDiagnosticsService:

    def for_workspace(self, db: Session, workspace_id: int) -> dict:
        """Return full per-action diagnostics for every BRD in the workspace."""
        knowledge_rows = (
            db.query(WorkflowKnowledge)
            .filter(WorkflowKnowledge.workspace_id == workspace_id)
            .order_by(WorkflowKnowledge.id.asc())
            .all()
        )

        brd_diagnostics = []
        totals = {
            "extracted_actions": 0,
            "mapped":            0,
            "unmapped":          0,
            "retrieval_miss":    0,
            "mapping_rejected":  0,
            "pending":           0,
        }

        for wk in knowledge_rows:
            mappings = (
                db.query(WorkflowActionMapping)
                .filter(WorkflowActionMapping.workflow_knowledge_id == wk.id)
                .all()
            )

            actions = []
            for m in mappings:
                totals["extracted_actions"] += 1
                classification = _classify(m)

                # Count per classification
                if classification == "MAPPED":
                    totals["mapped"] += 1
                elif classification == "RETRIEVAL_MISS":
                    totals["retrieval_miss"] += 1
                elif classification == "MAPPING_REJECTED":
                    totals["mapping_rejected"] += 1
                elif classification == "PENDING":
                    totals["pending"] += 1

                if classification != "MAPPED":
                    totals["unmapped"] += 1 if classification != "PENDING" else 0

                matched_action = None
                if m.matched_action_definition_id is not None:
                    ad = m.action_definition
                    if ad:
                        matched_action = {
                            "id":           ad.id,
                            "name":         ad.name,
                            "display_name": ad.display_name,
                        }

                actions.append({
                    "mapping_id":          m.id,
                    "extract_name":        m.extract_name,
                    "description":         m.description,
                    "query_text":          m.query_text,
                    "status":              m.status.value if m.status else "PENDING",
                    "similarity_score":    m.similarity_score,
                    "confidence":          m.confidence,
                    "matched_action":      matched_action,
                    "top_candidates":      m.top_candidates or [],
                    "diagnostic":          classification,
                })

            brd_diagnostics.append({
                "workflow_knowledge_id": wk.id,
                "workflow_name":         wk.workflow_name,
                "source_document":       wk.source_document,
                "actions":               actions,
            })

        return {
            "workspace_id":    workspace_id,
            "totals":          totals,
            "brds":            brd_diagnostics,
        }
