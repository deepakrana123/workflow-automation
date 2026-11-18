# Comprehensive test script for RuntimeRuleEngine safety implementation
# Run this script to verify all changes
# Usage: .\scripts\run_all_tests.ps1

$ErrorActionPreference = "Stop"

$PROJECT_ROOT = "c:\Users\Devendra\projects\mflows"
Set-Location $PROJECT_ROOT

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "RuntimeRuleEngine Safety Implementation - Test Suite" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Colors helper
function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Step {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

# Activate virtual environment
Write-Step "[1/6] Activating virtual environment..."
& .\.venv312\Scripts\Activate.ps1
Write-Success "Virtual environment activated"
Write-Host ""

# Step 1: Verify Python syntax
Write-Step "[2/6] Verifying Python syntax..."
try {
    python -m py_compile app/runtime/context.py
    python -m py_compile app/runtime/rule_engine.py
    python -m py_compile app/execution/rules/step_rule_evaluator.py
    python -m py_compile app/routes/runtime.py
    Write-Success "All files have valid Python syntax"
}
catch {
    Write-Error-Custom "Syntax check failed: $_"
    exit 1
}
Write-Host ""

# Step 2: Test imports
Write-Step "[3/6] Testing imports..."
try {
    python -c "from app.runtime.rule_engine import RuntimeRuleEngine; print('  ✓ RuntimeRuleEngine')"
    python -c "from app.execution.rules.step_rule_evaluator import evaluate_step_rules; print('  ✓ step_rule_evaluator')"
    python -c "from app.runtime.context import RuleEvaluationResult; print('  ✓ RuleEvaluationResult')"
    python -c "from app.rbac.rule_extractor import _classify_rule; print('  ✓ _classify_rule')"
    python -c "from app.models.business_rule_definition import RuleEvaluationStatus; print('  ✓ RuleEvaluationStatus')"
    Write-Success "All imports successful"
}
catch {
    Write-Error-Custom "Import test failed: $_"
    exit 1
}
Write-Host ""

# Step 3: Run classification unit tests
Write-Step "[4/6] Running classification unit tests (18 tests)..."
try {
    python scripts/test_rule_classification.py
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Classification tests failed"
        exit 1
    }
}
catch {
    Write-Error-Custom "Classification tests failed: $_"
    exit 1
}
Write-Host ""

# Step 4: Run integration tests
Write-Step "[5/6] Running integration tests (12 tests)..."
try {
    python scripts/test_runtime_safety_integration.py
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Integration tests failed"
        exit 1
    }
}
catch {
    Write-Error-Custom "Integration tests failed: $_"
    exit 1
}
Write-Host ""

# Step 5: Run extraction tests (regression check)
Write-Step "[6/6] Running extraction tests (regression check)..."
try {
    python scripts/test_rule_extraction.py
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Extraction tests failed (regression detected)"
        exit 1
    }
}
catch {
    Write-Error-Custom "Extraction tests failed: $_"
    exit 1
}
Write-Host ""

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "ALL TESTS PASSED ✓" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  • Python syntax: ✓" -ForegroundColor Green
Write-Host "  • Imports: ✓" -ForegroundColor Green
Write-Host "  • Classification unit tests: ✓ (18 tests)" -ForegroundColor Green
Write-Host "  • Integration tests: ✓ (12 tests)" -ForegroundColor Green
Write-Host "  • Extraction tests: ✓ (no regressions)" -ForegroundColor Green
Write-Host ""
Write-Host "Implementation is complete and ready for deployment." -ForegroundColor Green
