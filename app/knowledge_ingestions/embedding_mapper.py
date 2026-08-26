"""
app/knowledge_ingestions/embedding_mapper.py

Maps extracted workflow actions and triggers to catalog definitions.

Calls RetrievalPipeline.search_actions / search_triggers which internally runs:
  embed → vector + BM25 + Postgres → RRF → cross-encoder → decision engine

Observability:
  - query_text stored on every mapping (the combined text sent to BM25/Postgres)
  - top_candidates stored as JSONB (top-K with per-source ranks + scores)
  - confidence stored as sigmoid(cross_encoder_score) — the actual decision metric
  - MappingStatus updated to MAPPED or UNMAPPED (never left as PENDING)
"""

import math

from app.knowledge_ingestions.workflow_repository import WorkflowRepository
from app.retrieval.pipeline import RetrievalPipeline
from app.retrieval.models import RankedCandidate
from sentence_transformers import SentenceTransformer


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _serialize_candidates(candidates: list[RankedCandidate], top_k: int = 10) -> list[dict]:
    """Serialize top-K candidates for JSONB storage — no vectors, metadata only."""
    result = []
    for c in candidates[:top_k]:
        entry: dict = {
            "name":           getattr(c.entity, "name", None),
            "display_name":   getattr(c.entity, "display_name", None),
            "rrf_score":      round(float(c.rrf_score), 6),
            "vector_rank":    c.vector_rank,
            "bm25_rank":      c.bm25_rank,
            "postgres_rank":  c.postgres_rank,
        }
        if c.cross_encoder_score is not None:
            entry["cross_encoder_score"]  = round(float(c.cross_encoder_score), 6)
            entry["confidence"]           = round(_sigmoid(float(c.cross_encoder_score)), 6)
        result.append(entry)
    return result


class EmbeddingMapper:
    def __init__(
        self,
        repository: WorkflowRepository,
        pipeline: RetrievalPipeline,
        model_name: str = "BAAI/bge-small-en-v1.5",
    ):
        self.repository = repository
        self.pipeline   = pipeline
        self._model     = SentenceTransformer(model_name)

    def _embed(self, text: str) -> list[float]:
        return self._model.encode(text, normalize_embeddings=True).tolist()
    
    def _build_embedding_text(
        self,
        name: str,
        description: str | None,
        variant: str = "name_only",
    ) -> str:
        if variant == "name_only":
            return name

        if variant == "name_description":
            return f"{name} {description or ''}".strip()

        raise ValueError(f"Unknown embedding variant: {variant}")

    def map_actions(self, embedding_variant: str = "name_only") -> None:
        for action in self.repository.get_unmapped_actions():
            query = f"{action.extract_name} {action.description or ''}".strip()

            embedding_text = self._build_embedding_text(
                action.extract_name,
                action.description,
                embedding_variant,
            )
            embedding = self._embed(embedding_text)

            # Retrieve full top-K for observability
            all_candidates = self.pipeline.retrieve_actions(
                query=query, embedding=embedding
            )
            top_candidates_json = _serialize_candidates(all_candidates)

            # Decision engine picks best or None
            from app.retrieval.thresholds import RetrievalType
            best: RankedCandidate | None = self.pipeline._decision.decide(
                all_candidates, entity_type=RetrievalType.ACTION
            )

            if best is not None:
                # Use sigmoid(cross_encoder_score) as confidence if available,
                # else fall back to rrf_score
                if best.cross_encoder_score is not None:
                    real_confidence = _sigmoid(float(best.cross_encoder_score))
                else:
                    real_confidence = float(best.rrf_score)

                self.repository.update_action_mapping(
                    mapping_id=action.id,
                    action_definition_id=best.entity.id,
                    similarity_score=float(best.rrf_score),
                    confidence=real_confidence,
                    query_text=query,
                    top_candidates=top_candidates_json,
                )
            else:
                # Mark unmapped with full diagnostics so we can see WHY
                self.repository.mark_action_unmapped(
                    mapping_id=action.id,
                    query_text=query,
                    top_candidates=top_candidates_json,
                )

    def map_triggers(self) -> None:
        for trigger in self.repository.get_unmapped_triggers():
            query     = f"{trigger.extracted_name} {trigger.description or ''}"
            embedding = self._embed(trigger.extracted_name)

            best: RankedCandidate | None = self.pipeline.search_triggers(
                query=query, embedding=embedding
            )
            if best is None:
                continue

            self.repository.update_trigger_mapping(
                mapping_id=trigger.id,
                trigger_definition_id=best.entity.id,
                similarity_score=float(best.rrf_score),
                confidence=float(best.rrf_score),
            )
