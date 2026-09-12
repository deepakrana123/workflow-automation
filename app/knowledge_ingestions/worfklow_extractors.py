from pydantic import ValidationError

from app.nlp.llm_manager.llm_manager import LLMManager
from app.knowledge_ingestions.schemas import WorkflowExtraction
from app.knowledge_ingestions.exceptions import WorkflowExtractionError
from app.core.logger import logger

from app.prompting import PromptManager, PromptContext, PromptKey


# ── Compact output example ────────────────────────────────────────────────────
# Passed to the LLM as {schema} instead of model_json_schema().
#
# Why: Pydantic's model_json_schema() emits a verbose $defs-heavy JSON Schema
# object. Smaller models (GPT-4o-mini, Llama) confuse it with the expected
# output and echo the schema back instead of filling it. A concrete filled
# example is unambiguous — the model sees exactly what shape to return.
#
# The example deliberately shows 7+ actions and 5+ rules to signal that
# exhaustive extraction is expected — not a brief summary.
_OUTPUT_EXAMPLE = """{
  "workflow_name": "Retail Loan Sourcing and Evaluation",
  "summary": "End-to-end workflow for capturing, validating, evaluating, and routing retail loan applications across digital and branch channels prior to underwriting handoff.",
  "triggers": [
    {
      "name": "Customer submits loan application",
      "description": "Customer submits a retail loan application via digital portal, branch, or DSA channel.",
      "applicable_rules": ["Mandatory fields must be complete before LRN is created"],
      "responsible_actors": ["Customer (initiator)"]
    },
    {
      "name": "Valid customer consent received",
      "description": "Customer provides OTP-based consent for bureau pull and Aadhaar e-KYC.",
      "applicable_rules": ["Bureau pull requires explicit timestamped OTP consent"],
      "responsible_actors": ["Customer (initiator)"]
    }
  ],
  "action_references": [
    {
      "name": "Create Lead Reference Number",
      "description": "Generate unique Lead Reference Number as soon as initial customer contact is initiated.",
      "applicable_rules": ["LRN must be created before eligibility evaluation begins"],
      "responsible_actors": []
    },
    {
      "name": "Validate Mandatory Fields",
      "description": "Check that all mandatory fields are present and block lead progression if any are missing.",
      "applicable_rules": ["Hard stop if Name, Mobile, PAN, Pincode, Product, Amount, or Consent are missing"],
      "responsible_actors": ["Sales Executive (initiator)"]
    },
    {
      "name": "Verify PAN",
      "description": "Validate PAN status and name match against NSDL database in real time.",
      "applicable_rules": [
        "PAN status must be EXISTING AND VALID",
        "Name must match customer entry within 85% fuzzy match threshold",
        "Lead must be halted if PAN is marked Inoperative"
      ],
      "responsible_actors": []
    },
    {
      "name": "Perform Aadhaar e-KYC",
      "description": "Execute OTP-based or offline XML Aadhaar verification to retrieve demographic data.",
      "applicable_rules": ["Switch to biometric or OKYC after 3 failed OTP attempts"],
      "responsible_actors": []
    },
    {
      "name": "Execute Deduplication Check",
      "description": "Check incoming lead against existing records using PAN, Mobile Number, Aadhaar Hash, and Bank Account Number.",
      "applicable_rules": [
        "Reject new lead if matching PAN or Aadhaar is in active pending sanction",
        "Block lead under cooling-off period if rejection was within past 90 days"
      ],
      "responsible_actors": []
    },
    {
      "name": "Trigger Credit Bureau Pull",
      "description": "Initiate automated credit bureau enquiry and parse score and history from the response.",
      "applicable_rules": [
        "Bureau pull requires valid customer consent",
        "Minimum bureau score of 675 required for PL and BL",
        "Score below 675 results in automated immediate rejection",
        "Borderline score 675 to 719 requires Senior Credit Officer review"
      ],
      "responsible_actors": ["Credit Officer (reviewer)"]
    },
    {
      "name": "Calculate FOIR",
      "description": "Compute Fixed Obligation to Income Ratio based on existing EMIs and proposed loan EMI against verified net monthly income.",
      "applicable_rules": [
        "Maximum permissible FOIR is 45% for income slab 20000 to 35000",
        "Maximum permissible FOIR is 55% for income slab 35001 to 75000",
        "Maximum permissible FOIR is 65% for income above 75000",
        "FOIR exceeding hard threshold results in automatic rejection REJ-FOIR-03"
      ],
      "responsible_actors": []
    },
    {
      "name": "Classify Lead",
      "description": "Assign lead to one of five categories: STP, Non-STP, Needs Additional Information, Manual Review, or Hard Reject.",
      "applicable_rules": [
        "STP requires credit score above 720, FOIR within limit, digital KYC verified, zero document defects"
      ],
      "responsible_actors": ["Sourcing Operations (classifier)"]
    },
    {
      "name": "Route Lead to Fulfillment Queue",
      "description": "Assign eligible lead to appropriate branch and RM based on pincode mapping and workload.",
      "applicable_rules": [
        "Maximum 25 active leads per RM at any time",
        "Personal Loans above 1000000 or Business Loans above 2500000 tagged Priority 1 High Value"
      ],
      "responsible_actors": ["Sales Executive (assignee)"]
    },
    {
      "name": "Generate Rejection Notice",
      "description": "Produce standardized rejection code and customer-facing communication for every rejected lead.",
      "applicable_rules": ["Every rejected lead must carry a standardized rejection code"],
      "responsible_actors": []
    }
  ],
  "business_rules": [
    {"rule": "Minimum bureau score of 675 required for Personal Loan and Business Loan approval."},
    {"rule": "Hard rejection for bureau score below 675. No manual overrides except ETB customers with 24 months spotless repayment."},
    {"rule": "Zero instances of DPD greater than 30 days allowed in the past 6 months."},
    {"rule": "FOIR hard rejection thresholds: above 50% for income 20000-35000, above 60% for 35001-75000, above 70% for above 75000."},
    {"rule": "Sourcing restricted to active pincodes within 35 km radius for unsecured loans and 50 km for secured loans."},
    {"rule": "Leads generated outside active pincodes must be tagged Rejected Non-Serviced Location."},
    {"rule": "Cooling-off period of 90 calendar days applies after any application rejection."},
    {"rule": "Maximum 3 unsecured loan inquiries permitted in the past 30 days before flagging as Credit Hungry."},
    {"rule": "DSA code must be active and verified before lead submission is accepted."},
    {"rule": "Digital channel takes precedence over DSA for the same customer within 7 days."}
  ],
  "actors": [
    {"name": "Customer", "role": "Applicant"},
    {"name": "Sales Executive", "role": "Relationship Manager"},
    {"name": "Sourcing Operations", "role": "Central Operations"},
    {"name": "Credit Officer", "role": "Underwriter"},
    {"name": "Compliance Officer", "role": "Legal and Regulatory"},
    {"name": "DSA", "role": "Channel Partner"}
  ],
  "external_systems": [
    {"name": "NSDL", "description": "PAN verification authority."},
    {"name": "UIDAI", "description": "Aadhaar e-KYC provider."},
    {"name": "CIBIL", "description": "Primary credit bureau for score and history."},
    {"name": "CKYC Registry", "description": "Centralized KYC repository fallback when Aadhaar is unavailable."}
  ],
  "assumptions": [
    "Customer has consented to bureau pull and Aadhaar verification before processing begins.",
    "All pincodes are pre-mapped to branches in the master geography database."
  ]
}"""


class WorkflowExtractor:
    def __init__(self):
        self.prompt_manager = PromptManager()
        self._llm = LLMManager()

    def extract(self, document_text: str) -> WorkflowExtraction:
        if not document_text.strip():
            raise WorkflowExtractionError("Document text is empty.")

        prompt = self.prompt_manager.build(
            PromptKey.WORKFLOW_EXTRACTION,
            PromptContext(
                variables={
                    "schema": _OUTPUT_EXAMPLE,
                    "text": document_text,
                }
            ),
        )

        # BRD extraction requires a large-context, instruction-following model.
        # Try Gemini first (real key, 90s timeout, large context window).
        # Fall back to the standard waterfall if Gemini is unhealthy or fails.
        result = None
        try:
            result = self._llm.generate_with_provider(prompt, "gemini")
        except Exception:
            pass

        if result is None or not result.get("success"):
            result = self._llm.generate(prompt)

        if not result["success"]:
            raise WorkflowExtractionError(result.get("error", "LLM call failed"))

        try:
            extraction = WorkflowExtraction.model_validate_json(result["output"])
            logger.info(
                "workflow_extraction_complete",
                extra={"extra_data": {
                    "provider":          result.get("provider"),
                    "actions_extracted": len(extraction.action_references),
                    "rules_extracted":   len(extraction.business_rules),
                    "triggers_extracted": len(extraction.triggers),
                    "workflow_name":     extraction.workflow_name,
                }},
            )
            return extraction

        except ValidationError as e:
            raise WorkflowExtractionError(
                f"Invalid workflow extraction: {e}"
            ) from e
