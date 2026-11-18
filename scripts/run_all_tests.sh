#!/bin/bash

# Comprehensive test script for RuntimeRuleEngine safety implementation
# Run this script to verify all changes

set -e

PROJECT_ROOT="c:\Users\Devendra\projects\mflows"
cd "$PROJECT_ROOT"

echo "========================================================================"
echo "RuntimeRuleEngine Safety Implementation - Test Suite"
echo "========================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Activate virtual environment
echo "[1/6] Activating virtual environment..."
source .\.venv312\Scripts\activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Step 1: Verify Python syntax
echo "[2/6] Verifying Python syntax..."
python -m py_compile app/runtime/context.py
python -m py_compile app/runtime/rule_engine.py
python -m py_compile app/execution/rules/step_rule_evaluator.py
python -m py_compile app/routes/runtime.py
echo -e "${GREEN}✓ All files have valid Python syntax${NC}"
echo ""

# Step 2: Test imports
echo "[3/6] Testing imports..."
python -c "from app.runtime.rule_engine import RuntimeRuleEngine; print('  ✓ RuntimeRuleEngine')"
python -c "from app.execution.rules.step_rule_evaluator import evaluate_step_rules; print('  ✓ step_rule_evaluator')"
python -c "from app.runtime.context import RuleEvaluationResult; print('  ✓ RuleEvaluationResult')"
python -c "from app.rbac.rule_extractor import _classify_rule; print('  ✓ _classify_rule')"
python -c "from app.models.business_rule_definition import RuleEvaluationStatus; print('  ✓ RuleEvaluationStatus')"
echo -e "${GREEN}✓ All imports successful${NC}"
echo ""

# Step 3: Run classification unit tests
echo "[4/6] Running classification unit tests (18 tests)..."
python scripts/test_rule_classification.py
echo ""

# Step 4: Run integration tests
echo "[5/6] Running integration tests (12 tests)..."
python scripts/test_runtime_safety_integration.py
echo ""

# Step 5: Run extraction tests (regression check)
echo "[6/6] Running extraction tests (regression check)..."
python scripts/test_rule_extraction.py
echo ""

echo "========================================================================"
echo -e "${GREEN}ALL TESTS PASSED ✓${NC}"
echo "========================================================================"
echo ""
echo "Summary:"
echo "  • Python syntax: ✓"
echo "  • Imports: ✓"
echo "  • Classification unit tests: ✓ (18 tests)"
echo "  • Integration tests: ✓ (12 tests)"
echo "  • Extraction tests: ✓ (no regressions)"
echo ""
echo "Implementation is complete and ready for deployment."
