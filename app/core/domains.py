"""
app/core/domains.py

Canonical list of supported banking domains.
Single source of truth — imported by any module needing domain validation.

MFlows is a Banking Workflow Platform. All domains must represent
banking business verticals.
"""

ALLOWED_DOMAINS: set[str] = {
    "finance",
}


def validate_domain(domain: str) -> None:
    """Raise ValueError if domain is not in the allowed set."""
    if domain not in ALLOWED_DOMAINS:
        raise ValueError(
            f"Invalid domain '{domain}'. Allowed: {sorted(ALLOWED_DOMAINS)}"
        )
