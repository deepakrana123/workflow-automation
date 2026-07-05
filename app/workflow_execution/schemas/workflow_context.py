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

    outputs — merged from every successful ActionResult.outputs
               Keys from later steps overwrite earlier ones with the same key.
    """

    outputs: dict[str, Any] = field(default_factory=dict)

    def update(self, result_outputs: dict[str, Any]) -> None:
        """Merge a step's outputs into the shared context."""
        self.outputs.update(result_outputs)
