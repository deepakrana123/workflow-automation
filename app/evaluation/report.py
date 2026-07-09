# -*- coding: utf-8 -*-
"""
app/evaluation/report.py

Console reporter for EvaluationReport.

Formats and prints a human-readable evaluation summary including ranking
breakdown (vector/BM25/Postgres ranks and RRF scores) and MRR.
"""

from app.evaluation.models import EvaluationReport, WorkflowEvaluation


# Number of top candidates to show in the ranking breakdown
_TOP_N_DISPLAY = 5


def print_report(report: EvaluationReport) -> None:
    """
    Pretty-print an EvaluationReport to stdout.

    Sections printed:
      1. Aggregate metrics (accuracy, MRR, avg similarity, unknowns)
      2. Per-workflow accuracy breakdown
      3. Per-workflow detailed ranking tables (with ✓/✗ per item)
    """
    W = 70
    sep  = "═" * W
    dash = "─" * W
    thin = "─" * W

    # ── 1. Aggregate metrics ──────────────────────────────────────────────────
    print(f"\n{sep}")
    print(f"  MFlows Evaluation Report")
    print(sep)
    print(f"  {'Workflows':<28} {report.total_workflows}")
    print(f"  {'Actions evaluated':<28} {report.total_actions}")
    print(f"  {'Triggers evaluated':<28} {report.total_triggers}")
    print(f"  {dash}")
    print(f"  {'Action Accuracy':<28} {report.action_accuracy * 100:.1f}%")
    print(f"  {'Trigger Accuracy':<28} {report.trigger_accuracy * 100:.1f}%")
    print(f"  {'Action MRR':<28} {report.mean_reciprocal_rank_actions:.3f}")
    print(f"  {'Trigger MRR':<28} {report.mean_reciprocal_rank_triggers:.3f}")
    print(f"  {'Avg RRF Score (top-1)':<28} {report.average_similarity:.4f}")
    print(f"  {dash}")
    print(f"  {'Unknown Actions':<28} {report.unknown_actions}")
    print(f"  {'Unknown Triggers':<28} {report.unknown_triggers}")
    print(sep)

    if not report.workflow_results:
        return

    # ── 2. Per-workflow accuracy summary ──────────────────────────────────────
    print()
    print(f"  Per-Workflow Accuracy")
    print(sep)

    for wf in report.workflow_results:
        total_a = len(wf.action_results)
        correct_a = sum(1 for r in wf.action_results if r.correct)
        pct_a = correct_a / total_a * 100 if total_a else 0.0

        total_t = len(wf.trigger_results)
        correct_t = sum(1 for r in wf.trigger_results if r.correct)
        pct_t = correct_t / total_t * 100 if total_t else 0.0

        print(f"  Workflow: {wf.workflow_name}")
        print(
            f"    Actions  : {total_a:>3}  │  Correct: {correct_a:>3}  │  "
            f"Accuracy: {pct_a:.1f}%"
        )
        print(
            f"    Triggers : {total_t:>3}  │  Correct: {correct_t:>3}  │  "
            f"Accuracy: {pct_t:.1f}%"
        )
        print()

    print(sep)

    # ── 3. Detailed ranking tables per workflow ───────────────────────────────
    print()
    print(f"  Detailed Ranking Breakdown  (top-{_TOP_N_DISPLAY} candidates per query)")
    print(sep)

    for wf in report.workflow_results:
        _print_workflow_ranking(wf)

    print(sep)


def _print_workflow_ranking(wf: WorkflowEvaluation) -> None:
    W = 70
    sep  = "═" * W
    thin = "─" * W

    print(f"\n  ┌{'─' * 68}┐")
    print(f"  │  Workflow: {wf.workflow_name:<56}│")
    print(f"  └{'─' * 68}┘")

    # ── Triggers ─────────────────────────────────────────────────────────────
    if wf.trigger_results:
        print(f"\n  TRIGGERS")
        print(f"  {thin}")

        for r in wf.trigger_results:
            mark = "✓" if r.correct else "✗"
            score_str = f"{r.similarity_score:.4f}" if r.similarity_score is not None else "  n/a"
            rank_str  = f"rank {r.expected_rank}" if r.expected_rank is not None else "not in top-N"

            print(
                f"  [{mark}] Extracted : {r.extracted_trigger}"
            )
            print(
                f"      Predicted : {r.predicted_trigger or 'NOT MATCHED':<30}  "
                f"RRF={score_str}  │  expected @ {rank_str}"
            )

            if r.top_candidates:
                _print_candidates(r.top_candidates, expected_name=r.expected_trigger)

            print()

    # ── Actions ──────────────────────────────────────────────────────────────
    if wf.action_results:
        print(f"  ACTIONS")
        print(f"  {thin}")

        for r in wf.action_results:
            mark = "✓" if r.correct else "✗"
            score_str = f"{r.similarity_score:.4f}" if r.similarity_score is not None else "  n/a"
            rank_str  = f"rank {r.expected_rank}" if r.expected_rank is not None else "not in top-N"

            print(
                f"  [{mark}] Extracted : {r.extracted_action}"
            )
            print(
                f"      Predicted : {r.predicted_action or 'NOT MATCHED':<30}  "
                f"RRF={score_str}  │  expected @ {rank_str}"
            )

            if r.top_candidates:
                _print_candidates(r.top_candidates, expected_name=r.expected_action)

            print()


def _print_candidates(candidates, expected_name: str) -> None:
    """Print top-N candidates in a compact ranked table."""
    print(
        f"      {'#':<4} {'Name':<35} {'RRF':>7}  {'Vec':>5}  {'BM25':>5}  {'PG':>5}"
    )
    print(f"      {'─'*4} {'─'*35} {'─'*7}  {'─'*5}  {'─'*5}  {'─'*5}")

    for i, c in enumerate(candidates[:_TOP_N_DISPLAY], start=1):
        marker = "◀" if c.name == expected_name else " "
        vec_r  = str(c.vector_rank)   if c.vector_rank   is not None else "  -"
        bm25_r = str(c.bm25_rank)     if c.bm25_rank     is not None else "  -"
        pg_r   = str(c.postgres_rank) if c.postgres_rank is not None else "  -"

        print(
            f"      {i:<4} {c.name:<35} {c.rrf_score:>7.4f}  {vec_r:>5}  {bm25_r:>5}  {pg_r:>5}  {marker}"
        )
