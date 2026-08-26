# # scripts/test_postgress.py

# from app.db.session import SessionLocal
# from app.knowledge_ingestions.workflow_repository import WorkflowRepository
# from app.retrieval.postgress_retriever import PostgressRetriever


# def main():
#     db = SessionLocal()

#     try:
#         repository = WorkflowRepository(db)
#         retriever = PostgressRetriever(repository)

#         queries = [
#             "Apply Interest",
#             "Apply Interest Rate",
#             "Apply Interest Rate Apply the applicable interest rate to the loan account",
#         ]

#         for query in queries:
#             print(f"\nQUERY: {query}")

#             results = retriever.search_actions(query, limit=20)

#             for result in results:
#                 print(
#                     result.entity.id,
#                     result.entity.name,
#                     result.score,
#                 )

#     finally:
#         db.close()


# if __name__ == "__main__":
#     main()


# scripts/test_postgress.py

from sqlalchemy import func

from app.db.session import SessionLocal
from app.models.action_definitions import ActionDefinition


QUERIES = [
    "Apply Interest",
    "Apply Interest Rate",
    "Apply Interest Rate Apply the applicable interest rate to the loan account",
]


def build_text_vector():
    """
    FTS document:
        name + display_name + aliases

    Deliberately excludes description for this experiment.
    """
    text_vector = func.to_tsvector(
        "english",
        func.concat(
            func.replace(ActionDefinition.name, "_", " "),
            " ",
            func.coalesce(ActionDefinition.display_name, " "),
        ),
    )

    alias_vector = func.jsonb_to_tsvector(
        "english",
        func.coalesce(
            ActionDefinition.aliases,
            "[]",
        ),
        '["string"]',
    )

    return text_vector.op("||")(alias_vector)


def run_query(db, label, ts_query, vector, limit=10):
    """
    Execute one FTS strategy and print results.
    """
    rank = func.ts_rank(vector, ts_query)

    rows = (
        db.query(
            ActionDefinition.id,
            ActionDefinition.name,
            ActionDefinition.display_name,
            rank.label("rank"),
        )
        .filter(vector.op("@@")(ts_query))
        .order_by(rank.desc())
        .limit(limit)
        .all()
    )

    print(f"\n{'=' * 70}")
    print(f"METHOD: {label}")
    print(f"{'=' * 70}")

    if not rows:
        print("NO RESULTS")
        return

    for row in rows:
        print(
            f"id={row.id:<4} "
            f"name={row.name:<30} "
            f"rank={float(row.rank):.6f}"
        )


def main():
    db = SessionLocal()

    try:
        vector = build_text_vector()

        for query in QUERIES:
            print("\n\n")
            print("#" * 80)
            print(f"QUERY: {query}")
            print("#" * 80)

            # ---------------------------------------------------------
            # 1. plainto_tsquery
            # ---------------------------------------------------------
            ts_query = func.plainto_tsquery(
                "english",
                query,
            )

            run_query(
                db,
                "1. plainto_tsquery (AND)",
                ts_query,
                vector,
            )

            # ---------------------------------------------------------
            # 2. websearch_to_tsquery
            # ---------------------------------------------------------
            ts_query = func.websearch_to_tsquery(
                "english",
                query,
            )

            run_query(
                db,
                "2. websearch_to_tsquery",
                ts_query,
                vector,
            )

            # ---------------------------------------------------------
            # 3. OR query
            #
            # Build OR query from the sentence using PostgreSQL.
            # We use tsquery generated from each token and combine
            # them with OR using the tsquery OR operator (||).
            # NOTE: tsquery uses || for OR, NOT the single pipe |
            # ---------------------------------------------------------
            words = query.split()

            token_queries = [
                func.plainto_tsquery("english", word)
                for word in words
            ]

            or_query = token_queries[0]

            for token_query in token_queries[1:]:
                or_query = or_query.op("||")(token_query)

            run_query(
                db,
                "3. OR across query terms",
                or_query,
                vector,
            )

            # ---------------------------------------------------------
            # 4. phraseto_tsquery
            #
            # Test the complete sentence as a phrase.
            # ---------------------------------------------------------
            ts_query = func.phraseto_tsquery(
                "english",
                query,
            )

            run_query(
                db,
                "4. phraseto_tsquery (full phrase)",
                ts_query,
                vector,
            )

            # ---------------------------------------------------------
            # 5. Direct/manual PostgreSQL query
            #
            # Explicitly test the important lexical phrase:
            # "Apply Interest"
            #
            # This is our controlled lexical baseline.
            # ---------------------------------------------------------
            ts_query = func.phraseto_tsquery(
                "english",
                "Apply Interest",
            )

            run_query(
                db,
                "5. Direct phrase: 'Apply Interest'",
                ts_query,
                vector,
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()