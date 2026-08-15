"""
app/workflow/rule_conflicts.py

Deterministic, dependency-free detection of conflicting business rules across a
workspace's BRDs.

Scope (intentionally simple — see requirement 14): detect when two rules talk
about the SAME subject but specify DIFFERENT monetary thresholds, e.g.

    BRD A: "Approval required above ₹5 lakh."
    BRD B: "Approval required above ₹10 lakh."
        → threshold_conflict on subject "approval required above"

We do NOT try to resolve the conflict — we surface it for human review. Pure
functions only, so this is fully unit-testable.
"""

import re

# Multipliers for Indian + common magnitude words.
_UNITS = {
    "lakh": 100_000, "lakhs": 100_000, "lac": 100_000, "lacs": 100_000,
    "crore": 10_000_000, "crores": 10_000_000, "cr": 10_000_000,
    "k": 1_000, "thousand": 1_000,
    "million": 1_000_000, "mn": 1_000_000,
    "billion": 1_000_000_000, "bn": 1_000_000_000,
}

# Rule must express a threshold to be considered for a threshold conflict.
_THRESHOLD_WORDS = (
    "above", "exceed", "exceeds", "exceeding", "greater", "more than", "over",
    "at least", "minimum", "min", "below", "less than", "under", "up to",
    "maximum", "max", "threshold", "limit",
)

# Words dropped when computing a rule's subject signature.
_STOP = {
    "the", "a", "an", "is", "are", "be", "must", "should", "shall", "of", "to",
    "for", "and", "or", "than", "then", "rs", "inr", "than", "amount", "amounts",
    "value", "rupees", "rupee",
}

_AMOUNT_RE = re.compile(
    r"(?:₹|rs\.?|inr)?\s*"
    r"([0-9][0-9,]*(?:\.[0-9]+)?)"
    r"\s*(lakh|lakhs|lac|lacs|crore|crores|cr|k|thousand|million|mn|billion|bn)?",
    re.IGNORECASE,
)


def extract_amounts(text: str) -> list[float]:
    """Extract monetary amounts, normalizing units (lakh/crore/k/...) to a number.

    Only meaningful amounts are kept: a bare small integer with no currency or
    unit (e.g. a step count "3") is ignored to avoid false positives.
    """
    amounts: list[float] = []
    for m in _AMOUNT_RE.finditer(text):
        raw = m.group(0).strip().lower()
        num_str = m.group(1).replace(",", "")
        unit = (m.group(2) or "").lower()
        try:
            val = float(num_str)
        except ValueError:
            continue

        has_currency = bool(re.match(r"^(₹|rs\.?|inr)", raw))
        has_comma = "," in m.group(1)

        if unit:
            val *= _UNITS[unit]
        elif not has_currency and not has_comma:
            # bare number, no currency/unit/grouping → not a monetary threshold
            continue
        amounts.append(val)
    return amounts


def _has_threshold_word(text: str) -> bool:
    low = text.lower()
    return any(w in low for w in _THRESHOLD_WORDS)


def subject_key(text: str) -> tuple[str, ...]:
    """Signature of a rule with amounts/currency/units/stopwords stripped."""
    t = text.lower().replace("₹", " ")
    t = _AMOUNT_RE.sub(" ", t)
    # drop any leftover unit words
    for unit in _UNITS:
        t = re.sub(rf"\b{unit}\b", " ", t)
    t = re.sub(r"[^a-z\s]", " ", t)
    words = [w for w in t.split() if w and w not in _STOP]
    return tuple(sorted(set(words)))


def detect_rule_conflicts(rules: list[dict]) -> list[dict]:
    """Find threshold conflicts among business rules.

    Args:
        rules: [{"rule": str, "source_document": str | None}, ...]

    Returns:
        [{"type": "threshold_conflict", "subject": str,
          "rules": [{"rule", "source_document", "amounts"}]}, ...]
    """
    # subject_key -> list of {rule, source_document, amounts}
    groups: dict[tuple, list[dict]] = {}
    for r in rules:
        text = r.get("rule") or ""
        if not _has_threshold_word(text):
            continue
        amounts = extract_amounts(text)
        if not amounts:
            continue
        key = subject_key(text)
        if not key:
            continue
        groups.setdefault(key, []).append({
            "rule": text,
            "source_document": r.get("source_document"),
            "amounts": amounts,
        })

    conflicts: list[dict] = []
    for key, members in groups.items():
        if len(members) < 2:
            continue
        distinct_amounts = {a for m in members for a in m["amounts"]}
        if len(distinct_amounts) < 2:
            continue  # same threshold everywhere → consensus, not a conflict
        conflicts.append({
            "type": "threshold_conflict",
            "subject": " ".join(key),
            "rules": members,
        })
    return conflicts
