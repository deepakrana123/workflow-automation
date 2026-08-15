"""
app/execution/runtime/output_validation.py

Validates a step's outputs against the producing action's declared
``output_schema`` — the contract the rule engine grounds onto.

Non-fatal by design: a contract violation is reported (attached to metadata,
logged) but does NOT fail the step. This keeps existing actions working while
surfacing which outputs are unreliable for branching. Enforcement decisions
(e.g. blocking a rule that references an undeclared field) happen at rule
grounding/compile time, not by crashing execution.

The schema is interpreted flexibly:
  - JSON-Schema style: {"properties": {...}, "required": [...]}  -> check required
    (or all properties if 'required' is absent).
  - Simple map style:  {"field": "type", ...}                    -> check all keys.
"""

from app.core.logger import logger
from app.models.action_definitions import ActionDefinition


def _expected_keys(output_schema: dict) -> list[str]:
    if not isinstance(output_schema, dict):
        return []
    if "properties" in output_schema and isinstance(output_schema["properties"], dict):
        required = output_schema.get("required")
        if isinstance(required, list) and required:
            return list(required)
        return list(output_schema["properties"].keys())
    # Simple {field: type} map — every key is expected.
    return list(output_schema.keys())


def validate_outputs(outputs: dict, output_schema: dict | None) -> dict:
    """Pure check: are the schema's declared keys present in ``outputs``?

    Returns:
        {"validated": bool, "missing": [...], "checked": [...]}
        validated is False only when a schema exists AND declared keys are missing.
    """
    if not output_schema:
        return {"validated": True, "missing": [], "checked": []}

    expected = _expected_keys(output_schema)
    outputs = outputs or {}
    missing = [k for k in expected if k not in outputs]

    return {
        "validated": len(missing) == 0,
        "missing": missing,
        "checked": expected,
    }


def validate_action_outputs(db, action_configuration, outputs: dict) -> dict | None:
    """DB wrapper: load the action's output_schema and validate outputs.

    Returns the validation dict, or None if no schema / lookup fails. Never
    raises — output validation must not break execution.
    """
    try:
        action_def_id = getattr(action_configuration, "action_definition_id", None)
        if action_def_id is None:
            return None
        row = (
            db.query(ActionDefinition.output_schema)
            .filter(ActionDefinition.id == action_def_id)
            .first()
        )
        if row is None or row.output_schema is None:
            return None
        result = validate_outputs(outputs, row.output_schema)
        if not result["validated"]:
            logger.warning(
                "output_contract_violation",
                extra={"extra_data": {
                    "action_configuration_id": getattr(action_configuration, "id", None),
                    "missing_keys": result["missing"],
                }},
            )
        return result
    except Exception as exc:  # noqa: BLE001 - validation is best-effort
        logger.warning(
            "output_validation_error",
            extra={"extra_data": {"error": str(exc)}},
        )
        return None
