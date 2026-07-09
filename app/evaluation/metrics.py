"""
app/evaluation/metrics.py

Pure utility functions for computing evaluation metrics.

All functions are stateless, side-effect-free, and contain no database logic.
They operate only on the evaluation model types from models.py.
"""

from app.evaluation.models import ActionEvaluation, TriggerEvaluation


def calculate_action_accuracy(action_results: list[ActionEvaluation]) -> float:
    """
    Fraction of action evaluations where predicted_action is correct
    (set-based: predicted is in the expected set for the workflow).

    Returns 0.0 if the list is empty.
    """
    if not action_results:
        return 0.0
    correct = sum(1 for r in action_results if r.correct)
    return correct / len(action_results)


def calculate_trigger_accuracy(trigger_results: list[TriggerEvaluation]) -> float:
    """
    Fraction of trigger evaluations where predicted_trigger is correct.

    Returns 0.0 if the list is empty.
    """
    if not trigger_results:
        return 0.0
    correct = sum(1 for r in trigger_results if r.correct)
    return correct / len(trigger_results)


def calculate_average_similarity(
    action_results: list[ActionEvaluation],
    trigger_results: list[TriggerEvaluation],
) -> float:
    """
    Mean RRF score of the top candidate across all action and trigger evaluations
    that have a non-None similarity_score.

    Returns 0.0 if no scored entries exist.
    """
    scores = [
        r.similarity_score
        for r in action_results
        if r.similarity_score is not None
    ] + [
        r.similarity_score
        for r in trigger_results
        if r.similarity_score is not None
    ]
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def count_unknown_actions(action_results: list[ActionEvaluation]) -> int:
    """
    Count of action evaluations where no catalog match was found
    (predicted_action is None).
    """
    return sum(1 for r in action_results if r.predicted_action is None)


def count_unknown_triggers(trigger_results: list[TriggerEvaluation]) -> int:
    """
    Count of trigger evaluations where no catalog match was found
    (predicted_trigger is None).
    """
    return sum(1 for r in trigger_results if r.predicted_trigger is None)


def calculate_mean_reciprocal_rank_actions(
    action_results: list[ActionEvaluation],
) -> float:
    """
    Mean Reciprocal Rank (MRR) for action retrieval.

    For each query, reciprocal rank = 1 / expected_rank if the expected action
    appeared in the candidates list, else 0.
    MRR = mean of all reciprocal ranks.

    Returns 0.0 if the list is empty.
    """
    if not action_results:
        return 0.0
    rr_sum = 0.0
    for r in action_results:
        if r.expected_rank is not None:
            rr_sum += 1.0 / r.expected_rank
    return rr_sum / len(action_results)


def calculate_mean_reciprocal_rank_triggers(
    trigger_results: list[TriggerEvaluation],
) -> float:
    """
    Mean Reciprocal Rank (MRR) for trigger retrieval.

    Returns 0.0 if the list is empty.
    """
    if not trigger_results:
        return 0.0
    rr_sum = 0.0
    for r in trigger_results:
        if r.expected_rank is not None:
            rr_sum += 1.0 / r.expected_rank
    return rr_sum / len(trigger_results)
