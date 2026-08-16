"""
scripts/evaluate.py

Retrieval evaluation CLI.

Commands:
  import-cases              Import seed evaluation cases into the DB
  evaluate --run-name NAME  Run one evaluation experiment
  report   --run-name NAME  Print aggregate + per-case report for a run
  compare  --run-a A --run-b B  Compare two runs side by side
  list                      List all evaluation runs

Usage examples:
  .venv\\Scripts\\python.exe -m scripts.evaluate import-cases
  .venv\\Scripts\\python.exe -m scripts.evaluate evaluate --run-name baseline-name-only
  .venv\\Scripts\\python.exe -m scripts.evaluate report   --run-name baseline-name-only
  .venv\\Scripts\\python.exe -m scripts.evaluate compare  --run-a baseline-name-only --run-b v2-with-description
  .venv\\Scripts\\python.exe -m scripts.evaluate list
"""

import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure the project root is on sys.path regardless of how the script is invoked
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

load_dotenv()

# Ensure all SQLAlchemy models are registered before any query is made
import app.db.base  # noqa: F401 — side-effect: registers all models with Base

from app.db.session import SessionLocal
from app.evaluation_runner.importer import import_cases
from app.evaluation_runner.report import print_aggregate, print_per_case, print_compare
from app.models.retrieval_eval import EvaluationRun


def _build_pipeline(db):
    from app.knowledge_ingestions.workflow_repository import WorkflowRepository
    from app.retrieval.vector_retriever import VectorRetriever
    from app.retrieval.keyword_retriever import KeywordRetriever
    from app.retrieval.postgress_retriever import PostgressRetriever
    from app.retrieval.reciprocal_rank_fusion import ReciprocalRankFusion
    from app.retrieval.cross_encoder import CrossEncoderReRanker
    from app.retrieval.decision_engine import MappingDecisionEngine
    from app.retrieval.confidene_estimator import ConfidenceEstimator
    from app.retrieval.thresholds import RetrievalThresholds
    from app.retrieval.unknown_detector import UnkownDetetor
    from app.retrieval.pipeline import RetrievalPipeline

    repo = WorkflowRepository(db)
    return RetrievalPipeline(
        vector_retriever   = VectorRetriever(repo),
        keyword_retriever  = KeywordRetriever(repo),
        postgres_retriever = PostgressRetriever(repo),
        rrf                = ReciprocalRankFusion(),
        cross_encoder      = CrossEncoderReRanker(),
        decision_engine    = MappingDecisionEngine(
            confidene_estimator = ConfidenceEstimator(),
            thresholds          = RetrievalThresholds(),
            unknown_detector    = UnkownDetetor(),
        ),
    )


def cmd_import(args):
    db = SessionLocal()
    try:
        csv_text = None
        if args.csv:
            p = Path(args.csv)
            if not p.exists():
                print(f"CSV file not found: {p}")
                sys.exit(1)
            csv_text = p.read_text(encoding="utf-8")

        result = import_cases(db, csv_text=csv_text, skip_existing=not args.replace)
        print(f"Import complete:")
        print(f"  Imported       : {result['imported']}")
        print(f"  Skipped        : {result['skipped']}")
        print(f"  Catalog missing: {result['catalog_missing']}")
    finally:
        db.close()


def cmd_evaluate(args):
    db = SessionLocal()
    try:
        print(f"Building retrieval pipeline...")
        pipeline = _build_pipeline(db)

        from app.evaluation_runner.service import EvaluationService
        svc = EvaluationService(db=db, pipeline=pipeline)

        print(f"Running evaluation: {args.run_name}")
        agg = svc.run(run_name=args.run_name, top_k=args.top_k)

        print(f"\nRun complete.")
        print_aggregate(db, args.run_name)

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        db.close()


def cmd_report(args):
    db = SessionLocal()
    try:
        print_aggregate(db, args.run_name)
        if not args.summary_only:
            print_per_case(db, args.run_name, top_k_display=args.top_k)
    finally:
        db.close()


def cmd_compare(args):
    db = SessionLocal()
    try:
        print_compare(db, args.run_a, args.run_b)
        print_aggregate(db, args.run_a)
        print_aggregate(db, args.run_b)
    finally:
        db.close()


def cmd_list(args):
    db = SessionLocal()
    try:
        runs = db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).all()
        if not runs:
            print("No evaluation runs yet.")
            return
        print(f"\n{'ID':<6} {'Name':<40} {'Created'}")
        print("─" * 70)
        for r in runs:
            print(f"  {r.id:<4} {r.name:<40} {r.created_at.strftime('%Y-%m-%d %H:%M')}")
        print()
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        prog="evaluate",
        description="MFlows retrieval evaluation CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # import-cases
    p_import = sub.add_parser("import-cases", help="Import evaluation cases")
    p_import.add_argument("--csv",     default=None, help="Path to CSV file (default: built-in seed)")
    p_import.add_argument("--replace", action="store_true", help="Re-import even if case already exists")

    # evaluate
    p_eval = sub.add_parser("evaluate", help="Run one evaluation experiment")
    p_eval.add_argument("--run-name", required=True, help="Unique name for this run")
    p_eval.add_argument("--top-k",   type=int, default=20, help="Top-K candidates to retrieve (default: 20)")

    # report
    p_report = sub.add_parser("report", help="Print report for a run")
    p_report.add_argument("--run-name",     required=True)
    p_report.add_argument("--top-k",        type=int, default=5, help="Candidates to show per case")
    p_report.add_argument("--summary-only", action="store_true", help="Skip per-case detail")

    # compare
    p_compare = sub.add_parser("compare", help="Compare two runs")
    p_compare.add_argument("--run-a", required=True)
    p_compare.add_argument("--run-b", required=True)

    # list
    sub.add_parser("list", help="List all evaluation runs")

    args = parser.parse_args()

    dispatch = {
        "import-cases": cmd_import,
        "evaluate":     cmd_evaluate,
        "report":       cmd_report,
        "compare":      cmd_compare,
        "list":         cmd_list,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
