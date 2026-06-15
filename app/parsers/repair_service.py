"""
app/parsers/repair_service.py

Stub — LLM-based DSL repair is not wired up yet.
The dag_orchestrator only calls this when a parse result is flagged
as `repairable=True`. For NLP pipeline testing this path is never hit,
so returning a failure response is safe.
"""


def repair_dsl_with_llm(text: str) -> dict:
    """Stub — returns failure so dag_orchestrator falls back to hard_fail."""
    return {
        "success": False,
        "error": "repair_service_not_implemented",
    }
