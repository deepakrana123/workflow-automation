"""
Phase 4 — Synthetic business rule fixtures for ground-truth evaluation.

These rules are manually curated to support Phase 4 ground-truth queries.
They are NOT auto-generated and are versioned with the ground-truth dataset.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SyntheticBusinessRule:
    """Synthetic WorkflowBusinessRule for evaluation."""
    rule_id: str
    rule_name: str
    rule_text: str
    workspace_id: str
    tenant_id: str
    description: str


# Synthetic business rules indexed by rule_id
SYNTHETIC_RULES: dict[str, SyntheticBusinessRule] = {}


def _add_rule(
    rule_id: str,
    rule_name: str,
    rule_text: str,
    workspace_id: str,
    tenant_id: str = "tenant_001",
    description: str = "",
):
    """Helper to add a rule to the fixture database."""
    SYNTHETIC_RULES[rule_id] = SyntheticBusinessRule(
        rule_id=rule_id,
        rule_name=rule_name,
        rule_text=rule_text,
        workspace_id=workspace_id,
        tenant_id=tenant_id,
        description=description,
    )


# === ELIGIBILITY RULES (BR_ELIGIBILITY_*) ===
_add_rule(
    "BR_ELIGIBILITY_001",
    "Base Eligibility Requirements",
    "Applicant must be a resident of India, possess a valid government-issued ID, maintain an active bank account, and have no ongoing fraud investigations.",
    "ws_alpha",
    description="Core eligibility: residency, ID, bank account, clean record.",
)

_add_rule(
    "BR_ELIGIBILITY_002",
    "Salaried vs. Self-Employed Eligibility",
    "Both salaried employees and self-employed individuals are eligible. Self-employed applicants must provide additional documentation.",
    "ws_alpha",
    description="Employment type eligibility with documentation variance.",
)

# === EMPLOYMENT RULES (BR_EMPLOYMENT_*) ===
_add_rule(
    "BR_EMPLOYMENT_003",
    "Self-Employed Applicant Requirements",
    "Self-employed individuals must have been in business for at least 2 years and provide tax returns, business registration, and profit-loss statements.",
    "ws_alpha",
    description="Self-employed specific requirements: 2-year tenure, documentation.",
)

_add_rule(
    "BR_EMPLOYMENT_009",
    "Work Experience Requirement",
    "Applicant must have a minimum of 2 years of continuous work experience in the current field.",
    "ws_alpha",
    description="Minimum 2 years continuous work experience.",
)

_add_rule(
    "BR_EMPLOYMENT_010",
    "Experience Calculation",
    "Work experience is calculated from the date of joining to the application date. Career breaks of more than 3 months in the last 5 years require written justification.",
    "ws_alpha",
    description="Experience calculation method and career break tolerance.",
)

_add_rule(
    "BR_EMPLOYMENT_011",
    "Continuous Employment History",
    "Employment history must be continuous without unexplained gaps exceeding 3 months. Job changes are acceptable if the applicant remains employed in a similar field.",
    "ws_alpha",
    description="Continuity requirement: max 3-month gaps, field consistency.",
)

_add_rule(
    "BR_EMPLOYMENT_012",
    "Employment Category Coverage",
    "This program covers: Salaried employees, Self-employed (business owners), Professionals (doctors, lawyers, CA, engineers), Farmers (with land ownership proof), and Gig workers (with 1-year documented history).",
    "ws_alpha",
    description="Supported employment categories and gig worker inclusion.",
)

# === INCOME RULES (BR_INCOME_*) ===
_add_rule(
    "BR_INCOME_005",
    "Minimum Monthly Income",
    "Applicant must have a minimum monthly income of INR 20,000.",
    "ws_alpha",
    description="Base income threshold: 20,000 INR/month.",
)

_add_rule(
    "BR_INCOME_006",
    "Income Verification Methods",
    "Income must be verified through salary slips for salaried employees, income tax returns for self-employed, or bank statements for gig workers. Minimum 3 months of proof required.",
    "ws_alpha",
    description="Income proof methods and tenure (3 months).",
)

_add_rule(
    "BR_INCOME_007",
    "Joint and Household Income",
    "Household income (including spouse/co-applicant) can be combined towards the minimum income requirement. Co-applicant must meet all other eligibility criteria.",
    "ws_alpha",
    description="Joint income eligibility; co-applicant must qualify.",
)

_add_rule(
    "BR_INCOME_008",
    "Upper Income Ceiling",
    "There is no upper income limit; however, applicants with annual income exceeding INR 50 lakh are routed to the premium loan product.",
    "ws_alpha",
    description="No cap; high earners redirected to premium product.",
)

# === CREDIT RULES (BR_CREDIT_*) ===
_add_rule(
    "BR_CREDIT_015",
    "Minimum Credit Score",
    "Applicant must have a CIBIL score of at least 650 for standard approval.",
    "ws_alpha",
    description="Minimum CIBIL score threshold: 650.",
)

_add_rule(
    "BR_CREDIT_016",
    "Credit Score Range for Approval",
    "CIBIL scores between 650 and 900 are eligible. Scores below 650 are subject to manual review.",
    "ws_alpha",
    description="Credit score range eligibility and review threshold.",
)

_add_rule(
    "BR_CREDIT_017",
    "Credit History Assessment",
    "Credit history must span at least 12 months with no defaults, payment delays >30 days, or active legal disputes in the past 12 months.",
    "ws_alpha",
    description="12-month clean history: no defaults, delays >30 days, or disputes.",
)

_add_rule(
    "BR_CREDIT_018",
    "Payment History Weight",
    "A clean payment history is the primary factor in credit assessment. One-time delays <30 days do not disqualify but reduce approval limit.",
    "ws_alpha",
    description="Payment history priority; minor delays impact limit, not approval.",
)

_add_rule(
    "BR_CREDIT_019",
    "Past Defaults and Bankruptcies",
    "Applicants with a bankruptcy in the past 7 years or an active default are not eligible.",
    "ws_alpha",
    description="Bankruptcy (7-year bar) and active default disqualify.",
)

# === AGE RULES (BR_AGE_*) ===
_add_rule(
    "BR_AGE_024",
    "Minimum Age Requirement",
    "Applicant must be at least 21 years old at the time of application.",
    "ws_alpha",
    description="Minimum age: 21 years.",
)

_add_rule(
    "BR_AGE_025",
    "Age Proof Documentation",
    "Age must be verified through a valid government-issued ID (Aadhar, PAN, passport, or driver's license).",
    "ws_alpha",
    description="Age proof methods: Aadhar, PAN, passport, driver's license.",
)

_add_rule(
    "BR_AGE_026",
    "Maximum Age Limit",
    "Applicant must not exceed 60 years of age. Loan tenure cannot extend beyond the applicant's 65th birthday.",
    "ws_alpha",
    description="Max age 60; tenure constraint to age 65.",
)

# === LOAN LIMITS RULES (BR_LOAN_*) ===
_add_rule(
    "BR_LOAN_027",
    "Maximum Loan Amount",
    "Maximum loan amount is the minimum of: (a) 50x monthly income, or (b) INR 25 lakh.",
    "ws_alpha",
    description="Loan cap: min(50x monthly income, 25 lakh).",
)

_add_rule(
    "BR_LOAN_028",
    "Loan Amount Based on Credit Score",
    "Applicants with CIBIL ≥750 qualify for up to 60x monthly income (capped at 30 lakh). Applicants with CIBIL 650–749 qualify for standard limits.",
    "ws_alpha",
    description="Credit-score-based loan ceiling: ≥750 → higher limit.",
)

_add_rule(
    "BR_LOAN_029",
    "Minimum Loan Amount",
    "Minimum loan amount is INR 50,000.",
    "ws_alpha",
    description="Minimum loan size: 50K INR.",
)

_add_rule(
    "BR_LOAN_030",
    "Loan Tenure Options",
    "Loan tenure can range from 12 months to 84 months (7 years). Tenure can be selected in multiples of 6 months.",
    "ws_alpha",
    description="Tenure: 12–84 months, 6-month increments.",
)

_add_rule(
    "BR_LOAN_031",
    "Tenure Based on Loan Amount",
    "Loans ≤5 lakh: 12–60 months. Loans 5–15 lakh: 12–72 months. Loans >15 lakh: 12–84 months.",
    "ws_alpha",
    description="Tenure brackets by loan amount.",
)

# === GEOGRAPHIC RULES (BR_GEO_*) ===
_add_rule(
    "BR_GEO_032",
    "Eligible States and Territories",
    "Personal loans are available in all Indian states and Union Territories, except: Manipur, Mizoram, and Nagaland (ongoing due diligence).",
    "ws_alpha",
    description="Coverage: all states except Manipur, Mizoram, Nagaland.",
)

_add_rule(
    "BR_GEO_033",
    "Urban and Rural Availability",
    "Loans are available in both urban and rural areas, provided the applicant's residence is documented and verifiable.",
    "ws_alpha",
    description="Urban + rural coverage with residence verification.",
)

_add_rule(
    "BR_GEO_034",
    "Remote Area Processing",
    "Remote/tribal areas may require additional KYC verification. Applications are processed but may involve a 2–3 week extended review.",
    "ws_alpha",
    description="Remote/tribal areas: additional KYC, 2–3 week review.",
)

_add_rule(
    "BR_GEO_035",
    "Excluded Regions",
    "The following regions are currently excluded: Lakshadweep (processing constraints), and disaster-affected areas declared by government (temporary).",
    "ws_alpha",
    description="Exclusions: Lakshadweep, declared disaster zones.",
)

# === EXCEPTION RULES (BR_EXCEPTIONS_*) ===
_add_rule(
    "BR_EXCEPTIONS_012",
    "Self-Employment Exception",
    "Self-employed applicants with <2 years tenure but ≥1 year and strong credit profile (CIBIL ≥750) may apply for loans up to INR 10 lakh.",
    "ws_alpha",
    description="Self-employed <2yr exception: 1+ yr + CIBIL≥750 → max 10L.",
)

_add_rule(
    "BR_EXCEPTIONS_013",
    "Joint Income Exception",
    "If primary applicant's income is below INR 20,000 but household income ≥20,000 with co-applicant, both must meet all other criteria. Co-applicant liability is 100%.",
    "ws_alpha",
    description="Joint income exception: co-applicant fully liable.",
)

_add_rule(
    "BR_EXCEPTIONS_014",
    "Recent Job Change Exception",
    "Applicants with <3 months in current role but ≥5 years in the field and CIBIL ≥700 may apply.",
    "ws_alpha",
    description="New job exception: <3mo current, 5y+ field, CIBIL≥700.",
)

_add_rule(
    "BR_EXCEPTIONS_015",
    "Senior Applicant Exception",
    "Applicants aged 60–70 may apply with additional health/life insurance requirement. Loans must mature by age 75.",
    "ws_alpha",
    description="Senior exception (60–70): insurance required, mature by 75.",
)

_add_rule(
    "BR_EXCEPTIONS_016",
    "Rural Applicant Fast-Track",
    "Applicants in NABARD-classified rural areas with proven income may get 50% fee waiver and simplified documentation.",
    "ws_alpha",
    description="Rural fast-track: 50% fee waiver, simplified docs.",
)

_add_rule(
    "BR_EXCEPTIONS_017",
    "Non-Traditional Income Proof",
    "Gig workers and contract workers with <3 months of bank statement history may provide employer letters or platform earnings statements (last 12 months).",
    "ws_alpha",
    description="Gig/contract: employer letter or platform statement (12mo).",
)

_add_rule(
    "BR_EXCEPTIONS_018",
    "Guarantor/Co-Borrower Option",
    "Applicant who does not meet all criteria may apply with a guarantor who meets full eligibility. Guarantor's income can supplement.",
    "ws_alpha",
    description="Guarantor/co-borrower option for partial disqualification.",
)

_add_rule(
    "BR_EXCEPTIONS_019",
    "Existing Customer Fast-Track",
    "Existing deposit or loan customers with 1+ year relationship and no defaults get 25% faster processing and relaxed income documentation.",
    "ws_alpha",
    description="Existing customer fast-track: 25% faster, relaxed docs.",
)

# === REJECTION RULES (BR_REJECTION_*) ===
_add_rule(
    "BR_REJECTION_020",
    "Primary Rejection Criteria",
    "Application is rejected if: (a) CIBIL score <650, (b) Active fraud investigation, (c) Ongoing bankruptcy/insolvency proceedings, (d) Age <21 or >60, (e) No verifiable income.",
    "ws_alpha",
    description="Primary rejection: CIBIL<650, fraud, bankruptcy, age, no income.",
)

_add_rule(
    "BR_REJECTION_021",
    "Rejection by Default History",
    "Applicant is rejected if any of: (a) 2+ defaults in last 24 months, (b) 1 default in last 12 months, (c) Ongoing legal dispute over loan/debt.",
    "ws_alpha",
    description="Rejection by defaults: 2+ in 24mo, 1 in 12mo, legal disputes.",
)

_add_rule(
    "BR_REJECTION_022",
    "Credit Score Below Minimum",
    "CIBIL score below 650 is grounds for automatic rejection unless applicant qualifies for manual review exception.",
    "ws_alpha",
    description="CIBIL<650 automatic rejection (manual review possible).",
)

_add_rule(
    "BR_REJECTION_023",
    "Bankruptcy and Fraud",
    "Any applicant with bankruptcy in past 7 years or history of fraud/forgery is automatically rejected.",
    "ws_alpha",
    description="Bankruptcy (7yr) or fraud → automatic rejection.",
)

_add_rule(
    "BR_REJECTION_024",
    "Existing High Debt Burden",
    "Applicant is rejected if existing EMI obligations exceed 50% of monthly income.",
    "ws_alpha",
    description="Rejection: existing EMI >50% of income.",
)

_add_rule(
    "BR_REJECTION_025",
    "Debt-to-Income Ratio Limit",
    "Total debt-to-income ratio (including proposed EMI) cannot exceed 60%. Applicants exceeding this are rejected.",
    "ws_alpha",
    description="Rejection: total DTI (with new loan) >60%.",
)

_add_rule(
    "BR_REJECTION_026",
    "Fraud and Enforcement History",
    "Any applicant with a fraud/forgery conviction in the past 10 years is rejected. Cases of cheque bounce or willful default in past 5 years require manual review.",
    "ws_alpha",
    description="Fraud (10yr) rejection; cheque bounce/willful default (5yr) manual review.",
)

# Build index
RULES_BY_ID = SYNTHETIC_RULES
RULES_BY_WORKSPACE = {}
for rule_id, rule in SYNTHETIC_RULES.items():
    ws_id = rule.workspace_id
    if ws_id not in RULES_BY_WORKSPACE:
        RULES_BY_WORKSPACE[ws_id] = []
    RULES_BY_WORKSPACE[ws_id].append(rule)

# Summary statistics
FIXTURE_STATS = {
    "total_rules": len(SYNTHETIC_RULES),
    "rules_by_category": {
        "eligibility": 2,
        "employment": 4,
        "income": 4,
        "credit": 6,
        "age": 3,
        "loan_limits": 5,
        "geographic": 4,
        "exceptions": 8,
        "rejection": 7,
    },
}
