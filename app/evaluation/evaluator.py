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
    RankingCandidate,
    TriggerEvaluation,
    WorkflowEvaluation,
)
from app.evaluation.metrics import (
    calculate_action_accuracy,
    calculate_average_similarity,
    calculate_mean_reciprocal_rank_actions,
    calculate_mean_reciprocal_rank_triggers,
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
    similarity_score  — RRF score of the top candidate
                        (None if no match was found)
    top_candidates    — ranked list of RankedCandidate objects from the retriever
                        (optional; populated when --ranking flag is used)
    """

    __slots__ = ("extracted_name", "predicted_name", "similarity_score", "top_candidates")

    def __init__(
        self,
        extracted_name: str,
        predicted_name: str | None,
        similarity_score: float | None,
        top_candidates: list | None = None,
    ) -> None:
        self.extracted_name = extracted_name
        self.predicted_name = predicted_name
        self.similarity_score = similarity_score
        self.top_candidates = top_candidates or []


class ExtractedTrigger:
    """
    Represents a single trigger as produced by the ingestion pipeline.

    extracted_name    — raw name extracted from the BRD by the LLM
    predicted_name    — catalog trigger name matched by the embedding mapper
                        (None if no match was found)
    similarity_score  — RRF score of the top candidate
                        (None if no match was found)
    top_candidates    — ranked list of RankedCandidate objects from the retriever
                        (optional; populated when --ranking flag is used)
    """

    __slots__ = ("extracted_name", "predicted_name", "similarity_score", "top_candidates")

    def __init__(
        self,
        extracted_name: str,
        predicted_name: str | None,
        similarity_score: float | None,
        top_candidates: list | None = None,
    ) -> None:
        self.extracted_name = extracted_name
        self.predicted_name = predicted_name
        self.similarity_score = similarity_score
        self.top_candidates = top_candidates or []


class ExpectedWorkflow:
    """
    Ground truth for a single workflow.

    workflow_name         — expected workflow name
    expected_actions      — list of canonical action names (from catalog)
    expected_triggers     — list of canonical trigger names (from catalog)

    Matching is set-based: an action is correct if its predicted name appears
    anywhere in expected_actions, regardless of order.
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

    Matching is set-based: a prediction is correct if it appears anywhere in
    the expected set for that workflow, regardless of extraction order.

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

        Matching is set-based — a prediction is correct if it is in the
        expected set for that workflow. expected_rank is computed from
        top_candidates if available.

        Returns a WorkflowEvaluation with per-item ActionEvaluation
        and TriggerEvaluation results.
        """
        action_results = self._evaluate_actions(
            extracted_actions, set(expected.expected_actions)
        )
        trigger_results = self._evaluate_triggers(
            extracted_triggers, set(expected.expected_triggers)
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
        and computes aggregate metrics including MRR.
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
            mean_reciprocal_rank_actions=calculate_mean_reciprocal_rank_actions(all_actions),
            mean_reciprocal_rank_triggers=calculate_mean_reciprocal_rank_triggers(all_triggers),
            workflow_results=workflow_evaluations,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _evaluate_actions(
        self,
        extracted: list[ExtractedAction],
        expected_set: set[str],
    ) -> list[ActionEvaluation]:
        results: list[ActionEvaluation] = []

        for ext in extracted:
            # Find rank of expected match in candidate list (1-based)
            expected_rank = self._find_expected_rank(ext.top_candidates, expected_set)

            # Convert raw retriever candidates to RankingCandidate models
            ranking = self._to_ranking_candidates(ext.top_candidates)

            # Set-based correctness: predicted is in expected set
            correct = (
                ext.predicted_name in expected_set
                if ext.predicted_name is not None
                else False
            )

            # Best matching expected action for display (first found in candidates, else first in set)
            matched_expected = (
                ext.predicted_name
                if ext.predicted_name in expected_set
                else next(iter(expected_set), "")
            )

            results.append(
                ActionEvaluation(
                    extracted_action=ext.extracted_name,
                    expected_action=matched_expected,
                    predicted_action=ext.predicted_name,
                    similarity_score=ext.similarity_score,
                    correct=correct,
                    expected_rank=expected_rank,
                    top_candidates=ranking,
                )
            )

        return results

    def _evaluate_triggers(
        self,
        extracted: list[ExtractedTrigger],
        expected_set: set[str],
    ) -> list[TriggerEvaluation]:
        results: list[TriggerEvaluation] = []

        for ext in extracted:
            expected_rank = self._find_expected_rank(ext.top_candidates, expected_set)
            ranking = self._to_ranking_candidates(ext.top_candidates)

            correct = (
                ext.predicted_name in expected_set
                if ext.predicted_name is not None
                else False
            )

            matched_expected = (
                ext.predicted_name
                if ext.predicted_name in expected_set
                else next(iter(expected_set), "")
            )

            results.append(
                TriggerEvaluation(
                    extracted_trigger=ext.extracted_name,
                    expected_trigger=matched_expected,
                    predicted_trigger=ext.predicted_name,
                    similarity_score=ext.similarity_score,
                    correct=correct,
                    expected_rank=expected_rank,
                    top_candidates=ranking,
                )
            )

        return results

    @staticmethod
    def _find_expected_rank(candidates: list, expected_set: set[str]) -> int | None:
        """
        Return 1-based rank of the first candidate whose name is in expected_set.
        Returns None if not found in the candidates list.
        """
        for rank, candidate in enumerate(candidates, start=1):
            name = getattr(candidate, "name", None) or getattr(
                getattr(candidate, "entity", None), "name", None
            )
            if name in expected_set:
                return rank
        return None

    @staticmethod
    def _to_ranking_candidates(candidates: list) -> list[RankingCandidate]:
        """
        Convert raw retriever RankedCandidate objects to RankingCandidate models.
        Handles both RankedCandidate dataclass objects and plain dicts.
        """
        result = []
        for c in candidates:
            # Support RankedCandidate dataclass from app.retrieval.models
            if hasattr(c, "entity"):
                result.append(
                    RankingCandidate(
                        name=c.entity.name,
                        rrf_score=float(c.rrf_score),
                        vector_rank=c.vector_rank,
                        bm25_rank=c.bm25_rank,
                        postgres_rank=c.postgres_rank,
                    )
                )
            elif isinstance(c, dict):
                result.append(
                    RankingCandidate(
                        name=c.get("name", ""),
                        rrf_score=float(c.get("rrf_score", 0.0)),
                        vector_rank=c.get("vector_rank"),
                        bm25_rank=c.get("bm25_rank"),
                        postgres_rank=c.get("postgres_rank"),
                    )
                )
        return result
