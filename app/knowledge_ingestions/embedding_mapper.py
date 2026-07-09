"""
app/knowledge_ingestions/embedding_mapper.py

Maps extracted workflow actions and triggers to catalog definitions.

Calls RetrievalPipeline.search_actions / search_triggers which internally runs:
  embed → vector + BM25 + Postgres → RRF → cross-encoder → decision engine

Returns the winning RankedCandidate or None (below confidence threshold).
EmbeddingMapper only orchestrates between ingestion and persistence —
it knows nothing about individual retrievers or confidence thresholds.
"""

from app.knowledge_ingestions.workflow_repository import WorkflowRepository
from app.retrieval.pipeline import RetrievalPipeline
from app.retrieval.models import RankedCandidate
from sentence_transformers import SentenceTransformer


class EmbeddingMapper:
    def __init__(
        self,
        repository: WorkflowRepository,
        pipeline: RetrievalPipeline,
        model_name: str = "BAAI/bge-small-en-v1.5",
    ):
        self.repository = repository
        self.pipeline = pipeline
        self._model = SentenceTransformer(model_name)

    def _embed(self, text: str) -> list[float]:
        return self._model.encode(text, normalize_embeddings=True).tolist()

    def map_actions(self) -> None:
        for action in self.repository.get_unmapped_actions():
            query     = f"{action.extract_name} {action.description or ''}"
            embedding = self._embed(action.extract_name)

            best: RankedCandidate | None = self.pipeline.search_actions(
                query=query, embedding=embedding
            )
            if best is None:
                continue

            self.repository.update_action_mapping(
                mapping_id=action.id,
                action_definitation_id=best.entity.id,
                similarity_score=best.rrf_score,
                confidence=best.rrf_score,
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
                trigger_definitation_id=best.entity.id,
                similarity_score=best.rrf_score,
                confidence=best.rrf_score,
            )
