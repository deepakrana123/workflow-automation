"""
scripts/test_runtime_safety_integration.py

Integration tests for RuntimeRuleEngine classification-based safety.

Tests verify:
1. Classification function works for all 5 categories
2. Status field is correctly set
3. Step-level rules respect classification
4. to_dict() includes status
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rbac.rule_extractor import _classify_rule
from app.runtime.context import RuleEvaluationResult
from app.execution.rules.step_rule_evaluator import evaluate_step_rules, build_metadata_entry
from app.models.business_rule_definition import RuleEvaluationStatus


def test_1_evaluable_classification():
    """Test 1: EVALUABLE classification for complete rule."""
    result = _classify_rule(
        field="credit_score",
        op=">=",
        value=700,
        description="Credit score must be at least 700"
    )
    assert result == RuleEvaluationStatus.EVALUABLE, f"Expected EVALUABLE, got {result}"
    print("✓ Test 1: EVALUABLE classification for complete rule")


def test_2_informational_classification():
    """Test 2: INFORMATIONAL classification for all-null rule."""
    result = _classify_rule(
        field=None,
        op=None,
        value=None,
        description="It is a requirement that applicants must submit documents"
    )
    assert result == RuleEvaluationStatus.INFORMATIONAL, f"Expected INFORMATIONAL, got {result}"
    print("✓ Test 2: INFORMATIONAL classification for all-null rule")


def test_3_partial_classification():
    """Test 3: PARTIAL classification for incomplete rule."""
    result = _classify_rule(
        field="loan_amount",
        op=">=",
        value=None,
        description="Loan amount must be above threshold"
    )
    assert result == RuleEvaluationStatus.PARTIAL, f"Expected PARTIAL, got {result}"
    print("✓ Test 3: PARTIAL classification for incomplete rule")


def test_4_unsupported_classification():
    """Test 4: UNSUPPORTED classification for bad operator."""
    result = _classify_rule(
        field="loan_amount",
        op="range",
        value=(500000, 1000000),
        description="Loan in range"
    )
    assert result == RuleEvaluationStatus.UNSUPPORTED, f"Expected UNSUPPORTED, got {result}"
    print("✓ Test 4: UNSUPPORTED classification for bad operator")


def test_5_invalid_classification():
    """Test 5: INVALID classification for type mismatch."""
    result = _classify_rule(
        field="credit_score",
        op=">=",
        value="excellent",
        description="Credit score excellent"
    )
    assert result == RuleEvaluationStatus.INVALID, f"Expected INVALID, got {result}"
    print("✓ Test 5: INVALID classification for type mismatch")


def test_6_result_status_field():
    """Test 6: RuleEvaluationResult includes status field."""
    result = RuleEvaluationResult(
        allowed=False,
        status="REVIEW_REQUIRED",
        decisions=[],
        failed_rules=[],
        warnings=[]
    )
    assert result.status == "REVIEW_REQUIRED"
    assert hasattr(result, 'status'), "Result must have status field"
    print("✓ Test 6: RuleEvaluationResult includes status field")


def test_7_result_to_dict_includes_status():
    """Test 7: to_dict() includes status."""
    result = RuleEvaluationResult(
        allowed=False,
        status="FAIL",
        decisions=[],
        failed_rules=[],
        warnings=[]
    )
    d = result.to_dict()
    assert "status" in d, "to_dict() must include status"
    assert d["status"] == "FAIL"
    print("✓ Test 7: to_dict() includes status")


def test_8_step_evaluable_rule():
    """Test 8: Step-level EVALUABLE rule evaluation."""
    step_def = {
        "id": "step_1",
        "action": "review",
        "business_rules": [
            {
                "field": "credit_score",
                "op": ">=",
                "value": 700,
                "description": "Score check"
            }
        ]
    }
    context_outputs = {"credit_score": 750}
    result = evaluate_step_rules(step_def, context_outputs)
    
    assert result.passed == True
    assert len(result.evaluations) == 1
    assert result.evaluations[0].evaluable == True
    assert result.evaluations[0].classification == "EVALUABLE"
    print("✓ Test 8: Step-level EVALUABLE rule passes when satisfied")


def test_9_step_non_evaluable_rule():
    """Test 9: Step-level non-evaluable rule halts."""
    step_def = {
        "id": "step_1",
        "action": "review",
        "business_rules": [
            {
                "field": None,
                "op": None,
                "value": None,
                "description": "Information only"
            }
        ]
    }
    context_outputs = {}
    result = evaluate_step_rules(step_def, context_outputs)
    
    assert result.passed == False
    assert result.blocking_rule is not None
    assert result.blocking_rule.evaluable == False
    assert result.blocking_rule.classification == "INFORMATIONAL"
    print("✓ Test 9: Step-level non-evaluable rule halts execution")


def test_10_step_evaluable_fail():
    """Test 10: Step-level EVALUABLE rule fails when not satisfied."""
    step_def = {
        "id": "step_1",
        "action": "review",
        "business_rules": [
            {
                "field": "credit_score",
                "op": ">=",
                "value": 700,
                "description": "Score check"
            }
        ]
    }
    context_outputs = {"credit_score": 650}  # Below threshold
    result = evaluate_step_rules(step_def, context_outputs)
    
    assert result.passed == False
    assert result.blocking_rule is not None
    assert result.blocking_rule.evaluable == True
    assert result.blocking_rule.result == False
    print("✓ Test 10: Step-level EVALUABLE rule fails when not satisfied")


def test_11_step_rule_metadata_includes_classification():
    """Test 11: Step metadata includes classification."""
    step_def = {
        "id": "step_1",
        "action": "review",
        "business_rules": [
            {
                "field": "credit_score",
                "op": ">=",
                "value": 700,
                "description": "Score check"
            }
        ]
    }
    context_outputs = {"credit_score": 750}
    eval_result = evaluate_step_rules(step_def, context_outputs)
    metadata = build_metadata_entry(eval_result)
    
    assert "passed" in metadata
    assert "evaluations" in metadata
    assert len(metadata["evaluations"]) == 1
    assert "classification" in metadata["evaluations"][0]
    assert metadata["evaluations"][0]["classification"] == "EVALUABLE"
    print("✓ Test 11: Step metadata includes classification")


def test_12_classification_never_misclassifies_evaluable():
    """Test 12: Non-evaluable rules never classified as EVALUABLE."""
    non_evaluable_cases = [
        (None, None, None, "info"),
        ("field", None, None, "partial1"),
        (None, ">=", None, "partial2"),
        (None, None, 100, "partial3"),
        ("field", "range", (1, 10), "unsupported"),
        ("field", ">=", "text", "invalid"),
    ]
    
    for field, op, value, desc in non_evaluable_cases:
        result = _classify_rule(field, op, value, desc)
        assert result != RuleEvaluationStatus.EVALUABLE, \
            f"Non-evaluable rule misclassified as EVALUABLE: {field}/{op}/{value}"
    
    print("✓ Test 12: Non-evaluable rules never misclassified as EVALUABLE")


def run_all_tests():
    """Run all integration tests."""
    tests = [
        test_1_evaluable_classification,
        test_2_informational_classification,
        test_3_partial_classification,
        test_4_unsupported_classification,
        test_5_invalid_classification,
        test_6_result_status_field,
        test_7_result_to_dict_includes_status,
        test_8_step_evaluable_rule,
        test_9_step_non_evaluable_rule,
        test_10_step_evaluable_fail,
        test_11_step_rule_metadata_includes_classification,
        test_12_classification_never_misclassifies_evaluable,
    ]
    
    print("\n" + "="*70)
    print("RUNTIME SAFETY INTEGRATION TEST SUITE")
    print("="*70 + "\n")
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
