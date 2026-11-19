"""
Phase 4 — Ground-truth evaluation dataset for business rule retrieval quality benchmark.

This dataset contains:
- 40 synthetic queries covering 10 categories (Personal Loan BRD scenarios)
- Manually defined expected relevant WorkflowBusinessRule IDs per query
- Query category, rationale, and difficulty classification

Ground truth is versioned and NOT auto-generated from retrieval results.
"""

from dataclasses import dataclass
from typing import List, Set
from enum import Enum


class QueryCategory(Enum):
    """Query categories from Phase 4 specification."""
    ELIGIBILITY = "eligibility_criteria"
    INCOME = "minimum_income_requirements"
    EMPLOYMENT = "employment_and_work_experience"
    CREDIT = "credit_score_and_history"
    AGE = "age_restrictions"
    LOAN_LIMITS = "loan_amount_and_tenure_limits"
    GEOGRAPHY = "geographic_restrictions"
    EXCEPTIONS = "exceptions_and_conditional_policies"
    REJECTION = "rejection_conditions"
    SIMILAR_WORDING = "similar_wording_different_meaning"


class QueryDifficulty(Enum):
    """Query difficulty for ranking analysis."""
    EASY = "easy"  # Exact keyword match
    MEDIUM = "medium"  # Semantic paraphrase or partial match
    HARD = "hard"  # Ambiguous, complex, or indirect reference
    IMPOSSIBLE = "impossible"  # No relevant result exists


@dataclass
class GroundTruthQuery:
    """Single ground-truth query with expected relevant rules."""
    query_id: str
    query_text: str
    category: QueryCategory
    difficulty: QueryDifficulty
    workspace_id: str
    expected_relevant_rule_ids: Set[str]
    rationale: str


# Synthetic ground-truth dataset (40 queries, 10 categories × 4 per category)
GROUND_TRUTH_QUERIES = [
    # === ELIGIBILITY (1–4) ===
    GroundTruthQuery(
        query_id="Q001",
        query_text="What are the basic eligibility criteria for a personal loan?",
        category=QueryCategory.ELIGIBILITY,
        difficulty=QueryDifficulty.EASY,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_ELIGIBILITY_001", "BR_ELIGIBILITY_002"},
        rationale="Direct keyword match on 'eligibility criteria'; should match rules covering base eligibility.",
    ),
    GroundTruthQuery(
        query_id="Q002",
        query_text="Can self-employed individuals apply for a personal loan?",
        category=QueryCategory.ELIGIBILITY,
        difficulty=QueryDifficulty.MEDIUM,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_EMPLOYMENT_003", "BR_EXCEPTIONS_012"},
        rationale="Semantic: self-employed → employment type; may require exception rule.",
    ),
    GroundTruthQuery(
        query_id="Q003",
        query_text="Am I eligible if I have a valid ID and a bank account?",
        category=QueryCategory.ELIGIBILITY,
        difficulty=QueryDifficulty.HARD,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_ELIGIBILITY_001"},
        rationale="Indirect reference to KYC/documentation; ambiguous wording.",
    ),
    GroundTruthQuery(
        query_id="Q004",
        query_text="What disqualifies someone from getting a personal loan?",
        category=QueryCategory.ELIGIBILITY,
        difficulty=QueryDifficulty.MEDIUM,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_REJECTION_020", "BR_REJECTION_021"},
        rationale="Semantic: disqualifies → rejection conditions; synonym mapping needed.",
    ),

    # === INCOME (5–8) ===
    GroundTruthQuery(
        query_id="Q005",
        query_text="What is the minimum monthly income required?",
        category=QueryCategory.INCOME,
        difficulty=QueryDifficulty.EASY,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_INCOME_005", "BR_INCOME_006"},
        rationale="Direct keyword match on 'minimum monthly income'.",
    ),
    GroundTruthQuery(
        query_id="Q006",
        query_text="Does household income count towards the income requirement?",
        category=QueryCategory.INCOME,
        difficulty=QueryDifficulty.MEDIUM,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_INCOME_007", "BR_EXCEPTIONS_013"},
        rationale="Semantic: household income → combined/joint income rules.",
    ),
    GroundTruthQuery(
        query_id="Q007",
        query_text="How much must I earn to qualify?",
        category=QueryCategory.INCOME,
        difficulty=QueryDifficulty.EASY,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_INCOME_005"},
        rationale="Paraphrase of income requirement; should match with synonym detection.",
    ),
    GroundTruthQuery(
        query_id="Q008",
        query_text="Is there a maximum income limit beyond which I cannot apply?",
        category=QueryCategory.INCOME,
        difficulty=QueryDifficulty.HARD,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_INCOME_008"},
        rationale="Indirect: maximum income → income cap rules; may be rare.",
    ),

    # === EMPLOYMENT (9–12) ===
    GroundTruthQuery(
        query_id="Q009",
        query_text="How many years of work experience do I need?",
        category=QueryCategory.EMPLOYMENT,
        difficulty=QueryDifficulty.EASY,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_EMPLOYMENT_009", "BR_EMPLOYMENT_010"},
        rationale="Direct keyword match on 'work experience'.",
    ),
    GroundTruthQuery(
        query_id="Q010",
        query_text="Can someone with less than 1 year at their current job apply?",
        category=QueryCategory.EMPLOYMENT,
        difficulty=QueryDifficulty.MEDIUM,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_EMPLOYMENT_009", "BR_EXCEPTIONS_014"},
        rationale="Semantic: job tenure → employment duration rules.",
    ),
    GroundTruthQuery(
        query_id="Q011",
        query_text="Does the experience have to be continuous?",
        category=QueryCategory.EMPLOYMENT,
        difficulty=QueryDifficulty.HARD,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_EMPLOYMENT_011"},
        rationale="Implicit: continuous work history vs. gaps; requires domain knowledge.",
    ),
    GroundTruthQuery(
        query_id="Q012",
        query_text="What employment types are covered by this personal loan program?",
        category=QueryCategory.EMPLOYMENT,
        difficulty=QueryDifficulty.MEDIUM,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_EMPLOYMENT_003", "BR_EMPLOYMENT_012"},
        rationale="Broad query; should match rules covering multiple employment categories.",
    ),

    # === CREDIT (13–16) ===
    GroundTruthQuery(
        query_id="Q013",
        query_text="What credit score is required to get approved?",
        category=QueryCategory.CREDIT,
        difficulty=QueryDifficulty.EASY,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_CREDIT_015", "BR_CREDIT_016"},
        rationale="Direct keyword match on 'credit score'.",
    ),
    GroundTruthQuery(
        query_id="Q014",
        query_text="Will I be rejected if my credit score is below 500?",
        category=QueryCategory.CREDIT,
        difficulty=QueryDifficulty.MEDIUM,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_CREDIT_015", "BR_REJECTION_022"},
        rationale="Semantic: credit score threshold → rejection condition.",
    ),
    GroundTruthQuery(
        query_id="Q015",
        query_text="Does credit history matter, or just the current score?",
        category=QueryCategory.CREDIT,
        difficulty=QueryDifficulty.HARD,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_CREDIT_017", "BR_CREDIT_018"},
        rationale="Implicit: credit history vs. score distinction; nuanced policy.",
    ),
    GroundTruthQuery(
        query_id="Q016",
        query_text="What if I've had past defaults or bankruptcies?",
        category=QueryCategory.CREDIT,
        difficulty=QueryDifficulty.MEDIUM,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_CREDIT_019", "BR_REJECTION_023"},
        rationale="Semantic: defaults/bankruptcies → credit history factors → rejection.",
    ),

    # === AGE (17–20) ===
    GroundTruthQuery(
        query_id="Q017",
        query_text="What is the minimum age to apply for a personal loan?",
        category=QueryCategory.AGE,
        difficulty=QueryDifficulty.EASY,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_AGE_024", "BR_AGE_025"},
        rationale="Direct keyword match on 'minimum age'.",
    ),
    GroundTruthQuery(
        query_id="Q018",
        query_text="Can seniors above 70 still get a loan?",
        category=QueryCategory.AGE,
        difficulty=QueryDifficulty.MEDIUM,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_AGE_026", "BR_EXCEPTIONS_015"},
        rationale="Semantic: seniors → age group; may have exceptions.",
    ),
    GroundTruthQuery(
        query_id="Q019",
        query_text="Is there an upper age limit?",
        category=QueryCategory.AGE,
        difficulty=QueryDifficulty.EASY,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_AGE_026"},
        rationale="Direct: upper age limit → maximum age rule.",
    ),
    GroundTruthQuery(
        query_id="Q020",
        query_text="Must the borrower be 18 or above at the time of application?",
        category=QueryCategory.AGE,
        difficulty=QueryDifficulty.HARD,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_AGE_024"},
        rationale="Explicit temporal constraint; requires careful interpretation.",
    ),

    # === LOAN LIMITS (21–24) ===
    GroundTruthQuery(
        query_id="Q021",
        query_text="What is the maximum loan amount I can borrow?",
        category=QueryCategory.LOAN_LIMITS,
        difficulty=QueryDifficulty.EASY,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_LOAN_027", "BR_LOAN_028"},
        rationale="Direct keyword match on 'maximum loan amount'.",
    ),
    GroundTruthQuery(
        query_id="Q022",
        query_text="Can I get a personal loan for less than 10,000?",
        category=QueryCategory.LOAN_LIMITS,
        difficulty=QueryDifficulty.MEDIUM,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_LOAN_029"},
        rationale="Semantic: minimum loan amount implied by question.",
    ),
    GroundTruthQuery(
        query_id="Q023",
        query_text="What loan tenure options are available?",
        category=QueryCategory.LOAN_LIMITS,
        difficulty=QueryDifficulty.EASY,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_LOAN_030", "BR_LOAN_031"},
        rationale="Direct keyword match on 'loan tenure'.",
    ),
    GroundTruthQuery(
        query_id="Q024",
        query_text="Is a 10-year repayment period allowed?",
        category=QueryCategory.LOAN_LIMITS,
        difficulty=QueryDifficulty.MEDIUM,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_LOAN_030"},
        rationale="Specific tenure value; should match tenure range rules.",
    ),

    # === GEOGRAPHY (25–28) ===
    GroundTruthQuery(
        query_id="Q025",
        query_text="Which states or regions are eligible for this loan?",
        category=QueryCategory.GEOGRAPHY,
        difficulty=QueryDifficulty.EASY,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_GEO_032", "BR_GEO_033"},
        rationale="Direct keyword match on 'states/regions eligible'.",
    ),
    GroundTruthQuery(
        query_id="Q026",
        query_text="Can I apply if I live in a remote or rural area?",
        category=QueryCategory.GEOGRAPHY,
        difficulty=QueryDifficulty.MEDIUM,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_GEO_034", "BR_EXCEPTIONS_016"},
        rationale="Semantic: remote/rural → geographic area classification.",
    ),
    GroundTruthQuery(
        query_id="Q027",
        query_text="Are metro cities the only areas covered?",
        category=QueryCategory.GEOGRAPHY,
        difficulty=QueryDifficulty.HARD,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_GEO_032"},
        rationale="Implicit: metro-only → geographic restriction; negation handling.",
    ),
    GroundTruthQuery(
        query_id="Q028",
        query_text="Is there any region where loans are not available?",
        category=QueryCategory.GEOGRAPHY,
        difficulty=QueryDifficulty.MEDIUM,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_GEO_035"},
        rationale="Negation: excluded regions; inverse geographic rules.",
    ),

    # === EXCEPTIONS (29–32) ===
    GroundTruthQuery(
        query_id="Q029",
        query_text="Are there any exceptions to the standard eligibility rules?",
        category=QueryCategory.EXCEPTIONS,
        difficulty=QueryDifficulty.EASY,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_EXCEPTIONS_012", "BR_EXCEPTIONS_013"},
        rationale="Direct keyword match on 'exceptions'.",
    ),
    GroundTruthQuery(
        query_id="Q030",
        query_text="What if I can prove income through non-traditional sources?",
        category=QueryCategory.EXCEPTIONS,
        difficulty=QueryDifficulty.HARD,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_EXCEPTIONS_017", "BR_INCOME_007"},
        rationale="Conditional: non-traditional income → exception to standard income proof.",
    ),
    GroundTruthQuery(
        query_id="Q031",
        query_text="Can a guarantor help me qualify if I don't meet all criteria?",
        category=QueryCategory.EXCEPTIONS,
        difficulty=QueryDifficulty.MEDIUM,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_EXCEPTIONS_018"},
        rationale="Semantic: guarantor → conditional exception mechanism.",
    ),
    GroundTruthQuery(
        query_id="Q032",
        query_text="Is there a waiver or fast-track option for existing customers?",
        category=QueryCategory.EXCEPTIONS,
        difficulty=QueryDifficulty.MEDIUM,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_EXCEPTIONS_019"},
        rationale="Semantic: existing customers → loyalty exception.",
    ),

    # === REJECTION (33–36) ===
    GroundTruthQuery(
        query_id="Q033",
        query_text="What are the main reasons for loan rejection?",
        category=QueryCategory.REJECTION,
        difficulty=QueryDifficulty.EASY,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_REJECTION_020", "BR_REJECTION_021"},
        rationale="Direct keyword match on 'rejection reasons'.",
    ),
    GroundTruthQuery(
        query_id="Q034",
        query_text="Will I be rejected for having existing loans?",
        category=QueryCategory.REJECTION,
        difficulty=QueryDifficulty.MEDIUM,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_REJECTION_024"},
        rationale="Semantic: existing loans → debt/liability factor.",
    ),
    GroundTruthQuery(
        query_id="Q035",
        query_text="What if my debt-to-income ratio is too high?",
        category=QueryCategory.REJECTION,
        difficulty=QueryDifficulty.MEDIUM,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_REJECTION_025"},
        rationale="Direct: debt-to-income ratio → financial stability criterion.",
    ),
    GroundTruthQuery(
        query_id="Q036",
        query_text="Can a prior fraud case disqualify me permanently?",
        category=QueryCategory.REJECTION,
        difficulty=QueryDifficulty.HARD,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={"BR_REJECTION_026"},
        rationale="Implicit: fraud → serious background check factor; temporal scope unclear.",
    ),

    # === SIMILAR WORDING / DIFFERENT MEANING (37–40) ===
    GroundTruthQuery(
        query_id="Q037",
        query_text="Does the bank offer personal loans?",
        category=QueryCategory.SIMILAR_WORDING,
        difficulty=QueryDifficulty.HARD,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={},  # No relevant rules; product confirmation query
        rationale="Off-topic: product availability ≠ eligibility/policy rule.",
    ),
    GroundTruthQuery(
        query_id="Q038",
        query_text="Can I refinance an existing personal loan?",
        category=QueryCategory.SIMILAR_WORDING,
        difficulty=QueryDifficulty.HARD,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={},  # Outside scope: refinance ≠ new application
        rationale="Out of scope: refinance policy ≠ new loan eligibility.",
    ),
    GroundTruthQuery(
        query_id="Q039",
        query_text="What documents are required for the application?",
        category=QueryCategory.SIMILAR_WORDING,
        difficulty=QueryDifficulty.HARD,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={},  # Process, not policy
        rationale="Operational: document requirements ≠ business rule.",
    ),
    GroundTruthQuery(
        query_id="Q040",
        query_text="How long does the approval process take?",
        category=QueryCategory.SIMILAR_WORDING,
        difficulty=QueryDifficulty.HARD,
        workspace_id="ws_alpha",
        expected_relevant_rule_ids={},  # Process timeline, not eligibility
        rationale="Operational: processing time ≠ business rule.",
    ),
]


def get_queries_by_category(category: QueryCategory) -> List[GroundTruthQuery]:
    """Get all ground-truth queries for a given category."""
    return [q for q in GROUND_TRUTH_QUERIES if q.category == category]


def get_queries_by_difficulty(difficulty: QueryDifficulty) -> List[GroundTruthQuery]:
    """Get all ground-truth queries for a given difficulty level."""
    return [q for q in GROUND_TRUTH_QUERIES if q.difficulty == difficulty]


def get_queries_for_workspace(workspace_id: str) -> List[GroundTruthQuery]:
    """Get all ground-truth queries for a given workspace."""
    return [q for q in GROUND_TRUTH_QUERIES if q.workspace_id == workspace_id]


# Summary statistics
DATASET_STATS = {
    "total_queries": len(GROUND_TRUTH_QUERIES),
    "categories": len(QueryCategory),
    "queries_per_category": len(GROUND_TRUTH_QUERIES) // len(QueryCategory),
    "total_expected_relevant": sum(len(q.expected_relevant_rule_ids) for q in GROUND_TRUTH_QUERIES),
    "no_result_queries": len([q for q in GROUND_TRUTH_QUERIES if not q.expected_relevant_rule_ids]),
    "difficulty_breakdown": {
        diff.value: len(get_queries_by_difficulty(diff))
        for diff in QueryDifficulty
    },
}
