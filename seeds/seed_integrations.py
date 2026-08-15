"""
Seed script: Workspace Integrations + Action Configurations
============================================================
Seeds realistic workspace integrations using free/dummy APIs,
then creates ActionConfiguration records for both Python executors
and HTTP executors referencing those integrations.

Usage:
    python -m seeds.seed_integrations

Design:
    - WorkspaceIntegrations use dummy APIs (DummyJSON, ReqRes, HTTPBin, etc.)
    - When going live, only WorkspaceIntegration records change (base_url, auth).
    - ActionConfiguration never hardcodes URLs — HTTP actions reference an integration.
    - Python actions execute entirely inside MFlows with handler references.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.workspace import Workspace
from app.models.workspace_integration import WorkspaceIntegration
from app.models.action_definitions import ActionDefinition
from app.models.action_configurations_model import ActionConfiguration
from app.models.workflow_knowledge import WorkflowKnowledge


# ═══════════════════════════════════════════════════════════════════════════════
# WORKSPACE
# ═══════════════════════════════════════════════════════════════════════════════

WORKSPACE = {
    "name": "mflows_bank",
    "display_name": "MFlows Bank",
    "description": "Primary banking workspace for development and testing",
    "organization_name": "MFlows Financial Services",
    "active": True,
}


# ═══════════════════════════════════════════════════════════════════════════════
# WORKSPACE INTEGRATIONS (Dummy APIs simulating real banking services)
# ═══════════════════════════════════════════════════════════════════════════════

INTEGRATIONS = [
    {
        "name": "CBS Customer API",
        "provider": "dummyjson",
        "integration_type": "http",
        "base_url": "https://dummyjson.com",
        "authentication": {
            "type": "bearer_token",
            "token_endpoint": "/auth/login",
            "refresh_enabled": True,
        },
        "credentials": {
            "username": "{{CBS_USERNAME}}",
            "password": "{{CBS_PASSWORD}}",
        },
    },
    {
        "name": "Loan Eligibility API",
        "provider": "reqres",
        "integration_type": "http",
        "base_url": "https://reqres.in/api",
        "authentication": {
            "type": "api_key",
            "header_name": "X-Api-Key",
        },
        "credentials": {
            "api_key": "{{LOAN_API_KEY}}",
        },
    },
    {
        "name": "KYC Verification API",
        "provider": "httpbin",
        "integration_type": "http",
        "base_url": "https://httpbin.org",
        "authentication": {
            "type": "basic_auth",
        },
        "credentials": {
            "username": "{{KYC_USERNAME}}",
            "password": "{{KYC_PASSWORD}}",
        },
    },
    {
        "name": "Notification Gateway",
        "provider": "postman_echo",
        "integration_type": "http",
        "base_url": "https://postman-echo.com",
        "authentication": {
            "type": "none",
        },
        "credentials": {},
    },
    {
        "name": "Document Validation API",
        "provider": "mockapi",
        "integration_type": "http",
        "base_url": "https://jsonplaceholder.typicode.com",
        "authentication": {
            "type": "bearer_token",
            "token_endpoint": None,
            "static_token": True,
        },
        "credentials": {
            "token": "{{DOC_SERVICE_TOKEN}}",
        },
    },
    {
        "name": "Payment Processing API",
        "provider": "dummyjson",
        "integration_type": "http",
        "base_url": "https://dummyjson.com",
        "authentication": {
            "type": "bearer_token",
            "token_endpoint": "/auth/login",
            "refresh_enabled": True,
        },
        "credentials": {
            "username": "{{PAYMENT_USERNAME}}",
            "password": "{{PAYMENT_PASSWORD}}",
        },
    },
    {
        "name": "Fraud Detection API",
        "provider": "reqres",
        "integration_type": "http",
        "base_url": "https://reqres.in/api",
        "authentication": {
            "type": "api_key",
            "header_name": "X-Api-Key",
        },
        "credentials": {
            "api_key": "{{FRAUD_API_KEY}}",
        },
    },
    {
        "name": "Account Service API",
        "provider": "dummyjson",
        "integration_type": "http",
        "base_url": "https://dummyjson.com",
        "authentication": {
            "type": "bearer_token",
            "token_endpoint": "/auth/login",
            "refresh_enabled": True,
        },
        "credentials": {
            "username": "{{ACCOUNT_USERNAME}}",
            "password": "{{ACCOUNT_PASSWORD}}",
        },
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# PYTHON EXECUTOR ACTION CONFIGURATIONS
# (Internal handlers — no external API call)
# ═══════════════════════════════════════════════════════════════════════════════

PYTHON_ACTIONS = [
    {
        "action_name": "generate_pdf",
        "execution_type": "python",
        "configuration": {
            "handler": "generate_pdf",
            "timeout": 30,
            "retry": 2,
        },
    },
    {
        "action_name": "generate_excel",
        "execution_type": "python",
        "configuration": {
            "handler": "generate_excel",
            "timeout": 30,
            "retry": 2,
        },
    },
    {
        "action_name": "generate_csv",
        "execution_type": "python",
        "configuration": {
            "handler": "generate_csv",
            "timeout": 15,
            "retry": 1,
        },
    },
    {
        "action_name": "ocr_extract",
        "execution_type": "python",
        "configuration": {
            "handler": "ocr_extract",
            "timeout": 60,
            "retry": 2,
        },
    },
    {
        "action_name": "extract_text",
        "execution_type": "python",
        "configuration": {
            "handler": "extract_text",
            "timeout": 30,
            "retry": 1,
        },
    },
    {
        "action_name": "calculate_emi",
        "execution_type": "python",
        "configuration": {
            "handler": "calculate_emi",
            "timeout": 5,
            "retry": 0,
        },
    },
    {
        "action_name": "calculate_interest",
        "execution_type": "python",
        "configuration": {
            "handler": "calculate_interest",
            "timeout": 5,
            "retry": 0,
        },
    },
    {
        "action_name": "generate_loan_schedule",
        "execution_type": "python",
        "configuration": {
            "handler": "generate_loan_schedule",
            "timeout": 15,
            "retry": 1,
        },
    },
    {
        "action_name": "generate_statement",
        "execution_type": "python",
        "configuration": {
            "handler": "generate_statement",
            "timeout": 30,
            "retry": 2,
        },
    },
    {
        "action_name": "validate_pan",
        "execution_type": "python",
        "configuration": {
            "handler": "validate_pan",
            "timeout": 5,
            "retry": 0,
        },
    },
    {
        "action_name": "validate_aadhaar_format",
        "execution_type": "python",
        "configuration": {
            "handler": "validate_aadhaar_format",
            "timeout": 5,
            "retry": 0,
        },
    },
    {
        "action_name": "validate_ifsc",
        "execution_type": "python",
        "configuration": {
            "handler": "validate_ifsc",
            "timeout": 5,
            "retry": 0,
        },
    },
    {
        "action_name": "generate_audit_report",
        "execution_type": "python",
        "configuration": {
            "handler": "generate_audit_report",
            "timeout": 60,
            "retry": 2,
        },
    },
    {
        "action_name": "generate_customer_summary",
        "execution_type": "python",
        "configuration": {
            "handler": "generate_customer_summary",
            "timeout": 30,
            "retry": 1,
        },
    },
    {
        "action_name": "risk_score_calculation",
        "execution_type": "python",
        "configuration": {
            "handler": "risk_score_calculation",
            "timeout": 15,
            "retry": 1,
        },
    },
    {
        "action_name": "document_classification",
        "execution_type": "python",
        "configuration": {
            "handler": "document_classification",
            "timeout": 30,
            "retry": 2,
        },
    },
    {
        "action_name": "rule_engine_evaluation",
        "execution_type": "python",
        "configuration": {
            "handler": "rule_engine_evaluation",
            "timeout": 10,
            "retry": 1,
        },
    },
    {
        "action_name": "decision_engine",
        "execution_type": "python",
        "configuration": {
            "handler": "decision_engine",
            "timeout": 15,
            "retry": 1,
        },
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP EXECUTOR ACTION CONFIGURATIONS
# (Reference WorkspaceIntegration — no hardcoded URLs)
# ═══════════════════════════════════════════════════════════════════════════════

HTTP_ACTIONS = [
    # CBS Customer API actions
    {
        "action_name": "fetch_customer",
        "integration_name": "CBS Customer API",
        "execution_type": "http",
        "configuration": {
            "method": "GET",
            "endpoint": "/users/{{customer_id}}",
            "headers": {"Accept": "application/json"},
            "body_template": {},
            "response_mapping": {
                "customer_name": "$.firstName",
                "email": "$.email",
                "phone": "$.phone",
            },
            "timeout": 30,
            "retry_policy": {"max_retries": 3, "backoff_multiplier": 2},
        },
    },
    {
        "action_name": "search_customer",
        "integration_name": "CBS Customer API",
        "execution_type": "http",
        "configuration": {
            "method": "GET",
            "endpoint": "/users/search",
            "headers": {"Accept": "application/json"},
            "query_params": {"q": "{{search_term}}"},
            "body_template": {},
            "response_mapping": {
                "customers": "$.users",
                "total": "$.total",
            },
            "timeout": 30,
            "retry_policy": {"max_retries": 2, "backoff_multiplier": 2},
        },
    },
    {
        "action_name": "create_customer",
        "integration_name": "CBS Customer API",
        "execution_type": "http",
        "configuration": {
            "method": "POST",
            "endpoint": "/users/add",
            "headers": {"Content-Type": "application/json"},
            "body_template": {
                "firstName": "{{first_name}}",
                "lastName": "{{last_name}}",
                "email": "{{email}}",
                "phone": "{{phone}}",
            },
            "response_mapping": {
                "customer_id": "$.id",
                "status": "$.status",
            },
            "timeout": 30,
            "retry_policy": {"max_retries": 3, "backoff_multiplier": 2},
        },
    },
    # Loan Eligibility API actions
    {
        "action_name": "check_loan_eligibility",
        "integration_name": "Loan Eligibility API",
        "execution_type": "http",
        "configuration": {
            "method": "POST",
            "endpoint": "/users",
            "headers": {"Content-Type": "application/json"},
            "body_template": {
                "name": "{{customer_name}}",
                "job": "eligibility_check",
            },
            "response_mapping": {
                "eligibility_id": "$.id",
                "created_at": "$.createdAt",
            },
            "timeout": 30,
            "retry_policy": {"max_retries": 3, "backoff_multiplier": 2},
        },
    },
    {
        "action_name": "fetch_loan_status",
        "integration_name": "Loan Eligibility API",
        "execution_type": "http",
        "configuration": {
            "method": "GET",
            "endpoint": "/users/{{loan_application_id}}",
            "headers": {"Accept": "application/json"},
            "body_template": {},
            "response_mapping": {
                "applicant_name": "$.data.first_name",
                "status": "$.data.last_name",
            },
            "timeout": 30,
            "retry_policy": {"max_retries": 2, "backoff_multiplier": 2},
        },
    },
    # KYC Verification API actions
    {
        "action_name": "verify_kyc",
        "integration_name": "KYC Verification API",
        "execution_type": "http",
        "configuration": {
            "method": "POST",
            "endpoint": "/post",
            "headers": {"Content-Type": "application/json"},
            "body_template": {
                "document_type": "{{document_type}}",
                "document_number": "{{document_number}}",
                "customer_name": "{{customer_name}}",
            },
            "response_mapping": {
                "verified": "$.json.document_type",
                "request_url": "$.url",
            },
            "timeout": 45,
            "retry_policy": {"max_retries": 3, "backoff_multiplier": 3},
        },
    },
    {
        "action_name": "fetch_kyc_status",
        "integration_name": "KYC Verification API",
        "execution_type": "http",
        "configuration": {
            "method": "GET",
            "endpoint": "/get",
            "headers": {"Accept": "application/json"},
            "query_params": {"kyc_id": "{{kyc_id}}"},
            "body_template": {},
            "response_mapping": {
                "status": "$.args.kyc_id",
                "origin": "$.origin",
            },
            "timeout": 30,
            "retry_policy": {"max_retries": 2, "backoff_multiplier": 2},
        },
    },
    # Notification Gateway actions
    {
        "action_name": "send_sms",
        "integration_name": "Notification Gateway",
        "execution_type": "http",
        "configuration": {
            "method": "POST",
            "endpoint": "/post",
            "headers": {"Content-Type": "application/json"},
            "body_template": {
                "channel": "sms",
                "to": "{{phone_number}}",
                "message": "{{message_body}}",
            },
            "response_mapping": {
                "delivery_id": "$.headers.x-forwarded-proto",
                "status": "$.data",
            },
            "timeout": 15,
            "retry_policy": {"max_retries": 3, "backoff_multiplier": 2},
        },
    },
    {
        "action_name": "send_email",
        "integration_name": "Notification Gateway",
        "execution_type": "http",
        "configuration": {
            "method": "POST",
            "endpoint": "/post",
            "headers": {"Content-Type": "application/json"},
            "body_template": {
                "channel": "email",
                "to": "{{email_address}}",
                "subject": "{{subject}}",
                "body": "{{email_body}}",
            },
            "response_mapping": {
                "message_id": "$.headers.x-forwarded-proto",
                "status": "$.data",
            },
            "timeout": 15,
            "retry_policy": {"max_retries": 3, "backoff_multiplier": 2},
        },
    },
    {
        "action_name": "send_push_notification",
        "integration_name": "Notification Gateway",
        "execution_type": "http",
        "configuration": {
            "method": "POST",
            "endpoint": "/post",
            "headers": {"Content-Type": "application/json"},
            "body_template": {
                "channel": "push",
                "device_token": "{{device_token}}",
                "title": "{{title}}",
                "body": "{{notification_body}}",
            },
            "response_mapping": {
                "notification_id": "$.headers.x-forwarded-proto",
                "status": "$.data",
            },
            "timeout": 10,
            "retry_policy": {"max_retries": 2, "backoff_multiplier": 2},
        },
    },
    # Document Validation API actions
    {
        "action_name": "validate_document",
        "integration_name": "Document Validation API",
        "execution_type": "http",
        "configuration": {
            "method": "POST",
            "endpoint": "/posts",
            "headers": {"Content-Type": "application/json"},
            "body_template": {
                "title": "{{document_type}}",
                "body": "{{document_content}}",
                "userId": 1,
            },
            "response_mapping": {
                "validation_id": "$.id",
                "document_type": "$.title",
            },
            "timeout": 30,
            "retry_policy": {"max_retries": 2, "backoff_multiplier": 2},
        },
    },
    {
        "action_name": "fetch_document",
        "integration_name": "Document Validation API",
        "execution_type": "http",
        "configuration": {
            "method": "GET",
            "endpoint": "/posts/{{document_id}}",
            "headers": {"Accept": "application/json"},
            "body_template": {},
            "response_mapping": {
                "document_title": "$.title",
                "document_body": "$.body",
            },
            "timeout": 30,
            "retry_policy": {"max_retries": 2, "backoff_multiplier": 2},
        },
    },
    # Payment Processing API actions
    {
        "action_name": "initiate_payment",
        "integration_name": "Payment Processing API",
        "execution_type": "http",
        "configuration": {
            "method": "POST",
            "endpoint": "/carts/add",
            "headers": {"Content-Type": "application/json"},
            "body_template": {
                "userId": "{{customer_id}}",
                "products": [
                    {"id": 1, "quantity": 1}
                ],
            },
            "response_mapping": {
                "payment_id": "$.id",
                "total": "$.total",
                "status": "$.discountedTotal",
            },
            "timeout": 45,
            "retry_policy": {"max_retries": 3, "backoff_multiplier": 3},
        },
    },
    {
        "action_name": "verify_payment",
        "integration_name": "Payment Processing API",
        "execution_type": "http",
        "configuration": {
            "method": "GET",
            "endpoint": "/carts/{{payment_id}}",
            "headers": {"Accept": "application/json"},
            "body_template": {},
            "response_mapping": {
                "payment_status": "$.total",
                "products": "$.products",
            },
            "timeout": 30,
            "retry_policy": {"max_retries": 2, "backoff_multiplier": 2},
        },
    },
    # Fraud Detection API actions
    {
        "action_name": "check_fraud",
        "integration_name": "Fraud Detection API",
        "execution_type": "http",
        "configuration": {
            "method": "POST",
            "endpoint": "/users",
            "headers": {"Content-Type": "application/json"},
            "body_template": {
                "name": "{{customer_name}}",
                "job": "fraud_check",
            },
            "response_mapping": {
                "fraud_check_id": "$.id",
                "checked_at": "$.createdAt",
            },
            "timeout": 30,
            "retry_policy": {"max_retries": 3, "backoff_multiplier": 2},
        },
    },
    {
        "action_name": "report_suspicious_activity",
        "integration_name": "Fraud Detection API",
        "execution_type": "http",
        "configuration": {
            "method": "POST",
            "endpoint": "/users",
            "headers": {"Content-Type": "application/json"},
            "body_template": {
                "name": "{{reporter}}",
                "job": "suspicious_activity_report",
            },
            "response_mapping": {
                "report_id": "$.id",
                "reported_at": "$.createdAt",
            },
            "timeout": 30,
            "retry_policy": {"max_retries": 2, "backoff_multiplier": 2},
        },
    },
    # Account Service API actions
    {
        "action_name": "create_account",
        "integration_name": "Account Service API",
        "execution_type": "http",
        "configuration": {
            "method": "POST",
            "endpoint": "/users/add",
            "headers": {"Content-Type": "application/json"},
            "body_template": {
                "firstName": "{{first_name}}",
                "lastName": "{{last_name}}",
                "email": "{{email}}",
                "username": "{{account_number}}",
            },
            "response_mapping": {
                "account_id": "$.id",
                "status": "$.firstName",
            },
            "timeout": 30,
            "retry_policy": {"max_retries": 3, "backoff_multiplier": 2},
        },
    },
    {
        "action_name": "fetch_account_details",
        "integration_name": "Account Service API",
        "execution_type": "http",
        "configuration": {
            "method": "GET",
            "endpoint": "/users/{{account_id}}",
            "headers": {"Accept": "application/json"},
            "body_template": {},
            "response_mapping": {
                "account_holder": "$.firstName",
                "email": "$.email",
                "phone": "$.phone",
                "status": "$.role",
            },
            "timeout": 30,
            "retry_policy": {"max_retries": 2, "backoff_multiplier": 2},
        },
    },
    {
        "action_name": "update_account",
        "integration_name": "Account Service API",
        "execution_type": "http",
        "configuration": {
            "method": "PUT",
            "endpoint": "/users/{{account_id}}",
            "headers": {"Content-Type": "application/json"},
            "body_template": {
                "firstName": "{{first_name}}",
                "lastName": "{{last_name}}",
                "email": "{{email}}",
            },
            "response_mapping": {
                "updated_id": "$.id",
                "status": "$.firstName",
            },
            "timeout": 30,
            "retry_policy": {"max_retries": 2, "backoff_multiplier": 2},
        },
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# SEEDER
# ═══════════════════════════════════════════════════════════════════════════════


def seed(db: Session):
    """Run full seed: workspace → integrations → action configs."""

    # ── 1. Workspace ──────────────────────────────────────────────────────────
    workspace = db.query(Workspace).filter_by(name=WORKSPACE["name"]).first()
    if not workspace:
        workspace = Workspace(**WORKSPACE)
        db.add(workspace)
        db.flush()
        print(f"✓ Created workspace: {workspace.name} (id={workspace.id})")
    else:
        print(f"• Workspace already exists: {workspace.name} (id={workspace.id})")

    # ── 2. Workspace Integrations ─────────────────────────────────────────────
    integration_map: dict[str, WorkspaceIntegration] = {}

    for integ_data in INTEGRATIONS:
        existing = (
            db.query(WorkspaceIntegration)
            .filter_by(workspace_id=workspace.id, name=integ_data["name"])
            .first()
        )
        if existing:
            integration_map[integ_data["name"]] = existing
            print(f"• Integration exists: {existing.name} (id={existing.id})")
            continue

        integ = WorkspaceIntegration(
            workspace_id=workspace.id,
            **integ_data,
        )
        db.add(integ)
        db.flush()
        integration_map[integ_data["name"]] = integ
        print(f"✓ Created integration: {integ.name} (id={integ.id})")

    # ── 3. Ensure we have a workflow_knowledge to attach configs to ───────────
    knowledge = db.query(WorkflowKnowledge).filter_by(workspace_id=workspace.id).first()
    if not knowledge:
        knowledge = WorkflowKnowledge(
            workflow_name="Seed Workflow",
            summary="Default workflow for seed action configurations",
            workspace_id=workspace.id,
        )
        db.add(knowledge)
        db.flush()
        print(f"✓ Created workflow_knowledge: id={knowledge.id}")
    else:
        print(f"• Using existing workflow_knowledge: id={knowledge.id}")

    # ── 4. Python Action Configurations ───────────────────────────────────────
    for action_data in PYTHON_ACTIONS:
        action_def = (
            db.query(ActionDefinition)
            .filter_by(name=action_data["action_name"])
            .first()
        )
        if not action_def:
            print(f"  ⚠ ActionDefinition not found: {action_data['action_name']} — skipping")
            continue

        existing = (
            db.query(ActionConfiguration)
            .filter_by(
                workflow_knowledge_id=knowledge.id,
                action_definition_id=action_def.id,
            )
            .first()
        )
        if existing:
            print(f"• Config exists: {action_data['action_name']} (id={existing.id})")
            continue

        config = ActionConfiguration(
            workflow_knowledge_id=knowledge.id,
            action_definition_id=action_def.id,
            workspace_integration_id=None,
            execution_type=action_data["execution_type"],
            configuration=action_data["configuration"],
        )
        db.add(config)
        db.flush()
        print(f"✓ Python config: {action_data['action_name']} (id={config.id})")

    # ── 5. HTTP Action Configurations ─────────────────────────────────────────
    for action_data in HTTP_ACTIONS:
        action_def = (
            db.query(ActionDefinition)
            .filter_by(name=action_data["action_name"])
            .first()
        )
        if not action_def:
            print(f"  ⚠ ActionDefinition not found: {action_data['action_name']} — skipping")
            continue

        integration = integration_map.get(action_data["integration_name"])
        if not integration:
            print(f"  ⚠ Integration not found: {action_data['integration_name']} — skipping")
            continue

        existing = (
            db.query(ActionConfiguration)
            .filter_by(
                workflow_knowledge_id=knowledge.id,
                action_definition_id=action_def.id,
            )
            .first()
        )
        if existing:
            print(f"• Config exists: {action_data['action_name']} (id={existing.id})")
            continue

        config = ActionConfiguration(
            workflow_knowledge_id=knowledge.id,
            action_definition_id=action_def.id,
            workspace_integration_id=integration.id,
            execution_type=action_data["execution_type"],
            configuration=action_data["configuration"],
        )
        db.add(config)
        db.flush()
        print(f"✓ HTTP config: {action_data['action_name']} → {integration.name} (id={config.id})")

    # ── Commit ────────────────────────────────────────────────────────────────
    db.commit()
    print("\n✅ Seed completed successfully.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed(db)
    except Exception as e:
        db.rollback()
        print(f"\n❌ Seed failed: {e}")
        raise
    finally:
        db.close()
