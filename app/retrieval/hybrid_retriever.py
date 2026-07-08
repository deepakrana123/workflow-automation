from .vector_retriever import VectorRetriever
from .keyword_retriever import KeywordRetriever
from .reciprocal_rank_fusion import ReciprocalRankFusion


class HybridRetriever:
    def __init__(self,repository):
        self.vector=VectorRetriever(repository)
        self.keyword=KeywordRetriever(repository)
        self.rrf=ReciprocalRankFusion()
        