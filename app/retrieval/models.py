from dataclasses import dataclass
from typing import Any

@dataclass
class RankedCandidate:

    entity: Any

    vector_rank: int | None

    bm25_rank: int | None

    postgres_rank: int | None

    rrf_score: float


@dataclass
class RetrievalCandidate:
    entity: Any
    score: float
    source: str