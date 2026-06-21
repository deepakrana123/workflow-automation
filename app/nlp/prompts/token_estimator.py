"""
app/nlp/prompts/token_estimator.py

Lightweight token count estimator.
Uses the standard heuristic: 1 token ≈ 4 characters.
No external dependency — swappable to tiktoken later without changing callers.
"""


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a string.

    Heuristic: 1 token ≈ 4 characters (accurate within ~10% for English text).
    Replace this function body with tiktoken for exact counts when needed.

    Args:
        text: The prompt or text to estimate.

    Returns:
        Estimated token count as an integer.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)
