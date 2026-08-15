"""
app/execution/rules

The rule engine's deterministic core.

  evaluator  — evaluate a single condition (op, actual, expected) -> bool.
               A reusable primitive: data facts drive workflow branching today;
               identity facts could drive RBAC later, sharing this evaluator.

  routing    — given a decision parent's outputs + its routing spec, decide
               which children activate, and which steps get SKIPPED (cascade).

Everything here is pure (no DB, no LLM) so branching logic is reproducible and
testable in isolation.
"""

from app.execution.rules.evaluator import evaluate_condition, RuleOperator
from app.execution.rules.routing import (
    resolve_activated_children,
    resolve_skipped_steps,
)

__all__ = [
    "evaluate_condition",
    "RuleOperator",
    "resolve_activated_children",
    "resolve_skipped_steps",
]
