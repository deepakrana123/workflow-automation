"""
app/execution/python/action_handler_registry.py

ActionHandlerRegistry — maps handler name strings to Python callables.

This is the sole consumer of the action handler implementations.
Only PythonExecutor reads this registry.

Rule for inclusion:
  A handler belongs here if its execution is internal Python logic —
  state transitions, financial calculations, compliance checks, fraud
  screening, internal record creation, or database state changes.

  Communication/delivery actions (email, SMS, webhook) do NOT belong here.
  Those are ActionConfiguration rows with execution_type=http.

  Document generation (PDF/CSV/Excel) DOES belong here: it is internal Python
  logic that produces a file and persists it via the file storage layer,
  returning a storage reference in the ActionResult.

CHAOS_MODE:
  If CHAOS_MODE=true, ACTION_HANDLER_MAP is replaced with its chaos-wrapped
  variant, which injects failure modes for testing retry/DLQ behaviour.
"""

import os

from app.execution.actions import (
    update_entity_status,
    flag_for_review,
    lock_account,
    unlock_account,
    close_case,
    escalate_case,
    assign_senior_officer,
    escalate_to_rm,
    create_audit_record,
    fail_randomly,
    validate_payment_handler,
    assess_creditworthiness,
    approve_loan,
    reject_loan,
    reject_loan_application,
    approve_underwriting,
    reject_underwriting,
    calculate_emi,
    calculate_risk_score,
    flag_high_risk_customer,
    disburse_loan,
    generate_loan_agreement,
    apply_credit,
    calculate_tax,
    create_payment,
    validate_transaction,
    verify_compliance,
    initiate_collection,
    assign_recovery_agent,
    initiate_legal_action,
    write_off_loan,
    restructure_loan,
    waive_penalty,
    open_account,
    close_account,
    upgrade_account,
    block_debit_card,
    issue_new_card,
    update_credit_limit,
    activate_overdraft,
    reactivate_dormant_account,
    hold_funds,
    release_funds,
    freeze_suspicious_account,
    reverse_transaction,
    charge_penalty,
    apply_interest,
    process_neft,
    process_rtgs,
    process_imps,
    aml_screening,
    sanctions_check,
    submit_regulatory_report,
    run_bureau_check,
    process_credit_check,
    reconcile_account,
    approve_invoice,
    initiate_kyc,
    complete_kyc,
    collect_documents,
    schedule_customer_callback,
)
from app.execution.domain_actions.support_actions import (
    create_support_ticket,
    assign_support_agent,
    escalate_to_tier2,
    flag_repeat_complaint,
    resolve_ticket,
    process_refund,
    close_ticket_no_response,
)
from app.execution.domain_actions.health_actions import (
    schedule_appointment,
    alert_care_team,
    escalate_to_specialist,
    trigger_emergency_protocol,
    flag_high_risk_patient,
    request_insurance_approval,
)
from app.execution.domain_actions.loan_actions import (
    run_cibil_check,
    run_income_verification,
    verify_submitted_documents,
    issue_sanction_letter,
    generate_repayment_schedule,
    link_insurance_to_loan,
    collect_post_disbursement_documents,
    generate_interest_certificate,
    update_cibil_post_closure,
)
from app.execution.domain_actions.home_loan_actions import (
    initiate_property_valuation,
    schedule_technical_visit,
    initiate_legal_verification,
    send_to_legal_team,
    raise_legal_query,
    legal_verification_cleared,
    register_mortgage,
    collect_original_property_documents,
    disburse_tranche,
    return_original_documents,
)
from app.execution.domain_actions.car_loan_actions import (
    initiate_vehicle_valuation,
    verify_dealer_invoice,
    coordinate_with_dealer,
    disburse_to_dealer,
    initiate_rc_hypothecation,
    verify_vehicle_insurance,
    release_hypothecation,
)
from app.execution.python.pdf.handler import generate_pdf
from app.execution.python.csv.handler import generate_csv
from app.execution.python.excel.handler import generate_excel
from app.execution.chaos_actions import (
    chaos_escalate_case,
    chaos_assign_senior_officer,
    chaos_reject_loan,
    chaos_close_case,
    _apply_chaos,
    _chaos_response,
)


# ── Production handler map ────────────────────────────────────────────────────

_PRODUCTION_HANDLER_MAP: dict = {

    # Internal state & lifecycle
    "update_entity_status":       update_entity_status,
    "flag_for_review":            flag_for_review,
    "lock_account":               lock_account,
    "unlock_account":             unlock_account,
    "close_case":                 close_case,
    "escalate_case":              escalate_case,
    "assign_senior_officer":      assign_senior_officer,
    "escalate_to_rm":             escalate_to_rm,
    "create_audit_record":        create_audit_record,
    "fail_randomly":              fail_randomly,

    # Loan decisioning
    "validate_payment":           validate_payment_handler,
    "assess_creditworthiness":    assess_creditworthiness,
    "approve_loan":               approve_loan,
    "reject_loan":                reject_loan,
    "reject_loan_application":    reject_loan_application,
    "approve_underwriting":       approve_underwriting,
    "reject_underwriting":        reject_underwriting,
    "calculate_emi":              calculate_emi,
    "calculate_risk_score":       calculate_risk_score,
    "flag_high_risk_customer":    flag_high_risk_customer,

    # Loan financial operations
    "disburse_loan":              disburse_loan,
    "generate_loan_agreement":    generate_loan_agreement,
    "apply_credit":               apply_credit,
    "calculate_tax":              calculate_tax,
    "create_payment":             create_payment,
    "validate_transaction":       validate_transaction,
    "verify_compliance":          verify_compliance,

    # Collections & recovery
    "initiate_collection":        initiate_collection,
    "assign_recovery_agent":      assign_recovery_agent,
    "initiate_legal_action":      initiate_legal_action,
    "write_off_loan":             write_off_loan,
    "restructure_loan":           restructure_loan,
    "waive_penalty":              waive_penalty,

    # Account management
    "open_account":               open_account,
    "close_account":              close_account,
    "upgrade_account":            upgrade_account,
    "block_debit_card":           block_debit_card,
    "issue_new_card":             issue_new_card,
    "update_credit_limit":        update_credit_limit,
    "activate_overdraft":         activate_overdraft,
    "reactivate_dormant_account": reactivate_dormant_account,

    # Funds & transaction management
    "hold_funds":                 hold_funds,
    "release_funds":              release_funds,
    "freeze_suspicious_account":  freeze_suspicious_account,
    "reverse_transaction":        reverse_transaction,
    "charge_penalty":             charge_penalty,
    "apply_interest":             apply_interest,
    "process_neft":               process_neft,
    "process_rtgs":               process_rtgs,
    "process_imps":               process_imps,

    # Compliance & risk screening
    "aml_screening":              aml_screening,
    "sanctions_check":            sanctions_check,
    "submit_regulatory_report":   submit_regulatory_report,
    "run_bureau_check":           run_bureau_check,
    "process_credit_check":       process_credit_check,
    "reconcile_account":          reconcile_account,
    "approve_invoice":            approve_invoice,

    # KYC lifecycle
    "initiate_kyc":               initiate_kyc,
    "complete_kyc":               complete_kyc,
    "collect_documents":          collect_documents,

    # Scheduling & internal assignment
    "schedule_customer_callback": schedule_customer_callback,

    # Document generation (persisted via file storage layer)
    "generate_pdf":               generate_pdf,
    "generate_csv":               generate_csv,
    "generate_excel":             generate_excel,

    # Support — internal operations
    "create_support_ticket":      create_support_ticket,
    "assign_support_agent":       assign_support_agent,
    "escalate_to_tier2":          escalate_to_tier2,
    "flag_repeat_complaint":      flag_repeat_complaint,
    "resolve_ticket":             resolve_ticket,
    "process_refund":             process_refund,
    "close_ticket_no_response":   close_ticket_no_response,

    # Health — internal clinical operations
    "schedule_appointment":       schedule_appointment,
    "alert_care_team":            alert_care_team,
    "escalate_to_specialist":     escalate_to_specialist,
    "trigger_emergency_protocol": trigger_emergency_protocol,
    "flag_high_risk_patient":     flag_high_risk_patient,
    "request_insurance_approval": request_insurance_approval,

    # Loan processing — internal verification
    "run_cibil_check":                     run_cibil_check,
    "run_income_verification":             run_income_verification,
    "verify_submitted_documents":          verify_submitted_documents,
    "issue_sanction_letter":               issue_sanction_letter,
    "generate_repayment_schedule":         generate_repayment_schedule,
    "link_insurance_to_loan":              link_insurance_to_loan,
    "collect_post_disbursement_documents": collect_post_disbursement_documents,
    "generate_interest_certificate":       generate_interest_certificate,
    "update_cibil_post_closure":           update_cibil_post_closure,

    # Home loan — physical verification
    "initiate_property_valuation":         initiate_property_valuation,
    "schedule_technical_visit":            schedule_technical_visit,
    "initiate_legal_verification":         initiate_legal_verification,
    "send_to_legal_team":                  send_to_legal_team,
    "raise_legal_query":                   raise_legal_query,
    "legal_verification_cleared":          legal_verification_cleared,
    "register_mortgage":                   register_mortgage,
    "collect_original_property_documents": collect_original_property_documents,
    "disburse_tranche":                    disburse_tranche,
    "return_original_documents":           return_original_documents,

    # Car loan — vehicle verification
    "initiate_vehicle_valuation":  initiate_vehicle_valuation,
    "verify_dealer_invoice":       verify_dealer_invoice,
    "coordinate_with_dealer":      coordinate_with_dealer,
    "disburse_to_dealer":          disburse_to_dealer,
    "initiate_rc_hypothecation":   initiate_rc_hypothecation,
    "verify_vehicle_insurance":    verify_vehicle_insurance,
    "release_hypothecation":       release_hypothecation,
}


# ── Chaos handler map ─────────────────────────────────────────────────────────

def _make_chaos_handler(action_name: str):
    def _chaos(payload: dict, config: dict) -> dict:
        _apply_chaos(action_name, payload, config)
        return _chaos_response(action_name)
    _chaos.__name__ = f"chaos_{action_name}"
    return _chaos


_CHAOS_HANDLER_MAP: dict = {
    name: _make_chaos_handler(name)
    for name in _PRODUCTION_HANDLER_MAP
}
_CHAOS_HANDLER_MAP.update({
    "escalate_case":         chaos_escalate_case,
    "assign_senior_officer": chaos_assign_senior_officer,
    "close_case":            chaos_close_case,
    "reject_loan":           chaos_reject_loan,
    "fail_randomly":         fail_randomly,
})


# ── Public export ─────────────────────────────────────────────────────────────

_CHAOS_ENABLED = os.getenv("CHAOS_MODE", "false").lower() == "true"

ACTION_HANDLER_MAP: dict = (
    _CHAOS_HANDLER_MAP if _CHAOS_ENABLED else _PRODUCTION_HANDLER_MAP
)
