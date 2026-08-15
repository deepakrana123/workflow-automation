"""
app/workflow/workflow_explainer.py

WorkflowExplainer — produces a deterministic, human-readable explanation of a
generated workflow.

The explanation is derived entirely from the compiled DAG plus the action /
trigger catalog descriptions already stored in the database. No LLM call — the
result is reproducible and auditable (grounded in the catalog), which is what
makes it trustworthy for review and compliance.

Shape of the explanation:
    {
      "summary": "...",
      "trigger": {"event": "...", "description": "..."},
      "steps": [
        {"id","action","display_name","description","depends_on","explanation"}
      ],
      "execution_order": ["a","b", ...]   # topologically ordered step ids
    }
"""

from sqlalchemy.orm import Session

from app.models.action_definitions import ActionDefinition
from app.models.trigger_definitions import TriggerDefinition


def _trigger_name(trigger: dict) -> str:
    """Best-effort extraction of the trigger identifier from the compiled DAG."""
    if not isinstance(trigger, dict):
        return ""
    return trigger.get("event_type") or trigger.get("name") or trigger.get("type") or ""


def _topological_order(steps: list[dict]) -> list[str]:
    """Return step ids in dependency order (Kahn's algorithm, stable).

    Falls back to declared order for any steps involved in a cycle so the
    explainer never raises on a malformed DAG.
    """
    ids = [s["id"] for s in steps]
    deps = {s["id"]: [d for d in (s.get("depends_on") or []) if d in ids] for s in steps}
    remaining = list(ids)
    ordered: list[str] = []

    while remaining:
        ready = [sid for sid in remaining if all(d in ordered for d in deps[sid])]
        if not ready:
            # Cycle or dangling dependency — append the rest in declared order.
            ordered.extend(remaining)
            break
        for sid in ready:
            ordered.append(sid)
            remaining.remove(sid)
    return ordered


def build_explanation(
    compiled: dict,
    action_meta: dict[str, dict],
    trigger_meta: dict | None,
    domain: str | None = None,
) -> dict:
    """Pure builder — no DB access. Assemble the explanation from lookups.

    Args:
        compiled: the compiled DAG ({trigger, steps}).
        action_meta: {action_name: {"display_name","description"}}.
        trigger_meta: {"display_name","description"} for the trigger, or None.
        domain: workflow domain, used in the summary sentence.
    """
    trigger = compiled.get("trigger", {}) or {}
    steps = compiled.get("steps", []) or []

    trigger_event = _trigger_name(trigger)
    trigger_desc = (trigger_meta or {}).get("description") or ""

    order = _topological_order(steps)
    position = {sid: i for i, sid in enumerate(order)}
    steps_sorted = sorted(steps, key=lambda s: position.get(s["id"], len(order)))

    step_explanations = []
    for step in steps_sorted:
        action = step.get("action", "")
        meta = action_meta.get(action, {})
        depends_on = [d for d in (step.get("depends_on") or [])]
        description = meta.get("description") or ""

        if not depends_on:
            reason = "Runs at the start of the workflow."
        else:
            reason = f"Runs after {', '.join(depends_on)} complete(s)."
        if description:
            reason = f"{reason} {description}"

        step_explanations.append({
            "id": step.get("id"),
            "action": action,
            "display_name": meta.get("display_name") or action,
            "description": description,
            "depends_on": depends_on,
            "explanation": reason.strip(),
        })

    action_titles = [se["display_name"] for se in step_explanations]
    domain_label = f"{domain} " if domain else ""
    if trigger_event:
        summary = (
            f"When '{trigger_event}' occurs, this {domain_label}workflow runs "
            f"{len(steps)} step(s): {', '.join(action_titles)}."
        )
    else:
        summary = (
            f"This {domain_label}workflow runs {len(steps)} step(s): "
            f"{', '.join(action_titles)}."
        )

    return {
        "summary": summary,
        "trigger": {"event": trigger_event, "description": trigger_desc},
        "steps": step_explanations,
        "execution_order": order,
    }


class WorkflowExplainer:
    """Builds a workflow explanation, sourcing descriptions from the catalog."""

    def explain(self, compiled: dict, db: Session, domain: str | None = None) -> dict:
        steps = compiled.get("steps", []) or []
        action_names = {s.get("action") for s in steps if s.get("action")}

        action_meta: dict[str, dict] = {}
        if action_names:
            rows = (
                db.query(
                    ActionDefinition.name,
                    ActionDefinition.display_name,
                    ActionDefinition.description,
                )
                .filter(ActionDefinition.name.in_(action_names))
                .all()
            )
            action_meta = {
                r.name: {"display_name": r.display_name, "description": r.description}
                for r in rows
            }

        trigger_meta = None
        trigger_event = _trigger_name(compiled.get("trigger", {}) or {})
        if trigger_event:
            row = (
                db.query(
                    TriggerDefinition.display_name,
                    TriggerDefinition.description,
                )
                .filter(TriggerDefinition.name == trigger_event)
                .first()
            )
            if row is not None:
                trigger_meta = {
                    "display_name": row.display_name,
                    "description": row.description,
                }

        return build_explanation(compiled, action_meta, trigger_meta, domain)
