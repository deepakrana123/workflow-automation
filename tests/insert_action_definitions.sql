-- ============================================================
-- Action Definitions - Clean Insert
-- 703 actions  |  no id column (DB auto-assigns)
-- ON CONFLICT (name) DO UPDATE  →  safe to re-run
-- ============================================================

BEGIN;

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('classify_npa', 'Classify NPA', 'Classify a loan account as Non-Performing Asset.', 'finance',
     '["npa classification", "asset classification", "mark npa", "non performing asset"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('rate_reset_notification', 'Rate Reset Notification', 'Notify customer about floating rate reset and new EMI.', 'finance',
     '["rate reset", "interest rate change", "rate revision", "emi revision", "rate change notification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('recalculate_emi', 'Recalculate EMI', 'Recalculate EMI after rate change, prepayment, or tenure modification.', 'finance',
     '["emi adjustment", "emi recalculation", "emi revision", "new emi calculation", "recalculate emi", "revise emi", "tenure reduction"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_provisional_certificate', 'Generate Provisional Certificate', 'Generate provisional interest certificate before year-end.', 'finance',
     '["provisional certificate", "interim certificate", "provisional statement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('create_group_loan', 'Create Group Loan', 'Create a Joint Liability Group or Self Help Group loan application.', 'finance',
     '["group loan", "jlg loan", "shg loan", "joint liability", "group lending", "microfinance group"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('assign_field_officer', 'Assign Field Officer', 'Assign field officer or loan officer for group supervision.', 'finance',
     '["assign field officer", "field officer", "loan officer", "assign officer", "field assignment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('flag_group_default', 'Flag Group Default', 'Flag group for default when members miss consecutive payments.', 'finance',
     '["group default", "flag default", "group delinquent", "default group", "group missed payment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_group_utilization', 'Calculate Group Utilization', 'Calculate loan utilization and repayment rate for the group.', 'finance',
     '["group utilization", "utilization rate", "repayment rate", "group performance", "collection efficiency"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('return_cheque', 'Return Cheque', 'Return a cheque due to insufficient funds or other reasons.', 'finance',
     '["cheque return", "cheque bounce", "dishonour cheque", "insufficient funds"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('update_kyc_details', 'Update KYC Details', 'Update customer KYC information - address, phone, email.', 'finance',
     '["update kyc", "kyc update", "modify kyc", "change address", "update contact"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('link_aadhaar', 'Link Aadhaar', 'Link Aadhaar number to customer bank or loan account.', 'finance',
     '["aadhaar linking", "aadhaar mapping", "aadhaar seeding", "aadhaar update", "account aadhaar link", "link aadhaar", "link aadhar"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('reset_banking_password', 'Reset Banking Password', 'Reset internet or mobile banking password for customer.', 'finance',
     '["reset password", "password reset", "forgot password", "change password", "banking password"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_rd_installment', 'Process RD Installment', 'Process monthly recurring deposit installment.', 'finance',
     '["rd installment", "recurring deposit", "rd payment", "monthly rd"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_early_warning_signal', 'Generate Early Warning Signal', 'Generate early warning signal for potential stress in loan account.', 'finance',
     '["early warning", "ews signal", "stress signal", "warning signal", "potential npa signal"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('upgrade_account_rating', 'Upgrade Account Rating', 'Upgrade internal credit rating after improved performance.', 'finance',
     '["upgrade rating", "rating upgrade", "credit upgrade", "account upgrade", "improve rating"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_pan', 'Verify PAN', 'Verify the applicant PAN card details against the Income Tax department database for name, date of birth, and status match.', 'kyc',
     '["pan verification", "pan check", "verify pan card", "pan validation", "income tax pan check", "pan authentication"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/pan/verify"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_aadhaar', 'Verify Aadhaar', 'Verify the applicant Aadhaar number using UIDAI authentication API for demographic and biometric match.', 'kyc',
     '["aadhaar verification", "uidai check", "aadhaar authentication", "verify aadhaar card", "aadhaar ekyc", "aadhaar validation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/aadhaar/verify"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_voter_id', 'Verify Voter ID', 'Verify the applicant Voter ID card against the Election Commission database for identity confirmation.', 'kyc',
     '["voter id check", "voter card verification", "verify voter card", "epic verification", "voter id validation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/voter-id/verify"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_passport', 'Verify Passport', 'Verify the applicant passport details for authenticity and validity as an accepted identity proof.', 'kyc',
     '["passport verification", "passport check", "verify passport", "passport validation", "passport authentication"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/passport/verify"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('fetch_ckyc_record', 'Fetch CKYC Record', 'Retrieve customer record from CERSAI Central KYC Registry.', 'finance',
     '["ckyc lookup", "central kyc fetch", "ckyc search", "cersai check"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('upload_ckyc_record', 'Upload CKYC Record', 'Upload verified KYC data to the Central KYC Registry.', 'finance',
     '["ckyc upload", "update central kyc", "ckyc submission"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('perform_customer_due_diligence', 'Perform Customer Due Diligence', 'Conduct standard due diligence assessment on a customer.', 'finance',
     '["cdd", "customer due diligence", "due diligence check", "standard due diligence"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('update_customer_profile', 'Update Customer Profile', 'Update customer demographic details such as name, address, phone number, email, or occupation in the core banking system.', 'account_management',
     '["profile update", "update customer details", "modify customer profile", "customer information update", "update kyc details", "amend customer record"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "PUT", "endpoint": "/customers/profile"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('assign_customer_segment', 'Assign Customer Segment', 'Classify customer into appropriate segment based on profile.', 'finance',
     '["customer segmentation", "segment assignment", "classify customer", "customer categorization"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_address', 'Verify Address', 'Verify the residential or office address of the customer through physical visit or utility bill validation.', 'kyc',
     '["address verification", "residence verification", "physical address check", "office address check", "verify residence", "address validation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/address/verify"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_account_balance', 'Calculate Account Balance', 'Calculate current available and ledger balance.', 'finance',
     '["balance enquiry", "check balance", "account balance", "available balance"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_eligibility', 'Calculate Eligibility', 'Calculate maximum loan amount customer is eligible for.', 'finance',
     '["loan eligibility", "eligibility calculation", "maximum loan amount", "borrowing capacity"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('refer_to_credit_committee', 'Refer to Credit Committee', 'Escalate loan application to credit committee for approval.', 'finance',
     '["committee approval", "credit committee", "credit committee referral", "credit panel", "escalate to committee", "loan committee", "send to committee"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_interest_rate', 'Calculate Interest Rate', 'Determine applicable interest rate based on risk profile.', 'finance',
     '["rate calculation", "interest pricing", "loan rate", "roi calculation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_prepayment_charges', 'Calculate Prepayment Charges', 'Calculate charges applicable for loan prepayment.', 'finance',
     '["prepayment penalty", "foreclosure charges", "early repayment charges"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_upi_payment', 'Process UPI Payment', 'Process a Unified Payments Interface transaction routed through NPCI for instant peer-to-peer or merchant transfer.', 'payments',
     '["upi transfer", "upi payment", "vpa transfer", "upi transaction", "npci upi", "instant upi"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/payments/upi"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('cancel_standing_instruction', 'Cancel Standing Instruction', 'Cancel an existing standing instruction on the customer account at customer request or after mandate expiry.', 'payments',
     '["cancel si", "stop standing instruction", "revoke auto debit", "remove recurring debit", "terminate si", "cancel mandate"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/payments/si/cancel"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_form_a2', 'Generate Form A2', 'Generate Form A2 for foreign remittance declaration.', 'finance',
     '["form a2", "fema declaration", "purpose code form", "remittance form"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('issue_debit_card', 'Issue Debit Card', 'Issue a new debit card linked to customer account.', 'finance',
     '["debit card issuance", "new debit card", "atm card", "create debit card"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('replace_card', 'Replace Card', 'Issue replacement for a lost, stolen, or damaged card.', 'finance',
     '["card issuance", "card renewal", "card replacement", "fresh card", "new card", "new card for lost", "new debit card", "reissue card", "replacement card"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('disable_international_usage', 'Disable International Usage', 'Disable card for international transactions.', 'finance',
     '["international deactivation", "block overseas", "disable foreign transactions"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('escalate_fraud_case', 'Escalate Fraud Case', 'Escalate a confirmed fraud case to investigation team.', 'finance',
     '["fraud escalation", "fraud investigation", "escalate fraud", "report fraud"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('close_fraud_case', 'Close Fraud Case', 'Close a fraud case after investigation completion.', 'finance',
     '["close investigation", "fraud case closure", "investigation complete"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('close_case', 'Close Case', 'Close a customer service case, complaint, or workflow task after successful resolution.', 'lifecycle',
     '["case closure", "resolve case", "close ticket", "case resolved", "close complaint", "close service request"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/cases/close"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('update_entity_status', 'Update Entity Status', 'Update the status of a customer, account, or loan entity in the system to reflect the current processing stage.', 'lifecycle',
     '["status update", "record status change", "entity status", "update record", "case status update", "workflow status"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "PUT", "endpoint": "/entities/status"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_rc_endorsement_notice', 'Send RC Endorsement Notice', 'Send notice confirming hypothecation on RC.', 'finance',
     '["rc notice", "hypothecation confirmation", "endorsement notice"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_vehicle_delivery_confirmation', 'Send Vehicle Delivery Confirmation', 'Confirm vehicle delivery to the customer.', 'finance',
     '["delivery confirmation", "vehicle delivered", "car delivery notice"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_document_for_signing', 'Send Document for Signing', 'Send a document for digital or physical signing.', 'finance',
     '["e-sign request", "signature request", "document signing", "sign request"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('activate_pos_terminal', 'Activate POS Terminal', 'Activate a point-of-sale terminal for the merchant.', 'finance',
     '["pos activation", "terminal activation", "swipe machine", "card machine setup"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('validate_payment', 'Validate Payment', 'Validate a payment transaction against account limits, available balance, and compliance rules before processing.', 'payments',
     '["payment check", "payment handler validation", "payment pre-check", "payment processing check", "payment screening", "payment validation", "transaction validation", "validate payment", "validate transaction", "verify payment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/payments/validate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('assign_senior_officer', 'Assign Senior Officer', 'Assign a senior bank officer to handle a complex case, high-value application, or escalated complaint.', 'lifecycle',
     '["assign senior officer", "senior assignment", "officer allocation", "assign manager", "senior review assignment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/cases/senior/assign"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_refund', 'Process Refund', 'Process a refund of erroneously charged fees, excess interest, or disputed transaction amount.', 'support',
     '["amount refund", "begin refund", "begin refund procedure", "begin reimbursement", "charge reversal", "fee refund", "initiate refund", "initiate reimbursement", "issue refund", "process reimbursement", "refund initiation", "refund processing", "refund request", "request refund", "start refund", "start refund process", "start reimbursement", "submit refund request"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/support/refund/process"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('classify_customer_risk', 'Classify Customer Risk', 'Assign risk classification category to the customer.', 'finance',
     '["risk classification", "customer risk rating", "risk categorization", "kyc risk"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_collateral', 'Verify Collateral', 'Verify the existence, ownership, and value of the collateral security offered against the loan.', 'loan_underwriting',
     '["collateral verification", "security verification", "check collateral", "asset verification", "hypothecation verification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/collateral/verify"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_provision_coverage', 'Calculate Provision Coverage', 'Calculate provision coverage ratio for NPA portfolio.', 'finance',
     '["provision coverage", "pcr calculation", "coverage ratio"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('report_cyber_incident', 'Report Cyber Incident', 'Report a cybersecurity incident to CERT-In and RBI.', 'finance',
     '["cyber incident", "security breach", "cert-in report", "cyber attack report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_credit_information_report', 'Generate Credit Information Report', 'Generate comprehensive credit information report from bureau.', 'finance',
     '["cir report", "credit information", "detailed credit report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_stock_audit_report', 'Generate Stock Audit Report', 'Generate stock and receivable audit report for working capital.', 'finance',
     '["stock audit", "inventory audit", "stock verification report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_letter_of_comfort', 'Process Letter of Comfort', 'Issue letter of comfort to support subsidiary borrowing.', 'finance',
     '["letter of comfort", "comfort letter", "support letter"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('initiate_video_kyc', 'Initiate Video KYC', 'Initiate a video-based KYC session with the customer for remote identity verification and live biometric capture.', 'kyc',
     '["video kyc", "vkyc", "video verification", "remote kyc", "digital kyc", "online kyc session"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/video/initiate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('flag_document_discrepancy', 'Flag Document Discrepancy', 'Flag any discrepancy or inconsistency found between submitted documents and applicant declarations for review.', 'kyc',
     '["document discrepancy", "flag mismatch", "document mismatch flag", "raise document issue", "flag inconsistency", "document conflict"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/documents/flag-discrepancy"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('add_nominee', 'Add Nominee', 'Add a nominee to a bank account or loan account for succession purposes.', 'account_management',
     '["nominee addition", "register nominee", "assign nominee", "add beneficiary nominee", "nominee registration"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/accounts/nominee/add"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('stop_cheque', 'Stop Cheque', 'Stop payment on a specific cheque number to prevent it from being honoured on presentation.', 'account_management',
     '["block cheque", "cancel cheque", "cheque stop", "cheque stop request", "hold cheque payment", "revoke cheque", "stop cheque", "stop payment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/accounts/cheque/stop"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('add_joint_holder', 'Add Joint Holder', 'Add a joint account holder to an existing customer account after KYC and consent capture.', 'account_management',
     '["add co-holder", "add joint holder", "add joint owner", "add second holder", "joint account", "joint account addition", "joint holder", "joint holder addition", "second holder"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/accounts/joint-holder/add"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('transfer_account_branch', 'Transfer Account Branch', 'Transfer a customer account from one branch to another with all associated services and standing instructions.', 'account_management',
     '["account migration", "account portability", "account transfer", "branch change", "branch transfer", "change branch", "home branch change", "transfer account"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/accounts/branch-transfer"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('create_loan_application', 'Create Loan Application', 'Create a new loan application record capturing product type, requested amount, tenure, and applicant details.', 'loan_underwriting',
     '["new loan application", "loan application creation", "start loan application", "initiate loan request", "loan request creation", "open loan application"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/application/create"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('withdraw_loan_application', 'Withdraw Loan Application', 'Withdraw a pending loan application at the request of the applicant before final decision.', 'loan_underwriting',
     '["cancel loan application", "withdraw application", "loan application cancellation", "cancel loan request", "abort loan application"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/application/withdraw"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('pre_approve_loan', 'Pre Approve Loan', 'Issue an in-principle pre-approval for a loan based on initial eligibility and bureau data, subject to final documentation.', 'loan_underwriting',
     '["in principle approval", "loan pre approval", "provisional loan approval", "loan sanction in principle", "conditional loan approval"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/pre-approve"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('conduct_personal_discussion', 'Conduct Personal Discussion', 'Conduct the personal discussion with the applicant and record findings on income, business, and repayment intent.', 'loan_underwriting',
     '["pd conduct", "hold personal discussion", "run pd", "customer interview", "credit discussion", "conduct pd"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/pd/conduct"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_guarantor', 'Verify Guarantor', 'Verify the identity, income, and creditworthiness of the guarantor supporting the loan application.', 'loan_underwriting',
     '["guarantor verification", "check guarantor", "guarantor kyc", "co-borrower verification", "surety verification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/guarantor/verify"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('foreclose_loan', 'Foreclose Loan', 'Process full foreclosure of a loan on receipt of the entire outstanding principal and applicable charges from the borrower.', 'loan_servicing',
     '["close loan early", "early closure", "foreclosure", "full loan settlement", "full prepayment", "loan closure", "loan foreclosure", "loan preclosure", "prepay loan in full"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/foreclose"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('part_prepay_loan', 'Part Prepay Loan', 'Accept a partial prepayment on a loan and adjust the outstanding principal, EMI, or tenure accordingly.', 'loan_servicing',
     '["advance payment", "lump sum payment", "part payment", "part prepayment", "partial loan payment", "partial prepayment", "principal reduction", "reduce principal"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/part-prepay"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('top_up_loan', 'Top Up Loan', 'Sanction an additional top-up loan amount on an existing loan account based on repayment history and eligibility.', 'loan_underwriting',
     '["top up loan", "additional loan", "loan enhancement", "loan augmentation", "loan top-up", "supplementary loan"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/top-up"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('initiate_sarfaesi_notice', 'Initiate SARFAESI Notice', 'Initiate a SARFAESI Section 13(2) notice against a defaulting borrower for enforcement of security interest.', 'collections',
     '["sarfaesi action", "section 13 notice", "sarfaesi notice", "enforcement notice", "sarfaesi initiation", "13(2) notice"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/sarfaesi/initiate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('take_possession', 'Take Possession', 'Take symbolic or physical possession of the mortgaged property or hypothecated asset under enforcement action.', 'collections',
     '["possess collateral", "symbolic possession", "physical possession", "take asset possession", "possession takeover", "seize collateral"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/possession/take"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('auction_collateral', 'Auction Collateral', 'Conduct an auction of possessed collateral asset to recover outstanding loan dues.', 'collections',
     '["asset auction", "auction property", "collateral auction", "e-auction", "property auction", "public auction", "sell collateral"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/auction/conduct"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('fatca_screening', 'FATCA Screening', 'Screen the customer for FATCA and CRS reportability based on US tax residency and foreign account indicators.', 'compliance',
     '["fatca check", "fatca compliance", "crs screening", "us tax residency check", "foreign tax check", "fatca crs screening"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/compliance/fatca/screen"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('str_reporting', 'STR Reporting', 'File a Suspicious Transaction Report with FIU-IND for a transaction flagged as suspicious by monitoring systems.', 'compliance',
     '["aml str", "file str", "fiu report", "str filing", "suspicious activity report", "suspicious transaction report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/compliance/str/file"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('ctr_reporting', 'CTR Reporting', 'File a Cash Transaction Report with FIU-IND for cash transactions exceeding the regulatory threshold.', 'compliance',
     '["cash reporting", "cash transaction report", "ctr filing", "file ctr", "fiu ctr", "high value cash report", "large cash report", "threshold transaction report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/compliance/ctr/file"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('kyc_periodic_review', 'KYC Periodic Review', 'Conduct a periodic risk-based review of customer KYC records as mandated by RBI for low, medium, and high risk categories.', 'compliance',
     '["annual kyc review", "customer risk review", "kyc audit", "kyc refresh", "kyc renewal", "kyc reverification", "kyc review", "periodic kyc", "periodic kyc review", "periodic review", "re-kyc", "recurring kyc", "rekyc", "risk based kyc review"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/compliance/kyc/periodic-review"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('start_workflow', 'Start Workflow', 'Start a business workflow instance for a specific case, application, or event with the initial payload.', 'lifecycle',
     '["workflow start", "trigger workflow", "kick off workflow", "initiate workflow", "launch workflow", "begin workflow"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/workflows/start"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('abort_workflow', 'Abort Workflow', 'Abort a running workflow instance and clean up any in-flight tasks or reservations.', 'lifecycle',
     '["workflow abort", "cancel workflow", "terminate workflow", "kill workflow", "stop workflow", "abandon workflow"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/workflows/abort"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('retry_task', 'Retry Task', 'Retry a previously failed workflow task after transient failure resolution or manual intervention.', 'lifecycle',
     '["task retry", "re-run task", "reattempt task", "retry action", "retry failed task", "re-execute task"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/workflows/task/retry"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('reset_card_pin', 'Reset Card PIN', 'Reset the PIN of a debit or credit card at customer request through secure channels.', 'cards',
     '["card pin change", "card pin reset", "change card pin", "forgot pin", "generate pin", "new card pin", "pin reset", "pin set", "regenerate pin"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/cards/pin/reset"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('set_card_limit', 'Set Card Limit', 'Set or modify the transaction, ATM withdrawal, or e-commerce limits on a debit or credit card.', 'cards',
     '["atm limit change", "card limit", "card limit change", "daily card limit", "ecommerce limit", "modify card limit", "pos limit change", "spending limit", "transaction cap", "update card limit"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "PUT", "endpoint": "/cards/limit"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('convert_to_card_emi', 'Convert To Card EMI', 'Convert an eligible credit card transaction into an equated monthly instalment loan for the cardholder.', 'cards',
     '["card emi conversion", "card instalment conversion", "credit card emi", "emi conversion", "emi on card", "flexipay", "installment conversion", "purchase emi", "transaction to emi"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/cards/emi/convert"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('create_support_ticket', 'Create Support Ticket', 'Create a customer service or complaint ticket for tracking and resolution.', 'support',
     '["service ticket", "complaint ticket", "support request", "raise complaint", "create complaint", "customer complaint"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/support/tickets/create"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('assign_support_agent', 'Assign Support Agent', 'Assign a customer support agent to handle and resolve a service ticket.', 'support',
     '["agent assignment", "assign agent", "support allocation", "ticket assignment", "case assignment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/support/agents/assign"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('escalate_to_tier2', 'Escalate To Tier 2', 'Escalate an unresolved customer complaint to the Tier 2 specialised support team.', 'support',
     '["tier 2 escalation", "second level support", "escalate complaint", "level 2 escalation", "senior support escalation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/support/escalate/tier2"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('flag_repeat_complaint', 'Flag Repeat Complaint', 'Flag a customer complaint as a repeat grievance requiring root cause analysis.', 'support',
     '["repeat complaint flag", "chronic complaint", "recurring issue", "repeat grievance", "repeat issue flag"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/support/complaints/flag-repeat"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('close_ticket_no_response', 'Close Ticket No Response', 'Close a service ticket due to no response from the customer after multiple follow-up attempts.', 'support',
     '["close no response", "auto close ticket", "no contact closure", "unresponsive customer close"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/support/tickets/close-no-response"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('schedule_appointment', 'Schedule Appointment', 'Schedule a medical or branch appointment for the customer.', 'health',
     '["appointment scheduling", "book appointment", "schedule visit"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/appointments/schedule"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('alert_care_team', 'Alert Care Team', 'Alert the care team about a critical customer situation requiring immediate attention.', 'health',
     '["care team alert", "notify care", "care alert"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/care/alert"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('trigger_emergency_protocol', 'Trigger Emergency Protocol', 'Activate emergency protocol for critical or time-sensitive situations.', 'health',
     '["emergency activation", "critical alert", "emergency response"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/emergency/trigger"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('flag_high_risk_patient', 'Flag High Risk Patient', 'Flag a high-risk patient or customer for priority handling.', 'health',
     '["high risk flag", "priority flag", "critical customer flag"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/care/patient/flag-high-risk"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('request_insurance_approval', 'Request Insurance Approval', 'Request insurance company approval for a claim or medical procedure.', 'health',
     '["insurance approval", "claim approval request", "insurance pre-auth"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/insurance/approval/request"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('fail_randomly', 'Fail Randomly', 'Simulate random failure for testing retry and DLQ behaviour in development environments.', 'testing',
     '["test failure", "simulate error", "chaos test"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"handler": "fail_randomly"}, "execution_type": "python"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_ach_debit', 'Process ACH Debit', 'Process an ACH debit transaction to auto-debit customer account for a scheduled payment or loan EMI.', 'payments',
     '["ach debit", "electronic clearing service", "ecs debit", "auto debit", "direct debit ach", "ach payment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/payments/ach/debit"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('create_standing_instruction', 'Create Standing Instruction', 'Create a standing instruction on the customer account for recurring auto-debits toward EMI, SIP, or bill payments.', 'payments',
     '["si setup", "standing instruction setup", "auto debit setup", "recurring debit setup", "si creation", "recurring instruction"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/payments/si/create"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_beneficiary', 'Verify Beneficiary', 'Verify the beneficiary account details through penny drop or name match before enabling for high-value transfers.', 'payments',
     '["beneficiary verification", "payee verification", "penny drop", "name match check", "verify payee account", "beneficiary validation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/payments/beneficiary/verify"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_payment_receipt', 'Generate Payment Receipt', 'Generate a formal payment receipt or acknowledgement for a completed transaction for customer records.', 'payments',
     '["payment receipt", "transaction receipt", "issue receipt", "generate receipt", "acknowledgement receipt", "payment proof"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"handler": "generate_payment_receipt"}, "execution_type": "python"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_address_details', 'Collect Address Details', 'Collect and verify the complete residential and correspondence address details including proof of address documents from the applicant or customer.', 'kyc',
     '["collect address", "get address details", "address collection", "residential address", "correspondence address", "address proof collection", "verify address details", "customer address collection"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/address/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_income_details', 'Collect Income Details', 'Collect the applicant income information including salary slips, bank statements, Form 16, and other income proof documents for assessment.', 'kyc',
     '["collect income", "income details collection", "salary details", "income proof collection", "financial details", "income verification", "salary slips", "income documents"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/income/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_personal_details', 'Collect Personal Details', 'Collect basic personal information of the applicant including name, date of birth, gender, marital status, nationality, and contact details.', 'kyc',
     '["personal details", "customer information", "collect personal info", "applicant details", "basic profile", "customer demographic", "personal profile"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/personal/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_family_details', 'Collect Family Details', 'Collect the applicant family information including dependents, spouse details, and family members for comprehensive profiling.', 'kyc',
     '["family details", "dependents information", "family members", "household details", "spouse details", "family profile"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/family/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_contact_details', 'Collect Contact Details', 'Collect the applicant contact information including primary phone number, secondary phone number, email address, and preferred communication channel.', 'kyc',
     '["contact details", "phone number", "email address", "mobile number", "communication details", "contact information"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/contact/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_bank_account_details', 'Collect Bank Account Details', 'Collect the applicant bank account information including account number, IFSC code, bank name, and branch for fund transfer and verification.', 'kyc',
     '["bank details", "account information", "collect bank account", "account number", "ifsc code", "bank verification", "banking details"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/bank/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_nominee_details', 'Collect Nominee Details', 'Collect the nominee information including name, relationship, age, and contact details for the customer account or loan.', 'account_management',
     '["nominee details", "collect nominee", "beneficiary details", "succession details", "nominee information"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/accounts/nominee/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_guarantor_details', 'Collect Guarantor Details', 'Collect the guarantor information including identity proof, address proof, income details, and relationship with the applicant.', 'loan_underwriting',
     '["guarantor details", "collect guarantor", "surety details", "co-borrower", "guarantor information", "security provider"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/guarantor/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_property_details', 'Collect Property Details', 'Collect the property information including full address, area, value, registration details, and ownership documents for loan processing.', 'home_loan',
     '["property details", "collect property", "asset details", "property information", "collateral details", "property documents"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/home-loan/property/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_vehicle_details', 'Collect Vehicle Details', 'Collect the vehicle information including make, model, year, registration number, engine number, chassis number, and insurance details.', 'car_loan',
     '["vehicle details", "car details", "collect vehicle", "automobile info", "vehicle registration", "car documents"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/car-loan/vehicle/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_asset_liability_details', 'Collect Asset Liability Details', 'Collect the applicant complete asset and liability details including property, investments, loans, and monthly obligations for net worth assessment.', 'loan_underwriting',
     '["asset liability", "collect asset", "liability details", "net worth", "financial position", "asset statement", "liability statement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/asset-liability/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_existing_loan_details', 'Collect Existing Loan Details', 'Collect details of the applicant existing loans including type, amount, tenure, EMI, and outstanding balance for debt servicing assessment.', 'loan_underwriting',
     '["existing loans", "collect existing loan", "current loans", "debt details", "loan portfolio", "outstanding loans"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/existing/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_reference_details', 'Collect Reference Details', 'Collect the applicant reference information including contact person, relationship, and contact details for background verification.', 'kyc',
     '["reference details", "collect reference", "reference check", "contact reference", "background verification", "professional reference"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/reference/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_next_of_kin_details', 'Collect Next Of Kin Details', 'Collect the next of kin details including name, relationship, address, and contact number for emergency communication.', 'kyc',
     '["next of kin", "emergency contact", "kin details", "emergency details", "family contact"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/next-of-kin/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_medical_history', 'Collect Medical History', 'Collect the applicant medical history and health insurance details for underwriting medical loan or life insurance products.', 'health',
     '["medical history", "health records", "collect medical", "health details", "medical conditions", "insurance medical"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/health/medical/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('apply_credit_card', 'Apply Credit Card', 'Process a credit card application including eligibility check, document collection, and credit limit assignment for the customer.', 'cards',
     '["credit card application", "apply card", "card application", "new credit card", "card request"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/cards/credit/apply"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('upgrade_credit_card', 'Upgrade Credit Card', 'Upgrade customer credit card to a higher variant with better features, increased limit, and premium benefits.', 'cards',
     '["card upgrade", "credit card upgrade", "upgrade card variant", "premium card", "card enhancement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/cards/credit/upgrade"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('close_credit_card', 'Close Credit Card', 'Close a credit card account at customer request after clearing all outstanding dues and pending transactions.', 'cards',
     '["close credit card", "card closure", "cancel card", "card closing", "credit card cancellation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/cards/credit/close"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('create_fixed_deposit', 'Create Fixed Deposit', 'Create a fixed deposit account for the customer with chosen tenure, interest rate, and payout frequency.', 'wealth',
     '["create fd", "deposit account", "fd creation", "fd opening", "fixed deposit", "fixed deposit opening", "new fd", "term deposit"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/wealth/fd/create"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('create_recurring_deposit', 'Create Recurring Deposit', 'Create a recurring deposit account with monthly contribution, tenure, and applicable interest rate.', 'wealth',
     '["create rd", "monthly deposit", "new rd", "rd account", "rd creation", "recurring deposit", "recurring deposit opening"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/wealth/rd/create"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('close_deposit', 'Close Deposit', 'Close a fixed or recurring deposit account and process maturity payout to the customer account.', 'wealth',
     '["close deposit", "deposit maturity", "fd closure", "rd closure", "deposit withdrawal"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/wealth/deposit/close"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('invest_in_mutual_fund', 'Invest In Mutual Fund', 'Process a mutual fund investment request for the customer including SIP or lump sum investment with appropriate scheme selection.', 'wealth',
     '["fund investment", "fund purchase", "fund redemption", "lump sum investment", "mf investment", "mf transaction", "mutual fund", "mutual fund investment", "sip", "sip investment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/wealth/mutual-fund/invest"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('start_sip', 'Start SIP', 'Start a Systematic Investment Plan for mutual fund investments with monthly contribution and fund selection.', 'wealth',
     '["sip start", "systematic investment plan", "start sip", "monthly investment", "sip registration"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/wealth/sip/start"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('stop_sip', 'Stop SIP', 'Stop an existing Systematic Investment Plan at customer request after valid redemption.', 'wealth',
     '["stop sip", "cancel sip", "sip stop", "pause sip", "sip cancellation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/wealth/sip/stop"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('register_netbanking', 'Register NetBanking', 'Register customer for internet banking facility with secure credentials and multi-factor authentication setup.', 'digital_banking',
     '["netbanking registration", "register netbanking", "online banking", "internet banking", "digital banking setup"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/digital/netbanking/register"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('register_mobile_banking', 'Register Mobile Banking', 'Register customer for mobile banking application with device authentication and transaction security.', 'digital_banking',
     '["mobile banking", "register mobile banking", "app registration", "phone banking", "bank app setup"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/digital/mobile-banking/register"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('register_upi_handle', 'Register UPI Handle', 'Register a Unified Payments Interface handle (VPA) for the customer for instant payment transactions.', 'digital_banking',
     '["create upi id", "register upi", "upi activation", "upi handle", "upi registration", "upi setup", "vpa creation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/digital/upi/register"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('reset_netbanking_password', 'Reset NetBanking Password', 'Reset the net banking password at customer request through secure authentication and OTP verification.', 'digital_banking',
     '["reset password", "netbanking password reset", "forgot password", "password reset", "online banking password"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/digital/netbanking/password/reset"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('enroll_health_insurance', 'Enroll Health Insurance', 'Enroll customer into a health or medical insurance policy with appropriate coverage amount and premium details.', 'insurance',
     '["health insurance", "medical insurance", "enroll insurance", "health cover", "insurance enrollment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/insurance/health/enroll"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('enroll_life_insurance', 'Enroll Life Insurance', 'Enroll customer into a life insurance policy with appropriate coverage, premium, and nominee details.', 'insurance',
     '["life insurance", "life cover", "term insurance", "insurance enrollment", "life policy"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/insurance/life/enroll"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('file_insurance_claim', 'File Insurance Claim', 'File a claim for life, health, or asset insurance with supporting documents for settlement processing.', 'insurance',
     '["insurance claim", "claim filing", "file claim", "claim request", "insurance settlement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/insurance/claim/file"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('renew_insurance_policy', 'Renew Insurance Policy', 'Renew an existing insurance policy for the next period with updated premium and coverage details.', 'insurance',
     '["policy renewal", "insurance renewal", "renew policy", "extend insurance", "policy extension"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/insurance/policy/renew"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_mis_report', 'Generate MIS Report', 'Generate a Management Information System report with key metrics, trends, and performance indicators for management review.', 'reporting',
     '["mis report", "management report", "generate report", "key metrics", "performance report", "dashboard report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"handler": "generate_mis_report"}, "execution_type": "python"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_audit_trail_report', 'Generate Audit Trail Report', 'Generate a comprehensive audit trail report for regulatory compliance review and internal audit purposes.', 'reporting',
     '["audit report", "audit trail", "compliance report", "audit trail report", "regulatory audit"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"handler": "generate_audit_trail_report"}, "execution_type": "python"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_customer_communication', 'Send Customer Communication', 'Send official communication to the customer including loan approval, statement, notification, or marketing communication.', 'communication',
     '["customer communication", "send email", "send sms", "customer notification", "official communication"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/communication/send"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('onboard_customer', 'Onboard Customer', 'Complete the end-to-end customer onboarding process including account creation, KYC, and product enrolment.', 'lifecycle',
     '["customer onboarding", "onboard customer", "new customer setup", "complete onboarding", "customer initiation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/lifecycle/onboard"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('offboard_customer', 'Offboard Customer', 'Complete the customer offboarding process including account closure, document return, and exit formalities.', 'lifecycle',
     '["offboard customer", "customer offboarding", "exit formalities", "account termination", "close customer relationship"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/lifecycle/offboard"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('report_fraud_incident', 'Report Fraud Incident', 'Report a suspected fraud incident for investigation and blocking of compromised accounts or cards.', 'compliance',
     '["fraud report", "report fraud", "suspicious activity", "fraud incident", "fraud reporting"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/fraud/report"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('investigate_fraud_case', 'Investigate Fraud Case', 'Investigate a reported fraud case including evidence collection, transaction analysis, and resolution.', 'compliance',
     '["fraud investigation", "investigate case", "fraud resolution", "fraud inquiry", "case investigation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/fraud/investigate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('pay_utility_bill', 'Pay Utility Bill', 'Process payment for utility bills including electricity, water, gas, and phone bills through the digital channels.', 'payments',
     '["utility bill payment", "pay bill", "electricity bill", "water bill", "gas bill", "phone bill"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/payments/utility/pay"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('pay_credit_card_bill', 'Pay Credit Card Bill', 'Process credit card bill payment from the customer account for outstanding amount.', 'payments',
     '["card bill payment", "card bill settlement", "card dues payment", "card payment", "credit card bill", "credit card payment", "pay card bill"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/payments/card/pay"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_otp', 'Verify OTP', 'Verify the one-time password for transaction authentication, password reset, or identity verification.', 'security',
     '["otp verification", "verify otp", "authenticate otp", "one time password", "otp check"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/security/otp/verify"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_otp', 'Generate OTP', 'Generate a one-time password for secure transaction authentication, login, or identity verification.', 'security',
     '["generate otp", "otp generation", "create otp", "send otp", "one time password"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/security/otp/generate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_identity_proof', 'Collect Identity Proof', 'Collect identity proof documents such as PAN card, Aadhaar, passport, or voter ID for KYC verification.', 'kyc',
     '["identity proof collection", "collect id proof", "pan collection", "aadhaar collection", "passport collection", "voter id collection", "identity documents"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/kyc/identity"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_address_proof', 'Collect Address Proof', 'Collect address proof documents such as utility bills, rent agreement, or bank statement for KYC verification.', 'kyc',
     '["address proof collection", "collect address proof", "utility bill", "rent agreement", "bank statement", "address documents"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/kyc/address"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_photo', 'Collect Photo', 'Collect a recent passport-size photograph of the applicant for KYC and identity verification purposes.', 'kyc',
     '["collect photo", "photograph collection", "passport photo", "applicant photo", "identity photo"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/kyc/photo"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_signature', 'Collect Signature', 'Collect the applicant signature for account opening, loan documentation, and mandate verification.', 'kyc',
     '["signature collection", "collect signature", "signature capture", "applicant signature", "mandate signature"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/kyc/signature"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_income_proof', 'Collect Income Proof', 'Collect income proof documents such as salary slips, Form 16, ITR, or bank statements for loan assessment.', 'loan_underwriting',
     '["income proof collection", "collect income proof", "salary slips", "form 16", "itr collection", "income documents"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/loan/income"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_bank_statement', 'Collect Bank Statement', 'Collect bank statements for the last 6-12 months for income verification and financial assessment.', 'loan_underwriting',
     '["bank statement collection", "collect bank statement", "statement collection", "account statement", "transaction history"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/loan/bank-statement"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_employment_certificate', 'Collect Employment Certificate', 'Collect employment certificate or appointment letter from the applicant current employer for job verification.', 'loan_underwriting',
     '["employment certificate", "appointment letter", "work certificate", "employer letter", "job proof"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/loan/employment"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_business_proof', 'Collect Business Proof', 'Collect business registration documents, GST certificate, and business profile for self-employed applicants.', 'loan_underwriting',
     '["business proof", "gst certificate", "business registration", "company incorporation", "business documents"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/loan/business"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_itr_documents', 'Collect ITR Documents', 'Collect Income Tax Returns for the last 2-3 years for income verification and tax compliance.', 'loan_underwriting',
     '["itr collection", "income tax return", "tax return", "itr documents", "income tax filing"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/loan/itr"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_property_documents', 'Collect Property Documents', 'Collect property title deeds, sale deed, encumbrance certificate, and other property ownership documents.', 'home_loan',
     '["property documents", "title deeds", "sale deed", "encumbrance certificate", "property ownership", "property papers"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/home-loan/property"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_legal_documents', 'Collect Legal Documents', 'Collect legal documents for property title verification including chain of title, legal opinion, and advocate report.', 'home_loan',
     '["legal documents", "title verification", "advocate report", "legal opinion", "chain of title"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/home-loan/legal"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_technical_documents', 'Collect Technical Documents', 'Collect technical documents including property valuation report, structural report, and building plan approval.', 'home_loan',
     '["technical documents", "valuation report", "structural report", "building plan", "property valuation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/home-loan/technical"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_mortgage_documents', 'Collect Mortgage Documents', 'Collect mortgage creation documents including registered mortgage deed, charge creation, and NOC from other lenders.', 'home_loan',
     '["mortgage documents", "mortgage deed", "charge creation", "registered mortgage", "noc collection"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/home-loan/mortgage"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_vehicle_documents', 'Collect Vehicle Documents', 'Collect vehicle registration certificate, invoice, insurance policy, and road tax receipt for car loan processing.', 'car_loan',
     '["vehicle documents", "rc collection", "car invoice", "vehicle insurance", "road tax", "car documents"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/car-loan/vehicle"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_insurance_documents', 'Collect Insurance Documents', 'Collect comprehensive insurance policy document covering the vehicle for the loan tenure.', 'car_loan',
     '["insurance documents", "car insurance", "policy document", "insurance cover", "vehicle insurance"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/car-loan/insurance"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_marital_status', 'Collect Marital Status', 'Collect the applicant marital status details for profile completion and regulatory reporting.', 'kyc',
     '["marital status", "collect marital status", "marital details", "relationship status", "family profile"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/customer/marital"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_dependents_details', 'Collect Dependents Details', 'Collect the number and details of dependents for loan eligibility and insurance coverage assessment.', 'kyc',
     '["dependents details", "family dependents", "collect dependents", "household size", "dependent information"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/customer/dependents"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_occupation_details', 'Collect Occupation Details', 'Collect detailed occupation information including industry, job role, employment type, and years of experience.', 'kyc',
     '["occupation details", "job role", "employment type", "industry details", "work experience"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/customer/occupation"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_field_verification', 'Collect Field Verification', 'Collect field verification data including site visit report, property inspection, and photograph evidence.', 'field_collection',
     '["field verification", "site visit", "property inspection", "field report", "physical verification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/field/verification"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_geotag_data', 'Collect Geotag Data', 'Collect geotagged location data for field verification, property location confirmation, and fraud prevention.', 'field_collection',
     '["geotag data", "location collection", "geotagging", "property location", "gps coordinates"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/field/geotag"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_field_photographs', 'Collect Field Photographs', 'Collect field photographs including property front view, site condition, and surrounding area documentation.', 'field_collection',
     '["field photographs", "site photos", "property pictures", "field images", "photographic evidence"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/field/photos"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_digital_consent', 'Collect Digital Consent', 'Collect digital consent from the customer for processing personal data, loan application, and document verification.', 'kyc',
     '["digital consent", "customer consent", "e-consent", "consent collection", "data consent"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/digital/consent"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_selfie_verification', 'Collect Selfie Verification', 'Collect a live selfie photo for biometric verification and match against identity proof photo.', 'kyc',
     '["selfie verification", "live photo", "biometric selfie", "face match", "identity verification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/digital/selfie"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_voice_biometric', 'Collect Voice Biometric', 'Collect voice biometric sample for voice-based authentication and verification.', 'kyc',
     '["voice biometric", "voice sample", "voice authentication", "audio verification", "biometric collection"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/digital/voice"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_sanction_letter_copy', 'Collect Sanction Letter Copy', 'Collect and archive the signed loan sanction letter copy from the customer for records.', 'loan_servicing',
     '["sanction letter copy", "collect sanction letter", "signed sanction", "loan sanction copy", "approval letter"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/loan/sanction-letter"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_insurance_certificate', 'Collect Insurance Certificate', 'Collect the insurance certificate or policy copy for property, vehicle, or loan protection.', 'loan_servicing',
     '["insurance certificate", "policy copy", "insurance document", "coverage certificate", "insurance proof"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/loan/insurance-certificate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_signed_agreement', 'Collect Signed Agreement', 'Collect the signed loan agreement or contract document from all applicable parties.', 'loan_underwriting',
     '["signed agreement", "loan contract", "signed documents", "agreement collection", "contract signing"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collection/loan/signed-agreement"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('initiate_telecall', 'Initiate Telecall', 'Initiate a telecall or phone call to the borrower for repayment follow-up and payment negotiation.', 'collections',
     '["telecall", "phone call", "collection call", "follow-up call", "borrower call", "recovery call"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/telecall/initiate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('assign_collection_agent', 'Assign Collection Agent', 'Assign a collection agent to a delinquent account for field follow-up, visit, and repayment negotiation.', 'collections',
     '["assign agent", "collection agent", "recovery agent", "field agent", "agent allocation", "agent assignment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/agent/assign"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('approve_one_time_settlement', 'Approve One Time Settlement', 'Approve the one-time settlement offer from the borrower for closure of the account.', 'collections',
     '["accept settlement", "approve settlement", "compromise settlement", "final settlement", "one time settlement", "one-time settlement", "ots approval", "ots approved", "ots sign-off", "reduced settlement", "settlement approval", "settlement approved", "settlement clearance", "settlement closure", "settlement offer"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/ots/approve"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_settlement_payment', 'Process Settlement Payment', 'Process the payment received against the approved settlement offer and close the loan account.', 'collections',
     '["settlement payment", "final payment", "settlement amount", "payment processing", "settlement closure", "ots payment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/settlement/payment"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('mark_as_irrecoverable', 'Mark As Irrecoverable', 'Mark the loan account as irrecoverable and prepare for write-off after exhausting all recovery options.', 'collections',
     '["irrecoverable", "bad debt", "write-off", "loan write-off", "npa write-off", "charge-off"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/irrecoverable/mark"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('update_collection_status', 'Update Collection Status', 'Update the collection status of the loan account as the case progresses through different recovery stages.', 'collections',
     '["case status", "collection progress", "collection status", "recovery stage", "recovery status", "recovery update", "status change", "status update", "update recovery"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "PUT", "endpoint": "/collections/status/update"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('log_collection_remarks', 'Log Collection Remarks', 'Log collection officer remarks, negotiation details, and next follow-up plan for the loan account.', 'collections',
     '["collection remarks", "officer remarks", "case remarks", "follow-up notes", "collection log", "remarks entry"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/remarks/log"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('compute_recovery_progress', 'Compute Recovery Progress', 'Compute the recovery progress for a set of loan accounts for portfolio and collections performance tracking.', 'collections',
     '["recovery progress", "collection progress", "portfolio recovery", "collections performance", "recovery analytics"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"handler": "compute_recovery_progress"}, "execution_type": "python"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_collections_report', 'Generate Collections Report', 'Generate a comprehensive collections and recovery report for management review.', 'collections',
     '["collections report", "recovery report", "npa report", "delinquency report", "collection dashboard"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"handler": "generate_collections_report"}, "execution_type": "python"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('schedule_daily_message', 'Schedule Daily Message', 'Schedule a daily automated message to be sent to customers via SMS, email, or WhatsApp at a configured time.', 'scheduler',
     '["daily message", "schedule message", "daily notification", "automated message", "daily communication", "recurring message"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/scheduler/message/daily"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('schedule_bulk_message', 'Schedule Bulk Message', 'Schedule a bulk message campaign to be sent to a group of customers at a specified date and time.', 'scheduler',
     '["bulk message", "mass communication", "broadcast message", "bulk sms", "bulk email", "message campaign"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/scheduler/message/bulk"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('schedule_daily_call', 'Schedule Daily Call', 'Schedule a daily automated voice call to be made to customers for reminders, verification, or updates.', 'scheduler',
     '["daily call", "schedule call", "automated call", "voice call", "daily voice call", "call schedule"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/scheduler/call/daily"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('schedule_bulk_call', 'Schedule Bulk Call', 'Schedule a bulk voice call campaign to a list of customers for announcements, reminders, or alerts.', 'scheduler',
     '["bulk call", "mass calling", "broadcast call", "voice campaign", "call campaign", "bulk voice call"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/scheduler/call/bulk"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('initiate_telecalling_campaign', 'Initiate Telecalling Campaign', 'Initiate a telecalling campaign where agents will call customers for collections, verification, or sales.', 'scheduler',
     '["telecalling campaign", "call campaign", "agent calling", "telecall campaign", "outbound calling", "telecalling initiation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/scheduler/telecalling/initiate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('assign_telecalling_agents', 'Assign Telecalling Agents', 'Assign telecalling agents to a campaign with specific customer lists and call targets.', 'scheduler',
     '["assign agents", "telecaller assignment", "agent allocation", "call agent assignment", "campaign agents", "telecalling agents"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/scheduler/telecalling/agents"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('schedule_telecalling_shift', 'Schedule Telecalling Shift', 'Schedule the telecalling shift for agents including start time, end time, and break slots.', 'scheduler',
     '["telecalling shift", "call shift", "agent shift", "shift scheduling", "call centre shift", "telecaller shift"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/scheduler/telecalling/shift"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('record_telecalling_outcome', 'Record Telecalling Outcome', 'Record the outcome of a telecalling attempt including customer response, promise to pay, or next action.', 'scheduler',
     '["call outcome", "telecalling result", "call response", "customer response", "call disposition", "outcome recording"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/scheduler/telecalling/outcome"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('schedule_whatsapp_message', 'Schedule WhatsApp Message', 'Schedule a WhatsApp message to be sent to customers for reminders, promotions, or notifications.', 'scheduler',
     '["whatsapp message", "whatsapp broadcast", "whatsapp notification", "whatsapp reminder", "schedule whatsapp"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/scheduler/whatsapp/message"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('schedule_email_campaign', 'Schedule Email Campaign', 'Schedule an email campaign to be sent to a list of customers with configured templates and tracking.', 'scheduler',
     '["email campaign", "email blast", "bulk email", "newsletter", "email schedule", "marketing email"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/scheduler/email/campaign"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('schedule_sms_campaign', 'Schedule SMS Campaign', 'Schedule an SMS campaign to be sent to a list of customers with configured message templates.', 'scheduler',
     '["sms campaign", "sms blast", "bulk sms", "sms schedule", "marketing sms", "promotional sms"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/scheduler/sms/campaign"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('schedule_ivr_call', 'Schedule IVR Call', 'Schedule an Interactive Voice Response call to collect customer inputs, verify details, or provide information.', 'scheduler',
     '["ivr call", "ivr campaign", "interactive voice", "voice response", "ivr outbound", "schedule ivr"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/scheduler/ivr/call"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('schedule_follow_up', 'Schedule Follow Up', 'Schedule a follow-up activity such as call, visit, or message for a specific customer or case.', 'scheduler',
     '["follow-up", "schedule follow-up", "next action", "reminder", "follow-up schedule", "case follow-up"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/scheduler/follow-up/schedule"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('trigger_workflow_at_time', 'Trigger Workflow At Time', 'Trigger a specific workflow at a scheduled time based on a configured cron expression or datetime.', 'scheduler',
     '["workflow trigger", "scheduled workflow", "cron trigger", "time-based trigger", "schedule workflow", "auto trigger"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/scheduler/workflow/trigger"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('pause_scheduled_job', 'Pause Scheduled Job', 'Pause an active scheduled job or campaign temporarily without deleting it.', 'scheduler',
     '["pause job", "pause campaign", "suspend schedule", "pause schedule", "job hold", "campaign pause"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/scheduler/job/pause"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('resume_scheduled_job', 'Resume Scheduled Job', 'Resume a previously paused scheduled job or campaign.', 'scheduler',
     '["resume job", "resume campaign", "restart schedule", "job resume", "campaign resume", "unpause"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/scheduler/job/resume"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('link_pan', 'Link PAN', 'Link PAN card to customer account for tax compliance.', 'finance',
     '["account pan link", "link pan", "link pan card", "pan linking", "pan mapping", "pan seeding", "pan update"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('approve_restructuring', 'Approve Restructuring', 'Approve the restructuring of the loan including revised tenure, interest rate, or EMI based on the borrowers repayment capacity.', 'collections',
     '["restructure approval", "loan restructuring", "restructure sanction", "revised terms", "restructuring approval"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/restructure/approve"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('escalate_case', 'Escalate Case', 'Escalate a customer case, loan application, or compliance issue to a higher authority for resolution.', 'lifecycle',
     '["case escalation", "escalate to manager", "senior escalation", "escalate complaint", "raise escalation", "escalation", "escalate issue"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/cases/escalate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('flag_for_review', 'Flag For Review', 'Flag a customer, account, or transaction for manual review by a senior officer or compliance team.', 'lifecycle',
     '["review flag", "mark for review", "escalate for review", "flag account", "manual review flag", "compliance review"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/review/flag"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('create_audit_record', 'Create Audit Record', 'Create a formal audit record of a transaction, decision, or activity for compliance and traceability.', 'compliance',
     '["audit record", "create audit trail", "audit log entry", "compliance record", "activity record", "audit documentation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/audit/record"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('approve_invoice', 'Approve Invoice', 'Approve a vendor or supplier invoice for payment processing after verification.', 'payments',
     '["invoice approval", "bill approval", "vendor invoice", "approve bill", "invoice verification", "payment approval"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/invoices/approve"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('validate_transaction', 'Validate Transaction', 'Validate a financial transaction for correctness, completeness, and compliance before execution.', 'payments',
     '["transaction validation", "verify transaction", "transaction check", "payment verification", "transaction screening", "pre-processing check"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/transactions/validate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('reconcile_account', 'Reconcile Account', 'Reconcile account balances against transaction records to identify discrepancies and ensure accuracy.', 'account_management',
     '["account reconciliation", "balance reconciliation", "statement reconciliation", "reconcile transactions", "account audit", "balance matching"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/accounts/reconcile"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_compliance', 'Verify Compliance', 'Verify that a transaction or process complies with all applicable regulatory, policy, and internal guidelines.', 'compliance',
     '["compliance verification", "regulatory check", "compliance check", "policy verification", "regulatory compliance", "compliance validation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/compliance/verify"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_kyc_reminder', 'Send KYC Reminder', 'Send a reminder to the customer to complete pending KYC.', 'finance',
     '["kyc reminder", "remind kyc", "kyc pending notification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('sanctions_check', 'Sanctions Check', 'Screen the customer or transaction against global sanctions lists, OFAC watchlists, and denied party databases before processing.', 'compliance',
     '["blacklist screening", "denied party check", "denied party screening", "embargo check", "global sanctions check", "ofac check", "sanctions compliance", "sanctions screening", "sanctions verification", "terror financing check", "watchlist check", "watchlist screening"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/compliance/sanctions"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('submit_regulatory_report', 'Submit Regulatory Report', 'Submit mandatory regulatory report to RBI, SEBI, or other regulators within the prescribed deadline.', 'compliance',
     '["regulatory submission", "rbi report", "compliance report", "file regulatory report", "regulatory filing", "submit compliance report", "mandatory report submission"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/compliance/reports/submit"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_overdue_notice', 'Send Overdue Notice', 'Send a formal overdue notice to the borrower informing them of the overdue amount and pending payment.', 'collections',
     '["overdue notice", "default notice", "late payment notice", "overdue intimation", "notice to borrower"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/overdue/notice"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('initiate_collection', 'Initiate Collection', 'Initiate the collections process for a delinquent loan account by contacting the borrower and establishing a recovery plan.', 'collections',
     '["collection initiation", "start collections", "recovery initiation", "debt collection start", "delinquency action", "overdue recovery", "collections process", "initiate recovery"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/initiate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('write_off_loan', 'Write Off Loan', 'Write off the loan amount from the banks books as a bad debt after regulatory approval.', 'collections',
     '["loan write-off", "write off loan", "npa write-off", "debt write-off", "bad debt write-off", "charge off loan"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/write-off/loan"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('notify_manager', 'Notify Manager', 'Send notification to the responsible manager.', 'finance',
     '["manager notification", "alert manager", "inform manager", "manager alert", "notify supervisor"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('waive_penalty', 'Waive Penalty', 'Waive penalty charges on a loan account as a customer goodwill gesture or per settlement agreement.', 'collections',
     '["penalty waiver", "waive late charges", "fee waiver", "penalty removal", "interest waiver", "charges waiver", "overdue charges waiver"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/penalty/waive"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('block_debit_card', 'Block Debit Card', 'Block a lost, stolen, or compromised debit card to prevent unauthorised use.', 'cards',
     '["debit card block", "card blocking", "hot card", "block card", "debit card stop", "card suspension", "stop debit card"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/cards/debit/block"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_neft', 'Process NEFT', 'Process a National Electronic Funds Transfer payment through the NEFT clearing system.', 'payments',
     '["neft transfer", "neft payment", "process neft transfer", "national funds transfer", "bank transfer neft", "bank to bank neft", "inter bank transfer"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/payments/neft"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('issue_credit_card', 'Issue Credit Card', 'Issue a new credit card to the customer.', 'finance',
     '["credit card issuance", "new credit card", "create credit card"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_financial_report', 'Generate Financial Report', 'Generate a financial performance or MIS report.', 'finance',
     '["financial report", "mis report", "finance report", "management report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_payment_confirmation', 'Send Payment Confirmation', 'Send a payment confirmation notification to the borrower acknowledging receipt of the payment.', 'collections',
     '["payment confirmation", "receipt confirmation", "acknowledge payment", "payment received", "confirmation notification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/payment/confirmation"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('update_payment_method', 'Update Payment Method', 'Update customer preferred payment method.', 'finance',
     '["payment method change", "update payment", "change payment mode"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('notify_payment_failure', 'Notify Payment Failure', 'Notify customer and system about a failed payment.', 'finance',
     '["payment failure notification", "failed payment alert", "transaction failure notice"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_rtgs', 'Process RTGS', 'Process a Real Time Gross Settlement high-value funds transfer through the RTGS system.', 'payments',
     '["rtgs transfer", "rtgs payment", "high value transfer", "real time transfer", "large value transfer"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/payments/rtgs"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_reminder', 'Send Reminder', 'Send a generic reminder notification to the customer.', 'finance',
     '["reminder", "send reminder", "follow up", "notification reminder"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_imps', 'Process IMPS', 'Process an Immediate Payment Service transfer for instant 24x7 fund movement.', 'payments',
     '["imps transfer", "immediate payment", "instant transfer", "imps payment", "mobile payment transfer"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/payments/imps"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('request_additional_information', 'Request Additional Information', 'Request additional information or clarification from the applicant during loan processing or underwriting.', 'loan_underwriting',
     '["additional info request", "ask for clarification", "raise info request", "seek additional details", "info request to applicant"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/application/request-info"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_audit_report', 'Send Audit Report', 'Send completed audit report to stakeholders.', 'finance',
     '["audit report dispatch", "share audit report", "audit findings"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_credit_check', 'Process Credit Check', 'Run a comprehensive credit check on the applicant from all available bureaus to assess credit risk.', 'kyc',
     '["credit check", "credit assessment", "credit inquiry", "credit screening", "comprehensive credit check", "multi bureau check"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/credit/check"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('assess_creditworthiness', 'Assess Creditworthiness', 'Evaluate borrower creditworthiness by analysing credit score, income, existing obligations, and repayment capacity before loan decision.', 'loan_underwriting',
     '["creditworthiness assessment", "credit evaluation", "credit analysis", "borrower assessment", "repayment capacity check", "credit capacity", "loan eligibility assessment", "financial assessment", "credit appraisal", "risk assessment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/underwriting/assess"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('escalate_to_rm', 'Escalate To RM', 'Escalate a customer issue or application to the Relationship Manager for personal handling.', 'lifecycle',
     '["escalate to rm", "rm escalation", "relationship manager escalation", "send to relationship manager"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/cases/escalate/rm"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('approve_loan', 'Approve Loan', 'Approve a loan application after successful underwriting, credit assessment, and compliance verification.', 'loan_underwriting',
     '["loan approval", "sanction loan", "credit approval", "loan sanctioned", "approve credit", "loan clearance", "sanction credit", "approve loan application", "loan accepted", "credit granted"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/approve"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('reject_loan_application', 'Reject Loan Application', 'Formally reject and close a loan application with written communication citing reasons for rejection.', 'loan_underwriting',
     '["application rejection", "close declined application", "credit denied", "decline application", "decline loan", "formal loan rejection", "loan declined", "loan not approved", "loan refusal", "loan rejection", "notify loan rejection", "reject borrower", "reject credit application"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/application/reject"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('disburse_loan', 'Disburse Loan', 'Disburse the approved loan amount by transferring funds to the borrower account or directly to the vendor.', 'loan_servicing',
     '["loan disbursement", "fund loan", "transfer loan principal", "disburse funds", "credit loan amount", "loan payout", "release loan funds", "loan transfer", "fund disbursement", "transfer principal funds", "disburse loan amount"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/disburse"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_loan_agreement', 'Generate Loan Agreement', 'Generate the loan agreement document with all terms, conditions, interest rate, and repayment schedule for customer signature.', 'loan_underwriting',
     '["loan agreement", "sanction letter", "loan document generation", "generate sanction letter", "loan contract", "credit agreement", "loan deed", "term sheet generation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"handler": "generate_loan_agreement"}, "execution_type": "python"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_welcome_kit', 'Send Welcome Kit', 'Dispatch welcome kit with account details to new customer.', 'finance',
     '["welcome package", "onboarding kit", "account kit", "welcome letter"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_emi', 'Calculate EMI', 'Calculate the monthly Equated Monthly Instalment for a loan based on principal, interest rate, and tenure.', 'loan_underwriting',
     '["emi calculation", "monthly instalment calculation", "compute emi", "loan emi", "emi computation", "monthly payment calculation", "instalment amount calculation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"handler": "calculate_emi"}, "execution_type": "python"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_loan_offer', 'Send Loan Offer', 'Send pre-approved or personalized loan offer to customer.', 'finance',
     '["loan offer", "credit offer", "pre-approved offer", "loan proposal"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('initiate_kyc', 'Initiate KYC', 'Start the Know Your Customer identity verification process for a new or existing customer before account opening or loan disbursement.', 'kyc',
     '["start kyc", "begin kyc", "kyc initiation", "know your customer verification", "identity verification start", "customer identification process", "kyc process begin", "identity check initiation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/initiate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_disbursement_advice', 'Send Disbursement Advice', 'Send disbursement confirmation and details to customer.', 'finance',
     '["disbursement notice", "disbursement confirmation", "loan credited notification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('complete_kyc', 'Complete KYC', 'Mark the Know Your Customer verification as successfully completed after all identity and address documents have been validated.', 'kyc',
     '["kyc done", "kyc completed", "kyc verified", "finish kyc", "kyc approved", "kyc clearance", "identity verified", "kyc successful", "verification complete"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/complete"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_post_disbursement_documents', 'Collect Post-Disbursement Documents', 'Collect documents required after loan disbursement such as property registration, insurance, or utilization certificates.', 'loan_servicing',
     '["post disbursement docs", "collect post disbursal documents", "post loan documents", "post disbursement collection"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/post-disbursement/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('schedule_personal_discussion', 'Schedule Personal Discussion', 'Schedule a personal discussion with the applicant to discuss income, business, and loan purpose before credit decision.', 'loan_underwriting',
     '["pd scheduling", "book personal discussion", "arrange pd", "schedule pd", "customer pd", "credit interview scheduling"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/pd/schedule"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('freeze_suspicious_account', 'Freeze Suspicious Account', 'Freeze a bank account flagged for suspicious or fraudulent activity to prevent further unauthorized transactions during investigation.', 'compliance',
     '["freeze suspicious account", "fraud account freeze", "suspicious activity freeze", "block fraud account", "security freeze", "fraud hold", "AML account freeze", "freeze for investigation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/accounts/freeze-suspicious"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_technical_report', 'Send Technical Report', 'Send property technical appraisal report to stakeholders.', 'finance',
     '["technical report", "valuation report", "site report", "inspection report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_payment_reminder', 'Send Payment Reminder', 'Send EMI or payment due reminder to the customer.', 'finance',
     '["due reminder", "emi reminder", "installment reminder", "overdue reminder", "payment reminder", "reminder notification", "reminder sms", "repayment reminder", "send reminder"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_employment_details', 'Collect Employment Details', 'Collect the applicant employment information including current employer, designation, years of experience, and employment type.', 'kyc',
     '["employment details", "job details", "work information", "occupation details", "employer information", "professional details", "career details"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/employment/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_pmegp_loan', 'Process PMEGP Loan', 'Process loan under Prime Minister Employment Generation Programme.', 'finance',
     '["pmegp", "employment generation", "startup loan", "pmegp subsidy"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_business_details', 'Collect Business Details', 'Collect the applicant business information including business type, years in operation, annual turnover, and business registration details.', 'kyc',
     '["business details", "business information", "enterprise details", "company information", "business profile", "firm details", "proprietorship details"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/business/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('assign_recovery_agent', 'Assign Recovery Agent', 'Assign a field recovery agent to visit and collect outstanding dues from a defaulting borrower.', 'collections',
     '["recovery agent assignment", "field agent allocation", "assign collector", "assign field agent", "collection agent", "recovery agent"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/agent/assign"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_legal_notice', 'Send Legal Notice', 'Issue formal legal notice to defaulting borrower.', 'finance',
     '["legal notice", "demand notice", "legal warning", "notice under sarfaesi"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('initiate_legal_action', 'Initiate Legal Action', 'Initiate legal proceedings against a defaulting borrower for recovery of outstanding loan amount.', 'collections',
     '["court filing", "debt recovery legal", "file legal case", "legal action", "legal notice", "legal proceedings", "legal recovery", "litigation", "litigation initiation", "recovery suit"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/legal/initiate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('raise_legal_query', 'Raise Legal Query', 'Raise a legal query or clarification request regarding property title or documentation discrepancies.', 'home_loan',
     '["legal query", "title query", "legal clarification", "documentation query", "legal question", "legal issue flagged"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/home-loan/legal/query"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('legal_verification_cleared', 'Legal Verification Cleared', 'Mark legal verification as cleared and property title as clean, allowing loan to proceed.', 'home_loan',
     '["legal approved", "legal clearance", "legal cleared", "legal ok", "legal passed", "no legal objection", "title clear", "title verified"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/home-loan/legal/clear"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('restructure_loan', 'Restructure Loan', 'Restructure loan repayment terms by modifying interest rate, tenure, or instalment amount to help a distressed borrower.', 'collections',
     '["loan restructuring", "loan modification", "rescheduling", "debt restructuring", "loan restructure", "repayment restructure", "emi restructure", "loan rescheduling"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/restructure"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('register_mortgage', 'Register Mortgage', 'Register mortgage charge on property with the sub-registrar office to secure the bank loan.', 'home_loan',
     '["mortgage registration", "register charge", "property mortgage", "equitable mortgage", "create mortgage", "charge registration", "mortgage creation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/home-loan/mortgage/register"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('disburse_tranche', 'Disburse Tranche', 'Disburse a partial tranche of loan amount linked to construction milestone or stage completion.', 'home_loan',
     '["tranche disbursement", "stage disbursement", "partial disbursement", "construction stage payout", "milestone payment", "tranche release"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/home-loan/tranche/disburse"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('close_account', 'Close Account', 'Close and archive a completed loan file or bank account after final settlement, filing all related documents.', 'account_management',
     '["account closure", "close loan file", "archive loan", "terminate account", "close bank account", "account termination", "loan file closure", "close and archive", "loan closure", "file closure"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/accounts/close"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('upgrade_account', 'Upgrade Account', 'Upgrade customer account to a higher product tier or premium category with enhanced features and limits.', 'account_management',
     '["account upgrade", "tier upgrade", "premium account", "account promotion", "upgrade to premium", "enhance account", "account tier change"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/accounts/upgrade"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_possession_notice', 'Send Possession Notice', 'Send property possession notice to customer.', 'finance',
     '["asset possession", "handover notice", "possession notice", "property ready", "recovery possession", "sarfaesi possession", "take possession"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('return_original_documents', 'Return Original Documents', 'Return original property documents to the customer after full loan repayment and account closure.', 'home_loan',
     '["document return", "return title deeds", "release documents", "return original deeds", "property document return"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/home-loan/documents/return"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('initiate_vehicle_valuation', 'Initiate Vehicle Valuation', 'Initiate formal valuation of the vehicle to determine its market value for loan security purposes.', 'car_loan',
     '["vehicle valuation", "car valuation", "vehicle appraisal", "automobile valuation", "car assessment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/car-loan/valuation/initiate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('activate_overdraft', 'Activate Overdraft', 'Enable overdraft facility on a current or savings account allowing the customer to withdraw beyond available balance up to approved limit.', 'account_management',
     '["overdraft activation", "enable overdraft", "od facility setup", "overdraft setup", "activate od", "credit line activation", "overdraft enable", "od activation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/accounts/overdraft/activate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_dealer_invoice', 'Verify Dealer Invoice', 'Verify the dealer proforma invoice for the vehicle to confirm price, model, and dealer credentials.', 'car_loan',
     '["invoice verification", "dealer invoice check", "vehicle invoice", "car invoice verification", "proforma verification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/car-loan/dealer/invoice/verify"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('reactivate_dormant_account', 'Reactivate Dormant Account', 'Reactivate a dormant or inactive bank account after customer verification and compliance check.', 'account_management',
     '["account revival", "activate inactive account", "dormant account reactivation", "dormant revival", "inoperative activation", "reactivate inactive customer", "reactivate inoperative", "revive dormant account", "wake dormant account"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/accounts/dormant/reactivate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('coordinate_with_dealer', 'Coordinate With Dealer', 'Coordinate with the automobile dealer for vehicle delivery, RC transfer, and insurance confirmation.', 'car_loan',
     '["dealer coordination", "dealer communication", "vehicle delivery coordination", "dealer liaison", "car dealer follow-up"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/car-loan/dealer/coordinate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('disburse_to_dealer', 'Disburse To Dealer', 'Disburse the loan amount directly to the automobile dealer on behalf of the borrower.', 'car_loan',
     '["dealer payment", "pay dealer", "disburse to dealer", "dealer disbursement", "direct dealer payment", "car loan disbursement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/car-loan/dealer/disburse"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('initiate_rc_hypothecation', 'Initiate RC Hypothecation', 'Initiate endorsement of bank hypothecation on the vehicle Registration Certificate.', 'car_loan',
     '["rc hypothecation", "vehicle hypothecation", "hypothecation endorsement", "registration hypothecation", "rc endorsement", "hypothecation registration"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/car-loan/hypothecation/initiate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_vehicle_insurance', 'Verify Vehicle Insurance', 'Verify that the vehicle has adequate comprehensive insurance coverage as required for the loan.', 'car_loan',
     '["vehicle insurance check", "car insurance verification", "insurance validation", "motor insurance check", "insurance coverage verification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/car-loan/insurance/verify"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('release_hypothecation', 'Release Hypothecation', 'Release the hypothecation charge on the vehicle Registration Certificate after full loan repayment.', 'car_loan',
     '["hypothecation release", "remove hypothecation", "noc for vehicle", "rc hypothecation removal", "vehicle charge release"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/car-loan/hypothecation/release"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_foreclosure_statement', 'Send Foreclosure Statement', 'Send loan foreclosure statement with outstanding amount.', 'finance',
     '["foreclosure statement", "pre-closure statement", "early closure amount", "prepayment statement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('reverse_transaction', 'Reverse Transaction', 'Reverse an incorrectly processed transaction and restore the account balance to its prior state.', 'account_management',
     '["transaction reversal", "reverse payment", "undo transaction", "chargeback", "transaction cancel", "payment reversal", "debit reversal", "credit reversal"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/transactions/reverse"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('hold_funds', 'Hold Funds', 'Place a hold or debit block on customer account funds to prevent withdrawals pending authorization, investigation, or loan disbursement processing.', 'account_management',
     '["fund hold", "place debit block", "account hold", "debit restriction", "block account funds", "payment stop", "funds freeze", "hold customer funds", "debit block", "fund restriction", "hold amount", "lien on funds"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/accounts/funds/hold"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('receive_loan_application', 'Receive Loan Application', 'Receive and register a new loan application from customer or channel partner.', 'finance',
     '["receive application", "new loan application", "register loan application", "loan received", "application intake"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('release_funds', 'Release Funds', 'Release previously held or blocked funds in a customer account after authorization or completion of the triggering condition.', 'account_management',
     '["fund release", "lift hold", "unblock funds", "release debit block", "remove fund hold", "funds unfreeze", "release lien", "debit block removal", "fund unblock"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/accounts/funds/release"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('assign_credit_officer', 'Assign Credit Officer', 'Assign a credit officer to process loan application.', 'finance',
     '["credit officer assignment", "loan officer", "assign underwriter"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('charge_penalty', 'Charge Penalty', 'Apply a financial penalty charge to a customer account for missed payment, cheque bounce, or policy violation.', 'account_management',
     '["penalty charge", "apply penalty", "fine charge", "penal charge", "late fee", "penalty fee", "overdue charge", "default charge"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/accounts/penalty/charge"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('apply_interest', 'Apply Interest', 'Apply the applicable interest rate to a loan or deposit account and post the interest amount to the account ledger.', 'loan_servicing',
     '["interest application", "post interest", "interest calculation", "apply interest rate", "interest accrual", "interest posting", "calculate and apply interest", "interest charge", "interest debit", "interest credit", "rate application"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/interest/apply"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_risk_score', 'Calculate Risk Score', 'Calculate an internal risk score for a borrower or transaction to guide the credit or fraud decision.', 'loan_underwriting',
     '["risk score calculation", "risk scoring", "credit risk score", "borrower risk score", "internal risk rating", "risk grade"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"handler": "calculate_risk_score"}, "execution_type": "python"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('flag_high_risk_customer', 'Flag High Risk Customer', 'Flag a customer as high risk based on credit profile, behaviour, or compliance assessment results.', 'loan_underwriting',
     '["high risk flag", "mark high risk", "risk customer flag", "flag risky customer", "high risk classification", "risk alert"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/risk/customer/flag"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('approve_underwriting', 'Approve Underwriting', 'Approve the underwriting assessment for a loan application confirming it meets all risk and policy criteria.', 'loan_underwriting',
     '["underwriting approval", "approve underwriting", "uw approval", "risk approval", "credit committee approval", "underwriting clearance"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/underwriting/approve"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_employment', 'Verify Employment', 'Confirm customer employment details with the employer.', 'finance',
     '["employment check", "employer verification", "job verification", "employment validation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_residence', 'Verify Residence', 'Verify applicant residential address through field visit or document check.', 'finance',
     '["verify residence", "address verification", "residence check", "home verification", "address check"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_risk_alert', 'Send Risk Alert', 'Send internal risk alert to the concerned team.', 'finance',
     '["risk notification", "risk warning", "alert risk team"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_statement', 'Send Statement', 'Send account or loan statement to the customer.', 'finance',
     '["send statement", "account statement", "deliver statement", "statement dispatch"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('schedule_customer_callback', 'Schedule Customer Callback', 'Schedule a callback to the customer for follow-up.', 'finance',
     '["callback scheduling", "schedule call", "follow up call", "customer call"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('run_dedupe_check', 'Run Dedupe Check', 'Check for duplicate applications or existing customer records in the system.', 'finance',
     '["dedupe check", "duplicate check", "deduplication", "check duplicates", "existing customer check"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_cam_report', 'Generate CAM Report', 'Generate Credit Appraisal Memorandum report for loan decision.', 'finance',
     '["cam report", "credit appraisal memo", "generate cam", "credit memo", "appraisal report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('run_bureau_check', 'Run Bureau Check', 'Retrieve credit report and score from any registered credit bureau to evaluate borrower repayment history and outstanding liabilities.', 'kyc',
     '["bureau check", "credit bureau query", "credit report fetch", "bureau enquiry", "credit information check", "credit score retrieval", "crif check", "experian check", "equifax check", "bureau report pull", "credit history verification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/bureau/query"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('notify_branch', 'Notify Branch', 'Send notification to the branch office.', 'finance',
     '["branch notification", "inform branch", "branch alert", "branch communication"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('conditional_approve_loan', 'Conditional Approve Loan', 'Approve loan with conditions that must be fulfilled before disbursement.', 'finance',
     '["conditional approval", "approve with conditions", "conditional sanction", "conditional clearance"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_cibil_low_alert', 'Send CIBIL Low Alert', 'Notify customer that their credit score is below threshold.', 'finance',
     '["low cibil alert", "poor credit score", "low score notification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('run_income_verification', 'Run Income Verification', 'Verify applicant income and financial capacity through salary slips, bank statements, or income tax returns before credit decision.', 'kyc',
     '["earnings verification", "financial capacity check", "income assessment", "income check", "income validation", "income verification", "itr verification", "salary proof check", "salary verification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/verification/income"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_property_title', 'Verify Property Title', 'Verify clear title and ownership of collateral property.', 'finance',
     '["title verification", "verify title", "property title check", "title search", "ownership verification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_document_checklist', 'Send Document Checklist', 'Send list of required documents to the customer.', 'finance',
     '["document checklist", "required documents", "document list", "pending documents"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_submitted_documents', 'Verify Submitted Documents', 'Verify authenticity and completeness of all documents submitted by the applicant for loan processing or account opening.', 'kyc',
     '["document verification", "verify documents", "document check", "check submitted papers", "document validation", "paper verification", "document authenticity check", "verify applicant papers"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/documents/verify"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_validation_documents', 'Send Validation Documents', 'Send validated document confirmation to customer.', 'finance',
     '["validation confirmation", "document validated", "verified documents notification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('create_mortgage_deed', 'Create Mortgage Deed', 'Create and register mortgage deed for secured loan collateral.', 'finance',
     '["mortgage deed", "create mortgage", "register mortgage deed", "mortgage document", "deed creation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('aml_screening', 'AML Screening', 'Screen the customer or transaction against anti-money laundering databases and suspicious activity patterns to detect financial crime risk.', 'compliance',
     '["aml check", "aml compliance", "aml due diligence", "aml verification", "anti money laundering", "anti money laundering screening", "financial crime screening", "money laundering check", "money laundering screening", "suspicious activity screening"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/compliance/aml"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('stamp_duty_payment', 'Stamp Duty Payment', 'Process stamp duty payment for mortgage or loan agreement registration.', 'finance',
     '["stamp duty", "pay stamp duty", "stamp duty payment", "registration charges", "stamp fee"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_loan_account_number', 'Generate Loan Account Number', 'Generate unique loan account number after sanction approval.', 'finance',
     '["loan account number", "generate account", "create loan account", "loan number", "account creation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('set_repayment_mode', 'Set Repayment Mode', 'Set EMI repayment mode - ECS, NACH, auto-debit, or cheque.', 'finance',
     '["set repayment mode", "ecs setup", "nach mandate", "auto debit setup", "repayment method"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('register_nach_mandate', 'Register NACH Mandate', 'Register NACH mandate for automatic EMI deduction from customer bank account.', 'finance',
     '["auto debit", "ecs mandate", "mandate registration", "nach mandate", "nach registration", "register nach", "standing instruction"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_nach_status', 'Verify NACH Status', 'Check status of NACH mandate registration - approved or rejected.', 'finance',
     '["nach status", "mandate status", "check nach", "verify mandate", "nach confirmation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_rejection_letter', 'Send Rejection Letter', 'Send formal rejection communication to the customer.', 'finance',
     '["rejection letter", "decline letter", "loan rejection notice"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_sanction_terms', 'Send Sanction Terms', 'Send detailed terms and conditions of loan sanction.', 'finance',
     '["sanction terms", "loan terms", "offer terms", "sanction conditions"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_repayment_schedule', 'Generate Repayment Schedule', 'Generate a complete loan repayment schedule showing all EMI dates, principal, interest, and outstanding balance.', 'loan_servicing',
     '["repayment schedule", "amortisation schedule", "emi schedule", "loan repayment plan", "instalment schedule", "payment schedule", "amortization table"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"handler": "generate_repayment_schedule"}, "execution_type": "python"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('link_insurance_to_loan', 'Link Insurance To Loan', 'Link a credit life or property insurance policy to a loan account for protection coverage.', 'loan_servicing',
     '["insurance linkage", "loan insurance", "link insurance", "attach insurance policy", "credit life insurance", "property insurance link"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/loans/insurance/link"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('open_account', 'Open Account', 'Open and activate a new bank account or loan account ledger for the customer after completing KYC and documentation requirements.', 'account_management',
     '["account opening", "create account", "activate account ledger", "open bank account", "new account creation", "account setup", "account activation", "open customer account", "initiate account", "activate account", "open ledger"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/accounts/open"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('pre_disbursement_check', 'Pre Disbursement Check', 'Run all pre-disbursement checks before releasing loan amount.', 'finance',
     '["pre disbursement", "pre disbursal check", "disbursement checklist", "pre release check"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_insurance_reminder', 'Send Insurance Reminder', 'Remind customer about mandatory insurance for their loan.', 'finance',
     '["insurance reminder", "insurance pending", "insurance notification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_noc', 'Send NOC', 'Issue a No Objection Certificate to a customer after full loan repayment.', 'finance',
     '["closure certificate", "issue noc", "loan clearance certificate", "loan closure certificate", "loan noc", "no objection certificate", "noc issuance", "noc letter", "send noc"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_interest_certificate', 'Generate Interest Certificate', 'Generate the annual interest certificate for a loan account for tax filing purposes.', 'loan_servicing',
     '["interest certificate", "annual interest statement", "loan interest certificate", "tax certificate", "interest paid certificate"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"handler": "generate_interest_certificate"}, "execution_type": "python"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('update_cibil_post_closure', 'Update CIBIL Post Closure', 'Update the CIBIL credit bureau with loan closure status after full repayment or settlement.', 'loan_servicing',
     '["cibil update", "bureau update post closure", "credit report update", "close cibil record", "cibil closure update"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/bureau/cibil/closure-update"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('initiate_property_valuation', 'Initiate Property Valuation', 'Initiate formal property valuation by a registered valuer to determine market and distress value of collateral.', 'home_loan',
     '["property valuation", "property appraisal", "collateral valuation", "asset valuation", "property assessment", "valuation initiation", "technical valuation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/home-loan/valuation/initiate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('schedule_technical_visit', 'Schedule Technical Visit', 'Schedule a technical site visit by a bank-appointed engineer to assess property condition and construction stage.', 'home_loan',
     '["technical visit", "site visit", "property inspection", "engineer visit", "field inspection", "technical inspection"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/home-loan/technical/schedule"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('initiate_legal_verification', 'Initiate Legal Verification', 'Initiate legal verification of property title and ownership documents by a panel advocate.', 'home_loan',
     '["legal verification", "title verification", "property legal check", "title search", "legal due diligence", "property title check", "legal opinion", "advocate verification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/home-loan/legal/initiate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('partial_disbursement', 'Partial Disbursement', 'Disburse partial loan amount based on construction stage or conditions.', 'finance',
     '["partial disbursement", "stage disbursement", "partial release", "tranche release", "part disbursement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_to_legal_team', 'Send To Legal Team', 'Send property documents to the legal team for review, title search, and due diligence.', 'home_loan',
     '["legal team referral", "send for legal review", "legal review", "document legal review", "legal examination"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/home-loan/legal/send"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('update_credit_limit', 'Update Credit Limit', 'Increase or decrease the approved credit limit on a credit card or overdraft account based on credit review.', 'account_management',
     '["credit limit change", "increase credit limit", "reduce credit limit", "credit line update", "od limit change", "credit limit revision"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "PUT", "endpoint": "/accounts/credit-limit"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_original_property_documents', 'Collect Original Property Documents', 'Collect original title deeds and property documents from the applicant for safe custody during the loan tenure.', 'home_loan',
     '["collect title deeds", "take original documents", "property documents collection", "original deed custody", "collect property papers"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/home-loan/documents/collect-original"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('notify_developer_disbursement', 'Notify Developer Disbursement', 'Notify builder or developer about loan disbursement.', 'finance',
     '["developer notification", "builder notification", "developer disbursement notice"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_login_fee_receipt', 'Send Login Fee Receipt', 'Send receipt for loan processing or login fee payment.', 'finance',
     '["login fee receipt", "processing fee receipt", "fee receipt", "login fee", "processing fee"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_balance_transfer_request', 'Send Balance Transfer Request', 'Initiate balance transfer request to existing lender.', 'finance',
     '["balance transfer", "bt request", "loan transfer", "takeover request", "bt initiation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('fetch_existing_loan_details', 'Fetch Existing Loan Details', 'Fetch outstanding details from existing lender for balance transfer.', 'finance',
     '["fetch loan details", "existing loan", "outstanding details", "current loan details", "bt details"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_emi_payment', 'Process EMI Payment', 'Process incoming EMI payment and update loan account.', 'finance',
     '["process emi", "emi payment", "monthly installment", "emi received", "payment received"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('mark_emi_bounce', 'Mark EMI Bounce', 'Mark EMI as bounced due to insufficient funds or mandate failure.', 'finance',
     '["emi bounce", "payment bounce", "nach bounce", "emi failed", "installment bounce"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('reject_underwriting', 'Reject Underwriting', 'Reject a loan application at the underwriting stage due to unacceptable risk profile or policy non-compliance.', 'loan_underwriting',
     '["underwriting rejection", "uw decline", "risk rejection", "underwriting failed", "credit committee rejection"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/underwriting/reject"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('apply_bounce_charges', 'Apply Bounce Charges', 'Apply penalty charges for bounced EMI payment.', 'finance',
     '["bounce charges", "bounce penalty", "emi bounce fee", "nach bounce charges", "penalty charges"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_bounce_notification', 'Send Bounce Notification', 'Notify customer about bounced EMI and next steps.', 'finance',
     '["bounce notification", "emi bounce alert", "payment bounce notice", "bounce intimation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('apply_credit', 'Apply Credit', 'Apply a credit adjustment or payment to a loan or account ledger to reduce outstanding balance.', 'loan_servicing',
     '["credit application", "post credit", "apply payment credit", "account credit", "credit adjustment", "credit posting"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/ledger/credit"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_tax', 'Calculate Tax', 'Calculate applicable taxes such as GST or TDS on interest, fees, or transaction amounts.', 'loan_servicing',
     '["tax calculation", "gst calculation", "tds calculation", "compute tax", "interest tax", "tax assessment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"handler": "calculate_tax"}, "execution_type": "python"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_documents', 'Collect Documents', 'Collect and upload required KYC documents including identity proof, address proof, income documents, and financial statements from the borrower or applicant.', 'kyc',
     '["document collection", "gather documents", "collect kyc papers", "upload documents", "document submission", "collect applicant documents", "gather borrower information", "collect personal details", "collect financial documents", "document gathering", "collect customer paperwork", "gather identity documents"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/documents/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('issue_sanction_letter', 'Issue Sanction Letter', 'Issue the formal loan sanction letter to the borrower detailing approved loan amount, interest rate, and terms.', 'loan_servicing',
     '["sanction letter issuance", "send sanction letter", "loan offer letter", "sanction communication", "approval letter", "loan sanction"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"handler": "issue_sanction_letter"}, "execution_type": "python"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('create_payment', 'Create Payment', 'Create a payment instruction for fund transfer via NEFT, RTGS, IMPS, or internal transfer.', 'payments',
     '["payment creation", "initiate payment", "create transfer", "payment instruction", "fund transfer", "create transaction"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/payments/create"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_invoice', 'Send Invoice', 'Generate and send an invoice to the customer.', 'finance',
     '["invoice dispatch", "send bill", "invoice generation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_dpd_alert', 'Send DPD Alert', 'Send alert when account crosses DPD threshold.', 'finance',
     '["dpd alert", "delinquency alert", "overdue alert", "dpd threshold", "past due alert"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('change_emi_date', 'Change EMI Date', 'Change the monthly EMI deduction date as per customer request.', 'finance',
     '["change emi date", "emi date change", "modify emi date", "reschedule emi", "payment date change"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_foreclosure_amount', 'Calculate Foreclosure Amount', 'Calculate total outstanding amount for loan foreclosure.', 'finance',
     '["foreclosure amount", "closure amount", "outstanding for closure", "payoff amount", "settlement amount"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_soa', 'Generate SOA', 'Generate Statement of Account for customer loan.', 'finance',
     '["statement of account", "soa", "generate soa", "loan statement", "account statement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('update_dpd_bucket', 'Update DPD Bucket', 'Update Days Past Due bucket classification for loan account.', 'finance',
     '["dpd update", "days past due", "bucket update", "dpd bucket", "delinquency bucket"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('initiate_sarfaesi', 'Initiate SARFAESI', 'Initiate SARFAESI proceedings for NPA recovery.', 'finance',
     '["asset recovery", "asset seizure", "initiate sarfaesi", "property seizure", "sarfaesi", "sarfaesi notice", "sarfaesi proceedings", "secured asset recovery"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_demand_notice', 'Send Demand Notice', 'Send a formal demand notice to a defaulting borrower demanding immediate payment of outstanding dues.', 'collections',
     '["demand letter", "demand notice", "demand notice generation", "formal demand", "legal demand", "payment demand", "recall notice", "section 13(2) notice"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/demand-notice/send"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('extend_loan_tenure', 'Extend Loan Tenure', 'Extend loan tenure to reduce EMI burden on customer.', 'finance',
     '["extend tenure", "tenure extension", "increase tenure", "loan extension", "modify tenure"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('reduce_loan_tenure', 'Reduce Loan Tenure', 'Reduce loan tenure after prepayment keeping EMI same.', 'finance',
     '["reduce tenure", "tenure reduction", "shorten tenure", "decrease tenure", "tenure cut"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_moratorium', 'Process Moratorium', 'Apply payment moratorium period on a loan account.', 'finance',
     '["moratorium", "payment holiday", "emi holiday", "repayment deferment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_subsidy_credit', 'Process Subsidy Credit', 'Credit government subsidy (PMAY/CLSS) to loan account.', 'finance',
     '["subsidy credit", "pmay credit", "clss credit", "government subsidy", "subsidy applied"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('update_collateral_value', 'Update Collateral Value', 'Update collateral market value based on latest valuation.', 'finance',
     '["update collateral", "collateral revaluation", "property revaluation", "asset value update"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('release_collateral', 'Release Collateral', 'Release collateral documents and lien after loan closure.', 'finance',
     '["release collateral", "release security", "release lien", "collateral release", "security release"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('conduct_cgt', 'Conduct CGT', 'Conduct Compulsory Group Training for microfinance borrowers.', 'finance',
     '["cgt", "group training", "compulsory training", "borrower training", "financial literacy training"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('conduct_grt', 'Conduct GRT', 'Conduct Group Recognition Test to validate group eligibility.', 'finance',
     '["grt", "group recognition", "recognition test", "group validation", "group eligibility test"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_group_members', 'Verify Group Members', 'Verify identity and eligibility of all group members.', 'finance',
     '["verify members", "member verification", "group member check", "member eligibility", "identity check"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('schedule_center_meeting', 'Schedule Center Meeting', 'Schedule weekly or monthly center meeting for collections.', 'finance',
     '["center meeting", "schedule meeting", "collection meeting", "weekly meeting", "group meeting"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('record_center_attendance', 'Record Center Attendance', 'Record attendance at center meeting.', 'finance',
     '["center attendance", "meeting attendance", "mark attendance", "record attendance", "group attendance"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_group_repayment', 'Collect Group Repayment', 'Collect weekly or monthly group repayment at center meeting.', 'finance',
     '["group repayment", "collect repayment", "weekly collection", "group collection", "center collection"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('dissolve_group', 'Dissolve Group', 'Dissolve JLG/SHG group after loan closure or default.', 'finance',
     '["dissolve group", "close group", "group closure", "terminate group", "end group"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_group_insurance', 'Process Group Insurance', 'Process group credit life insurance for microfinance borrowers.', 'finance',
     '["group insurance", "credit life insurance", "microfinance insurance", "borrower insurance"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_repayment_sms', 'Send Repayment SMS', 'Send SMS reminder for upcoming repayment to group members.', 'finance',
     '["repayment sms", "payment sms", "emi sms", "collection sms", "reminder sms"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('upgrade_borrower_cycle', 'Upgrade Borrower Cycle', 'Upgrade borrower to next loan cycle based on repayment history.', 'finance',
     '["upgrade cycle", "loan cycle", "next cycle", "cycle upgrade", "borrower upgrade"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('reject_group_application', 'Reject Group Application', 'Reject group loan application due to failed GRT or eligibility issues.', 'finance',
     '["reject group", "group rejected", "decline group loan", "group application rejected"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_cheque_deposit', 'Process Cheque Deposit', 'Process inward cheque deposit and clearing.', 'finance',
     '["cheque deposit", "process cheque", "deposit cheque", "cheque clearing", "inward cheque"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_dd_request', 'Process DD Request', 'Process demand draft issuance request from customer.', 'finance',
     '["banker cheque", "banker''s draft", "dd creation", "dd issuance", "dd request", "demand draft", "issue dd", "process dd"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('update_nominee', 'Update Nominee', 'Update or change the existing nominee details for a customer account.', 'account_management',
     '["nominee update", "change nominee", "modify nominee", "amend nominee", "nominee modification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "PUT", "endpoint": "/accounts/nominee"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_account_statement', 'Generate Account Statement', 'Generate an account transaction statement for a specific period for customer or auditor use.', 'account_management',
     '["statement generation", "account statement", "issue statement", "transaction statement", "generate passbook", "account history"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"handler": "generate_account_statement"}, "execution_type": "python"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('enable_upi', 'Enable UPI', 'Enable UPI payment facility on customer account.', 'finance',
     '["enable upi", "upi activation", "activate upi", "upi registration", "upi setup"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_standing_instruction', 'Process Standing Instruction', 'Execute a recurring standing instruction on the account.', 'finance',
     '["standing instruction", "auto transfer", "recurring payment", "si execution"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('issue_tds_certificate', 'Issue TDS Certificate', 'Issue TDS certificate for interest earned or paid.', 'finance',
     '["tds certificate", "form 16a", "tax deduction certificate", "tds cert", "interest tds"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_passbook_update', 'Send Passbook Update', 'Send passbook update or mini statement to customer.', 'finance',
     '["passbook update", "mini statement", "passbook printing", "account update", "balance update"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('initiate_wire_transfer', 'Initiate Wire Transfer', 'Initiate international wire transfer for customer.', 'finance',
     '["wire transfer", "international transfer", "swift transfer", "foreign remittance", "cross border payment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_forex_transaction', 'Process Forex Transaction', 'Process foreign exchange transaction for customer.', 'finance',
     '["forex transaction", "foreign exchange", "currency exchange", "forex deal", "fx transaction"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_collection_schedule', 'Generate Collection Schedule', 'Generate collection visit schedule for field agents.', 'finance',
     '["collection schedule", "visit schedule", "field schedule", "agent schedule", "collection plan"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_settlement_offer', 'Send Settlement Offer', 'Send one-time settlement offer to defaulting borrower.', 'finance',
     '["compromise offer", "compromise settlement", "final settlement", "one time settlement", "one-time settlement", "ots", "ots offer", "settlement offer", "settlement proposal"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('initiate_auction', 'Initiate Auction', 'Initiate auction of secured asset under SARFAESI.', 'finance',
     '["initiate auction", "asset auction", "property auction", "sarfaesi auction", "auction notice"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('assign_legal_counsel', 'Assign Legal Counsel', 'Assign legal counsel for recovery proceedings.', 'finance',
     '["assign legal", "legal counsel", "recovery lawyer", "legal assignment", "engage lawyer"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('file_drt_case', 'File DRT Case', 'File recovery case in Debt Recovery Tribunal.', 'finance',
     '["drt filing", "debt recovery tribunal", "drt case", "recovery tribunal"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('monitor_end_use', 'Monitor End Use', 'Monitor end use of disbursed loan funds.', 'finance',
     '["end use monitoring", "fund utilization", "loan utilization", "end use check", "utilization monitoring"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('conduct_stock_audit', 'Conduct Stock Audit', 'Conduct stock or inventory audit for working capital loans.', 'finance',
     '["stock audit", "inventory audit", "stock verification", "warehouse audit", "collateral audit"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('review_credit_limit', 'Review Credit Limit', 'Periodic review of sanctioned credit limit for renewal.', 'finance',
     '["review limit", "credit review", "limit review", "annual review", "credit renewal"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('run_portfolio_analysis', 'Run Portfolio Analysis', 'Run portfolio quality analysis for loan book.', 'finance',
     '["portfolio analysis", "loan book analysis", "portfolio quality", "asset quality", "portfolio review"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_covenant_breach_alert', 'Send Covenant Breach Alert', 'Alert when loan covenant or condition is breached.', 'finance',
     '["covenant breach", "condition breach", "loan condition", "covenant alert", "breach notification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('downgrade_account_rating', 'Downgrade Account Rating', 'Downgrade internal credit rating of loan account.', 'finance',
     '["downgrade rating", "rating downgrade", "credit downgrade", "internal rating", "account downgrade"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_driving_license', 'Verify Driving License', 'Verify the applicant driving license against the RTO database for validity and identity confirmation.', 'kyc',
     '["dl verification", "driving license check", "verify dl", "rto license verification", "license validation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/driving-license/verify"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('reject_kyc', 'Reject KYC', 'Reject KYC application due to failed verification.', 'finance',
     '["kyc rejected", "kyc failed", "decline kyc", "kyc not approved"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('perform_enhanced_due_diligence', 'Perform Enhanced Due Diligence', 'Conduct enhanced due diligence for high-risk customers.', 'finance',
     '["edd", "enhanced due diligence", "high risk due diligence", "enhanced cdd"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('create_customer_profile', 'Create Customer Profile', 'Create a new customer master record in the core banking system.', 'finance',
     '["customer creation", "new customer record", "create customer", "customer onboarding"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('assign_relationship_manager', 'Assign Relationship Manager', 'Assign a dedicated relationship manager to the customer.', 'finance',
     '["assign rm", "rm allocation", "relationship manager assignment", "allocate rm"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_customer_id', 'Generate Customer ID', 'Generate a unique customer identification number.', 'finance',
     '["cif generation", "customer id creation", "generate cif", "unique customer number"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_biometrics', 'Collect Biometrics', 'Capture customer biometric data for identity verification.', 'finance',
     '["biometric capture", "fingerprint collection", "biometric enrollment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('perform_video_kyc', 'Perform Video KYC', 'Conduct video-based KYC verification with the customer.', 'finance',
     '["video kyc", "vkyc", "video verification", "remote kyc"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_kyc_report', 'Generate KYC Report', 'Generate consolidated KYC verification report.', 'finance',
     '["kyc report", "kyc summary", "verification report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('flag_adverse_media', 'Flag Adverse Media', 'Flag customer based on negative news or adverse media screening.', 'finance',
     '["negative news check", "adverse media screening", "media screening", "negative publicity check"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('open_savings_account', 'Open Savings Account', 'Open a new savings bank account for the customer.', 'finance',
     '["savings account opening", "new savings account", "create savings account", "sb account"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('open_current_account', 'Open Current Account', 'Open a new current account for business or individual.', 'finance',
     '["current account opening", "new current account", "create current account", "ca account"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('freeze_account', 'Freeze Account', 'Freeze a bank account to prevent any transactions.', 'finance',
     '["account block", "account freeze", "account hold", "account lock", "block account", "freeze account", "lock account", "lock customer account", "place account freeze", "restrict account", "suspend account"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('unfreeze_account', 'Unfreeze Account', 'Remove freeze on a bank account and restore normal operations.', 'finance',
     '["account unblock", "account unfreeze", "lift account hold", "lift hold", "reactivate account", "remove account freeze", "restore account", "unblock account", "unfreeze account", "unlock account", "unlock customer account"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('downgrade_account', 'Downgrade Account', 'Downgrade customer account to a lower tier.', 'finance',
     '["account downgrade", "tier reduction", "account demotion"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('deactivate_overdraft', 'Deactivate Overdraft', 'Disable overdraft facility on an account.', 'finance',
     '["overdraft deactivation", "disable overdraft", "remove od", "cancel overdraft"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_account_number', 'Generate Account Number', 'Generate a unique bank account number.', 'finance',
     '["account number generation", "new account number", "assign account number"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('update_account_mandate', 'Update Account Mandate', 'Change the operating mandate or signatory rules on an account.', 'finance',
     '["mandate change", "signatory update", "operating instructions change"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('set_transaction_limit', 'Set Transaction Limit', 'Configure daily or per-transaction limits on an account.', 'finance',
     '["transaction limit", "set limit", "daily limit", "transfer limit"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('enable_internet_banking', 'Enable Internet Banking', 'Activate internet banking access for the customer.', 'finance',
     '["activate internet banking", "digital banking", "ibanking", "internet banking", "internet banking setup", "net banking", "net banking activation", "online banking"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('enable_mobile_banking', 'Enable Mobile Banking', 'Activate mobile banking access for the customer.', 'finance',
     '["activate mobile", "app banking", "enable mobile banking", "mobile banking", "mobile banking activation", "mobile banking registration", "mobile banking setup"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('issue_cheque_book', 'Issue Cheque Book', 'Issue a new cheque book to the customer against a savings or current account.', 'account_management',
     '["cheque book issuance", "new cheque book", "chequebook request", "issue chequebook", "cheque book order"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/accounts/cheque-book/issue"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_debt_service_ratio', 'Calculate Debt Service Ratio', 'Calculate customer debt-to-income ratio.', 'finance',
     '["dsr calculation", "debt to income", "foir", "fixed obligation ratio", "dti ratio"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('upgrade_npa_to_standard', 'Upgrade NPA to Standard', 'Upgrade an NPA account back to standard asset category.', 'finance',
     '["npa upgrade", "standard asset", "npa recovery", "asset upgrade"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('transfer_to_securitization', 'Transfer to Securitization', 'Transfer loan to securitization pool.', 'finance',
     '["securitization", "loan sale", "pool transfer", "asset securitization"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('mark_wilful_defaulter', 'Mark Wilful Defaulter', 'Classify borrower as wilful defaulter per RBI guidelines.', 'finance',
     '["wilful defaulter", "intentional default", "willful default classification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('compute_provisioning', 'Compute Provisioning', 'Calculate provisioning amount for NPA accounts.', 'finance',
     '["provisioning calculation", "npa provision", "provision requirement", "loan loss provision"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_swift_transfer', 'Process SWIFT Transfer', 'Process an international wire transfer via SWIFT network.', 'finance',
     '["swift payment", "wire transfer", "international transfer", "foreign remittance", "swift message"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('validate_ifsc', 'Validate IFSC', 'Validate beneficiary bank IFSC code.', 'finance',
     '["ifsc validation", "ifsc check", "bank code verification", "branch code check"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('validate_account_number', 'Validate Account Number', 'Validate beneficiary account number format and existence.', 'finance',
     '["account validation", "beneficiary check", "account number check"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_bulk_payment', 'Process Bulk Payment', 'Process a batch of multiple payments together.', 'finance',
     '["bulk payment", "batch payment", "mass transfer", "salary upload", "bulk disbursement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_payment_advice', 'Generate Payment Advice', 'Generate payment advice document for the transaction.', 'finance',
     '["payment advice", "remittance advice", "payment note"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_pay_order', 'Process Pay Order', 'Issue a pay order or banker''s cheque.', 'finance',
     '["pay order", "banker cheque", "cashier cheque"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_inward_remittance', 'Process Inward Remittance', 'Process incoming foreign remittance to customer account.', 'finance',
     '["inward remittance", "incoming wire", "foreign credit", "inward swift"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_outward_remittance', 'Process Outward Remittance', 'Process outgoing foreign remittance from customer account.', 'finance',
     '["outward remittance", "foreign transfer", "overseas payment", "outward swift"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('check_fema_compliance', 'Check FEMA Compliance', 'Verify transaction compliance with FEMA regulations.', 'finance',
     '["fema check", "forex compliance", "rbi liberalized remittance", "lrs check"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_tcs_on_remittance', 'Collect TCS on Remittance', 'Collect Tax Collected at Source on foreign remittances.', 'finance',
     '["tcs collection", "tax on remittance", "tcs deduction", "remittance tax"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('reconcile_transaction', 'Reconcile Transaction', 'Reconcile a transaction against bank records.', 'finance',
     '["transaction reconciliation", "payment reconciliation", "reconcile payment", "match transaction"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('settle_transaction', 'Settle Transaction', 'Complete final settlement of a financial transaction.', 'finance',
     '["transaction settlement", "payment settlement", "final settlement", "clear transaction"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('issue_virtual_card', 'Issue Virtual Card', 'Generate a virtual card for online transactions.', 'finance',
     '["virtual card creation", "digital card", "online card", "e-card"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('block_credit_card', 'Block Credit Card', 'Temporarily or permanently block a credit card.', 'finance',
     '["credit card block", "hotlist credit card", "disable credit card"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('unblock_card', 'Unblock Card', 'Unblock a debit or credit card previously blocked at customer or bank request after verification.', 'cards',
     '["card unblock", "reactivate card", "restore card", "lift card block", "enable card", "remove card block"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/cards/unblock"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('activate_card', 'Activate Card', 'Activate a newly issued debit or credit card for the customer after delivery confirmation.', 'cards',
     '["card activation", "activate new card", "enable card", "card enablement", "first time activation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/cards/activate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_card_statement', 'Generate Card Statement', 'Generate monthly credit card statement.', 'finance',
     '["card statement", "credit card bill", "card billing statement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('dispute_card_transaction', 'Dispute Card Transaction', 'Raise a dispute on a card transaction.', 'finance',
     '["card dispute", "transaction dispute", "chargeback request", "contest charge"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('resolve_card_dispute', 'Resolve Card Dispute', 'Resolve an existing card transaction dispute.', 'finance',
     '["dispute resolution", "settle dispute", "close dispute", "chargeback resolution"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('enable_international_usage', 'Enable International Usage', 'Enable card for international transactions.', 'finance',
     '["international activation", "overseas card", "foreign transaction enable", "global card"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('enroll_rewards_program', 'Enroll Rewards Program', 'Enroll credit card in a rewards or loyalty program.', 'finance',
     '["rewards enrollment", "loyalty program", "reward points", "card rewards"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('redeem_reward_points', 'Redeem Reward Points', 'Redeem accumulated credit card reward points.', 'finance',
     '["reward redemption", "points redemption", "use reward points", "cashback redemption"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('perform_transaction_monitoring', 'Perform Transaction Monitoring', 'Monitor transactions against fraud and AML rules.', 'finance',
     '["transaction monitoring", "aml monitoring", "fraud monitoring", "transaction surveillance"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_risk_report', 'Generate Risk Report', 'Generate risk assessment report for management review.', 'finance',
     '["risk report", "risk assessment report", "credit risk report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('block_fraudulent_transaction', 'Block Fraudulent Transaction', 'Block a transaction identified as fraudulent in real-time.', 'finance',
     '["block fraud", "stop fraudulent payment", "decline fraud transaction"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_fraud_alert', 'Send Fraud Alert', 'Alert customer about potential fraud on their account.', 'finance',
     '["fraud alert", "fraud notification", "suspicious activity alert", "fraud warning"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('initiate_fraud_investigation', 'Initiate Fraud Investigation', 'Start formal investigation of a suspected fraud case.', 'finance',
     '["fraud investigation", "investigation start", "fraud case opening"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('compute_gst', 'Compute GST', 'Calculate GST applicable on banking services.', 'finance',
     '["gst calculation", "goods and services tax", "service tax", "gst computation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('deduct_tds', 'Deduct TDS', 'Deduct Tax Deducted at Source on interest or payments.', 'finance',
     '["tds deduction", "tax deduction at source", "tds on interest", "withholding tax"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_form_16a', 'Generate Form 16A', 'Generate TDS certificate Form 16A for the customer.', 'finance',
     '["form 16a", "tds certificate", "tax certificate generation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('file_gst_return', 'File GST Return', 'File periodic GST return for banking operations.', 'finance',
     '["gst return", "gst filing", "gstr filing", "gst compliance"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('perform_fatca_reporting', 'Perform FATCA Reporting', 'Report account information as per FATCA/CRS requirements.', 'finance',
     '["fatca report", "crs reporting", "foreign account reporting", "fatca compliance"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_basel_report', 'Generate Basel Report', 'Generate capital adequacy report as per Basel norms.', 'finance',
     '["basel report", "capital adequacy", "car report", "regulatory capital report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_slr_report', 'Generate SLR Report', 'Generate Statutory Liquidity Ratio compliance report.', 'finance',
     '["slr report", "statutory liquidity", "slr compliance"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_crr_report', 'Generate CRR Report', 'Generate Cash Reserve Ratio compliance report.', 'finance',
     '["crr report", "cash reserve", "crr compliance", "reserve requirement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('report_fraud_to_rbi', 'Report Fraud to RBI', 'Report fraud incident to Reserve Bank of India.', 'finance',
     '["rbi fraud report", "central bank fraud reporting", "regulatory fraud notification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('issue_letter_of_credit', 'Issue Letter of Credit', 'Issue a letter of credit for trade finance.', 'finance',
     '["lc issuance", "letter of credit", "documentary credit", "trade lc"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('advise_letter_of_credit', 'Advise Letter of Credit', 'Advise a received letter of credit to the beneficiary.', 'finance',
     '["lc advising", "advise lc", "lc notification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('confirm_letter_of_credit', 'Confirm Letter of Credit', 'Add confirmation to a letter of credit.', 'finance',
     '["lc confirmation", "confirmed lc", "add confirmation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('amend_letter_of_credit', 'Amend Letter of Credit', 'Process an amendment to an existing letter of credit.', 'finance',
     '["lc amendment", "modify lc", "change lc terms"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('negotiate_lc_documents', 'Negotiate LC Documents', 'Negotiate documents presented under a letter of credit.', 'finance',
     '["document negotiation", "lc negotiation", "bill negotiation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('issue_bank_guarantee', 'Issue Bank Guarantee', 'Issue a bank guarantee on behalf of customer.', 'finance',
     '["bg issuance", "bank guarantee", "guarantee issuance", "performance guarantee"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('invoke_bank_guarantee', 'Invoke Bank Guarantee', 'Process invocation claim on a bank guarantee.', 'finance',
     '["bg invocation", "guarantee claim", "invoke guarantee", "bg encashment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('release_bank_guarantee', 'Release Bank Guarantee', 'Release a bank guarantee after obligation fulfillment.', 'finance',
     '["bg release", "guarantee release", "cancel guarantee"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_bill_discounting', 'Process Bill Discounting', 'Discount a trade bill for the customer.', 'finance',
     '["bill discounting", "invoice discounting", "bill purchase", "trade bill"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_export_bill', 'Process Export Bill', 'Process export bill for collection or negotiation.', 'finance',
     '["export bill", "foreign bill", "export collection", "bill for collection"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_import_bill', 'Process Import Bill', 'Process import bill received from overseas bank.', 'finance',
     '["import bill", "inward bill", "import collection", "documents against payment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('book_forex_deal', 'Book Forex Deal', 'Book a foreign exchange deal for the customer.', 'finance',
     '["fx booking", "forex deal", "currency deal", "exchange booking"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('execute_forex_conversion', 'Execute Forex Conversion', 'Execute a foreign currency conversion transaction.', 'finance',
     '["currency conversion", "forex exchange", "fx conversion", "currency swap"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_forward_contract', 'Process Forward Contract', 'Book or settle a forex forward contract.', 'finance',
     '["forward contract", "fx forward", "forward booking", "forward deal"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('manage_nostro_account', 'Manage Nostro Account', 'Manage bank''s nostro account transactions and reconciliation.', 'finance',
     '["nostro management", "correspondent account", "nostro reconciliation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('manage_vostro_account', 'Manage Vostro Account', 'Manage vostro account for correspondent banking partner.', 'finance',
     '["vostro management", "mirror account", "vostro reconciliation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_forex_margin', 'Calculate Forex Margin', 'Calculate margin on foreign exchange transactions.', 'finance',
     '["fx margin", "forex spread", "exchange margin", "conversion charge"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_email_notification', 'Send Email Notification', 'Send an email notification to the customer.', 'finance',
     '["email notification", "send email", "email alert", "email communication"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_sms_notification', 'Send SMS Notification', 'Send an SMS notification to customer mobile.', 'finance',
     '["sms notification", "send sms", "text message", "sms alert"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_push_notification', 'Send Push Notification', 'Send a push notification via mobile banking app.', 'finance',
     '["push notification", "app notification", "mobile alert", "in-app notification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('send_whatsapp_notification', 'Send WhatsApp Notification', 'Send notification via WhatsApp Business.', 'finance',
     '["whatsapp message", "whatsapp alert", "wa notification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('notify_customer', 'Notify Customer', 'Send a generic notification to the customer.', 'finance',
     '["customer notification", "inform customer", "customer alert", "notify client"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_report', 'Generate Report', 'Generate a standard business report.', 'finance',
     '["report generation", "create report", "build report", "produce report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('trigger_webhook', 'Trigger Webhook', 'Trigger an outbound webhook to external system.', 'finance',
     '["webhook trigger", "api callback", "event notification", "webhook call"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('archive_document', 'Archive Document', 'Archive a document in the document management system.', 'finance',
     '["document archival", "archive file", "store document", "dms upload"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('retrieve_document', 'Retrieve Document', 'Retrieve a document from the document management system.', 'finance',
     '["document retrieval", "fetch document", "get document", "dms fetch"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_digital_signature', 'Verify Digital Signature', 'Verify digital signature on an electronic document.', 'finance',
     '["signature verification", "digital signature check", "dsc verification", "e-sign validation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_e_stamp', 'Generate E-Stamp', 'Generate electronic stamp paper for legal documents.', 'finance',
     '["e-stamp", "electronic stamp", "stamp duty", "e-stamp certificate"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_fd_interest', 'Calculate FD Interest', 'Calculate interest on a fixed deposit.', 'finance',
     '["fd interest", "fixed deposit interest", "term deposit interest", "fd maturity value"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_fd_maturity', 'Process FD Maturity', 'Process a fixed deposit on its maturity date.', 'finance',
     '["fd maturity", "deposit maturity", "fd encashment", "mature fd"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('renew_fixed_deposit', 'Renew Fixed Deposit', 'Auto-renew or manually renew a maturing fixed deposit.', 'finance',
     '["fd renewal", "reinvest fd", "rollover fd", "fd extension"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('premature_close_fd', 'Premature Close FD', 'Close a fixed deposit before maturity with penalty.', 'finance',
     '["break fd", "close fd", "early fd withdrawal", "fd break", "fd closure", "fd premature", "premature closure"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_rd_maturity', 'Calculate RD Maturity', 'Calculate recurring deposit maturity amount.', 'finance',
     '["rd maturity", "rd maturity value", "rd final amount"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('credit_interest_to_account', 'Credit Interest to Account', 'Credit accrued interest to customer savings or deposit account.', 'finance',
     '["interest credit", "pay interest", "interest payout", "interest posting"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('perform_eod_processing', 'Perform EOD Processing', 'Execute end-of-day batch processing for the banking system.', 'finance',
     '["eod processing", "end of day", "day end batch", "eod run", "day close"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('perform_month_end_processing', 'Perform Month End Processing', 'Execute month-end batch processing and accruals.', 'finance',
     '["month end", "monthly close", "month end batch", "periodic processing"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('reconcile_inter_branch', 'Reconcile Inter-Branch', 'Reconcile transactions between bank branches.', 'finance',
     '["inter branch reconciliation", "ibr", "branch reconciliation", "inter office entries"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('reconcile_atm_transactions', 'Reconcile ATM Transactions', 'Reconcile ATM transactions with switch and CBS.', 'finance',
     '["atm reconciliation", "atm settlement", "switch reconciliation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('reconcile_upi_transactions', 'Reconcile UPI Transactions', 'Reconcile UPI transactions with NPCI settlement.', 'finance',
     '["upi reconciliation", "npci reconciliation", "upi settlement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('settle_clearing_batch', 'Settle Clearing Batch', 'Process and settle cheque clearing batch.', 'finance',
     '["clearing settlement", "cheque clearing", "batch settlement", "cts clearing"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_inward_clearing', 'Process Inward Clearing', 'Process cheques received in inward clearing.', 'finance',
     '["inward clearing", "inward cheque", "clearing inward"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_outward_clearing', 'Process Outward Clearing', 'Process cheques sent in outward clearing.', 'finance',
     '["outward clearing", "outward cheque", "clearing outward"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('allot_safe_deposit_locker', 'Allot Safe Deposit Locker', 'Allot a safe deposit locker to the customer.', 'finance',
     '["allot locker", "assign locker", "locker allotment", "locker booking", "locker request", "safe deposit", "safe deposit box", "safe locker"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('surrender_locker', 'Surrender Locker', 'Process surrender of a safe deposit locker.', 'finance',
     '["locker surrender", "close locker", "vacate locker", "locker termination"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('charge_locker_rent', 'Charge Locker Rent', 'Debit annual rent for safe deposit locker.', 'finance',
     '["locker rent", "locker fee", "annual locker charge"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('drill_locker', 'Drill Locker', 'Break open locker due to non-payment or legal order.', 'finance',
     '["locker break open", "force open locker", "locker drilling"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_bancassurance_referral', 'Process Bancassurance Referral', 'Refer customer for insurance product through bancassurance.', 'finance',
     '["insurance referral", "bancassurance", "insurance cross-sell", "insurance lead"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('issue_bank_certificate', 'Issue Bank Certificate', 'Issue a bank certificate or balance confirmation letter.', 'finance',
     '["bank certificate", "balance certificate", "solvency certificate", "bank letter"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_tds_refund_claim', 'Process TDS Refund Claim', 'Process customer claim for TDS refund.', 'finance',
     '["tds refund", "tax refund", "tds claim", "excess tds refund"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('issue_no_due_certificate', 'Issue No Due Certificate', 'Issue no dues certificate confirming zero liability.', 'finance',
     '["no due certificate", "nil balance certificate", "zero dues confirmation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_succession_claim', 'Process Succession Claim', 'Process claim on a deceased customer account.', 'finance',
     '["succession claim", "death claim", "nominee claim", "estate settlement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_court_attachment', 'Process Court Attachment', 'Process a court-ordered attachment on customer account.', 'finance',
     '["court order", "attachment order", "garnishee order", "legal attachment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_income_tax_attachment', 'Process Income Tax Attachment', 'Process income tax department attachment order.', 'finance',
     '["it attachment", "tax attachment", "income tax order", "tax lien"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('onboard_merchant', 'Onboard Merchant', 'Onboard a new merchant for payment acceptance.', 'finance',
     '["merchant onboarding", "new merchant", "merchant registration", "acquire merchant"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_merchant_settlement', 'Process Merchant Settlement', 'Process daily settlement payout to merchant.', 'finance',
     '["merchant settlement", "merchant payout", "mdr settlement", "acquiring settlement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_merchant_statement', 'Generate Merchant Statement', 'Generate periodic statement for merchant transactions.', 'finance',
     '["merchant statement", "merchant report", "transaction summary"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_qr_payment', 'Process QR Payment', 'Process a QR code-based payment.', 'finance',
     '["qr payment", "scan and pay", "qr code transaction", "bharat qr"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('register_e_mandate', 'Register E-Mandate', 'Register electronic mandate for recurring payments.', 'finance',
     '["e-mandate", "electronic mandate", "auto pay registration", "recurring mandate"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_bbps_payment', 'Process BBPS Payment', 'Process bill payment through Bharat Bill Payment System.', 'finance',
     '["bbps payment", "bill payment", "utility payment", "bharat bill"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_virtual_account', 'Generate Virtual Account', 'Generate a virtual account number for collections.', 'finance',
     '["virtual account", "va generation", "collection account", "virtual id"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_aeps_transaction', 'Process AEPS Transaction', 'Process an Aadhaar Enabled Payment System transaction.', 'finance',
     '["aeps", "aadhaar payment", "aadhaar banking", "micro atm"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('enable_upi_autopay', 'Enable UPI AutoPay', 'Enable UPI recurring payment mandate.', 'finance',
     '["upi autopay", "upi mandate", "upi recurring", "upi si"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('mark_account_unclaimed', 'Mark Account Unclaimed', 'Mark an account as unclaimed after inactivity period.', 'finance',
     '["unclaimed deposit", "inoperative account", "unclaimed account"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('transfer_to_deaf', 'Transfer to DEAF', 'Transfer unclaimed deposits to Depositor Education Fund.', 'finance',
     '["deaf transfer", "depositor education fund", "unclaimed fund transfer"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_cibil_report', 'Generate CIBIL Report', 'Generate comprehensive CIBIL credit report for customer.', 'finance',
     '["bureau check cibil", "bureau report", "cibil check", "cibil enquiry", "cibil report", "cibil report generation", "cibil score fetch", "cibil verification", "credit bureau pull", "credit history check", "credit report", "credit score check", "run credit check"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('schedule_field_verification', 'Schedule Field Verification', 'Schedule in-person field verification at customer address.', 'finance',
     '["field verification", "physical verification", "address visit", "site verification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('capture_customer_photograph', 'Capture Customer Photograph', 'Capture and store customer photograph for records.', 'finance',
     '["photo capture", "customer photo", "image capture"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_gst_registration', 'Verify GST Registration', 'Verify customer GST registration number.', 'finance',
     '["gst verification", "gstin check", "gst number validation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_company_registration', 'Verify Company Registration', 'Verify company incorporation and registration details.', 'finance',
     '["company verification", "cin check", "mca verification", "incorporation check"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_beneficial_ownership', 'Verify Beneficial Ownership', 'Identify and verify ultimate beneficial owners of an entity.', 'finance',
     '["ubo verification", "beneficial owner", "ubo identification", "ownership structure"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('deactivate_customer', 'Deactivate Customer', 'Deactivate a customer profile in the system.', 'finance',
     '["customer deactivation", "disable customer", "inactive customer"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('merge_duplicate_customers', 'Merge Duplicate Customers', 'Merge duplicate customer records into a single profile.', 'finance',
     '["customer dedup", "merge customers", "duplicate resolution", "deduplication"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('update_fatca_declaration', 'Update FATCA Declaration', 'Update customer FATCA self-certification declaration.', 'finance',
     '["fatca update", "fatca self certification", "crs declaration"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('validate_tin', 'Validate TIN', 'Validate Tax Identification Number for cross-border reporting.', 'finance',
     '["tin validation", "tax id check", "foreign tin verification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_customer_consent', 'Generate Customer Consent', 'Generate and record customer consent for data processing.', 'finance',
     '["consent generation", "data consent", "privacy consent", "authorization form"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_minor_to_major_conversion', 'Process Minor to Major Conversion', 'Convert a minor account to major upon customer attaining majority.', 'finance',
     '["minor conversion", "age conversion", "minor to major", "majority conversion"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('remove_joint_holder', 'Remove Joint Holder', 'Remove a joint holder from an existing account.', 'finance',
     '["remove holder", "delete joint holder", "joint holder removal"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('score_application', 'Score Application', 'Run credit scoring model on loan application.', 'finance',
     '["application scoring", "credit score", "scorecard execution", "model scoring"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('create_collateral_charge', 'Create Collateral Charge', 'Create a charge or lien on collateral with CERSAI.', 'finance',
     '["charge creation", "cersai registration", "lien registration", "create lien"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('release_collateral_charge', 'Release Collateral Charge', 'Release the charge on collateral after loan closure.', 'finance',
     '["charge release", "lien removal", "cersai release", "release security"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_ltv_ratio', 'Calculate LTV Ratio', 'Calculate Loan-to-Value ratio for secured loans.', 'finance',
     '["ltv calculation", "loan to value", "ltv ratio", "collateral coverage"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_loan_transfer', 'Process Loan Transfer', 'Process transfer of loan from one lender to another.', 'finance',
     '["loan transfer", "balance transfer", "loan takeover", "bt processing"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('approve_top_up_loan', 'Approve Top Up Loan', 'Approve additional top-up loan on existing loan.', 'finance',
     '["top up approval", "additional loan", "top up sanction", "loan enhancement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_penal_interest', 'Calculate Penal Interest', 'Calculate penal interest for late or missed payments.', 'finance',
     '["interest on overdue", "late interest", "overdue charges", "overdue interest", "penal interest", "penalty interest calculation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('apply_subvention', 'Apply Subvention', 'Apply interest subvention or subsidy to a loan.', 'finance',
     '["subvention", "interest subsidy", "rate subvention", "government subsidy"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_interest_rate_reset', 'Process Interest Rate Reset', 'Process periodic interest rate reset for floating rate loans.', 'finance',
     '["rate reset", "floating rate revision", "interest reset", "mclr reset"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_subsidy_claim', 'Process Subsidy Claim', 'Process government subsidy claim on priority sector loans.', 'finance',
     '["subsidy claim", "government claim", "priority sector subsidy", "clss claim"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_priority_sector_report', 'Generate Priority Sector Report', 'Generate priority sector lending compliance report.', 'finance',
     '["psl report", "priority sector", "weaker section report", "psl compliance"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('classify_asset_quality', 'Classify Asset Quality', 'Classify loan asset as standard, sub-standard, doubtful, or loss.', 'finance',
     '["asset classification", "loan classification", "irac norms", "asset quality"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_technical_write_off', 'Process Technical Write Off', 'Process technical write-off while retaining recovery rights.', 'finance',
     '["technical write off", "book write off", "provisioned write off"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('initiate_lok_adalat', 'Initiate Lok Adalat', 'Refer NPA case to Lok Adalat for settlement.', 'finance',
     '["adalat case", "amicable settlement", "conciliation", "dispute resolution forum", "file lok adalat", "legal settlement", "lok adalat"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_mudra_loan', 'Process MUDRA Loan', 'Process loan under Pradhan Mantri MUDRA Yojana scheme.', 'finance',
     '["mudra loan", "pmmy", "shishu loan", "kishor loan", "tarun loan"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_pmay_subsidy', 'Process PMAY Subsidy', 'Process subsidy under Pradhan Mantri Awas Yojana.', 'finance',
     '["pmay subsidy", "housing subsidy", "clss", "awas yojana"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_cersai_registration', 'Verify CERSAI Registration', 'Verify security interest registration with CERSAI.', 'finance',
     '["cersai check", "security interest", "cersai verification", "charge search"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_loan_recall_notice', 'Generate Loan Recall Notice', 'Generate formal notice recalling the entire loan amount.', 'finance',
     '["recall notice", "loan recall", "acceleration notice", "demand for full payment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_rtgs_inward', 'Process RTGS Inward', 'Process incoming RTGS credit to customer account.', 'finance',
     '["rtgs inward", "incoming rtgs", "rtgs credit"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_neft_inward', 'Process NEFT Inward', 'Process incoming NEFT credit to customer account.', 'finance',
     '["neft inward", "incoming neft", "neft credit"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('return_inward_payment', 'Return Inward Payment', 'Return an inward payment due to invalid details.', 'finance',
     '["payment return", "reject inward", "return credit", "invalid beneficiary"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_positive_pay', 'Process Positive Pay', 'Verify cheque details against positive pay confirmation.', 'finance',
     '["positive pay", "cheque confirmation", "positive pay verification"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_penny_drop', 'Process Penny Drop', 'Execute penny drop verification to validate bank account.', 'finance',
     '["penny drop", "account verification", "name match", "bank validation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_utr_number', 'Generate UTR Number', 'Generate Unique Transaction Reference number.', 'finance',
     '["utr generation", "transaction reference", "unique reference"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_collect_request', 'Process Collect Request', 'Process a UPI collect payment request.', 'finance',
     '["collect request", "upi collect", "payment request", "pull payment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('register_upi_mandate', 'Register UPI Mandate', 'Register a UPI mandate for recurring payments.', 'finance',
     '["upi mandate registration", "upi si", "recurring upi"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_cash_deposit', 'Process Cash Deposit', 'Process cash deposit into customer account.', 'finance',
     '["cash deposit", "cash credit", "cash receipt", "counter deposit"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_cash_withdrawal', 'Process Cash Withdrawal', 'Process cash withdrawal from customer account.', 'finance',
     '["cash withdrawal", "cash debit", "counter withdrawal"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_challan', 'Generate Challan', 'Generate deposit challan or payment challan.', 'finance',
     '["challan generation", "deposit slip", "pay-in slip"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_govt_payment', 'Process Govt Payment', 'Process payment to government agencies.', 'finance',
     '["government payment", "tax payment", "challan payment", "gstn payment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_salary_upload', 'Process Salary Upload', 'Process bulk salary credit from employer account.', 'finance',
     '["salary upload", "payroll processing", "salary credit", "bulk salary"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_dividend_payment', 'Process Dividend Payment', 'Process dividend payment to shareholder accounts.', 'finance',
     '["dividend payment", "dividend credit", "dividend distribution"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_interest_payment', 'Process Interest Payment', 'Process periodic interest payout to deposit holders.', 'finance',
     '["interest payment", "interest payout", "coupon payment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('execute_money_market_deal', 'Execute Money Market Deal', 'Execute a money market deal for liquidity management.', 'finance',
     '["money market", "call money", "overnight deal", "repo deal"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_government_securities', 'Process Government Securities', 'Process purchase or sale of government securities.', 'finance',
     '["g-sec", "government bonds", "treasury bills", "gilt trading"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('manage_investment_portfolio', 'Manage Investment Portfolio', 'Manage the bank investment portfolio allocations.', 'finance',
     '["portfolio management", "investment management", "asset allocation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_mark_to_market', 'Calculate Mark to Market', 'Calculate mark-to-market valuation for trading book.', 'finance',
     '["mtm calculation", "mark to market", "fair value", "portfolio valuation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_repo_transaction', 'Process Repo Transaction', 'Process a repurchase agreement transaction.', 'finance',
     '["repo transaction", "repurchase agreement", "reverse repo", "laf"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_alm_gap', 'Calculate ALM Gap', 'Calculate Asset-Liability Management gap analysis.', 'finance',
     '["alm gap", "liquidity gap", "maturity mismatch", "asset liability"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_alm_report', 'Generate ALM Report', 'Generate Asset-Liability Management report for ALCO.', 'finance',
     '["alm report", "alco report", "liquidity report", "gap report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_interest_rate_swap', 'Process Interest Rate Swap', 'Process an interest rate swap derivative transaction.', 'finance',
     '["irs", "interest swap", "rate swap", "swap deal"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_currency_option', 'Process Currency Option', 'Process a currency option derivative contract.', 'finance',
     '["currency option", "fx option", "forex option", "option contract"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('settle_forex_deal', 'Settle Forex Deal', 'Settle a matured forex deal on value date.', 'finance',
     '["fx settlement", "forex settlement", "deal settlement", "value date settlement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_ecb_drawdown', 'Process ECB Drawdown', 'Process drawdown of External Commercial Borrowing.', 'finance',
     '["ecb drawdown", "external borrowing", "foreign loan drawdown"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('file_ecb_return', 'File ECB Return', 'File External Commercial Borrowing return with RBI.', 'finance',
     '["ecb return", "ecb reporting", "rbi ecb filing"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_hedge_effectiveness', 'Calculate Hedge Effectiveness', 'Calculate effectiveness of hedging instruments.', 'finance',
     '["hedge effectiveness", "hedge ratio", "hedging assessment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_gold_loan', 'Process Gold Loan', 'Process loan against gold ornaments as collateral.', 'finance',
     '["gold loan", "loan against gold", "gold pledge", "gold mortgage"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('appraise_gold', 'Appraise Gold', 'Appraise and value gold ornaments for loan purposes.', 'finance',
     '["gold appraisal", "gold valuation", "gold purity check", "gold assessment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_sar', 'Generate SAR', 'Generate Suspicious Activity Report for regulatory filing.', 'finance',
     '["sar generation", "suspicious activity", "sar report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('perform_name_screening', 'Perform Name Screening', 'Screen names against sanctions and watchlists.', 'finance',
     '["name screening", "watchlist check", "name check", "screening"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('perform_transaction_screening', 'Perform Transaction Screening', 'Screen individual transactions against sanctions rules.', 'finance',
     '["payment screening", "transaction filter", "sanction filter"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('escalate_compliance_issue', 'Escalate Compliance Issue', 'Escalate a compliance issue to the compliance officer.', 'finance',
     '["compliance escalation", "regulatory escalation", "cco escalation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_kyc_audit_trail', 'Generate KYC Audit Trail', 'Generate complete audit trail of KYC verification steps.', 'finance',
     '["kyc audit", "verification trail", "kyc history"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('perform_concurrent_audit', 'Perform Concurrent Audit', 'Execute concurrent audit checks on branch transactions.', 'finance',
     '["concurrent audit", "branch audit", "ongoing audit"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_rbi_return', 'Generate RBI Return', 'Generate periodic return submission to Reserve Bank of India.', 'finance',
     '["rbi return", "statutory return", "regulatory return", "section 42 return"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_rtc_reporting', 'Process RTC Reporting', 'Process Regulatory and Statutory Returns reporting.', 'finance',
     '["rtc report", "regulatory reporting", "statutory filing"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('perform_sox_compliance', 'Perform SOX Compliance', 'Perform Sarbanes-Oxley compliance checks.', 'finance',
     '["sox compliance", "sox audit", "internal control testing"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_disclosure_report', 'Generate Disclosure Report', 'Generate regulatory disclosure report for public filing.', 'finance',
     '["disclosure report", "pillar 3 disclosure", "public disclosure"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('validate_data_quality', 'Validate Data Quality', 'Run data quality validation checks on core data.', 'finance',
     '["data quality", "data validation", "data integrity check", "dq check"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_ifrs_report', 'Generate IFRS Report', 'Generate financial report as per IFRS/IndAS standards.', 'finance',
     '["ifrs report", "ind-as report", "accounting standards report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('compute_ecl', 'Compute ECL', 'Compute Expected Credit Loss as per IndAS 109.', 'finance',
     '["ecl computation", "expected credit loss", "ind-as 109", "impairment calculation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('perform_stress_testing', 'Perform Stress Testing', 'Execute stress testing scenarios on loan portfolio.', 'finance',
     '["stress test", "scenario analysis", "portfolio stress test", "rbi stress test"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_liquidity_report', 'Generate Liquidity Report', 'Generate Liquidity Coverage Ratio compliance report.', 'finance',
     '["lcr report", "liquidity coverage", "nsfr report", "liquidity compliance"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('perform_fraud_rule_update', 'Perform Fraud Rule Update', 'Update fraud detection rules in the monitoring system.', 'finance',
     '["rule update", "fraud rule change", "monitoring rule update"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_crar_report', 'Generate CRAR Report', 'Generate Capital to Risk-weighted Assets Ratio report.', 'finance',
     '["crar report", "capital adequacy", "car report", "tier 1 capital"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_whistle_blower_report', 'Process Whistle Blower Report', 'Process and route a whistle-blower complaint.', 'finance',
     '["whistle blower", "anonymous complaint", "ethics report", "vigilance complaint"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_large_exposure_report', 'Generate Large Exposure Report', 'Generate report on large exposures and group borrower limits.', 'finance',
     '["large exposure", "single borrower limit", "group exposure", "concentration risk"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('open_nre_account', 'Open NRE Account', 'Open Non-Resident External rupee account.', 'finance',
     '["nre account", "nri account nre", "non resident external"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('open_nro_account', 'Open NRO Account', 'Open Non-Resident Ordinary rupee account.', 'finance',
     '["nro account", "nri account nro", "non resident ordinary"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('open_fcnr_deposit', 'Open FCNR Deposit', 'Open Foreign Currency Non-Resident deposit.', 'finance',
     '["fcnr deposit", "foreign currency deposit", "fcnr-b"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_nri_repatriation', 'Process NRI Repatriation', 'Process repatriation of funds from NRO to overseas account.', 'finance',
     '["repatriation", "fund repatriation", "nro transfer abroad"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_jan_dhan_account', 'Process Jan Dhan Account', 'Open account under Pradhan Mantri Jan Dhan Yojana.', 'finance',
     '["jan dhan", "pmjdy", "zero balance account", "financial inclusion"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_atal_pension', 'Process Atal Pension', 'Process enrollment or contribution under Atal Pension Yojana.', 'finance',
     '["atal pension", "apy", "pension enrollment"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_sukanya_samriddhi', 'Process Sukanya Samriddhi', 'Process Sukanya Samriddhi Yojana account operations.', 'finance',
     '["sukanya samriddhi", "ssa", "girl child scheme"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_kisan_credit_card', 'Process Kisan Credit Card', 'Process Kisan Credit Card loan application or renewal.', 'finance',
     '["kcc", "kisan credit card", "agriculture credit", "farm loan"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_education_loan', 'Process Education Loan', 'Process education loan application.', 'finance',
     '["education loan", "student loan", "study loan", "vidya lakshmi"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_msme_loan', 'Process MSME Loan', 'Process loan for Micro, Small, and Medium Enterprises.', 'finance',
     '["msme loan", "sme loan", "business loan", "udyam loan"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('register_udyam', 'Register Udyam', 'Register enterprise under Udyam registration.', 'finance',
     '["udyam registration", "msme registration", "udyam certificate"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_crop_insurance', 'Process Crop Insurance', 'Process crop insurance under PMFBY scheme.', 'finance',
     '["crop insurance", "pmfby", "fasal bima", "agriculture insurance"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_pension_payment', 'Process Pension Payment', 'Process monthly pension payment to beneficiary.', 'finance',
     '["pension payment", "pension credit", "pension disbursement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_dbt_credit', 'Process DBT Credit', 'Process Direct Benefit Transfer credit to beneficiary.', 'finance',
     '["dbt", "direct benefit transfer", "subsidy credit", "government benefit"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_atm_withdrawal', 'Process ATM Withdrawal', 'Process cash withdrawal from ATM.', 'finance',
     '["atm withdrawal", "atm cash", "cash dispense", "atm transaction"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_atm_deposit', 'Process ATM Deposit', 'Process cash or cheque deposit at ATM.', 'finance',
     '["atm deposit", "cdm deposit", "cash deposit machine"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('reverse_atm_failed_transaction', 'Reverse ATM Failed Transaction', 'Reverse a failed ATM transaction where cash was not dispensed.', 'finance',
     '["atm reversal", "atm failed", "cash not dispensed", "atm complaint"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_atm_report', 'Generate ATM Report', 'Generate ATM operations and uptime report.', 'finance',
     '["atm report", "atm uptime", "atm availability report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('replenish_atm_cash', 'Replenish ATM Cash', 'Schedule and process ATM cash replenishment.', 'finance',
     '["atm replenishment", "cash loading", "atm refill"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_passbook_printing', 'Process Passbook Printing', 'Print transaction entries in customer passbook.', 'finance',
     '["passbook printing", "passbook update", "print passbook"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('open_staff_account', 'Open Staff Account', 'Open a salary account for bank staff.', 'finance',
     '["staff account", "employee account", "salary account staff"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('perform_cash_verification', 'Perform Cash Verification', 'Perform cash verification and tally at branch.', 'finance',
     '["cash verification", "vault verification", "cash tally", "cash audit"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_day_book', 'Generate Day Book', 'Generate branch day book with all transactions.', 'finance',
     '["day book", "daily ledger", "branch journal", "daily report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_token_issuance', 'Process Token Issuance', 'Issue token to customer at branch for queue management.', 'finance',
     '["token issue", "queue token", "branch token", "waiting token"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_will_registration', 'Process Will Registration', 'Register customer will in safe custody.', 'finance',
     '["will registration", "safe custody will", "testament registration"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('issue_demand_draft_cancellation', 'Issue Demand Draft Cancellation', 'Cancel a previously issued demand draft.', 'finance',
     '["dd cancellation", "cancel demand draft", "dd refund"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_tds_exemption', 'Process TDS Exemption', 'Process TDS exemption based on Form 15G/15H submission.', 'finance',
     '["tds exemption", "form 15g", "form 15h", "tds waiver"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_balance_certificate', 'Generate Balance Certificate', 'Generate account balance confirmation certificate.', 'finance',
     '["balance certificate", "account confirmation", "bank balance letter"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_e_nach_mandate', 'Generate E-NACH Mandate', 'Generate electronic NACH mandate for auto-debit.', 'finance',
     '["e-nach", "electronic nach", "nach generation", "auto debit mandate"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('cancel_nach_mandate', 'Cancel NACH Mandate', 'Cancel an active NACH auto-debit mandate.', 'finance',
     '["nach cancellation", "stop auto debit", "mandate cancellation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_nach_return', 'Process NACH Return', 'Process a NACH debit that was returned by customer bank.', 'finance',
     '["nach return", "mandate bounce", "debit return", "ecs return"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('activate_account_aggregator', 'Activate Account Aggregator', 'Enable account aggregator consent for financial data sharing.', 'finance',
     '["account aggregator", "aa consent", "financial data sharing", "aa activation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('fetch_aa_data', 'Fetch AA Data', 'Fetch financial data via Account Aggregator framework.', 'finance',
     '["aa data fetch", "account aggregator pull", "financial information pull"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_digital_lending', 'Process Digital Lending', 'Process end-to-end digital lending journey.', 'finance',
     '["digital loan", "online lending", "instant loan", "app loan"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_esign', 'Verify E-Sign', 'Verify Aadhaar-based electronic signature on document.', 'finance',
     '["esign verification", "aadhaar esign", "digital signature", "e-sign check"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_loan_kyc_report', 'Generate Loan KYC Report', 'Generate consolidated KYC report for loan file.', 'finance',
     '["loan kyc report", "credit kyc", "underwriting kyc report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_co_lending', 'Process Co-Lending', 'Process loan under co-lending model with partner.', 'finance',
     '["co-lending", "co-origination", "partnership lending", "clm"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('assign_collection_bucket', 'Assign Collection Bucket', 'Assign delinquent account to appropriate collection bucket.', 'finance',
     '["bucket assignment", "dpd bucket", "collection category", "delinquency bucket"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_collection_letter', 'Generate Collection Letter', 'Generate automated collection communication letter.', 'finance',
     '["collection letter", "recovery letter", "collection notice"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_settlement_offer', 'Process Settlement Offer', 'Process and evaluate a settlement offer from defaulter.', 'finance',
     '["settlement processing", "ots processing", "compromise evaluation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('track_field_visit', 'Track Field Visit', 'Track and record field collection agent visit.', 'finance',
     '["field visit tracking", "agent visit", "collection visit", "geo tagging"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_broken_period_interest', 'Process Broken Period Interest', 'Calculate interest for broken period in deposits.', 'finance',
     '["broken period", "partial period interest", "odd days interest"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_sweep_instruction', 'Process Sweep Instruction', 'Process auto-sweep from savings to fixed deposit.', 'finance',
     '["sweep instruction", "auto sweep", "sweep in", "sweep out"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_flexi_deposit', 'Process Flexi Deposit', 'Process flexi fixed deposit linked to savings account.', 'finance',
     '["flexi deposit", "linked fd", "auto fd", "multi-option deposit"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_penalty_on_premature_withdrawal', 'Calculate Penalty on Premature Withdrawal', 'Calculate penalty for premature withdrawal of deposit.', 'finance',
     '["premature penalty", "early withdrawal penalty", "break penalty"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_tax_saving_fd', 'Process Tax Saving FD', 'Process fixed deposit under Section 80C tax saving.', 'finance',
     '["tax saver fd", "80c fd", "tax saving deposit", "five year fd"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_form_26as_data', 'Generate Form 26AS Data', 'Generate TDS data for customer Form 26AS.', 'finance',
     '["form 26as", "tds statement", "annual tax statement", "tax credit statement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_senior_citizen_fd', 'Process Senior Citizen FD', 'Process fixed deposit with senior citizen preferential rates.', 'finance',
     '["senior citizen fd", "senior fd", "higher rate fd"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('initiate_account_portability', 'Initiate Account Portability', 'Initiate request for account number portability across branches.', 'finance',
     '["account portability", "branch portability", "cbs portability"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_will_execution', 'Process Will Execution', 'Process will execution and distribute assets to nominees.', 'finance',
     '["will execution", "estate distribution", "probate processing"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('compute_internal_rating', 'Compute Internal Rating', 'Compute internal credit rating for borrower.', 'finance',
     '["internal rating", "credit rating", "borrower rating", "obligor rating"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_guarantee_commission', 'Process Guarantee Commission', 'Calculate and charge commission for bank guarantee.', 'finance',
     '["bg commission", "guarantee fee", "guarantee charges"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_lc_commission', 'Process LC Commission', 'Calculate and charge commission for letter of credit.', 'finance',
     '["lc commission", "lc charges", "documentary credit fee"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_swift_message', 'Generate SWIFT Message', 'Generate SWIFT message for international banking communication.', 'finance',
     '["swift message", "mt message", "swift format", "fin message"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_nostro_reconciliation', 'Process Nostro Reconciliation', 'Reconcile nostro account with correspondent bank.', 'finance',
     '["nostro recon", "correspondent reconciliation", "nostro matching"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('issue_travel_card', 'Issue Travel Card', 'Issue prepaid forex travel card to customer.', 'finance',
     '["forex card", "travel card", "prepaid forex", "multicurrency card"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('reload_travel_card', 'Reload Travel Card', 'Reload foreign currency on prepaid travel card.', 'finance',
     '["card reload", "forex card top up", "travel card reload"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_tc_issuance', 'Process TC Issuance', 'Issue travellers cheques to customer.', 'finance',
     '["travellers cheque", "tc issuance", "travel cheque"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_encashment', 'Process Encashment', 'Process encashment of foreign currency or instruments.', 'finance',
     '["forex encashment", "currency exchange", "money exchange", "encashment certificate"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_encashment_certificate', 'Generate Encashment Certificate', 'Generate foreign currency encashment certificate.', 'finance',
     '["encashment certificate", "forex certificate", "exchange certificate"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('block_upi_id', 'Block UPI ID', 'Block a UPI virtual payment address.', 'finance',
     '["upi block", "block vpa", "deactivate upi", "disable upi id"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_upi_dispute', 'Process UPI Dispute', 'Process a dispute raised on a UPI transaction.', 'finance',
     '["upi dispute", "upi complaint", "upi chargeback"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_merchant_mdr_report', 'Generate Merchant MDR Report', 'Generate Merchant Discount Rate billing report.', 'finance',
     '["mdr report", "merchant charges", "acquiring charges report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_pos_chargeback', 'Process POS Chargeback', 'Process a chargeback on a POS transaction.', 'finance',
     '["pos chargeback", "pos dispute", "terminal chargeback"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('deactivate_upi_mandate', 'Deactivate UPI Mandate', 'Deactivate an active UPI recurring mandate.', 'finance',
     '["upi mandate cancel", "revoke upi mandate", "stop upi autopay"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('verify_upi_registration', 'Verify UPI Registration', 'Verify customer UPI registration status.', 'finance',
     '["upi status", "upi verification", "check upi registration"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_prepaid_card_load', 'Process Prepaid Card Load', 'Load value onto a prepaid card.', 'finance',
     '["prepaid load", "card top up", "prepaid credit", "wallet load"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_tds_return', 'Generate TDS Return', 'Generate quarterly TDS return for filing.', 'finance',
     '["tds return", "26q filing", "quarterly tds", "tds statement filing"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_advance_tax', 'Process Advance Tax', 'Process advance tax payment for the bank.', 'finance',
     '["advance tax", "tax payment", "quarterly tax", "advance tax challan"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('compute_depreciation', 'Compute Depreciation', 'Compute depreciation on bank fixed assets.', 'finance',
     '["depreciation", "asset depreciation", "fixed asset depreciation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_vendor_payment', 'Process Vendor Payment', 'Process payment to bank vendors and service providers.', 'finance',
     '["vendor payment", "supplier payment", "accounts payable"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_profit_loss_report', 'Generate Profit Loss Report', 'Generate profit and loss statement.', 'finance',
     '["p&l report", "income statement", "profit loss", "earnings report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_balance_sheet', 'Generate Balance Sheet', 'Generate bank balance sheet report.', 'finance',
     '["balance sheet", "financial position", "assets liabilities"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_priority_sector_certificate', 'Process Priority Sector Certificate', 'Generate priority sector lending certificate for trading.', 'finance',
     '["pslc", "priority sector certificate", "psl certificate trading"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_ibpc_transaction', 'Process IBPC Transaction', 'Process Inter-Bank Participation Certificate transaction.', 'finance',
     '["ibpc", "participation certificate", "inter bank participation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('compute_nii', 'Compute NII', 'Compute Net Interest Income for the period.', 'finance',
     '["nii computation", "net interest income", "interest margin", "nim calculation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('compute_cost_of_funds', 'Compute Cost of Funds', 'Compute weighted average cost of funds.', 'finance',
     '["cost of funds", "funding cost", "weighted cost", "deposit cost"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_cd_issuance', 'Process CD Issuance', 'Issue Certificate of Deposit for wholesale funding.', 'finance',
     '["certificate of deposit", "cd issuance", "wholesale deposit", "cd placement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_cp_investment', 'Process CP Investment', 'Invest in Commercial Paper issued by corporate.', 'finance',
     '["commercial paper", "cp investment", "cp purchase", "money market paper"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_mclr', 'Calculate MCLR', 'Calculate Marginal Cost of Funds based Lending Rate.', 'finance',
     '["mclr calculation", "marginal cost", "lending rate", "mclr reset"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('calculate_eblr', 'Calculate EBLR', 'Calculate External Benchmark Linked Lending Rate.', 'finance',
     '["eblr", "external benchmark", "repo linked rate", "rllr"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_consortium_lending', 'Process Consortium Lending', 'Process loan participation in consortium arrangement.', 'finance',
     '["consortium loan", "syndication", "multiple banking", "consortium participation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_lead_bank_report', 'Process Lead Bank Report', 'Prepare lead bank district credit plan report.', 'finance',
     '["lead bank", "district credit plan", "dlrc report", "slbc report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_kyc_deficiency_notice', 'Generate KYC Deficiency Notice', 'Generate notice for KYC documentation deficiencies.', 'finance',
     '["kyc deficiency", "kyc pending notice", "document deficiency"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_mobile_number_update', 'Process Mobile Number Update', 'Update registered mobile number for customer account.', 'finance',
     '["mobile update", "phone number change", "contact update", "mobile registration"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_email_update', 'Process Email Update', 'Update registered email address for customer.', 'finance',
     '["email update", "email change", "email id update"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_duplicate_statement', 'Generate Duplicate Statement', 'Generate duplicate copy of account statement.', 'finance',
     '["duplicate statement", "statement copy", "reprint statement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('activate_sms_alerts', 'Activate SMS Alerts', 'Activate transaction SMS alerts for the account.', 'finance',
     '["sms alert activation", "transaction alert", "sms banking"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('deactivate_sms_alerts', 'Deactivate SMS Alerts', 'Deactivate transaction SMS alerts.', 'finance',
     '["sms deactivation", "stop sms alerts", "disable notifications"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_address_change', 'Process Address Change', 'Process customer communication address change.', 'finance',
     '["address change", "address update", "correspondence change"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_name_change', 'Process Name Change', 'Process legal name change on customer account.', 'finance',
     '["name change", "name correction", "name update"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_audit_certificate', 'Generate Audit Certificate', 'Generate certificate for statutory audit compliance.', 'finance',
     '["audit certificate", "statutory certificate", "compliance certificate"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_itr_acknowledgement', 'Generate ITR Acknowledgement', 'Generate income tax return filing acknowledgement.', 'finance',
     '["itr ack", "tax filing", "income tax acknowledgement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_overdraft_review', 'Process Overdraft Review', 'Conduct annual review of overdraft facility.', 'finance',
     '["od review", "overdraft renewal", "facility review", "cc review"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_working_capital_assessment', 'Process Working Capital Assessment', 'Assess working capital requirement of business customer.', 'finance',
     '["working capital", "wc assessment", "fund based limit", "turnover method"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_limit_renewal', 'Process Limit Renewal', 'Renew credit limit for working capital or overdraft facility.', 'finance',
     '["limit renewal", "facility renewal", "credit limit renewal", "annual renewal"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_sanction_advice', 'Generate Sanction Advice', 'Generate internal sanction advice note for credit facility.', 'finance',
     '["sanction advice", "credit advice", "approval note"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('compute_drawing_power', 'Compute Drawing Power', 'Compute drawing power for cash credit or overdraft account.', 'finance',
     '["drawing power", "dp calculation", "eligible limit", "stock statement dp"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_adhoc_limit', 'Process Adhoc Limit', 'Grant temporary adhoc limit enhancement.', 'finance',
     '["adhoc limit", "temporary limit", "excess facility", "temporary enhancement"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_exposure_report', 'Generate Exposure Report', 'Generate borrower-wise exposure report.', 'finance',
     '["exposure report", "credit exposure", "borrower exposure", "limit utilization"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_credit_insurance', 'Process Credit Insurance', 'Process credit insurance for trade receivables.', 'finance',
     '["credit insurance", "trade credit insurance", "receivable insurance"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_credit_rating_migration', 'Generate Credit Rating Migration', 'Track and report credit rating migration of borrowers.', 'finance',
     '["rating migration", "credit migration", "rating transition", "downgrade report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_bill_collection', 'Process Bill Collection', 'Process domestic bill sent for collection.', 'finance',
     '["bill collection", "outstation cheque", "bill for collection"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('compute_interest_on_interest', 'Compute Interest on Interest', 'Compute compound interest or interest on interest.', 'finance',
     '["compound interest", "interest on interest", "ioi calculation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_escrow_account', 'Process Escrow Account', 'Open and manage escrow account for transaction security.', 'finance',
     '["escrow account", "escrow management", "trust account"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_provisional_statement', 'Generate Provisional Statement', 'Generate provisional financial statement for interim reporting.', 'finance',
     '["provisional financials", "interim statement", "quarterly results"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('process_project_finance_drawdown', 'Process Project Finance Drawdown', 'Process milestone-based drawdown for project finance loan.', 'finance',
     '["project drawdown", "milestone disbursement", "project finance release"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_cma_report', 'Generate CMA Report', 'Generate Credit Monitoring Arrangement data report.', 'finance',
     '["cma report", "cma data", "credit monitoring", "financial projection"]'::jsonb, NULL::jsonb, NULL::jsonb,
     NULL::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('capture_biometric', 'Capture Biometric', 'Capture the customer fingerprint or iris scan for biometric authentication during KYC or transaction authorization.', 'kyc',
     '["biometric capture", "fingerprint capture", "iris scan", "biometric enrollment", "capture fingerprint", "biometric registration"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/biometric/capture"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('check_pep_status', 'Check PEP Status', 'Screen the customer against the politically exposed persons database as part of enhanced due diligence.', 'compliance',
     '["enhanced due diligence pep", "pep check", "pep screening", "pep verification", "politically exposed person", "politically exposed person screening"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/compliance/pep/check"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('request_missing_documents', 'Request Missing Documents', 'Request additional or missing documents from the applicant to complete the KYC or loan application file.', 'kyc',
     '["missing documents request", "request additional documents", "ask for pending documents", "document deficiency notice", "request pending papers", "chase missing documents"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/documents/request-missing"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('resolve_ticket', 'Resolve Ticket', 'Mark a customer service ticket as resolved after the issue has been addressed.', 'support',
     '["ticket resolution", "close ticket", "resolve complaint", "complaint resolved", "case closed"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/support/tickets/resolve"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('escalate_to_specialist', 'Escalate To Specialist', 'Escalate a case to a specialist for expert review and decision.', 'health',
     '["specialist escalation", "expert referral", "escalate to expert"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/care/specialist/escalate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('add_beneficiary', 'Add Beneficiary', 'Add a new beneficiary account to the customer profile for future fund transfers.', 'payments',
     '["beneficiary addition", "add payee", "register beneficiary", "add transfer beneficiary", "new beneficiary", "beneficiary registration"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/payments/beneficiary/add"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_education_details', 'Collect Education Details', 'Collect the applicant education qualifications, institutions attended, degrees obtained, and year of completion for profiling.', 'kyc',
     '["education details", "qualifications", "educational background", "academic details", "degrees", "institution details"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/kyc/education/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_document_requirements', 'Collect Document Requirements', 'Collect and track the required documents based on customer profile, product type, and regulatory requirements.', 'kyc',
     '["document requirements", "required documents", "checklist", "document list", "collect requirements", "document tracking"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/documents/requirements/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('collect_witness_details', 'Collect Witness Details', 'Collect the details of witnesses required for legal document execution and verification purposes.', 'home_loan',
     '["witness details", "collect witness", "legal witness", "witness information", "verification witness"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/home-loan/witness/collect"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('schedule_field_visit', 'Schedule Field Visit', 'Schedule a field visit by the collection agent to the borrowers address for physical follow-up and recovery.', 'collections',
     '["field visit", "site visit", "home visit", "borrower visit", "collection visit", "field follow-up"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/field-visit/schedule"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('record_field_visit', 'Record Field Visit', 'Record the findings, outcome, and remarks from a field visit conducted by the collection agent.', 'collections',
     '["collection outcome", "collection report", "collection visit", "field remarks", "field report", "field visit", "field visit record", "visit findings", "visit log", "visit outcome", "visit record"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/field-visit/record"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('negotiate_payment_plan', 'Negotiate Payment Plan', 'Negotiate a revised payment plan or restructuring arrangement with the defaulting borrower.', 'collections',
     '["payment plan", "negotiate plan", "restructure plan", "repayment plan", "revised schedule", "payment negotiation"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/collections/payment-plan/negotiate"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('cancel_scheduled_job', 'Cancel Scheduled Job', 'Cancel and delete an existing scheduled job or campaign permanently.', 'scheduler',
     '["cancel job", "cancel campaign", "delete schedule", "stop job", "remove schedule", "cancel scheduler"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "DELETE", "endpoint": "/scheduler/job/cancel"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('log_daily_activity', 'Log Daily Activity', 'Log the daily activity summary for a scheduler or campaign including messages sent, calls made, and outcomes.', 'scheduler',
     '["daily log", "activity log", "campaign log", "scheduler log", "daily summary", "activity summary"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"method": "POST", "endpoint": "/scheduler/log/daily"}, "execution_type": "http"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

INSERT INTO action_definitions
    (name, display_name, description, workflow_type,
     aliases, input_schema, output_schema, execution_template, active)
VALUES
    ('generate_campaign_report', 'Generate Campaign Report', 'Generate a detailed report on campaign performance including reach, response rate, and conversion metrics.', 'scheduler',
     '["campaign report", "campaign analytics", "campaign performance", "reach report", "response report", "conversion report"]'::jsonb, NULL::jsonb, NULL::jsonb,
     '{"configuration": {"handler": "generate_campaign_report"}, "execution_type": "python"}'::jsonb, TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name       = EXCLUDED.display_name,
    description        = EXCLUDED.description,
    workflow_type      = EXCLUDED.workflow_type,
    aliases            = EXCLUDED.aliases,
    input_schema       = EXCLUDED.input_schema,
    output_schema      = EXCLUDED.output_schema,
    execution_template = EXCLUDED.execution_template,
    active             = EXCLUDED.active,
    updated_at         = now();

COMMIT;

-- Total rows upserted: 703