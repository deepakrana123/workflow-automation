# Domain Model

## Banking Domain

MFlows operates exclusively within the banking domain. All triggers, actions, and workflows represent banking business operations.

## Core Concepts

### Trigger
A business event that starts a workflow. Examples: `payment_missed`, `loan_requested`, `fraud_detected`, `account_opened`.

### Action
A single atomic business operation performed in response to a trigger. Examples: `send_payment_reminder`, `run_cibil_check`, `freeze_account`, `issue_sanction_letter`.

### Workflow
A compiled DAG of actions triggered by a business event. Stored as `parsed_rule_json` in the database.

### Workflow Knowledge
Structured knowledge extracted from a BRD document — triggers, action references, business rules, actors, external systems.

### Action Configuration
Per-workflow execution override for an action — specifies how to execute it (Python handler, HTTP endpoint, etc.).

### Workspace Integration
External system connection (HTTP endpoint with auth credentials) used by HTTP-type action configurations.

## Domain Relationships

```
TriggerDefinition (catalog)
    ↓ matched to
WorkflowTriggerMapping (extracted from BRD)
    ↓ belongs to
WorkflowKnowledge (BRD extraction result)
    ↓ generates
ActionConfiguration (how to execute each action)
    ↓ references
ActionDefinition (catalog)
    ↓ resolved at runtime by
Workflow (compiled DAG → parsed_rule_json)
    ↓ executes as
WorkflowExecution → ExecutionStep (runtime state)
```

## Banking Verticals Covered

| Vertical | Example Triggers | Example Actions |
|----------|-----------------|-----------------|
| Loan Origination | `loan_requested`, `loan_approved` | `run_cibil_check`, `issue_sanction_letter`, `disburse_loan` |
| Payments | `payment_due`, `payment_missed`, `payment_failed` | `process_neft`, `send_payment_reminder`, `charge_penalty` |
| KYC / AML | `kyc_documents_submitted`, `aml_alert_triggered` | `verify_pan`, `perform_aml_screening`, `screen_pep` |
| Collections | `npa_classified`, `recovery_initiated` | `assign_recovery_agent`, `send_legal_notice`, `initiate_sarfaesi_proceedings` |
| Cards | `card_reported_lost`, `card_expiry_approaching` | `block_debit_card`, `replace_card`, `update_credit_limit` |
| Fraud | `fraud_detected`, `high_risk_transaction` | `freeze_suspicious_account`, `escalate_fraud_case`, `block_fraudulent_transaction` |
| Trade Finance | `lc_application_received`, `bg_invoked` | `issue_letter_of_credit`, `issue_bank_guarantee` |
| Treasury | `forex_rate_threshold_breached` | `book_forex_deal`, `execute_forex_conversion` |
