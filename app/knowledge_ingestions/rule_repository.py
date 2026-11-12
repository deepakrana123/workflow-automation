from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.workflow_business_rule import WorkflowBusinessRule
from app.models.workflow_knowledge import WorkflowKnowledge


class RuleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_rules_for_workspace(
        self,
        workspace_id: int,
    ) -> list[WorkflowBusinessRule]:
        return (
            self.db.query(WorkflowBusinessRule)
            .join(
                WorkflowKnowledge,
                WorkflowKnowledge.id == WorkflowBusinessRule.workflow_knowledge_id,
            )
            .filter(WorkflowKnowledge.workspace_id == workspace_id)
            .all()
        )

    def search_by_embedding(
        self,
        workspace_id: int,
        embedding: list[float],
        limit: int = 20,
        allowed_ids: set[int] | None = None,
    ) -> list[tuple[WorkflowBusinessRule, float]]:
        # Explicit guard: empty allow-list means no candidates are eligible.
        if allowed_ids is not None and len(allowed_ids) == 0:
            return []
        distance = WorkflowBusinessRule.embedding.cosine_distance(embedding)
        q = (
            self.db.query(WorkflowBusinessRule, distance.label("distance"))
            .join(
                WorkflowKnowledge,
                WorkflowKnowledge.id == WorkflowBusinessRule.workflow_knowledge_id,
            )
            .filter(
                WorkflowKnowledge.workspace_id == workspace_id,
                WorkflowBusinessRule.embedding.isnot(None),
            )
        )
        if allowed_ids is not None:
            q = q.filter(WorkflowBusinessRule.id.in_(allowed_ids))
        return q.order_by(distance).limit(limit).all()

    def search_by_fts(
        self,
        workspace_id: int,
        query: str,
        limit: int = 20,
        allowed_ids: set[int] | None = None,
    ) -> list[tuple[WorkflowBusinessRule, float]]:
        from sqlalchemy import text as sa_text

        # Explicit early-return for empty allow-list so we never rely on
        # "AND r.id = ANY([])" database semantics.
        if allowed_ids is not None and len(allowed_ids) == 0:
            return []

        params: dict = {"q": query, "ws": workspace_id, "lim": max(1, min(limit, 100))}

        # Build the optional allowed-IDs filter as a named parameter, not by
        # string interpolation, so the clause is always syntactically fixed.
        # We use a separate conditional rather than f-string injection to keep
        # the SQL structure static and safe from accidental future injection.
        if allowed_ids is not None:
            ids_filter = "AND r.id = ANY(:ids)"
            params["ids"] = list(allowed_ids)
        else:
            ids_filter = ""

        and_sql = sa_text(
            "SELECT r.id,"
            "       ts_rank("
            "           to_tsvector('english',"
            "               concat_ws(' ', r.rule, r.condition, r.outcome,"
            "                         r.responsible_role, r.threshold)),"
            "           plainto_tsquery('english', :q)"
            "       ) AS rank"
            " FROM workflow_business_rule r"
            " JOIN workflow_knowledge wk ON wk.id = r.workflow_knowledge_id"
            " WHERE wk.workspace_id = :ws"
            f" {ids_filter}"
            " AND to_tsvector('english',"
            "         concat_ws(' ', r.rule, r.condition, r.outcome,"
            "                   r.responsible_role, r.threshold))"
            "     @@ plainto_tsquery('english', :q)"
            " ORDER BY rank DESC"
            " LIMIT :lim"
        )

        rows = self.db.execute(and_sql, params).fetchall()

        if not rows:
            # OR-fallback: replace & with | so partial-match queries surface.
            or_sql = sa_text(
                "SELECT r.id,"
                "       ts_rank("
                "           to_tsvector('english',"
                "               concat_ws(' ', r.rule, r.condition, r.outcome,"
                "                         r.responsible_role, r.threshold)),"
                "           cast(regexp_replace("
                "               cast(plainto_tsquery('english', :q) as text),"
                "               ' & ', ' | ', 'g') as tsquery)"
                "       ) AS rank"
                " FROM workflow_business_rule r"
                " JOIN workflow_knowledge wk ON wk.id = r.workflow_knowledge_id"
                " WHERE wk.workspace_id = :ws"
                f" {ids_filter}"
                " AND to_tsvector('english',"
                "         concat_ws(' ', r.rule, r.condition, r.outcome,"
                "                   r.responsible_role, r.threshold))"
                "     @@ cast(regexp_replace("
                "            cast(plainto_tsquery('english', :q) as text),"
                "            ' & ', ' | ', 'g') as tsquery)"
                " ORDER BY rank DESC"
                " LIMIT :lim"
            )
            rows = self.db.execute(or_sql, params).fetchall()

        if not rows:
            return []

        id_to_rank = {r[0]: float(r[1]) for r in rows}
        rules = (
            self.db.query(WorkflowBusinessRule)
            .filter(WorkflowBusinessRule.id.in_(id_to_rank.keys()))
            .all()
        )
        rules.sort(key=lambda r: id_to_rank[r.id], reverse=True)
        return [(r, id_to_rank[r.id]) for r in rules]
