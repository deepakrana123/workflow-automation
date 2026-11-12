"""
app/retrieval/query_intent.py

Rule query intent extractor.

Parses a natural-language rule question into structured fields:
  - product    : loan product type (home_loan, lap, personal_loan, gold_loan,
                 microfinance, business_loan, auto_loan)
  - workflow   : process area (kyc, disbursement, collection, lead, sanction,
                 appraisal, eligibility, auction, partner, compliance)
  - threshold  : numeric value + unit extracted from the query (e.g. "50%", "5 lakh", "30 days")
  - role       : actor/role mentioned (branch_manager, credit_officer, loan_officer, etc.)
  - cardinality: "single" — user wants one rule / "multiple" — user wants all applicable rules

All fields are Optional — a field is None when the query gives no signal for it.

Design: deterministic regex + keyword matching, no LLM, no external calls.
Fast enough to run on every query before retrieval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

@dataclass
class QueryIntent:
    product:     Optional[str]
    workflow:    Optional[str]
    threshold:   Optional[str]
    role:        Optional[str]
    cardinality: str            # "single" | "multiple"

    def to_dict(self) -> dict:
        return {
            "product":     self.product,
            "workflow":    self.workflow,
            "threshold":   self.threshold,
            "role":        self.role,
            "cardinality": self.cardinality,
        }


# ---------------------------------------------------------------------------
# Vocabulary tables
# ---------------------------------------------------------------------------

_PRODUCTS: list[tuple[str, list[str]]] = [
    ("home_loan",      ["home loan", "hl", "housing loan"]),
    ("lap",            ["lap", "loan against property"]),
    ("gold_loan",      ["gold loan", "gold"]),
    ("microfinance",   ["microfinance", "micro finance", "mfi", "jlg", "member loan"]),
    ("personal_loan",  ["personal loan"]),          # "pl" removed — matches inside "applicant"
    ("auto_loan",      ["auto loan", "vehicle loan", "two wheeler", "car loan"]),
    ("business_loan",  ["business loan", "sme loan", "msme loan"]),
]

_WORKFLOWS: list[tuple[str, list[str]]] = [
    ("kyc",          ["kyc", "know your customer", "pan", "form 60", "ckyc", "nsdl",
                      "identity", "aadhar", "aadhaar"]),
    ("lead",         ["lead", "sourcing", "partner", "channel", "attribution",
                      "draft lead", "lead creation", "lead queue"]),
    ("eligibility",  ["eligibility", "eligible", "bureau score", "cibil", "foir",
                      "credit score", "write-off", "settlement", "dpd",
                      "minimum score", "stp", "age", "tenure", "income"]),
    ("appraisal",    ["appraisal", "appraise", "valuation", "gold testing", "purity",
                      "ltv", "loan to value"]),
    ("sanction",     ["sanction", "sanction letter", "approval", "approve",
                      "credit committee", "sanctioned amount"]),
    ("disbursement", ["disbursement", "disburse", "margin", "release", "payout"]),
    ("collection",   ["collection", "overdue", "dpd", "repayment", "missed payment",
                      "reminder", "notice", "npa", "emi due"]),
    ("auction",      ["auction", "default", "cure period", "foreclosure"]),
    ("compliance",   ["compliance", "fraud", "maker checker", "segregation",
                      "separation of duties", "aml", "regulatory"]),
    ("partner",      ["partner", "dsa", "dealer", "channel partner",
                      "due diligence", "agreement", "payout reconcil"]),
]

_ROLES: list[tuple[str, list[str]]] = [
    ("branch_manager",      ["branch manager"]),
    ("credit_officer",      ["credit officer", "credit ops", "credit operations"]),
    ("credit_manager",      ["credit manager"]),
    ("credit_committee",    ["credit committee"]),
    ("loan_officer",        ["loan officer"]),
    ("compliance_officer",  ["compliance officer"]),
    ("recovery_officer",    ["recovery officer"]),
    ("field_officer",       ["field officer"]),
    ("operations_officer",  ["operations officer"]),
    ("gold_appraiser",      ["gold appraiser", "appraiser"]),
    ("sales_executive",     ["sales executive"]),
    ("relationship_manager",["relationship manager"]),
    ("finance_officer",     ["finance officer", "disbursement officer", "payout officer"]),
    ("sourcing_officer",    ["sourcing officer", "sourcing channel actor"]),
    ("legal_officer",       ["legal officer", "legal"]),
    ("vault_custodian",     ["vault custodian"]),
    ("channel_manager",     ["channel manager"]),
    ("audit",               ["audit", "auditor"]),
]

# Patterns that mean "give me one rule" vs "give me all rules"
_SINGLE_SIGNALS: list[str] = [
    r"\bwhat is\b",
    r"\bwhat's\b",
    r"\bwhen is\b",
    r"\bwhen does\b",
    r"\bwhich rule\b",
    r"\bthe rule\b",
    r"\bthe limit\b",
    r"\bthe threshold\b",
    r"\bthe minimum\b",
    r"\bthe maximum\b",
    r"\bthe requirement\b",
    r"\bwhat happens when\b",
    r"\bwhat action\b",
]

_MULTIPLE_SIGNALS: list[str] = [
    r"\ball rules\b",
    r"\bwhat rules\b",
    r"\bwhich rules\b",
    r"\blist.*rules?\b",
    r"\bshow.*rules?\b",
    r"\ball.*applicable\b",
    r"\beverything.*applies\b",
]

# Threshold pattern: number + optional unit
# Matches: "50%", "₹5 lakh", "5 lakh", "30 days", "700", "18 years", "2 years",
#          "1,000,000", "₹50,00,000", "675"
_THRESHOLD_RE = re.compile(
    r"(?:₹\s?)?(\d[\d,]*(?:\.\d+)?)\s*"
    r"(%|percent|lakh|crore|thousand|days?|years?|months?|k\b)?",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Extractor
# ---------------------------------------------------------------------------

class QueryIntentExtractor:

    def extract(self, query: str) -> QueryIntent:
        low = query.lower().strip()
        return QueryIntent(
            product     = self._extract_product(low),
            workflow    = self._extract_workflow(low),
            threshold   = self._extract_threshold(low),
            role        = self._extract_role(low),
            cardinality = self._extract_cardinality(low),
        )

    # ── Field extractors ──────────────────────────────────────────────────

   
    @staticmethod
    def _extract_product(low: str) -> Optional[str]:
        for canonical, keywords in _PRODUCTS:
            for kw in keywords:
                # Match phrases normally, but require word boundaries
                # for short aliases to avoid accidental substring matches.
                if len(kw) <= 3:
                    pattern = rf"\b{re.escape(kw)}\b"
                    if re.search(pattern, low):
                        return canonical
                elif kw in low:
                    return canonical
        return None

    @staticmethod
    def _extract_workflow(low: str) -> Optional[str]:
        # Score each workflow by number of keyword matches so the
        # most specific match wins when multiple workflows signal
        scores: dict[str, int] = {}
        for canonical, keywords in _WORKFLOWS:
            for kw in keywords:
                if kw in low:
                    scores[canonical] = scores.get(canonical, 0) + 1
        if not scores:
            return None
        return max(scores, key=lambda k: scores[k])

    @staticmethod
    def _extract_threshold(low: str) -> Optional[str]:
        matches = _THRESHOLD_RE.findall(low)
        if not matches:
            return None
        # Return the first meaningful match (skip bare "1" or "0")
        for number, unit in matches:
            num_clean = number.replace(",", "")
            try:
                val = float(num_clean)
            except ValueError:
                continue
            if val == 0:
                continue
            # Skip very small bare numbers that are likely ordinals ("top 5", "rank 1")
            if val < 10 and not unit:
                continue
            if unit:
                return f"{number} {unit}".strip()
            return number
        return None

    @staticmethod
    def _extract_role(low: str) -> Optional[str]:
        for canonical, keywords in _ROLES:
            for kw in keywords:
                if kw in low:
                    return canonical
        return None

    @staticmethod
    def _extract_cardinality(low: str) -> str:
        for pattern in _MULTIPLE_SIGNALS:
            if re.search(pattern, low):
                return "multiple"
        for pattern in _SINGLE_SIGNALS:
            if re.search(pattern, low):
                return "single"
        # Default: treat as single — most rule queries are point lookups
        return "single"


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_extractor = QueryIntentExtractor()


def extract_query_intent(query: str) -> QueryIntent:
    """Module-level convenience wrapper."""
    return _extractor.extract(query)
