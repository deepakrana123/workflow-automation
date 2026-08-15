"""
app/execution/rules/routing.py

The parent-decides-child branching logic.

A decision parent carries a ``routing`` spec:

    routing = {
        "field": "credit_score",          # read from the parent's OWN output
        "branches": [
            {"when": {"op": ">=", "value": 750}, "activate": ["s_approve"]},
            {"when": {"op": "<",  "value": 750}, "activate": ["s_reject"]},
        ],
        "default": ["s_manual_review"],    # optional; used when no branch matches
    }

Branches are evaluated in order; the FIRST match wins and its children are
activated. Children of the parent that are not activated (and their
descendants) are SKIPPED.

v1 scope: tree-structured branches. A join/merge step that depends on two
branch arms (a diamond) is NOT supported — it would remain unscheduled. This
matches the linear/tree DAGs the synthesizer produces today.

Pure functions — no DB, no LLM.
"""

from app.execution.rules.evaluator import evaluate_condition


def resolve_activated_children(routing: dict, parent_outputs: dict) -> list[str]:
    """Return the child step ids activated by the parent's routing decision.

    Evaluates branches in order against ``parent_outputs[routing['field']]``;
    first match wins. Falls back to ``default`` (or [] if absent).
    """
    if not routing:
        return []

    field = routing.get("field")
    actual = (parent_outputs or {}).get(field) if field else None

    for branch in routing.get("branches", []) or []:
        when = branch.get("when", {}) or {}
        op = when.get("op")
        expected = when.get("value")
        if evaluate_condition(op, actual, expected):
            return list(branch.get("activate", []) or [])

    return list(routing.get("default", []) or [])


def _children_of(steps: list[dict], parent_id: str) -> list[str]:
    return [
        s["id"]
        for s in steps
        if parent_id in (s.get("depends_on") or [])
    ]


def resolve_skipped_steps(
    steps: list[dict],
    parent_id: str,
    activated_children: list[str],
) -> set[str]:
    """Compute the set of steps skipped by a routing decision.

    Seed: direct children of ``parent_id`` that were NOT activated.
    Cascade: any step ALL of whose dependencies are skipped is also skipped
    (safe for trees; a merge step keeping a completed dependency is not skipped).
    """
    activated = set(activated_children or [])
    direct_children = _children_of(steps, parent_id)
    skipped = {c for c in direct_children if c not in activated}

    # Transitive cascade down the not-taken branch(es).
    changed = True
    while changed:
        changed = False
        for step in steps:
            sid = step["id"]
            if sid in skipped or sid in activated:
                continue
            deps = step.get("depends_on") or []
            if deps and all(d in skipped for d in deps):
                skipped.add(sid)
                changed = True

    return skipped
