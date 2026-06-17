from app.db.session import SessionLocal
from app.semantic.embedding_service import EmbeddingService
from app.semantic.semantic_repository import SemanticRepository




db =SessionLocal()
service=EmbeddingService()
repo=SemanticRepository()


query="payment overdue"

embedding=service.generate_embedding(query)

results = repo.search_triggers(
    db=db,
    embedding=embedding,
    limit=5
)

for row in results:
    print(row)