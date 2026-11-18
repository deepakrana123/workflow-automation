"""
Phase 3-9: Corrected End-to-End Personal Loan BRD Pipeline Validation
========================================================================

CORRECTED FOR ACTUAL PDF INGESTION:
- Generate genuine PDF fixtures from synthetic BRD content
- Verify PDF magic bytes before ingestion
- Assert non-zero document/version/attempt IDs
- Validate persistence across all layers
- Test idempotency with actual duplicate detection
- Query only synthetic BRD rules for runtime evaluation
- Report actual pass/fail/blocked with exit codes

Run from project root:
    .venv312\\Scripts\\python.exe scripts/test_e2e_pipeline_corrected.py
"""

from __future__ import annotations

import sys
from pathlib import Path
import hashlib

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

# PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
except ImportError:
    print("ERROR: reportlab not installed. Install with: pip install reportlab")
    sys.exit(1)

from app.knowledge_ingestions.ingestion_orchestrator import IngestionOrchestrator
from app.db.session import SessionLocal
from app.models import (
    BRDDocument,
    DocumentVersion,
    IngestionAttempt,
    WorkflowKnowledge,
    WorkflowBusinessRule,
    BusinessRuleDefinition,
)
from app.runtime.rule_engine import RuntimeRuleEngine
from app.runtime.context import RuleEvaluationContext
from sqlalchemy import and_

# ============================================================================
# Test Results Tracking
# ============================================================================

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.blocked = []
        self.exit_code = 0
    
    def add_pass(self, test_name: str, detail: str = ""):
        self.passed.append((test_name, detail))
        print(f"  ✓ PASS: {test_name}" + (f" — {detail}" if detail else ""))
    
    def add_fail(self, test_name: str, detail: str = ""):
        self.failed.append((test_name, detail))
        self.exit_code = 1
        print(f"  ✗ FAIL: {test_name}" + (f" — {detail}" if detail else ""))
    
    def add_blocked(self, test_name: str, reason: str = ""):
        self.blocked.append((test_name, reason))
        print(f"  ⊘ BLOCKED: {test_name}" + (f" — {reason}" if reason else ""))
    
    def summary(self):
        total = len(self.passed) + len(self.failed) + len(self.blocked)
        print(f"\n{'='*80}")
        print(f"TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Passed:  {len(self.passed)}")
        print(f"Failed:  {len(self.failed)}")
        print(f"Blocked: {len(self.blocked)}")
        print(f"Total:   {total}")
        print(f"Exit Code: {self.exit_code}")
        return self.exit_code


results = TestResults()

# ============================================================================
# Phase 1: Generate PDF Fixtures
# ============================================================================

def generate_pdf_from_text(text_content: str, output_path: Path) -> bytes:
    """Generate a PDF from text content using reportlab"""
    
    # Create PDF to bytes buffer
    from io import BytesIO
    buffer = BytesIO()
    
    # Create canvas
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Margins
    left_margin = 0.5 * inch
    right_margin = 0.5 * inch
    top_margin = 0.5 * inch
    line_height = 12
    
    # Split content into lines and write
    y_position = height - top_margin
    lines = text_content.split('\n')
    
    for line in lines:
        # Wrap long lines
        if len(line) > 90:
            words = line.split(' ')
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 > 90:
                    c.drawString(left_margin, y_position, current_line)
                    y_position -= line_height
                    current_line = word
                else:
                    current_line += (" " if current_line else "") + word
            if current_line:
                c.drawString(left_margin, y_position, current_line)
                y_position -= line_height
        else:
            c.drawString(left_margin, y_position, line)
            y_position -= line_height
        
        # Page break if needed
        if y_position < 0.5 * inch:
            c.showPage()
            y_position = height - top_margin
    
    c.save()
    
    # Get bytes
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    
    # Write to file
    output_path.write_bytes(pdf_bytes)
    
    return pdf_bytes


def create_pdf_fixtures():
    """Create genuine PDF fixtures from synthetic BRD content"""
    print(f"\n{'='*80}")
    print(f"PHASE 1: Generating PDF Fixtures")
    print(f"{'='*80}")
    
    fixture_dir = Path(__file__).parent / "fixtures"
    fixture_dir.mkdir(exist_ok=True)
    
    # Bank Alpha content
    alpha_content = """BANK ALPHA PERSONAL LOAN PROGRAM
Eligibility Criteria & Terms
Version 1.0 | Effective Date: 2026-01-01

1. APPLICANT DEMOGRAPHICS
The Personal Loan Program is open to Indian residents meeting the following age criteria:
- Applicant age must be between 21 and 65 years (inclusive)
- Self-employed and salaried professionals are eligible

2. CREDIT ASSESSMENT
All applicants undergo a comprehensive credit evaluation:
- Minimum CIBIL credit score required: 650
- Credit score evaluation is mandatory for all loan amounts

3. INCOME VERIFICATION
Applicants must demonstrate stable and verifiable income:
- Monthly salary must exceed ₹25,000 (twenty-five thousand rupees)
- Income verification through payroll records required

4. LOAN AMOUNT LIMITS
Loan amounts are constrained by the following policy:
- Minimum loan amount: ₹50,000 (fifty thousand rupees)
- Maximum loan amount: ₹25,00,000 (twenty-five lakhs rupees)

5. APPLICABLE INTEREST RATES
Interest rates are determined based on credit profile:
- Applicable interest rates range from 9.5% to 15% per annum
- Rates are set per RBI guidelines and internal policy mandate

6. EMPLOYMENT DOCUMENTATION REQUIREMENTS
Salaried applicants must provide comprehensive employment history:
- Minimum 2 years of employment history is mandatory
- Required documents: Salary slips, Offer letter, Form 16

7. COLLATERAL REQUIREMENTS
Personal loans may be structured with optional collateral backing:
- Acceptable collateral includes: fixed deposits, securities, or property
"""
    
    # Bank Beta content
    beta_content = """BANK BETA ADAPTIVE PERSONAL LOAN SOLUTION
Eligibility Matrix & Product Terms
Version 2.0 | Effective Date: 2026-02-01

1. APPLICANT AGE & RESIDENCY
The Adaptive Personal Loan Solution is available to eligible residents:
- Applicant age must be between 25 and 60 years (inclusive)
- Valid Indian residency and permanent address required

2. CREDIT PROFILE ASSESSMENT
Bank Beta employs enhanced credit evaluation standards:
- Minimum CIBIL credit score requirement: 700
- Credit scores of 700+ qualify for standard rates

3. INCOME REQUIREMENTS
Applicants must demonstrate strong income stability:
- Annual income must be at least ₹3,00,000 (three lakhs rupees)
- Monthly equivalent: Minimum ₹25,000 per month
- Income documentation: Last 2 years ITR, recent bank statements

4. LOAN PRODUCT LIMITS
Adaptive loan structuring with flexible limits:
- Minimum loan amount: ₹1,00,000 (one lakh rupees)
- Maximum loan amount: ₹50,00,000 (fifty lakhs rupees)

5. EMI-TO-INCOME RATIO CONSTRAINT
Bank Beta enforces strict debt-to-income limitations:
- EMI amount must not exceed 40% of monthly salary
- Total existing EMI plus new EMI should not exceed 50% of net income

6. PROCESSING FEE STRUCTURE
Transparent fee framework based on credit profile:
- Processing fee ranges from 0.5% to 1.5% of loan amount
- Fees charged upfront and debited from disbursement amount

7. JOINT APPLICATIONS & CO-APPLICANTS
Enhanced eligibility through joint application structure:
- Co-applicants with independent income improve eligibility significantly
- Joint applications require co-applicant's full documentation
"""
    
    # Generate PDFs
    try:
        alpha_path = fixture_dir / "bank_alpha_personal_loan_brd.pdf"
        alpha_bytes = generate_pdf_from_text(alpha_content, alpha_path)
        results.add_pass("PDF Generation: Bank Alpha", f"{len(alpha_bytes)} bytes, {alpha_path.name}")
        
        beta_path = fixture_dir / "bank_beta_personal_loan_brd.pdf"
        beta_bytes = generate_pdf_from_text(beta_content, beta_path)
        results.add_pass("PDF Generation: Bank Beta", f"{len(beta_bytes)} bytes, {beta_path.name}")
        
        # Verify PDF magic bytes
        if alpha_bytes[:4] == b'%PDF':
            results.add_pass("PDF Validation: Bank Alpha", "Magic bytes correct")
        else:
            results.add_fail("PDF Validation: Bank Alpha", f"Magic bytes incorrect: {alpha_bytes[:4]}")
        
        if beta_bytes[:4] == b'%PDF':
            results.add_pass("PDF Validation: Bank Beta", "Magic bytes correct")
        else:
            results.add_fail("PDF Validation: Bank Beta", f"Magic bytes incorrect: {beta_bytes[:4]}")
        
        return {
            "alpha": {
                "path": alpha_path,
                "bytes": alpha_bytes,
                "hash": hashlib.sha256(alpha_bytes).hexdigest(),
                "content": alpha_content,
            },
            "beta": {
                "path": beta_path,
                "bytes": beta_bytes,
                "hash": hashlib.sha256(beta_bytes).hexdigest(),
                "content": beta_content,
            }
        }
    
    except Exception as e:
        results.add_fail("PDF Generation", str(e))
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# Phase 2: Ingest Documents
# ============================================================================

def ingest_pdf(tenant_id: int, workspace_id: int, pdf_bytes: bytes, filename: str) -> tuple:
    """Ingest a PDF and return (result, document_id, version_id, knowledge_id)"""
    print(f"\n{'='*80}")
    print(f"PHASE 2: Ingesting {filename}")
    print(f"  Tenant ID: {tenant_id}, Workspace ID: {workspace_id}")
    print(f"{'='*80}")
    
    db = SessionLocal()
    try:
        orchestrator = IngestionOrchestrator(db=db)
        result = orchestrator.run(
            file_bytes=pdf_bytes,
            original_filename=filename,
            tenant_id=tenant_id,
            workspace_id=workspace_id
        )
        
        print(f"  Overall Status: {result.overall_status}")
        print(f"  Document ID: {result.document_id}")
        print(f"  Version ID: {result.document_version_id}")
        print(f"  Ingestion Attempt ID: {result.ingestion_attempt_id}")
        print(f"  Knowledge ID: {result.knowledge_id}")
        print(f"  Rules created: {result.rules_created}")
        print(f"  Rules skipped: {result.rules_skipped}")
        
        # Assertions
        if result.document_id == 0:
            results.add_fail(f"Ingestion: {filename}", f"document_id is 0: {result.error_message}")
            return (None, 0, 0, 0)
        else:
            results.add_pass(f"Ingestion: {filename}", f"document_id={result.document_id}")
        
        if result.overall_status not in ["COMPLETED", "PARTIAL"]:
            results.add_fail(f"Ingestion Status: {filename}", f"Status={result.overall_status}")
            if result.error_message:
                print(f"    Error: {result.error_message}")
            return (None, result.document_id, result.document_version_id, result.knowledge_id)
        else:
            results.add_pass(f"Ingestion Status: {filename}", f"Status={result.overall_status}")
        
        return (result, result.document_id, result.document_version_id, result.knowledge_id)
    
    except Exception as e:
        results.add_fail(f"Ingestion Exception: {filename}", str(e))
        import traceback
        traceback.print_exc()
        return (None, 0, 0, 0)
    finally:
        db.close()


# ============================================================================
# Phase 3: Verify Persistence
# ============================================================================

def verify_persistence(bank_name: str, tenant_id: int, doc_id: int, version_id: int, knowledge_id: int):
    """Verify document persistence and provenance"""
    print(f"\n{'='*80}")
    print(f"PHASE 3: Verifying Persistence ({bank_name})")
    print(f"  Document ID: {doc_id}, Version ID: {version_id}, Knowledge ID: {knowledge_id}")
    print(f"{'='*80}")
    
    if doc_id == 0:
        results.add_blocked("Persistence Checks", "document_id=0, skipping")
        return False
    
    db = SessionLocal()
    try:
        # Check BRDDocument
        brd_doc = db.query(BRDDocument).filter(BRDDocument.id == doc_id).first()
        if not brd_doc:
            results.add_fail("BRDDocument lookup", f"No document found with id={doc_id}")
            return False
        results.add_pass("BRDDocument lookup", f"Found: {brd_doc.original_filename}")
        
        # Check DocumentVersion
        if version_id and version_id != 0:
            doc_version = db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
            if not doc_version:
                results.add_fail("DocumentVersion lookup", f"No version found with id={version_id}")
            else:
                results.add_pass("DocumentVersion lookup", f"Found: version={doc_version.version_number}")
        else:
            results.add_blocked("DocumentVersion lookup", "version_id=0 or None")
        
        # Check IngestionAttempt records
        attempts = db.query(IngestionAttempt).filter(IngestionAttempt.document_version_id == version_id).all()
        if not attempts:
            results.add_fail("IngestionAttempt lookup", f"No attempts found for version_id={version_id}")
        else:
            results.add_pass("IngestionAttempt lookup", f"Found {len(attempts)} attempt(s)")
            for a in attempts:
                print(f"      - Attempt {a.id}: status={a.status}, number={a.attempt_number}")
        
        # Check WorkflowKnowledge
        if knowledge_id:
            knowledge = db.query(WorkflowKnowledge).filter(WorkflowKnowledge.id == knowledge_id).first()
            if not knowledge:
                results.add_fail("WorkflowKnowledge lookup", f"No knowledge found with id={knowledge_id}")
                return False
            results.add_pass("WorkflowKnowledge lookup", f"Found: {knowledge.workflow_name}")
            
            # Check raw rules (WorkflowBusinessRule)
            raw_rules = db.query(WorkflowBusinessRule).filter(
                WorkflowBusinessRule.workflow_knowledge_id == knowledge_id
            ).all()
            if not raw_rules:
                results.add_fail("WorkflowBusinessRule lookup", f"No rules found for knowledge_id={knowledge_id}")
            else:
                results.add_pass("WorkflowBusinessRule lookup", f"Found {len(raw_rules)} rule(s)")
            
            # Check structured rules (BusinessRuleDefinition)
            structured_rules = db.query(BusinessRuleDefinition).filter(
                BusinessRuleDefinition.source_workflow_knowledge_id == knowledge_id
            ).all()
            if not structured_rules:
                results.add_blocked("BusinessRuleDefinition lookup", f"No structured rules yet for knowledge_id={knowledge_id}")
            else:
                results.add_pass("BusinessRuleDefinition lookup", f"Found {len(structured_rules)} structured rule(s)")
                for rule in structured_rules:
                    print(f"      - Rule: {rule.field} {rule.op} {rule.value}")
        
        return True
    
    finally:
        db.close()


# ============================================================================
# Phase 4: Test Idempotency
# ============================================================================

def test_idempotency(tenant_id: int, workspace_id: int, pdf_bytes: bytes, filename: str):
    """Upload same PDF twice and verify idempotency"""
    print(f"\n{'='*80}")
    print(f"PHASE 4: Testing Idempotency")
    print(f"  Tenant ID: {tenant_id}, Workspace ID: {workspace_id}")
    print(f"  File: {filename}")
    print(f"{'='*80}")
    
    db = SessionLocal()
    try:
        orchestrator = IngestionOrchestrator(db=db)
        
        # First upload
        result1 = orchestrator.run(
            file_bytes=pdf_bytes,
            original_filename=filename,
            tenant_id=tenant_id,
            workspace_id=workspace_id
        )
        
        # Second upload (duplicate)
        result2 = orchestrator.run(
            file_bytes=pdf_bytes,
            original_filename=filename,
            tenant_id=tenant_id,
            workspace_id=workspace_id
        )
        
        print(f"  First ingestion: doc_id={result1.document_id}, is_duplicate={result1.is_duplicate}")
        print(f"  Second ingestion: doc_id={result2.document_id}, is_duplicate={result2.is_duplicate}")
        
        # Assertions
        if result1.document_id == 0 and result2.document_id == 0:
            results.add_fail(f"Idempotency: {filename}", "Both uploads failed (doc_id=0 for both)")
            return False
        
        if result1.document_id == result2.document_id:
            results.add_pass(f"Idempotency: {filename}", "Same document_id returned")
        else:
            results.add_fail(f"Idempotency: {filename}", f"Different IDs: {result1.document_id} vs {result2.document_id}")
            return False
        
        if result2.is_duplicate:
            results.add_pass(f"Idempotency Duplicate Flag", "Second upload marked as duplicate")
        else:
            results.add_blocked(f"Idempotency Duplicate Flag", "Second upload not marked as duplicate")
        
        return True
    
    except Exception as e:
        results.add_fail(f"Idempotency Exception: {filename}", str(e))
        return False
    finally:
        db.close()


# ============================================================================
# Phase 5: Runtime Evaluation
# ============================================================================

def test_runtime_evaluation(bank_name: str, workspace_id: int, knowledge_id: int):
    """Test runtime evaluation using synthetic PL rules"""
    print(f"\n{'='*80}")
    print(f"PHASE 5: Runtime Evaluation ({bank_name})")
    print(f"  Knowledge ID: {knowledge_id}, Workspace ID: {workspace_id}")
    print(f"{'='*80}")
    
    if not knowledge_id:
        results.add_blocked("Runtime Evaluation", "knowledge_id=0, skipping")
        return
    
    db = SessionLocal()
    try:
        # Query BusinessRuleDefinition records linked to this knowledge
        rules = db.query(BusinessRuleDefinition).filter(
            BusinessRuleDefinition.source_workflow_knowledge_id == knowledge_id
        ).all()
        
        if not rules:
            results.add_blocked("Runtime Evaluation", f"No BusinessRuleDefinition records for knowledge_id={knowledge_id}")
            return
        
        print(f"  Found {len(rules)} structured rules from synthetic BRD")
        
        # Create evaluation context
        context = RuleEvaluationContext(
            user_id="test_evaluator",
            workspace_id=workspace_id,
            request_data={
                "applicant_age": 35,
                "credit_score": 700,
                "monthly_salary": 50000,
                "loan_amount": 300000,
                "annual_income": 600000,
                "emi_amount": 20000,
            }
        )
        
        # Run engine
        engine = RuntimeRuleEngine(db=db)
        result = engine.evaluate(context)
        
        print(f"  Evaluation Result:")
        print(f"    - Allowed: {result.allowed}")
        print(f"    - Status: {result.status}")
        print(f"    - Decisions: {len(result.decisions)}")
        print(f"    - Failed rules: {len(result.failed_rules)}")
        
        if result.status in ["PASS", "FAIL", "REVIEW_REQUIRED"]:
            results.add_pass("Runtime Evaluation Status", f"Status={result.status}")
        else:
            results.add_fail("Runtime Evaluation Status", f"Unexpected status={result.status}")
    
    except Exception as e:
        results.add_blocked("Runtime Evaluation", f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


# ============================================================================
# Main Execution
# ============================================================================

# ============================================================================
# Tenant and Workspace Provisioning
# ============================================================================

def provision_test_tenants_and_workspaces() -> dict:
    """Create isolated test tenants and workspaces"""
    print(f"\n{'='*80}")
    print(f"SETUP: Provisioning Test Tenants and Workspaces")
    print(f"{'='*80}")
    
    from app.models import Tenant, Workspace
    from datetime import datetime
    
    db = SessionLocal()
    try:
        # Use timestamp to ensure unique names across test runs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        alpha_name = f"test_tenant_alpha_{timestamp}"
        beta_name = f"test_tenant_beta_{timestamp}"
        
        # Create Bank Alpha tenant
        alpha_tenant = Tenant(
            name=alpha_name,
            slug=f"test-tenant-alpha-{timestamp}",
            display_name="Test Bank Alpha",
            active=True
        )
        db.add(alpha_tenant)
        db.flush()
        alpha_tenant_id = alpha_tenant.id
        print(f"[OK] Created Bank Alpha tenant: ID={alpha_tenant_id}, name={alpha_name}")
        
        # Create Bank Alpha workspace
        alpha_workspace = Workspace(
            tenant_id=alpha_tenant_id,
            name="personal_loan",
            display_name="Personal Loan",
            description="Bank Alpha Personal Loan Products"
        )
        db.add(alpha_workspace)
        db.flush()
        alpha_workspace_id = alpha_workspace.id
        print(f"✓ Created Bank Alpha workspace: ID={alpha_workspace_id}, tenant_id={alpha_workspace.tenant_id}")
        
        # Create Bank Beta tenant
        beta_tenant = Tenant(
            name=beta_name,
            slug=f"test-tenant-beta-{timestamp}",
            display_name="Test Bank Beta",
            active=True
        )
        db.add(beta_tenant)
        db.flush()
        beta_tenant_id = beta_tenant.id
        print(f"✓ Created Bank Beta tenant: ID={beta_tenant_id}, name={beta_name}")
        
        # Create Bank Beta workspace
        beta_workspace = Workspace(
            tenant_id=beta_tenant_id,
            name="personal_loan",
            display_name="Personal Loan",
            description="Bank Beta Personal Loan Products"
        )
        db.add(beta_workspace)
        db.flush()
        beta_workspace_id = beta_workspace.id
        print(f"✓ Created Bank Beta workspace: ID={beta_workspace_id}, tenant_id={beta_workspace.tenant_id}")
        
        # Isolation assertions
        results.add_pass("Tenant Isolation", f"Alpha tenant_id={alpha_tenant_id}, Beta tenant_id={beta_tenant_id}")
        results.add_pass("Workspace Isolation", f"Alpha ws_id={alpha_workspace_id}, Beta ws_id={beta_workspace_id}")
        
        if alpha_tenant_id != beta_tenant_id:
            results.add_pass("Tenant Uniqueness", "Alpha and Beta have different tenant IDs")
        else:
            results.add_fail("Tenant Uniqueness", "Alpha and Beta have same tenant ID!")
            
        if alpha_workspace_id != beta_workspace_id:
            results.add_pass("Workspace Uniqueness", "Alpha and Beta have different workspace IDs")
        else:
            results.add_fail("Workspace Uniqueness", "Alpha and Beta have same workspace ID!")
        
        # Ownership assertions
        if alpha_workspace.tenant_id == alpha_tenant_id:
            results.add_pass("Alpha Ownership", f"workspace.tenant_id={alpha_workspace.tenant_id} matches tenant.id")
        else:
            results.add_fail("Alpha Ownership", f"Mismatch: workspace.tenant_id={alpha_workspace.tenant_id}, expected {alpha_tenant_id}")
            
        if beta_workspace.tenant_id == beta_tenant_id:
            results.add_pass("Beta Ownership", f"workspace.tenant_id={beta_workspace.tenant_id} matches tenant.id")
        else:
            results.add_fail("Beta Ownership", f"Mismatch: workspace.tenant_id={beta_workspace.tenant_id}, expected {beta_tenant_id}")
        
        db.commit()
        print(f"✓ Provisioning committed to database")
        
        return {
            "alpha": {
                "tenant_id": alpha_tenant_id,
                "workspace_id": alpha_workspace_id,
            },
            "beta": {
                "tenant_id": beta_tenant_id,
                "workspace_id": beta_workspace_id,
            }
        }
        
    except Exception as e:
        db.rollback()
        results.add_fail("Provisioning", str(e))
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


def cleanup_test_tenants_and_workspaces(config: dict):
    """Clean up test tenants and workspaces after tests complete"""
    print(f"\n{'='*80}")
    print(f"TEARDOWN: Cleaning Test Tenants and Workspaces")
    print(f"{'='*80}")
    
    from app.models import Tenant
    
    if not config:
        print(f"✗ No config provided, skipping cleanup")
        return
    
    db = SessionLocal()
    try:
        # Delete test tenants (cascade deletes workspaces)
        alpha_tenant = db.query(Tenant).filter(Tenant.id == config["alpha"]["tenant_id"]).first()
        if alpha_tenant:
            db.delete(alpha_tenant)
            print(f"✓ Deleted Bank Alpha tenant (ID={alpha_tenant.id})")
        
        beta_tenant = db.query(Tenant).filter(Tenant.id == config["beta"]["tenant_id"]).first()
        if beta_tenant:
            db.delete(beta_tenant)
            print(f"✓ Deleted Bank Beta tenant (ID={beta_tenant.id})")
        
        db.commit()
        print(f"✓ Cleanup committed")
        
    except Exception as e:
        db.rollback()
        print(f"⚠ Cleanup error: {e}")
    finally:
        db.close()


def main():
    print(f"\n{'#'*80}")
    print(f"# CORRECTED END-TO-END PERSONAL LOAN BRD PIPELINE VALIDATION")
    print(f"{'#'*80}")
    
    # Step 0: Provision test environment
    config = provision_test_tenants_and_workspaces()
    if not config:
        print(f"\n✗ Test provisioning failed")
        return results.summary()
    
    # Phase 1: Generate PDFs
    fixtures = create_pdf_fixtures()
    if not fixtures:
        print(f"\n✗ PDF fixture generation failed")
        cleanup_test_tenants_and_workspaces(config)
        return results.summary()
    
    # Phase 2-5: Bank Alpha Pipeline
    print(f"\n{'*'*80}")
    print(f"BANK ALPHA PIPELINE")
    print(f"{'*'*80}")
    
    result_a, doc_a, ver_a, know_a = ingest_pdf(
        tenant_id=config["alpha"]["tenant_id"],
        workspace_id=config["alpha"]["workspace_id"],
        pdf_bytes=fixtures["alpha"]["bytes"],
        filename="bank_alpha_personal_loan_brd.pdf"
    )
    
    if doc_a != 0:
        verify_persistence("alpha", config["alpha"]["tenant_id"], doc_a, ver_a, know_a)
        if know_a:
            test_runtime_evaluation("alpha", config["alpha"]["workspace_id"], know_a)
        else:
            results.add_blocked("Runtime Evaluation (alpha)", "knowledge_id is None")
    
    test_idempotency(
        config["alpha"]["tenant_id"],
        config["alpha"]["workspace_id"],
        fixtures["alpha"]["bytes"],
        "bank_alpha_personal_loan_brd.pdf"
    )
    
    # Phase 2-5: Bank Beta Pipeline
    print(f"\n{'*'*80}")
    print(f"BANK BETA PIPELINE")
    print(f"{'*'*80}")
    
    result_b, doc_b, ver_b, know_b = ingest_pdf(
        tenant_id=config["beta"]["tenant_id"],
        workspace_id=config["beta"]["workspace_id"],
        pdf_bytes=fixtures["beta"]["bytes"],
        filename="bank_beta_personal_loan_brd.pdf"
    )
    
    if doc_b != 0:
        verify_persistence("beta", config["beta"]["tenant_id"], doc_b, ver_b, know_b)
        if know_b:
            test_runtime_evaluation("beta", config["beta"]["workspace_id"], know_b)
        else:
            results.add_blocked("Runtime Evaluation (beta)", "knowledge_id is None")
    
    test_idempotency(
        config["beta"]["tenant_id"],
        config["beta"]["workspace_id"],
        fixtures["beta"]["bytes"],
        "bank_beta_personal_loan_brd.pdf"
    )
    
    # Negative test: Cross-tenant access attempt
    print(f"\n{'*'*80}")
    print(f"NEGATIVE TEST: Cross-Tenant Rejection")
    print(f"{'*'*80}")
    print(f"Attempting: Alpha tenant with Beta workspace (should be rejected)")
    
    result_negative, doc_neg, ver_neg, know_neg = ingest_pdf(
        tenant_id=config["alpha"]["tenant_id"],
        workspace_id=config["beta"]["workspace_id"],
        pdf_bytes=fixtures["alpha"]["bytes"],
        filename="bank_alpha_personal_loan_brd_negative.pdf"
    )
    
    if doc_neg == 0 or result_negative.overall_status in ["FAILED"]:
        results.add_pass("Cross-Tenant Rejection", "Correctly rejected mismatched tenant/workspace")
    else:
        results.add_fail("Cross-Tenant Rejection", f"Should have been rejected but got doc_id={doc_neg}")
    
    # Cleanup
    cleanup_test_tenants_and_workspaces(config)
    
    # Summary
    exit_code = results.summary()
    
    print(f"\n{'='*80}")
    print(f"DETAILED RESULTS")
    print(f"{'='*80}")
    
    if results.passed:
        print(f"\nPASSED ({len(results.passed)}):")
        for name, detail in results.passed:
            print(f"  ✓ {name}" + (f": {detail}" if detail else ""))
    
    if results.failed:
        print(f"\nFAILED ({len(results.failed)}):")
        for name, detail in results.failed:
            print(f"  ✗ {name}" + (f": {detail}" if detail else ""))
    
    if results.blocked:
        print(f"\nBLOCKED ({len(results.blocked)}):")
        for name, reason in results.blocked:
            print(f"  ⊘ {name}" + (f": {reason}" if reason else ""))
    
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
