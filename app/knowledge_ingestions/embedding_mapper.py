"""
app/knowledge_ingestions/embedding_mapper.py

Maps extracted workflow actions and triggers to catalog definitions.

Calls RetrievalPipeline.retrieve_actions / retrieve_triggers which internally runs:
  embed → vector + BM25 + Postgres → RRF → cross-encoder

Then calls MappingDecisionEngine.decide() with the full candidate list.
Both paths write diagnostics (query_text, top_candidates, confidence) before
committing a status so every MAPPED and UNMAPPED row is fully observable.

Changes from original:
  - embedding_variant default is "name_description" (richer vector space alignment)
  - map_triggers uses retrieve_triggers (full list) + explicit decide(), mirrors map_actions
  - map_triggers writes diagnostics and calls mark_trigger_unmapped on failure
  - _normalize_query() strips BRD boilerplate before retrieval
  - map_triggers embeds the full query text, not just the extracted name
"""

import logging
import math
import re

from app.knowledge_ingestions.workflow_repository import WorkflowRepository
from app.retrieval.pipeline import RetrievalPipeline
from app.retrieval.models import RankedCandidate
from app.retrieval.thresholds import RetrievalType
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _serialize_candidates(candidates: list[RankedCandidate], top_k: int = 10) -> list[dict]:
    """Serialize top-K candidates for JSONB storage — no vectors, metadata only."""
    result = []
    for c in candidates[:top_k]:
        entry: dict = {
            "name":          getattr(c.entity, "name", None),
            "display_name":  getattr(c.entity, "display_name", None),
            "rrf_score":     round(float(c.rrf_score), 6),
            "vector_rank":   c.vector_rank,
            "bm25_rank":     c.bm25_rank,
            "postgres_rank": c.postgres_rank,
        }
        if c.cross_encoder_score is not None:
            entry["cross_encoder_score"] = round(float(c.cross_encoder_score), 6)
            entry["confidence"]          = round(_sigmoid(float(c.cross_encoder_score)), 6)
        result.append(entry)
    return result


# ---------------------------------------------------------------------------
# Boilerplate phrases that frequently appear in BRD-extracted action/trigger
# names and dilute retrieval signal without adding semantic content.
# ---------------------------------------------------------------------------
_BOILERPLATE_RE = re.compile(
    r"\b(?:the|for the|of the|in the|to the|from the|"
    r"process of|ensure that|verify that|validate that|confirm that|"
    r"prior to|in order to|based on|as per|as required|"
    r"shall be|should be|must be|will be|"
    r"initiate(?:d)?|perform(?:ed)?|execute(?:d)?|carry out|"
    r"check(?:ing)?|review(?:ing)?)\b",
    re.IGNORECASE,
)


def _normalize_query(raw: str) -> str:
    """Strip BRD boilerplate from an extracted name to improve retrieval precision.

    E.g. "Verify that the applicant's CIBIL score has been validated prior to appraisal"
         → "applicant CIBIL score validated appraisal"
    """
    normalized = _BOILERPLATE_RE.sub(" ", raw)
    # Collapse runs of whitespace
    return " ".join(normalized.split())


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
        variant: str = "name_description",
    ) -> str:
        """Build the text that will be embedded for retrieval.

        "name_description" is the default and aligns with how the catalog
        embeddings are now built (name + aliases + description), putting
        BRD queries and catalog entries in the same embedding distribution.
        """
        if variant == "name_only":
            return name

        if variant == "name_description":
            return f"{name} {description or ''}".strip()

        raise ValueError(f"Unknown embedding variant: {variant}")

    # ── Actions ───────────────────────────────────────────────────────────────

    def map_actions(self, embedding_variant: str = "name_description") -> None:
        """Map every PENDING/UNMAPPED action against the catalog.

        For each mapping:
          1. Build the retrieval query from extract_name + BRD description
          2. Normalise the query to remove boilerplate
          3. Embed with the same model used to index the catalog
          4. Run the full retrieval pipeline (retrieve → fuse → rerank)
          5. Persist top-K candidates for observability
          6. Apply the decision threshold
          7. Write MAPPED or UNMAPPED with confidence/diagnostics
        """
        for action in self.repository.get_unmapped_actions():
            raw_query = f"{action.extract_name} {action.description or ''}".strip()
            query     = _normalize_query(raw_query)

            embedding_text = self._build_embedding_text(
                action.extract_name,
                action.description,
                embedding_variant,
            )
            embedding = self._embed(embedding_text)

            all_candidates = self.pipeline.retrieve_actions(
                query=query, embedding=embedding
            )
            top_candidates_json = _serialize_candidates(all_candidates)

            best: RankedCandidate | None = self.pipeline._decision.decide(
                all_candidates, entity_type=RetrievalType.ACTION
            )

            if best is not None:
                real_confidence = (
                    _sigmoid(float(best.cross_encoder_score))
                    if best.cross_encoder_score is not None
                    else float(best.rrf_score)
                )
                ad = best.entity

                self.repository.update_action_mapping(
                    mapping_id=action.id,
                    action_definition_id=ad.id,
                    similarity_score=float(best.rrf_score),
                    confidence=real_confidence,
                    query_text=query,
                    top_candidates=top_candidates_json,
                    action_name=ad.name,
                    display_name=getattr(ad, "display_name", None),
                    catalog_description=getattr(ad, "description", None),
                    aliases=getattr(ad, "aliases", None),
                    workflow_type=getattr(ad, "workflow_type", None),
                    input_schema=getattr(ad, "input_schema", None),
                    output_schema=getattr(ad, "output_schema", None),
                    execution_template=getattr(ad, "execution_template", None),
                )
            else:
                # Log why it failed when top candidates exist
                if all_candidates and all_candidates[0].cross_encoder_score is not None:
                    top_conf = _sigmoid(float(all_candidates[0].cross_encoder_score))
                    logger.info(
                        "action_unmapped id=%s name=%r top_candidate=%r confidence=%.3f",
                        action.id,
                        action.extract_name,
                        getattr(all_candidates[0].entity, "name", None),
                        top_conf,
                    )
                else:
                    logger.info(
                        "action_unmapped id=%s name=%r no_candidates=%s",
                        action.id,
                        action.extract_name,
                        len(all_candidates) == 0,
                    )

                self.repository.mark_action_unmapped(
                    mapping_id=action.id,
                    query_text=query,
                    top_candidates=top_candidates_json,
                )

    # ── Triggers ──────────────────────────────────────────────────────────────

    def map_triggers(self, embedding_variant: str = "name_description") -> None:
        """Map every PENDING/UNMAPPED trigger against the catalog.

        Mirrors map_actions exactly:
          - Uses retrieve_triggers (full list) so diagnostics are available
            before the threshold decision is applied.
          - Calls mark_trigger_unmapped on failure so every trigger row gets
            a final status (no more silent PENDING rows after ingestion).
          - Embeds the full query text (not just the extracted name) so the
            vector is in the same distribution as the catalog embeddings.
        """
        for trigger in self.repository.get_unmapped_triggers():
            raw_query = f"{trigger.extracted_name} {trigger.description or ''}".strip()
            query     = _normalize_query(raw_query)

            embedding_text = self._build_embedding_text(
                trigger.extracted_name,
                trigger.description,
                embedding_variant,
            )
            embedding = self._embed(embedding_text)

            all_candidates = self.pipeline.retrieve_triggers(
                query=query, embedding=embedding
            )
            top_candidates_json = _serialize_candidates(all_candidates)

            best: RankedCandidate | None = self.pipeline._decision.decide(
                all_candidates, entity_type=RetrievalType.TRIGGER
            )

            if best is not None:
                td = best.entity
                real_confidence = (
                    _sigmoid(float(best.cross_encoder_score))
                    if best.cross_encoder_score is not None
                    else float(best.rrf_score)
                )

                self.repository.update_trigger_mapping(
                    mapping_id=trigger.id,
                    trigger_definition_id=td.id,
                    similarity_score=float(best.rrf_score),
                    confidence=real_confidence,
                    trigger_name=td.name,
                    display_name=getattr(td, "display_name", None),
                    catalog_description=getattr(td, "description", None),
                    aliases=getattr(td, "aliases", None),
                    workflow_type=getattr(td, "workflow_type", None),
                )
            else:
                if all_candidates and all_candidates[0].cross_encoder_score is not None:
                    top_conf = _sigmoid(float(all_candidates[0].cross_encoder_score))
                    logger.info(
                        "trigger_unmapped id=%s name=%r top_candidate=%r confidence=%.3f",
                        trigger.id,
                        trigger.extracted_name,
                        getattr(all_candidates[0].entity, "name", None),
                        top_conf,
                    )
                else:
                    logger.info(
                        "trigger_unmapped id=%s name=%r no_candidates=%s",
                        trigger.id,
                        trigger.extracted_name,
                        len(all_candidates) == 0,
                    )

                self.repository.mark_trigger_unmapped(
                    mapping_id=trigger.id,
                    query_text=query,
                    top_candidates=top_candidates_json,
                )
