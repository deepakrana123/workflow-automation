"""
app/workflow/workspace_workflow_synthesizer.py

WorkspaceWorkflowSynthesizer — turns a workspace's aggregated multi-BRD
knowledge into ONE executable workflow (compiled DAG).

Pipeline (fully deterministic — no LLM):

  WorkspaceSynthesisService  (dedup + provenance across BRDs)
        │  ordered, deduped canonical actions
        ▼
  build_synthesis_workflow_json   (sequential chaining — ordering heuristic)
        ▼
  WorkflowCompilerService.compile  (DSL -> AST -> compiled DAG; all pure)
        ▼
  WorkflowPersistenceService.save  (Workflow row + explanation)
        ▼
  synthesized workflow + cross-BRD provenance

Note on ordering: BRD extraction has no sequence, so v1 chains actions
sequentially (consensus actions — contributed by more BRDs — first). Conditional
branching is intentionally deferred to the rule engine.
"""

import re

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.dsl.dsl_generator import DSLGenerator
from app.nlp.parsers.rule_parser import RuleParser
from app.nlp.ast.builder import WorkflowASTBuilder
from app.nlp.ast.validator import ASTValidator
from app.nlp.complier.workflow_complier import WorkflowComplier
from app.workflow.workflow_compiler_service import WorkflowCompilerService
from app.workflow.workflow_persistence_service import WorkflowPersistenceService
from app.workflow.workflow_explainer import WorkflowExplainer
from app.workflow.workspace_synthesis import WorkspaceSynthesisService

_DEFAULT_TRIGGER = "workspace_workflow_triggered"


def _slug(value: str | None) -> str:
    """Coerce a name into a single \\w+ token the DSL grammar accepts."""
    if not value:
        return _DEFAULT_TRIGGER
    slug = re.sub(r"\W+", "_", value).strip("_")
    return slug or _DEFAULT_TRIGGER


def order_actions(synthesis: dict) -> list[str]:
    """Deterministic action ordering: consensus first, then name (stable)."""
    actions = synthesis.get("actions", []) or []
    ordered = sorted(
        actions,
        key=lambda a: (-(a.get("contributed_by") or 0), a.get("action") or ""),
    )
    return [a["action"] for a in ordered if a.get("action")]


def pick_trigger(synthesis: dict) -> str:
    """Pick the trigger contributed by the most BRDs; fall back to a default."""
    triggers = synthesis.get("triggers", []) or []
    if not triggers:
        return _DEFAULT_TRIGGER
    best = max(triggers, key=lambda t: len(t.get("sources", []) or []))
    return _slug(best.get("trigger"))


def build_synthesis_workflow_json(synthesis: dict, trigger_name: str) -> dict:
    """Build the compiler's input from the aggregation (sequential chaining).

    Each action depends on the previous one, producing a valid linear DAG.
    """
    names = order_actions(synthesis)

    action_entries = []
    prev = None
    for name in names:
        action_entries.append({
            "name": name,
            "dependencies": [prev] if prev else [],
        })
        prev = name

    return {
        "workflow": {
            "triggers": [{"name": _slug(trigger_name)}],
            "actions": action_entries,
        }
    }


def build_synthesis_provenance(compiled: dict, synthesis: dict) -> list[dict]:
    """Attach each compiled step to the BRD sources of its action."""
    sources_by_action = {
        a["action"]: a.get("sources", [])
        for a in synthesis.get("actions", []) or []
    }
    provenance = []
    for step in compiled.get("steps", []) or []:
        action = step.get("action")
        provenance.append({
            "step_id": step.get("id"),
            "action": action,
            "sources": sources_by_action.get(action, []),
        })
    return provenance


def _build_compiler_service() -> WorkflowCompilerService:
    return WorkflowCompilerService(
        dsl_generator=DSLGenerator(),
        rule_parser=RuleParser(),
        ast_builder=WorkflowASTBuilder(),
        ast_validator=ASTValidator(),
        workflow_compiler=WorkflowComplier(),
    )


class WorkspaceWorkflowSynthesizer:
    """Synthesize one executable workflow from a workspace's BRD knowledge."""

    def __init__(
        self,
        synthesis_service: WorkspaceSynthesisService | None = None,
        compiler_service: WorkflowCompilerService | None = None,
        persistence_service: WorkflowPersistenceService | None = None,
        explainer: WorkflowExplainer | None = None,
    ):
        self._synthesis = synthesis_service or WorkspaceSynthesisService()
        self._compiler = compiler_service or _build_compiler_service()
        self._persistence = persistence_service or WorkflowPersistenceService()
        self._explainer = explainer or WorkflowExplainer()

    def synthesize(
        self,
        db: Session,
        workspace_id: int,
        name: str,
        domain: str,
    ) -> dict:
        """Compile + persist a workflow from all mapped actions in a workspace.

        Raises:
            ValueError: if the workspace has no mapped actions to synthesize,
                        or the domain is invalid (from persistence).
        """
        synthesis = self._synthesis.for_workspace(db, workspace_id)

        if not synthesis.get("actions"):
            raise ValueError(
                "Workspace has no mapped actions to synthesize. "
                "Ingest BRDs whose actions resolve to the catalog first."
            )

        trigger_name = pick_trigger(synthesis)
        workflow_json = build_synthesis_workflow_json(synthesis, trigger_name)

        compile_result = self._compiler.compile(domain, workflow_json)
        compiled = compile_result["compiled"]

        explanation = None
        try:
            explanation = self._explainer.explain(compiled, db, domain)
        except Exception as exc:  # noqa: BLE001 - best-effort, never blocks synthesis
            logger.warning(
                "synthesis_explanation_failed",
                extra={"extra_data": {"error": str(exc)}},
            )

        summary = (
            f"Synthesized from {synthesis['brd_count']} BRD(s) in workspace "
            f"{workspace_id}: {len(compiled.get('steps', []))} step(s)."
        )

        saved = self._persistence.save(
            db=db,
            name=name,
            domain=domain,
            user_request=summary,
            compile_result=compile_result,
            explanation=explanation,
            workspace_id=workspace_id,
        )

        logger.info(
            "workspace_workflow_synthesized",
            extra={"extra_data": {
                "workspace_id": workspace_id,
                "workflow_id": saved["workflow_id"],
                "brd_count": synthesis["brd_count"],
                "step_count": len(compiled.get("steps", [])),
            }},
        )

        return {
            **saved,
            "brd_count": synthesis["brd_count"],
            "provenance": build_synthesis_provenance(compiled, synthesis),
        }
