"""
Reciprocal Rank Fusion (RRF)

Formula:  RRF(d) = sum over each ranklist:  1 / (k + rank(d))

  - k is a smoothing constant (default 60, from the original Cormack 2009 paper)
  - rank is 1-based position of the document in that list
  - documents not present in a list contribute 0 for that list

Each retriever produces a list[RetrievalCandidate].
RRF merges them into a list[RankedCandidate], sorted by rrf_score descending.
"""

from app.retrieval.models import RetrievalCandidate, RankedCandidate


class ReciprocalRankFusion:

    def __init__(self, k: int = 60):
        # k=60 is the standard default; lower k rewards top ranks more aggressively
        self.k = k

    def fuse(
        self,
        vector_results: list[RetrievalCandidate],
        keyword_results: list[RetrievalCandidate],
        postgres_results: list[RetrievalCandidate],
    ) -> list[RankedCandidate]:
        """
        Merge three ranked lists into one using RRF.

        Returns list[RankedCandidate] sorted by rrf_score descending.
        entity identity is matched by entity.id.
        """

        # Build rank lookup per source: {entity_id: 1-based rank}
        vector_ranks = self._rank_map(vector_results)
        keyword_ranks = self._rank_map(keyword_results)
        postgres_ranks = self._rank_map(postgres_results)

        # Collect all unique entity ids across all lists
        all_ids = set(vector_ranks) | set(keyword_ranks) | set(postgres_ranks)

        # Build a quick id → entity lookup from whichever list has it
        entity_map = self._entity_map(vector_results, keyword_results, postgres_results)

        merged: list[RankedCandidate] = []

        for entity_id in all_ids:
            v_rank = vector_ranks.get(entity_id)
            b_rank = keyword_ranks.get(entity_id)
            p_rank = postgres_ranks.get(entity_id)

            # 1 / (k + rank) for each list that contains the document, 0 otherwise
            rrf_score = (
                self._rrf(v_rank)
                + self._rrf(b_rank)
                + self._rrf(p_rank)
            )

            merged.append(
                RankedCandidate(
                    entity=entity_map[entity_id],
                    vector_rank=v_rank,
                    bm25_rank=b_rank,
                    postgres_rank=p_rank,
                    rrf_score=rrf_score,
                )
            )

        # Higher rrf_score = better
        merged.sort(key=lambda c: c.rrf_score, reverse=True)
        return merged

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _rrf(self, rank: int | None) -> float:
        """Return RRF contribution for a given rank, or 0 if not ranked."""
        if rank is None:
            return 0.0
        return 1.0 / (self.k + rank)

    @staticmethod
    def _rank_map(results: list[RetrievalCandidate]) -> dict[int, int]:
        """Map entity_id → 1-based rank for a single retriever's result list."""
        return {candidate.entity.id: rank for rank, candidate in enumerate(results, start=1)}

    @staticmethod
    def _entity_map(*result_lists: list[RetrievalCandidate]) -> dict[int, object]:
        """Build a flat id → entity lookup from all result lists."""
        mapping: dict[int, object] = {}
        for results in result_lists:
            for candidate in results:
                mapping[candidate.entity.id] = candidate.entity
        return mapping
