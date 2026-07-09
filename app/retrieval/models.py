from dataclasses import dataclass, field
from typing import Any


@dataclass
class RankedCandidate:
    """
    Output of RRF fusion — one candidate with per-source rank breakdown.

    After cross-encoder re-ranking, cross_encoder_score is populated and
    the list is re-sorted by that score. rrf_score is preserved for
    traceability / confidence fallback.
    """

    entity: Any

    vector_rank: int | None
    bm25_rank: int | None
    postgres_rank: int | None

    rrf_score: float

    # Populated by CrossEncoderReRanker; None until reranking runs
    cross_encoder_score: float | None = field(default=None)


@dataclass
class RetrievalCandidate:
    entity: Any
    score: float
    source: str
