"""
app/runtime/rule_engine.py

RuntimeRuleEngine — evaluates workspace-level business rules and step rules
against a RuleEvaluationContext.

This is a deterministic layer. No LLM involved.

Evaluation order (layered, most-to-least specific):
  1. Global workspace rules (from root of ancestor chain)
  2. Regional / zone / branch rules (inherited)
  3. Step-embedded rules from the compiled DAG step definition

First failing rule halts evaluation. Returns RuleEvaluationResult with
structured failure info, never just a plain bool.

Reuses existing primitives:
  - app.rbac.rule_inheritance.resolve_effective_rules
  - app.execution.rules.step_rule_evaluator.evaluate_step_rules
  - app.execution.rules.evaluator.evaluate_condition
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.rbac.rule_inheritance import resolve_effective_rules
from app.execution.rules.evaluator import evaluate_condition
from app.models.workflow import Workflow
from app.runtime.context import RuleEvaluationContext, RuleEvaluationResult
from app.core.logger import logger


class RuntimeRuleEngine:
    """Deterministic rule engine for runtime authorization."""

    def __init__(self, db: Session):
        self._db = db

    def evaluate(self, ctx: RuleEvaluationContext) -> RuleEvaluationResult:
        """
        Evaluate all applicable rules for a given action request.

        Layers (in order):
          1. Workspace-inherited rules (global → branch)
          2. Step-embedded rules from the DAG definition

        Returns RuleEvaluationResult — never raises.
        """
        decisions: list[dict] = []
        failed_rules: list[dict] = []
        warnings: list[str] = []

        try:
            # ── Layer 1: Inherited workspace rules ────────────────────────────
            inherited = resolve_effective_rules(ctx.workspace_id, self._db, field=None)
            facts = {**ctx.previous_step_outputs, **ctx.request_data}

            for rule in inherited:
                if not rule.is_evaluable():
                    # Description-only rule — non-blocking, add as info
                    decisions.append({
                        "rule_id":     rule.id,
                        "description": rule.description,
                        "field":       None,
                        "evaluable":   False,
                        "result":      True,
                        "scope":       rule.scope_workspace_id,
                    })
                    continue

                actual = facts.get(rule.field)
                passed = evaluate_condition(rule.op, actual, rule.value)

                entry = {
                    "rule_id":     rule.id,
                    "description": rule.description,
                    "field":       rule.field,
                    "op":          rule.op,
                    "value":       rule.value,
                    "actual":      actual,
                    "result":      passed,
                    "scope":       rule.scope_workspace_id,
                    "evaluable":   True,
                }
                decisions.append(entry)

                if not passed:
                    failed_rules.append({
                        "rule_id": rule.id,
                        "code":    f"RULE_FAILED:{rule.field}:{rule.op}",
                        "message": rule.description,
                    })
                    logger.info(
                        "runtime_rule_engine_block",
                        extra={"extra_data": {
                            "user_id":      ctx.user_id,
                            "workspace_id": ctx.workspace_id,
                            "rule_id":      rule.id,
                            "field":        rule.field,
                            "op":           rule.op,
                            "value":        rule.value,
                            "actual":       actual,
                        }},
                    )
                    return RuleEvaluationResult(
                        allowed=False,
                        decisions=decisions,
                        failed_rules=failed_rules,
                        warnings=warnings,
                    )

            # ── Layer 2: Step-embedded rules from DAG ─────────────────────────
            if ctx.step_id and ctx.workflow_id:
                step_rules = self._get_step_rules(ctx.workflow_id, ctx.step_id)
                for rule in step_rules:
                    field = rule.get("field")
                    op    = rule.get("op")
                    value = rule.get("value")
                    desc  = rule.get("description", "")

                    if not (field and op and value is not None):
                        decisions.append({
                            "description": desc,
                            "evaluable":   False,
                            "result":      True,
                        })
                        continue

                    actual = facts.get(field)
                    passed = evaluate_condition(op, actual, value)

                    entry = {
                        "description": desc,
                        "field":       field,
                        "op":          op,
                        "value":       value,
                        "actual":      actual,
                        "result":      passed,
                        "evaluable":   True,
                        "scope":       "step",
                    }
                    decisions.append(entry)

                    if not passed:
                        failed_rules.append({
                            "rule_id": None,
                            "code":    f"STEP_RULE_FAILED:{field}:{op}",
                            "message": desc,
                        })
                        return RuleEvaluationResult(
                            allowed=False,
                            decisions=decisions,
                            failed_rules=failed_rules,
                            warnings=warnings,
                        )

            # ── Role check ────────────────────────────────────────────────────
            if ctx.step_id and ctx.workflow_id:
                role_warning = self._check_step_roles(
                    ctx.workflow_id, ctx.step_id, ctx.actor_roles
                )
                if role_warning:
                    warnings.append(role_warning)

            return RuleEvaluationResult(
                allowed=True,
                decisions=decisions,
                failed_rules=[],
                warnings=warnings,
            )

        except Exception as exc:
            logger.warning(
                "runtime_rule_engine_error",
                extra={"extra_data": {
                    "user_id":      ctx.user_id,
                    "workspace_id": ctx.workspace_id,
                    "error":        str(exc),
                }},
            )
            return RuleEvaluationResult(
                allowed=False,
                decisions=[],
                failed_rules=[{"rule_id": None, "code": "INTERNAL_ERROR", "message": str(exc)}],
                warnings=[],
            )

    # ── Private helpers ────────────────────────────────────────────────────────

    def _get_step_rules(self, workflow_id: int, step_id: str) -> list[dict]:
        """Return business_rules list from the compiled DAG step."""
        workflow = self._db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if workflow is None:
            return []
        steps = (workflow.parsed_rule_json or {}).get("steps", [])
        step = next((s for s in steps if str(s.get("id")) == str(step_id)), None)
        if step is None:
            return []
        return step.get("business_rules") or []

    def _check_step_roles(
        self, workflow_id: int, step_id: str, user_roles: list[str]
    ) -> str | None:
        """Return a warning string if the user's roles don't match the step's expected roles."""
        workflow = self._db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if workflow is None:
            return None
        steps = (workflow.parsed_rule_json or {}).get("steps", [])
        step = next((s for s in steps if str(s.get("id")) == str(step_id)), None)
        if step is None:
            return None

        required: list[str] = []
        for br in step.get("business_rules") or []:
            required.extend(br.get("allowed_roles") or [])

        if not required:
            return None

        if not set(user_roles).intersection(set(required)):
            return (
                f"Step {step_id} prefers roles {required}, "
                f"but user has {user_roles}. Step may require approval."
            )
        return None
