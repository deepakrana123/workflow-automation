"""
app/execution/rules/step_rule_evaluator.py

StepRuleEvaluator — evaluates business_rules[] attached to a compiled step
before the executor dispatches the action.

The result is one of:
  EvalResult(passed=True, ...)      — all rules satisfied, proceed
  EvalResult(passed=False, ...)     — at least one rule blocked, halt step

On a block, the caller (step_executor) sets ExecutionStep.status = RULE_BLOCKED
(that constant already exists in runtime/constants.py) and returns without
dispatching the executor. The DAG treats RULE_BLOCKED the same as WAITING —
the step is not retried, the DAG pauses.

Rule sources:
  1. step["business_rules"]     — rules embedded in the compiled DAG step
     (placed there by RuleInjector after compilation)
  2. Inherited rules from BusinessRuleDefinition table via
     RuleInheritanceResolver (if workspace_id is provided)

Each individual rule is evaluated by evaluate_condition() — reused unchanged.

Pure design: no DB calls required when step-embedded rules are used.
DB is only needed for inherited rule resolution (pass workspace_id).
"""

from __future__ import annotations

from typing import NamedTuple, Any

from app.execution.rules.evaluator import evaluate_condition
from app.core.logger import logger


class RuleEvalEntry(NamedTuple):
    rule_description: str
    field: str | None
    op: str | None
    value: Any
    actual: Any
    result: bool
    scope_workspace_id: int | None


class EvalResult(NamedTuple):
    passed: bool
    blocking_rule: RuleEvalEntry | None   # first rule that failed, or None
    evaluations: list[RuleEvalEntry]       # all evaluations (pass and fail)


def evaluate_step_rules(
    step_definition: dict,
    context_outputs: dict,
    inherited_rules: list[dict] | None = None,
) -> EvalResult:
    """Evaluate all business rules for a step against current WorkflowContext outputs.

    Evaluation order:
      1. Inherited rules (global → branch, already ordered by resolver)
      2. Step-embedded rules from step_definition["business_rules"]

    First failing rule halts evaluation and triggers RULE_BLOCKED.

    Args:
        step_definition:  The compiled step dict from parsed_rule_json.
                          May contain a "business_rules" list.
        context_outputs:  The current WorkflowContext.outputs dict.
                          Keys are field names, values are step outputs.
        inherited_rules:  Pre-resolved list of rule dicts from
                          RuleInheritanceResolver (optional).
                          Each dict: {field, op, value, description, scope_workspace_id}

    Returns:
        EvalResult — .passed indicates whether execution should proceed.
    """
    evaluations: list[RuleEvalEntry] = []

    # ── 1. Evaluate inherited rules first ─────────────────────────────────────
    for rule in (inherited_rules or []):
        entry = _eval_one_rule(rule, context_outputs)
        evaluations.append(entry)
        if not entry.result:
            _log_block(step_definition, entry)
            return EvalResult(
                passed=False,
                blocking_rule=entry,
                evaluations=evaluations,
            )

    # ── 2. Evaluate step-embedded rules ───────────────────────────────────────
    step_rules = step_definition.get("business_rules") or []
    for rule in step_rules:
        entry = _eval_one_rule(rule, context_outputs)
        evaluations.append(entry)
        if not entry.result:
            _log_block(step_definition, entry)
            return EvalResult(
                passed=False,
                blocking_rule=entry,
                evaluations=evaluations,
            )

    return EvalResult(passed=True, blocking_rule=None, evaluations=evaluations)


def _eval_one_rule(rule: dict, context_outputs: dict) -> RuleEvalEntry:
    """Evaluate a single rule dict against context_outputs."""
    field       = rule.get("field")
    op          = rule.get("op")
    value       = rule.get("value")
    description = rule.get("description") or ""
    scope_ws    = rule.get("scope_workspace_id")

    actual = context_outputs.get(field) if field else None

    # evaluate_condition is total — never raises
    if field and op and value is not None:
        passed = evaluate_condition(op, actual, value)
    else:
        # Description-only rule — no structured condition, always passes
        passed = True

    return RuleEvalEntry(
        rule_description=description,
        field=field,
        op=op,
        value=value,
        actual=actual,
        result=passed,
        scope_workspace_id=scope_ws,
    )


def _log_block(step_definition: dict, entry: RuleEvalEntry) -> None:
    logger.info(
        "step_rule_blocked",
        extra={"extra_data": {
            "step_id":          step_definition.get("id"),
            "action":           step_definition.get("action"),
            "rule_description": entry.rule_description,
            "field":            entry.field,
            "op":               entry.op,
            "value":            entry.value,
            "actual":           entry.actual,
            "scope_workspace_id": entry.scope_workspace_id,
        }},
    )


def build_metadata_entry(eval_result: EvalResult) -> dict:
    """Build the dict written to ExecutionStep.metadata["rule_evaluations"]."""
    return {
        "passed": eval_result.passed,
        "total": len(eval_result.evaluations),
        "passed_count": sum(1 for e in eval_result.evaluations if e.result),
        "failed_count": sum(1 for e in eval_result.evaluations if not e.result),
        "blocking_rule": (
            {
                "description":       eval_result.blocking_rule.rule_description,
                "field":             eval_result.blocking_rule.field,
                "op":                eval_result.blocking_rule.op,
                "value":             eval_result.blocking_rule.value,
                "actual":            eval_result.blocking_rule.actual,
                "scope_workspace_id": eval_result.blocking_rule.scope_workspace_id,
            }
            if eval_result.blocking_rule
            else None
        ),
        "evaluations": [
            {
                "description": e.rule_description,
                "field":       e.field,
                "op":          e.op,
                "value":       e.value,
                "actual":      e.actual,
                "result":      e.result,
                "scope_workspace_id": e.scope_workspace_id,
            }
            for e in eval_result.evaluations
        ],
    }
