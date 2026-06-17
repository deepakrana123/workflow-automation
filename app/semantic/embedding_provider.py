from sentence_transformers import SentenceTransformer


class EmbeddingProvider:
    def __init__(self):
        self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    def embed(self, text: str) -> list[float]:
        vector = self.model.encode(text, normalize_embeddings=True)
        return vector.tolist()
