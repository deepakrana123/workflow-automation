# scripts/test_postgress.py

from app.db.session import SessionLocal
from app.knowledge_ingestions.workflow_repository import WorkflowRepository
from app.retrieval.postgress_retriever import PostgressRetriever


def main():
    db = SessionLocal()

    try:
        repository = WorkflowRepository(db)
        retriever = PostgressRetriever(repository)

        queries = [
            "Apply Interest",
            "Apply Interest Rate",
            "Apply Interest Rate Apply the applicable interest rate to the loan account",
        ]

        for query in queries:
            print(f"\nQUERY: {query}")

            results = retriever.search_actions(query, limit=20)

            for result in results:
                print(
                    result.entity.id,
                    result.entity.name,
                    result.score,
                )

    finally:
        db.close()


if __name__ == "__main__":
    main()