"""
app/evaluation/evaluator.py

Evaluator class for the MFlows evaluation framework.

Compares extracted workflow knowledge (from the ingestion pipeline output)
against expected ground truth. Produces an EvaluationReport.

No database access. No printing. No side effects.
Accepts plain data structures — works with any input source.
"""

from app.evaluation.models import (
    ActionEvaluation,
    EvaluationReport,
    TriggerEvaluation,
    WorkflowEvaluation,
)
from app.evaluation.metrics import (
    calculate_action_accuracy,
    calculate_average_similarity,
    calculate_trigger_accuracy,
    count_unknown_actions,
    count_unknown_triggers,
)


class ExtractedAction:
    """
    Represents a single action as produced by the ingestion pipeline.

    extracted_name    — raw name extracted from the BRD by the LLM
    predicted_name    — catalog action name matched by the embedding mapper
                        (None if no match was found)
    similarity_score  — cosine similarity from the embedding mapper
                        (None if no match was found)
    """

    __slots__ = ("extracted_name", "predicted_name", "similarity_score")

    def __init__(
        self,
        extracted_name: str,
        predicted_name: str | None,
        similarity_score: float | None,
    ) -> None:
        self.extracted_name = extracted_name
        self.predicted_name = predicted_name
        self.similarity_score = similarity_score


class ExtractedTrigger:
    """
    Represents a single trigger as produced by the ingestion pipeline.

    extracted_name    — raw name extracted from the BRD by the LLM
    predicted_name    — catalog trigger name matched by the embedding mapper
                        (None if no match was found)
    similarity_score  — cosine similarity from the embedding mapper
                        (None if no match was found)
    """

    __slots__ = ("extracted_name", "predicted_name", "similarity_score")

    def __init__(
        self,
        extracted_name: str,
        predicted_name: str | None,
        similarity_score: float | None,
    ) -> None:
        self.extracted_name = extracted_name
        self.predicted_name = predicted_name
        self.similarity_score = similarity_score


class ExpectedWorkflow:
    """
    Ground truth for a single workflow.

    workflow_name         — expected workflow name
    expected_actions      — list of canonical action names (from catalog)
    expected_triggers     — list of canonical trigger names (from catalog)

    The order of expected_actions must correspond to the order of extracted actions
    when calling Evaluator.evaluate_workflow().
    """

    __slots__ = ("workflow_name", "expected_actions", "expected_triggers")

    def __init__(
        self,
        workflow_name: str,
        expected_actions: list[str],
        expected_triggers: list[str],
    ) -> None:
        self.workflow_name = workflow_name
        self.expected_actions = expected_actions
        self.expected_triggers = expected_triggers


class Evaluator:
    """
    Compares extracted workflow knowledge against expected ground truth.

    Usage:
        evaluator = Evaluator()

        workflow_eval = evaluator.evaluate_workflow(
            workflow_name="Loan Approval",
            extracted_actions=[ExtractedAction(...)],
            extracted_triggers=[ExtractedTrigger(...)],
            expected=ExpectedWorkflow(...)
        )

        report = evaluator.build_report([workflow_eval, ...])
    """

    def evaluate_workflow(
        self,
        workflow_name: str,
        extracted_actions: list[ExtractedAction],
        extracted_triggers: list[ExtractedTrigger],
        expected: ExpectedWorkflow,
    ) -> WorkflowEvaluation:
        """
        Compare one extracted workflow against its ground truth.

        Matching is positional for actions and triggers — the i-th extracted item
        is compared against the i-th expected item. If counts differ, extra items
        are evaluated as incorrect with no predicted match.

        Returns a WorkflowEvaluation with per-item ActionEvaluation
        and TriggerEvaluation results.
        """
        action_results = self._evaluate_actions(
            extracted_actions, expected.expected_actions
        )
        trigger_results = self._evaluate_triggers(
            extracted_triggers, expected.expected_triggers
        )
        return WorkflowEvaluation(
            workflow_name=workflow_name,
            action_results=action_results,
            trigger_results=trigger_results,
        )

    def build_report(
        self,
        workflow_evaluations: list[WorkflowEvaluation],
    ) -> EvaluationReport:
        """
        Aggregate per-workflow results into a single EvaluationReport.

        Flattens all action and trigger evaluations across workflows
        and computes aggregate metrics.
        """
        all_actions: list[ActionEvaluation] = []
        all_triggers: list[TriggerEvaluation] = []

        for wf in workflow_evaluations:
            all_actions.extend(wf.action_results)
            all_triggers.extend(wf.trigger_results)

        return EvaluationReport(
            total_workflows=len(workflow_evaluations),
            total_actions=len(all_actions),
            total_triggers=len(all_triggers),
            action_accuracy=calculate_action_accuracy(all_actions),
            trigger_accuracy=calculate_trigger_accuracy(all_triggers),
            average_similarity=calculate_average_similarity(all_actions, all_triggers),
            unknown_actions=count_unknown_actions(all_actions),
            unknown_triggers=count_unknown_triggers(all_triggers),
            workflow_results=workflow_evaluations,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _evaluate_actions(
        self,
        extracted: list[ExtractedAction],
        expected_names: list[str],
    ) -> list[ActionEvaluation]:
        results: list[ActionEvaluation] = []
        max_len = max(len(extracted), len(expected_names))

        for i in range(max_len):
            ext = extracted[i] if i < len(extracted) else None
            exp_name = expected_names[i] if i < len(expected_names) else ""

            if ext is None:
                # Ground truth has more items than were extracted
                results.append(
                    ActionEvaluation(
                        extracted_action="",
                        expected_action=exp_name,
                        predicted_action=None,
                        similarity_score=None,
                        correct=False,
                    )
                )
            else:
                results.append(
                    ActionEvaluation(
                        extracted_action=ext.extracted_name,
                        expected_action=exp_name,
                        predicted_action=ext.predicted_name,
                        similarity_score=ext.similarity_score,
                        correct=ext.predicted_name == exp_name
                        if ext.predicted_name is not None
                        else False,
                    )
                )

        return results

    def _evaluate_triggers(
        self,
        extracted: list[ExtractedTrigger],
        expected_names: list[str],
    ) -> list[TriggerEvaluation]:
        results: list[TriggerEvaluation] = []
        max_len = max(len(extracted), len(expected_names))

        for i in range(max_len):
            ext = extracted[i] if i < len(extracted) else None
            exp_name = expected_names[i] if i < len(expected_names) else ""

            if ext is None:
                results.append(
                    TriggerEvaluation(
                        extracted_trigger="",
                        expected_trigger=exp_name,
                        predicted_trigger=None,
                        similarity_score=None,
                        correct=False,
                    )
                )
            else:
                results.append(
                    TriggerEvaluation(
                        extracted_trigger=ext.extracted_name,
                        expected_trigger=exp_name,
                        predicted_trigger=ext.predicted_name,
                        similarity_score=ext.similarity_score,
                        correct=ext.predicted_name == exp_name
                        if ext.predicted_name is not None
                        else False,
                    )
                )

        return results
