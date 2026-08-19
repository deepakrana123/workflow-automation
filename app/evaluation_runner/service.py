"""
app/evaluation_runner/service.py

EvaluationService — runs one evaluation experiment.

Uses the existing RetrievalPipeline (retrieve_actions / retrieve_triggers)
without modifying production retrieval behavior.

Flow per case:
  1. Build query + embedding from brd_action (using current production strategy)
  2. Call pipeline.retrieve_actions() — full top-K, no decision filter
  3. Apply decision engine to find accepted candidate
  4. Compute metrics
  5. Persist results + candidates to DB
"""

from __future__ import annotations
import math

from sqlalchemy.orm import Session

from app.models.retrieval_eval import (
    EvaluationCase,
    EvaluationRun,
    EvaluationResult,
    EvaluationCandidate,
)
from app.models.action_definitions import ActionDefinition
from app.evaluation_runner.metrics import compute_case_metrics, aggregate, AggregateMetrics
from app.retrieval.pipeline import RetrievalPipeline
from app.retrieval.thresholds import RetrievalType
from app.retrieval.confidene_estimator import ConfidenceEstimator
from app.core.logger import logger
from sentence_transformers import SentenceTransformer

_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


class EvaluationService:

    def __init__(self, db: Session, pipeline: RetrievalPipeline):
        self.db       = db
        self.pipeline = pipeline
        self._model   = SentenceTransformer(_EMBEDDING_MODEL)
        self._confidence_estimator = ConfidenceEstimator()

    def run(self, run_name: str, top_k: int = 20,
    embedding_variant: str = "name_only",) -> AggregateMetrics:
        """Execute one full evaluation run against all evaluation_cases."""
        # Create or retrieve the run record
        if embedding_variant not in {"name_only", "name_description"}:
            raise ValueError(
                f"Unknown embedding variant: {embedding_variant}"
            )
        run = self.db.query(EvaluationRun).filter(EvaluationRun.name == run_name).first()
        if run is not None:
            raise ValueError(
                f"A run named '{run_name}' already exists (id={run.id}). "
                "Use a different name for each experiment."
            )

        run = EvaluationRun(
            name=run_name,
            embedding_model=_EMBEDDING_MODEL,
            embedding_input_strategy=embedding_variant,
            query_strategy="name_description",
            top_k=top_k,
            threshold=0.65,
        )
        self.db.add(run)
        self.db.flush()

        cases = self.db.query(EvaluationCase).all()
        if not cases:
            raise ValueError("No evaluation cases found. Import cases first with --import-cases.")

        case_metrics_list = []

        for case in cases:
            metrics = self._run_one_case(run, case, top_k,embedding_variant)
            case_metrics_list.append(metrics)

        self.db.commit()

        agg = aggregate(case_metrics_list)
        logger.info(
            "evaluation_run_complete",
            extra={"extra_data": {
                "run_name": run_name,
                "evaluated": agg.evaluated,
                "recall_5": round(agg.recall_5, 3),
                "mrr": round(agg.mrr, 3),
            }},
        )
        return agg,

    def _run_one_case(self, run: EvaluationRun, case: EvaluationCase, top_k: int,embedding_variant):
        from app.evaluation_runner.metrics import CaseMetrics

        # CATALOG_MISSING — skip retrieval, store placeholder result
        if case.expected_action_definition_id is None:
            result = EvaluationResult(
                run_id=run.id,
                case_id=case.id,
                correct_rank=None,
                reciprocal_rank=0.0,
                recall_at_1=False, recall_at_3=False, recall_at_5=False, recall_at_8=False,
                accepted=False,
                diagnostic_classification="CATALOG_MISSING",
            )
            self.db.add(result)
            self.db.flush()
            return CaseMetrics(
                correct_rank=None, reciprocal_rank=0.0,
                recall_at_1=False, recall_at_3=False, recall_at_5=False, recall_at_8=False,
                accepted=False, diagnostic_classification="CATALOG_MISSING",
            )

        # Build query + embedding (production strategy: name_only for embedding,
        # name + description for BM25/Postgres query)
        # embed_text = case.brd_action
        query_text = f"{case.brd_action} {case.description or ''}".strip()
        if embedding_variant=="name_only":
            embed_text = case.brd_action
        else:
            embed_text = query_text
        embedding  = self._model.encode(embed_text, normalize_embeddings=True).tolist()

        # Retrieve full top-K (no decision filter)
        candidates = self.pipeline.retrieve_actions(
            query=query_text, embedding=embedding, limit=top_k
        )

        # Apply decision engine to find what would be accepted in production
        accepted_candidate = self.pipeline._decision.decide(
            candidates, entity_type=RetrievalType.ACTION
        )

        accepted_id = accepted_candidate.entity.id if accepted_candidate else None
        accepted_conf = None
        accepted_ce   = None
        if accepted_candidate is not None:
            accepted_ce   = accepted_candidate.cross_encoder_score
            accepted_conf = _sigmoid(float(accepted_ce)) if accepted_ce is not None else float(accepted_candidate.rrf_score)

        # Serialize candidates for metric computation
        cand_dicts = [
            {
                "action_definition_id": c.entity.id,
                "action_name": c.entity.name,
                "rrf_score": float(c.rrf_score),
                "vector_rank": c.vector_rank,
                "bm25_rank": c.bm25_rank,
                "postgres_rank": c.postgres_rank,
                "cross_encoder_score": c.cross_encoder_score,
            }
            for c in candidates
        ]
        from app.evaluation_runner.metrics import get_expected_candidate_diagnostics
        diagnostics = get_expected_candidate_diagnostics(
                    candidates=cand_dicts,
                    expected_action_id=case.expected_action_definition_id,
                )
        print(diagnostics,"diagnostics")
        if diagnostics is not None:
            print(
                f"""
        Expected candidate diagnostics:
            Action          : {diagnostics["action_name"]}
            Final rank      : {diagnostics["final_rank"]}
            Vector rank     : {diagnostics["vector_rank"]}
            BM25 rank       : {diagnostics["bm25_rank"]}
            Postgres rank   : {diagnostics["postgres_rank"]}
            RRF score       : {diagnostics["rrf_score"]:.6f}
            Cross-encoder   : {diagnostics["cross_encoder_score"]}
        """
            )
        else:
            print(
                f"""
        Expected candidate diagnostics:
            Expected action ID {case.expected_action_definition_id}
            NOT FOUND in retrieved candidates
        """
            )
        m = compute_case_metrics(
            candidates=cand_dicts,
            expected_action_id=case.expected_action_definition_id,
            accepted_id=accepted_id,
            accepted_confidence=accepted_conf,
            accepted_cross_encoder=accepted_ce,
        )

        result = EvaluationResult(
            run_id=run.id,
            case_id=case.id,
            correct_rank=m.correct_rank,
            reciprocal_rank=m.reciprocal_rank,
            recall_at_1=m.recall_at_1,
            recall_at_3=m.recall_at_3,
            recall_at_5=m.recall_at_5,
            recall_at_8=m.recall_at_8,
            accepted=m.accepted,
            diagnostic_classification=m.diagnostic_classification,
            cross_encoder_score=m.cross_encoder_score,
            final_confidence=m.final_confidence,
        )
        self.db.add(result)
        self.db.flush()

        # Store full candidate list
        for rank, c in enumerate(candidates, start=1):
            self.db.add(EvaluationCandidate(
                result_id=result.id,
                action_definition_id=c.entity.id,
                action_name=c.entity.name,
                rank=rank,
                rrf_score=float(c.rrf_score),
                vector_rank=c.vector_rank,
                bm25_rank=c.bm25_rank,
                postgres_rank=c.postgres_rank,
                cross_encoder_score=c.cross_encoder_score,
            ))

        return m
