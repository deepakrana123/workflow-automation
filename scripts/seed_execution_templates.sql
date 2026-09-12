-- scripts/seed_execution_templates.sql
--
-- Sets a FULL execution_template on every action_definitions row.
--
-- Split:
--   PYTHON (~44) — pure in-process: calculations, document generation.
--                  No external call. No WorkspaceIntegration needed.
--
--   HTTP  (~686) — all business operations that call an external service.
--                  base_url is seeded to http://localhost:8000/api so every
--                  action routes to the built-in mock server by default.
--                  The /api/mock/{action_name} route returns schema-accurate
--                  responses — no real service needed during dev/demo.
--
--                  To point at a real service: update base_url directly on
--                  the action_definitions row, or set a workspace-local
--                  execution_template on the WorkflowActionMapping snapshot
--                  via the unmapped-action resolution flow.
--
-- Safe to re-run: WHERE execution_template IS NULL (add --force to overwrite).

-- ── STEP 1: PYTHON actions ────────────────────────────────────────────────────

UPDATE action_definitions
SET execution_template = jsonb_build_object(
    'execution_type', 'python',
    'configuration', jsonb_build_object(
        'handler',     name,
        'description', 'Pure Python in-process handler. No external call.'
    )
)
WHERE name IN (
    'calculate_emi',
    'calculate_risk_score',
    'calculate_tax',
    'calculate_credit_score',
    'calculate_ltv_ratio',
    'calculate_interest',
    'calculate_interest_rate',
    'calculate_eligibility',
    'calculate_loan_eligibility',
    'calculate_foreclosure_amount',
    'calculate_prepayment_charges',
    'calculate_penal_interest',
    'calculate_rd_maturity',
    'calculate_fd_interest',
    'calculate_alm_gap',
    'calculate_eblr',
    'calculate_mclr',
    'calculate_debt_service_ratio',
    'calculate_group_utilization',
    'calculate_hedge_effectiveness',
    'calculate_mark_to_market',
    'calculate_account_balance',
    'calculate_forex_margin',
    'calculate_penalty_on_premature_withdrawal',
    'calculate_provision_coverage',
    'recalculate_emi',
    'compute_ecl',
    'compute_gst',
    'compute_provisioning',
    'compute_depreciation',
    'compute_drawing_power',
    'compute_cost_of_funds',
    'compute_interest_on_interest',
    'compute_internal_rating',
    'compute_nii',
    'compute_recovery_progress',
    'generate_pdf',
    'generate_csv',
    'generate_excel',
    'generate_repayment_schedule',
    'generate_loan_agreement',
    'generate_interest_certificate'
)
AND execution_template IS NULL;

-- ── STEP 2: HTTP actions (all remaining) ─────────────────────────────────────
-- base_url is seeded to the local mock server so every HTTP action has a
-- working target out of the box for dev/demo.
-- The /api/mock/{action_name} route returns schema-accurate synthetic
-- responses — no real external service needed during development.
--
-- For production: update the action's execution_template.configuration.base_url
-- directly (via the unmapped-actionesolution UI or a targeted UPDATE), or
-- set a workspace-local execution_template on the WorkflowActionMapping row
-- that overrides this default with the real service URL.

UPDATE action_definitions
SET execution_template = jsonb_build_object(
    'execution_type', 'http',
    'configuration', jsonb_build_object(
        'base_url',  'http://localhost:8000/api',
        'method',    'POST',
        'endpoint',  '/mock/' || name,
        'timeout',   30,
        'headers',   jsonb_build_object(
            'Content-Type', 'application/json',
            'X-Action',     name
        ),
        'body_template', jsonb_build_object(
            'entity_id',   '{{entity_id}}',
            'action',      name,
            'workflow_id', '{{workflow_id}}'
        ),
        'response_mapping', jsonb_build_object(
            'status',    '$.status',
            'reference', '$.reference_id',
            'message',   '$.message'
        )
    )
)
WHERE execution_template.execution_type = 'http';

-- ── Verify ────────────────────────────────────────────────────────────────────

SELECT
    execution_template->>'execution_type' AS exec_type,
    COUNT(*)                               AS total
FROM action_definitions
GROUP BY exec_type
ORDER BY exec_type;
