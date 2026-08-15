"""
app/workflow_execution/schemas/workflow_context.py

WorkflowContext accumulates outputs from every completed step.
Passed through the entire DAG execution — each step can read
outputs from previous steps and add its own.

Will later be used by Decision Nodes to branch on outputs.
"""

from typing import Any
from dataclasses import dataclass, field


@dataclass
class WorkflowContext:
    """
    Carries accumulated outputs across all steps in a workflow execution.

    outputs — flat merge of every successful ActionResult.outputs. Convenient,
              but lossy when two steps share an output key.
    steps   — per-step outputs keyed by step id (steps["<id>"]["<field>"]). The
              rule engine evaluates a parent's routing against THIS, so a
              condition always references a specific parent's output, never an
              ambiguous flat key.
    """

    outputs: dict[str, Any] = field(default_factory=dict)
    steps: dict[str, dict[str, Any]] = field(default_factory=dict)

    def update(self, result_outputs: dict[str, Any]) -> None:
        """Merge a step's outputs into the flat shared context."""
        self.outputs.update(result_outputs)

    def update_step(self, step_id: str, result_outputs: dict[str, Any]) -> None:
        """Record a step's outputs both per-step (addressable) and flat."""
        self.steps[step_id] = dict(result_outputs or {})
        self.outputs.update(result_outputs or {})

    def step_outputs(self, step_id: str) -> dict[str, Any]:
        """Return the recorded outputs for a specific step (or {})."""
        return self.steps.get(step_id, {})
