"""
scripts/test_retriever.py

Hybrid Retrieval Pipeline Test Script.

Tests the full retrieval pipeline end-to-end:
  1. Wires up VectorRetriever + KeywordRetriever + PostgresRetriever + RRF
  2. Embeds a query using SentenceTransformer (BAAI/bge-small-en-v1.5)
  3. Runs search_actions and search_triggers through HybridRetriever
  4. Prints a ranked result table showing per-source ranks and RRF score

Also runs test_extractor evaluation (embedding mapper quality check) if --evaluate is passed.

Run:
    .venv\\Scripts\\python.exe scripts/test_retriever.py
    .venv\\Scripts\\python.exe scripts/test_retriever.py --query "send email to customer"
    .venv\\Scripts\\python.exe scripts/test_retriever.py --query "loan application received" --limit 5
    .venv\\Scripts\\python.exe scripts/test_retriever.py --evaluate
    .venv\\Scripts\\python.exe scripts/test_retriever.py --query "check credit score" --evaluate
"""

import argparse
import sys
from dotenv import load_dotenv

load_dotenv()

from app.db.session import SessionLocal
from app.knowledge_ingestions.workflow_repository import WorkflowRepository
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.vector_retriever import VectorRetriever
from app.retrieval.keyword_retriever import KeywordRetriever
from app.retrieval.postgress_retriever import PostgressRetriever
from app.retrieval.reciprocal_rank_fusion import ReciprocalRankFusion
from app.retrieval.models import RankedCandidate


# ── Formatting helpers ────────────────────────────────────────────────────────

def _rank_str(rank: int | None) -> str:
    return f"#{rank}" if rank is not None else "  -"


def print_results_table(
    results: list[RankedCandidate],
    title: str,
    limit: int,
) -> None:
    print(f"\n{'─' * 80}")
    print(f"  {title}  (top {limit})")
    print(f"{'─' * 80}")

    if not results:
        print("  No results found.")
        return

    header = f"  {'#':<4} {'Name':<40} {'Display':<30} {'Vec':>5} {'BM25':>5} {'PG':>5} {'RRF':>8}"
    print(header)
    print(f"  {'─'*3} {'─'*39} {'─'*29} {'─'*5} {'─'*5} {'─'*5} {'─'*8}")

    for i, r in enumerate(results[:limit], start=1):
        entity = r.entity
        name = (entity.name or "")[:39]
        display = (entity.display_name or "")[:29]
        vec  = _rank_str(r.vector_rank)
        bm25 = _rank_str(r.bm25_rank)
        pg   = _rank_str(r.postgres_rank)
        rrf  = f"{r.rrf_score:.5f}"
        print(f"  {i:<4} {name:<40} {display:<30} {vec:>5} {bm25:>5} {pg:>5} {rrf:>8}")


# ── Retrieval test ────────────────────────────────────────────────────────────

def run_retrieval_test(query: str, limit: int) -> None:
    print(f"\n{'=' * 80}")
    print(f"  Hybrid Retrieval Test")
    print(f"  Query : \"{query}\"")
    print(f"  Limit : {limit}")
    print(f"{'=' * 80}")

    db = SessionLocal()
    try:
        repo = WorkflowRepository(db)

        print("\n[1] Building retrievers...")
        vector_ret  = VectorRetriever(repo)
        keyword_ret = KeywordRetriever(repo)
        postgres_ret = PostgressRetriever(repo)
        rrf = ReciprocalRankFusion()

        print("[2] Loading SentenceTransformer model (BAAI/bge-small-en-v1.5)...")
        retriever = HybridRetriever(
            vector_retriever=vector_ret,
            keyword_retriever=keyword_ret,
            postgress_retriever=postgres_ret,
            rrf=rrf,
        )

        print(f"[3] Embedding query...")
        embedding = retriever.embed(query)
        print(f"    Embedding dim : {len(embedding)}")

        print(f"[4] Searching actions...")
        action_results = retriever.search_actions(query, embedding, limit=limit)
        print(f"    Candidates fused : {len(action_results)}")

        print(f"[5] Searching triggers...")
        trigger_results = retriever.search_triggers(query, embedding, limit=limit)
        print(f"    Candidates fused : {len(trigger_results)}")

        print_results_table(action_results,  "ACTIONS  — ranked by RRF score", limit)
        print_results_table(trigger_results, "TRIGGERS — ranked by RRF score", limit)

    except Exception as e:
        print(f"\n❌ Retrieval test failed: {type(e).__name__}: {e}")
        raise
    finally:
        db.close()


# ── Embedding mapper evaluation (reuses test_extractor logic) ─────────────────

def run_embedding_evaluation() -> None:
    """
    Delegates to the evaluation logic in test_extractor.
    Loads all workflows from DB and prints per-workflow mapping tables.
    Add GROUND_TRUTH entries in test_extractor.py to also see accuracy metrics.
    """
    print(f"\n{'=' * 80}")
    print(f"  Embedding Mapper Evaluation  (from test_extractor)")
    print(f"{'=' * 80}")

    # Import lazily so retrieval test still works if extractor deps are missing
    try:
        from scripts.test_extractor import run_evaluation
    except ImportError as e:
        print(f"❌ Could not import test_extractor: {e}")
        return

    run_evaluation(workflow_knowledge_ids=None)


# ── Main ──────────────────────────────────────────────────────────────────────

DEFAULT_QUERIES = [
    "send email notification to customer",
    "run credit check",
    "loan application received",
    "generate loan offer document",
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MFlows Hybrid Retrieval Pipeline Test"
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help=(
            "Query string to test retrieval with. "
            f"If omitted, runs {len(DEFAULT_QUERIES)} default queries."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of top results to display per search (default: 10)",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Also run embedding mapper evaluation (test_extractor logic)",
    )
    args = parser.parse_args()

    queries = [args.query] if args.query else DEFAULT_QUERIES

    for q in queries:
        run_retrieval_test(q, args.limit)

    if args.evaluate:
        run_embedding_evaluation()

    print(f"\n{'=' * 80}")
    print("  Done.")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
