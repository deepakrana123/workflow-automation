"""
app/evaluation_runner/report.py

Console report generators for evaluation runs.
"""

from __future__ import annotations
from sqlalchemy.orm import Session

from app.models.retrieval_eval import EvaluationRun, EvaluationResult, EvaluationCase, EvaluationCandidate
from app.evaluation_runner.metrics import aggregate, CaseMetrics


def _load_metrics(db: Session, run: EvaluationRun) -> list[CaseMetrics]:
    from app.evaluation_runner.metrics import CaseMetrics
    results = db.query(EvaluationResult).filter(EvaluationResult.run_id == run.id).all()
    return [
        CaseMetrics(
            correct_rank=r.correct_rank,
            reciprocal_rank=r.reciprocal_rank,
            recall_at_1=r.recall_at_1,
            recall_at_3=r.recall_at_3,
            recall_at_5=r.recall_at_5,
            recall_at_8=r.recall_at_8,
            accepted=r.accepted,
            diagnostic_classification=r.diagnostic_classification,
            cross_encoder_score=r.cross_encoder_score,
            final_confidence=r.final_confidence,
        )
        for r in results
    ]


def print_aggregate(db: Session, run_name: str) -> None:
    run = db.query(EvaluationRun).filter(EvaluationRun.name == run_name).first()
    if run is None:
        print(f"Run '{run_name}' not found.")
        return

    metrics = _load_metrics(db, run)
    agg = aggregate(metrics)

    W = 56
    print(f"\n{'═' * W}")
    print(f"  Evaluation Run: {run.name}")
    print(f"  Model:  {run.embedding_model or '—'}")
    print(f"  Query:  {run.query_strategy or '—'}  |  Embed: {run.embedding_input_strategy or '—'}")
    print(f"  Top-K:  {run.top_k or '—'}  |  Threshold: {run.threshold or '—'}")
    print(f"{'─' * W}")
    print(f"  {'Total cases':<30} {agg.total_cases}")
    print(f"  {'Catalog missing':<30} {agg.catalog_missing}")
    print(f"  {'Evaluated':<30} {agg.evaluated}")
    print(f"{'─' * W}")
    print(f"  {'Recall@1':<30} {agg.recall_1 * 100:.1f}%")
    print(f"  {'Recall@3':<30} {agg.recall_3 * 100:.1f}%")
    print(f"  {'Recall@5':<30} {agg.recall_5 * 100:.1f}%")
    print(f"  {'Recall@8':<30} {agg.recall_8 * 100:.1f}%")
    print(f"  {'MRR':<30} {agg.mrr:.4f}")
    print(f"  {'Acceptance rate':<30} {agg.acceptance_rate * 100:.1f}%")
    print(f"{'─' * W}")
    print(f"  Classification breakdown:")
    for cls, count in sorted(agg.by_classification.items(), key=lambda x: -x[1]):
        print(f"    {cls:<35} {count}")
    print(f"{'═' * W}\n")


def print_per_case(db: Session, run_name: str, top_k_display: int = 5) -> None:
    run = db.query(EvaluationRun).filter(EvaluationRun.name == run_name).first()
    if run is None:
        print(f"Run '{run_name}' not found.")
        return

    results = (
        db.query(EvaluationResult)
        .filter(EvaluationResult.run_id == run.id)
        .all()
    )

    case_map = {c.id: c for c in db.query(EvaluationCase).all()}

    print(f"\nPer-case diagnostics — run: {run.name}\n")

    for r in results:
        case = case_map.get(r.case_id)
        if not case:
            continue

        mark = "✓" if r.diagnostic_classification == "ACCEPTED" else "⚠"
        print(f"  [{mark}] {case.brd_action}")
        print(f"       Expected : {case.expected_action_name or 'CATALOG_MISSING'}")
        print(f"       Status   : {r.diagnostic_classification}")
        if r.correct_rank is not None:
            print(f"       Rank     : {r.correct_rank}   RR={r.reciprocal_rank:.3f}")
        if r.final_confidence is not None:
            print(f"       Conf     : {r.final_confidence:.4f}")

        candidates = (
            db.query(EvaluationCandidate)
            .filter(EvaluationCandidate.result_id == r.id)
            .order_by(EvaluationCandidate.rank)
            .limit(top_k_display)
            .all()
        )

        if candidates:
            print(f"       Top-{top_k_display} candidates:")
            for c in candidates:
                marker = " ◀" if c.action_definition_id == case.expected_action_definition_id else ""
                ce = f"  ce={c.cross_encoder_score:.3f}" if c.cross_encoder_score is not None else ""
                print(f"         {c.rank:>2}. {c.action_name:<40} rrf={c.rrf_score:.4f}{ce}{marker}")
        print()


def print_compare(db: Session, run_name_a: str, run_name_b: str) -> None:
    run_a = db.query(EvaluationRun).filter(EvaluationRun.name == run_name_a).first()
    run_b = db.query(EvaluationRun).filter(EvaluationRun.name == run_name_b).first()

    if run_a is None or run_b is None:
        missing = run_name_a if run_a is None else run_name_b
        print(f"Run '{missing}' not found.")
        return

    ma = aggregate(_load_metrics(db, run_a))
    mb = aggregate(_load_metrics(db, run_b))

    W = 64
    print(f"\n{'═' * W}")
    print(f"  Comparison")
    print(f"  A: {run_name_a}")
    print(f"  B: {run_name_b}")
    print(f"{'─' * W}")
    print(f"  {'Metric':<25} {'A':>10} {'B':>10} {'Δ':>10}")
    print(f"{'─' * W}")

    def row(label, a, b, pct=True):
        delta = b - a
        if pct:
            print(f"  {label:<25} {a*100:>9.1f}% {b*100:>9.1f}% {delta*100:>+9.1f}%")
        else:
            print(f"  {label:<25} {a:>10.4f} {b:>10.4f} {delta:>+10.4f}")

    row("Recall@1", ma.recall_1, mb.recall_1)
    row("Recall@3", ma.recall_3, mb.recall_3)
    row("Recall@5", ma.recall_5, mb.recall_5)
    row("Recall@8", ma.recall_8, mb.recall_8)
    row("MRR",     ma.mrr,      mb.mrr, pct=False)
    row("Acceptance",ma.acceptance_rate, mb.acceptance_rate)
    print(f"{'═' * W}\n")
