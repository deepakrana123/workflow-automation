"""
app/evaluation_runner/metrics.py

Pure metric calculation functions — no DB, no side effects.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class CaseMetrics:
    correct_rank: int | None
    reciprocal_rank: float
    recall_at_1: bool
    recall_at_3: bool
    recall_at_5: bool
    recall_at_8: bool
    accepted: bool
    diagnostic_classification: str
    cross_encoder_score: float | None = None
    final_confidence: float | None = None


@dataclass
class AggregateMetrics:
    total_cases: int
    catalog_missing: int
    evaluated: int          # cases with known expected action
    recall_1: float
    recall_3: float
    recall_5: float
    recall_8: float
    mrr: float
    acceptance_rate: float
    by_classification: dict[str, int] = field(default_factory=dict)


def compute_case_metrics(
    candidates: list[dict],          # list of {id, name, rrf_score, cross_encoder_score, ...}
    expected_action_id: int | None,
    accepted_id: int | None,         # action_definition_id of the accepted candidate (or None)
    accepted_confidence: float | None,
    accepted_cross_encoder: float | None,
) -> CaseMetrics:
    """
    Compute per-case metrics from the full ranked candidate list.

    candidates — ordered list (rank 1 first), each with at minimum:
        {action_definition_id, rrf_score, cross_encoder_score (optional)}
    """
    if expected_action_id is None:
        return CaseMetrics(
            correct_rank=None,
            reciprocal_rank=0.0,
            recall_at_1=False,
            recall_at_3=False,
            recall_at_5=False,
            recall_at_8=False,
            accepted=accepted_id is not None,
            diagnostic_classification="CATALOG_MISSING",
            cross_encoder_score=accepted_cross_encoder,
            final_confidence=accepted_confidence,
        )

    # Find rank of expected action in candidates (1-based)
    correct_rank: int | None = None
    for i, c in enumerate(candidates, start=1):
        if c.get("action_definition_id") == expected_action_id:
            correct_rank = i
            break

    reciprocal_rank = (1.0 / correct_rank) if correct_rank is not None else 0.0
    r1 = correct_rank is not None and correct_rank <= 1
    r3 = correct_rank is not None and correct_rank <= 3
    r5 = correct_rank is not None and correct_rank <= 5
    r8 = correct_rank is not None and correct_rank <= 8

    accepted = accepted_id is not None

    # Diagnostic classification
    if accepted and accepted_id == expected_action_id:
        classification = "ACCEPTED"
    elif correct_rank is None:
        classification = "RETRIEVAL_MISS"
    elif accepted and accepted_id != expected_action_id:
        # retrieved but wrong action was accepted → ranking failure
        classification = "RANKING_FAILURE"
    elif not accepted and correct_rank is not None and correct_rank <= 1:
        # top-1 was the right answer but was rejected → threshold failure
        classification = "THRESHOLD_FAILURE"
    elif not accepted and correct_rank is not None:
        # retrieved but not ranked at top → ranking issue + rejection
        classification = "TOP_K_RETRIEVED_BUT_REJECTED"
    else:
        classification = "UNKNOWN"

    return CaseMetrics(
        correct_rank=correct_rank,
        reciprocal_rank=reciprocal_rank,
        recall_at_1=r1,
        recall_at_3=r3,
        recall_at_5=r5,
        recall_at_8=r8,
        accepted=accepted,
        diagnostic_classification=classification,
        cross_encoder_score=accepted_cross_encoder,
        final_confidence=accepted_confidence,
    )


def aggregate(results: list[CaseMetrics]) -> AggregateMetrics:
    """Aggregate a list of per-case metrics into a run-level summary."""
    total = len(results)
    catalog_missing = sum(1 for r in results if r.diagnostic_classification == "CATALOG_MISSING")
    evaluated = [r for r in results if r.diagnostic_classification != "CATALOG_MISSING"]
    n = len(evaluated)

    if n == 0:
        return AggregateMetrics(
            total_cases=total,
            catalog_missing=catalog_missing,
            evaluated=0,
            recall_1=0, recall_3=0, recall_5=0, recall_8=0,
            mrr=0, acceptance_rate=0,
        )

    by_class: dict[str, int] = {}
    for r in results:
        by_class[r.diagnostic_classification] = by_class.get(r.diagnostic_classification, 0) + 1

    return AggregateMetrics(
        total_cases=total,
        catalog_missing=catalog_missing,
        evaluated=n,
        recall_1=sum(1 for r in evaluated if r.recall_at_1) / n,
        recall_3=sum(1 for r in evaluated if r.recall_at_3) / n,
        recall_5=sum(1 for r in evaluated if r.recall_at_5) / n,
        recall_8=sum(1 for r in evaluated if r.recall_at_8) / n,
        mrr=sum(r.reciprocal_rank for r in evaluated) / n,
        acceptance_rate=sum(1 for r in evaluated if r.accepted) / n,
        by_classification=by_class,
    )
