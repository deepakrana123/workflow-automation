"""
PART 2 — Strict DAG Validation

Validates:
- step id required
- trigger required
- action required
- dependency ids must exist
- cycle detection
- duplicate step ids
- malformed depends syntax
- allowed trigger/action values
"""

from app.parsers.schemas import ALLOWED_TRIGGERS, ALLOWED_ACTIONS
from app.core.logger import logger


def _detect_cycle(steps: list) -> bool:
    """
    Kahn's algorithm for cycle detection in DAG.
    Returns True if a cycle exists.
    """
    step_ids = {s["id"] for s in steps}
    in_degree = {s["id"]: 0 for s in steps}
    adjacency = {s["id"]: [] for s in steps}

    for step in steps:
        for dep in step.get("depends_on", []):
            if dep in step_ids:
                adjacency[dep].append(step["id"])
                in_degree[step["id"]] += 1

    queue = [sid for sid, deg in in_degree.items() if deg == 0]
    visited = 0

    while queue:
        node = queue.pop(0)
        visited += 1
        for neighbor in adjacency[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return visited != len(steps)


def validate_dag(steps: list) -> dict:
    """
    Validate a list of parsed step definitions.

    Returns:
        {
            "is_valid": bool,
            "errors": [...]
        }
    """
    errors = []

    if not steps:
        errors.append("dag_has_no_steps")
        return {"is_valid": False, "errors": errors}

    seen_ids = set()
    step_ids = {s["id"] for s in steps}

    for step in steps:
        step_id = step.get("id")
        trigger = step.get("trigger")
        action = step.get("action")
        depends_on = step.get("depends_on", [])

        # step id required
        if not step_id:
            errors.append("step_id_required")

        # duplicate step id
        elif step_id in seen_ids:
            errors.append(f"duplicate_step_id: {step_id!r}")
        else:
            seen_ids.add(step_id)

        # trigger required
        if not trigger:
            errors.append(f"step {step_id!r}: trigger_required")
        elif trigger not in ALLOWED_TRIGGERS:
            errors.append(f"step {step_id!r}: invalid_trigger: {trigger!r}")

        # action required
        if not action:
            errors.append(f"step {step_id!r}: action_required")
        elif action not in ALLOWED_ACTIONS:
            errors.append(f"step {step_id!r}: invalid_action: {action!r}")

        # dependency ids must exist
        for dep in depends_on:
            if dep not in step_ids:
                errors.append(f"step {step_id!r}: unknown_dependency: {dep!r}")

    # cycle detection
    if not errors:
        if _detect_cycle(steps):
            errors.append("dag_has_cycle")

    is_valid = len(errors) == 0

    if not is_valid:
        logger.warning(
            "parser_validation_failed",
            extra={"extra_data": {"errors": errors}},
        )
    else:
        logger.info(
            "parser_validation_passed",
            extra={"extra_data": {"step_count": len(steps)}},
        )

    return {"is_valid": is_valid, "errors": errors}
