from sqlalchemy import text


class SemanticRepository:
    def search_triggers(
        self,db,embedding,limit=5
    ):
        query=text(
            """Select id,name,display_name ,embedding <=> CAST(:embedding AS vector) AS distance
            FROM trigger_definitions
            where embedding IS NOT NULL
            ORDER By embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
            """
        )
        
        return db.execute(
            query,
            {
                "embedding":str(embedding),
                "limit":limit
            }
        ).fetchall()

    
    def search_action(self,db,embedding,limit=5):
        query = text("""
            SELECT
                id,
                name,
                display_name,
                embedding <=> CAST(:embedding AS vector) AS distance
            FROM action_definitions
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """)

        return db.execute(
            query,
            {
                "embedding": str(embedding),
                "limit": limit,
            },
        ).fetchall()
        