"""
app/core/text_similarity.py

Simple text-based similarity scoring utility.
Used as a fallback when pgvector semantic search is unavailable.
"""


def text_similarity(name: str, query: str) -> float:
    """
    Simple text-based similarity score.
    Returns 0.0–1.0. Higher = more similar.

    Scoring:
      1.0   — exact match
      0.85  — substring match
      0.5+  — word overlap
      0.1   — no match
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
