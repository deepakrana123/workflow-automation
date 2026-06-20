"""
app/routes/search.py

Semantic search endpoint for the frontend.
Currently implements substring/alias-based search as a fallback
(pgvector semantic search can be added later without changing the interface).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel

from app.db.session import get_db
from app.models.trigger_definitions import TriggerDefinition
from app.models.action_definitions import ActionDefinition

router = APIRouter(prefix="/search", tags=["search"])


class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = 10


def _text_similarity(name: str, query: str) -> float:
    """
    Simple text-based similarity score.
    Returns 0.0–1.0. Higher = more similar.
    Replace with pgvector cosine similarity when embeddings are ready.
    """
    q = query.lower()
    n = name.lower()
    if q == n:
        return 1.0
    if q in n or n in q:
        return 0.85
    # Word overlap score
    q_words = set(q.split())
    n_words = set(n.replace("_", " ").split())
    overlap = len(q_words & n_words)
    if overlap:
        return 0.5 + (overlap / max(len(q_words), len(n_words))) * 0.3
    return 0.1


@router.post("/semantic")
def semantic_search(
    body: SemanticSearchRequest,
    db: Session = Depends(get_db),
):
    query = body.query.strip()
    top_k = min(body.top_k, 20)

    # Search triggers
    trigger_rows = db.query(TriggerDefinition).filter(
        TriggerDefinition.active == True
    ).all()

    trigger_matches = []
    for t in trigger_rows:
        # Score against name, display_name, and aliases
        score = max(
            _text_similarity(t.name.replace("_", " "), query),
            _text_similarity(t.display_name or "", query),
            *[_text_similarity(a, query) for a in (t.aliases or [])],
        )
        if score > 0.1:
            trigger_matches.append({
                "name": t.name,
                "display_name": t.display_name,
                "distance_score": round(1.0 - score, 4),
                "similarity_score": round(score, 4),
                "type": "trigger",
            })

    trigger_matches.sort(key=lambda x: x["similarity_score"], reverse=True)
    trigger_matches = trigger_matches[:top_k]

    # Search actions
    action_rows = db.query(ActionDefinition).filter(
        ActionDefinition.active == True
    ).all()

    action_matches = []
    for a in action_rows:
        score = max(
            _text_similarity(a.name.replace("_", " "), query),
            _text_similarity(a.display_name or "", query),
            *[_text_similarity(al, query) for al in (a.aliases or [])],
        )
        if score > 0.1:
            action_matches.append({
                "name": a.name,
                "display_name": a.display_name,
                "distance_score": round(1.0 - score, 4),
                "similarity_score": round(score, 4),
                "type": "action",
            })

    action_matches.sort(key=lambda x: x["similarity_score"], reverse=True)
    action_matches = action_matches[:top_k]

    return {
        "trigger_matches": trigger_matches,
        "action_matches": action_matches,
    }
