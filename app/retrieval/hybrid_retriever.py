from .vector_retriever import VectorRetriever
from .keyword_retriever import KeywordRetriever
from .reciprocal_rank_fusion import ReciprocalRankFusion
from .postgress_retriever import PostgressRetriever
from sentence_transformers import SentenceTransformer



class HybridRetriever:
    def __init__(
        self,
        vector_retriever: VectorRetriever,
        keyword_retriever: KeywordRetriever,
        postgress_retriever: PostgressRetriever,
        rrf: ReciprocalRankFusion,
    ):
        self.vector = vector_retriever
        self.keyword = keyword_retriever
        self.postgress = postgress_retriever
        self.rrf = rrf
        self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    
    def embed(self, text: str) -> list[float]:
        vector = self.model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    def search_actions(self, query: str, embedding, limit: int = 50):
        vector_results = self.vector.search_actions(embedding, limit=limit)
        keyword_results = self.keyword.search_actions(query, limit=limit)
        postgress_results = self.postgress.search_actions(query, limit=limit)

        return self.rrf.fuse(vector_results, keyword_results, postgress_results)

    def search_triggers(self, query: str, embedding, limit: int = 50):
        vector_results = self.vector.search_triggers(embedding, limit=limit)
        keyword_results = self.keyword.search_triggers(query, limit=limit)
        postgress_results = self.postgress.search_triggers(query, limit=limit)

        return self.rrf.fuse(vector_results, keyword_results, postgress_results)
