@echo off
REM Comprehensive test script for RuntimeRuleEngine safety implementation
REM Run this batch file to verify all changes
REM Usage: scripts\run_all_tests.bat

setlocal enabledelayedexpansion

cd /d c:\Users\Devendra\projects\mflows

echo.
echo ========================================================================
echo RuntimeRuleEngine Safety Implementation - Test Suite
echo ========================================================================
echo.

REM Activate virtual environment
echo [1/6] Activating virtual environment...
call .\.venv312\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

REM Step 1: Verify Python syntax
echo [2/6] Verifying Python syntax...
python -m py_compile app/runtime/context.py
if errorlevel 1 (
    echo ERROR: Syntax check failed for app/runtime/context.py
    exit /b 1
)
python -m py_compile app/runtime/rule_engine.py
if errorlevel 1 (
    echo ERROR: Syntax check failed for app/runtime/rule_engine.py
    exit /b 1
)
python -m py_compile app/execution/rules/step_rule_evaluator.py
if errorlevel 1 (
    echo ERROR: Syntax check failed for app/execution/rules/step_rule_evaluator.py
    exit /b 1
)
python -m py_compile app/routes/runtime.py
if errorlevel 1 (
    echo ERROR: Syntax check failed for app/routes/runtime.py
    exit /b 1
)
echo [OK] All files have valid Python syntax
echo.

REM Step 2: Test imports
echo [3/6] Testing imports...
python -c "from app.runtime.rule_engine import RuntimeRuleEngine; print('  [OK] RuntimeRuleEngine')"
if errorlevel 1 goto import_error
python -c "from app.execution.rules.step_rule_evaluator import evaluate_step_rules; print('  [OK] step_rule_evaluator')"
if errorlevel 1 goto import_error
python -c "from app.runtime.context import RuleEvaluationResult; print('  [OK] RuleEvaluationResult')"
if errorlevel 1 goto import_error
python -c "from app.rbac.rule_extractor import _classify_rule; print('  [OK] _classify_rule')"
if errorlevel 1 goto import_error
python -c "from app.models.business_rule_definition import RuleEvaluationStatus; print('  [OK] RuleEvaluationStatus')"
if errorlevel 1 goto import_error
echo [OK] All imports successful
echo.
goto run_classification_tests

:import_error
echo ERROR: Import test failed
exit /b 1

REM Step 3: Run classification unit tests
:run_classification_tests
echo [4/6] Running classification unit tests (18 tests)...
python scripts/test_rule_classification.py
if errorlevel 1 (
    echo ERROR: Classification tests failed
    exit /b 1
)
echo.

REM Step 4: Run integration tests
echo [5/6] Running integration tests (12 tests)...
python scripts/test_runtime_safety_integration.py
if errorlevel 1 (
    echo ERROR: Integration tests failed
    exit /b 1
)
echo.

REM Step 5: Run extraction tests
echo [6/6] Running extraction tests (regression check)...
python scripts/test_rule_extraction.py
if errorlevel 1 (
    echo ERROR: Extraction tests failed (regression detected)
    exit /b 1
)
echo.

echo ========================================================================
echo ALL TESTS PASSED
echo ========================================================================
echo.
echo Summary:
echo   * Python syntax: [OK]
echo   * Imports: [OK]
echo   * Classification unit tests: [OK] (18 tests)
echo   * Integration tests: [OK] (12 tests)
echo   * Extraction tests: [OK] (no regressions)
echo.
echo Implementation is complete and ready for deployment.
echo.
pause
