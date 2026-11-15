"""
scripts/test_rule_classification.py

Comprehensive test suite for rule evaluation classification.

Tests the _classify_rule() function from app.rbac.rule_extractor to verify:
1. EVALUABLE: field, op, value all present; op supported; value type compatible
2. INFORMATIONAL: all three components NULL; description contains policy keywords
3. PARTIAL: some components present but not all
4. UNSUPPORTED: field + op where op ∉ SUPPORTED_OPERATORS
5. INVALID: type mismatch (e.g., op=">=", value="text")
6. Idempotency: multiple calls with same inputs produce same output
7. Provenance separation: no cross-contamination between different rules
8. Non-EVALUABLE rules never misclassified as EVALUABLE
"""

import sys
import os

# Add the project root to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rbac.rule_extractor import _classify_rule
from app.models.business_rule_definition import RuleEvaluationStatus
from app.execution.rules.evaluator import SUPPORTED_OPERATORS


def test_evaluable_numeric_threshold():
    """Test 1: EVALUABLE classification for numeric threshold with supported operator."""
    result = _classify_rule(
        field="credit_score",
        op=">=",
        value=700.0,
        description="Credit score must be at least 700"
    )
    assert result == RuleEvaluationStatus.EVALUABLE, \
        f"Expected EVALUABLE, got {result}"
    print("✓ Test 1: EVALUABLE for numeric threshold with supported operator")


def test_evaluable_with_integer_value():
    """Test 1b: EVALUABLE works with integer value for numeric operators."""
    result = _classify_rule(
        field="applicant_age",
        op="<=",
        value=65,
        description="Applicant age must not exceed 65"
    )
    assert result == RuleEvaluationStatus.EVALUABLE, \
        f"Expected EVALUABLE, got {result}"
    print("✓ Test 1b: EVALUABLE for integer value with numeric operator")


def test_evaluable_with_string_numeric_value():
    """Test 1c: EVALUABLE works when value is numeric string with numeric operator."""
    result = _classify_rule(
        field="loan_amount",
        op=">=",
        value="500000",
        description="Loan amount must be at least 500000"
    )
    assert result == RuleEvaluationStatus.EVALUABLE, \
        f"Expected EVALUABLE, got {result}"
    print("✓ Test 1c: EVALUABLE for numeric string value with numeric operator")


def test_evaluable_equality_operator():
    """Test 1d: EVALUABLE for equality operator (non-numeric)."""
    result = _classify_rule(
        field="employment_status",
        op="==",
        value="employed",
        description="Employment status must be employed"
    )
    assert result == RuleEvaluationStatus.EVALUABLE, \
        f"Expected EVALUABLE, got {result}"
    print("✓ Test 1d: EVALUABLE for equality operator with string value")


def test_informational_all_nulls_with_keywords():
    """Test 2: INFORMATIONAL classification when all components NULL and keywords present."""
    result = _classify_rule(
        field=None,
        op=None,
        value=None,
        description="It is a requirement that applicants must submit all required documents."
    )
    assert result == RuleEvaluationStatus.INFORMATIONAL, \
        f"Expected INFORMATIONAL, got {result}"
    print("✓ Test 2: INFORMATIONAL for all-null components with policy keywords")


def test_informational_all_nulls_no_keywords():
    """Test 2b: INFORMATIONAL fallback when all components NULL regardless of keywords."""
    result = _classify_rule(
        field=None,
        op=None,
        value=None,
        description="Some random note about the loan process."
    )
    assert result == RuleEvaluationStatus.INFORMATIONAL, \
        f"Expected INFORMATIONAL, got {result}"
    print("✓ Test 2b: INFORMATIONAL fallback for all-null with no keywords")


def test_informational_various_keywords():
    """Test 2c: INFORMATIONAL recognizes various policy keywords."""
    keywords = [
        ("The policy states that applicants...", "policy"),
        ("Branch managers should review files...", "should"),
        ("All documents shall be verified...", "shall"),
        ("The mandate requires two references...", "mandate"),
        ("This is a condition for approval...", "condition"),
    ]
    for desc, keyword in keywords:
        result = _classify_rule(
            field=None,
            op=None,
            value=None,
            description=desc
        )
        assert result == RuleEvaluationStatus.INFORMATIONAL, \
            f"Expected INFORMATIONAL for '{keyword}', got {result}"
    print("✓ Test 2c: INFORMATIONAL recognizes various policy keywords")


def test_partial_field_only():
    """Test 3: PARTIAL when only field is present."""
    result = _classify_rule(
        field="credit_score",
        op=None,
        value=None,
        description="Something about credit score"
    )
    assert result == RuleEvaluationStatus.PARTIAL, \
        f"Expected PARTIAL, got {result}"
    print("✓ Test 3: PARTIAL when only field is present")


def test_partial_field_and_op():
    """Test 3b: PARTIAL when field and op present but value missing."""
    result = _classify_rule(
        field="loan_amount",
        op=">=",
        value=None,
        description="Loan amount must be above some threshold"
    )
    assert result == RuleEvaluationStatus.PARTIAL, \
        f"Expected PARTIAL, got {result}"
    print("✓ Test 3b: PARTIAL when field and op present but value missing")


def test_partial_op_and_value():
    """Test 3c: PARTIAL when op and value present but field missing."""
    result = _classify_rule(
        field=None,
        op=">=",
        value=500000,
        description="Must be at least 500000"
    )
    assert result == RuleEvaluationStatus.PARTIAL, \
        f"Expected PARTIAL, got {result}"
    print("✓ Test 3c: PARTIAL when op and value present but field missing")


def test_unsupported_operator():
    """Test 4: UNSUPPORTED when operator is not in SUPPORTED_OPERATORS."""
    result = _classify_rule(
        field="loan_amount",
        op="range",  # Not a supported operator
        value=(500000, 1000000),
        description="Loan amount should be in range 5-10 lakh"
    )
    assert result == RuleEvaluationStatus.UNSUPPORTED, \
        f"Expected UNSUPPORTED, got {result}"
    print("✓ Test 4: UNSUPPORTED for unsupported operator")


def test_unsupported_with_partial_components():
    """Test 4b: UNSUPPORTED when field+op present but op not supported (partial case)."""
    result = _classify_rule(
        field="credit_score",
        op="composite",  # Not supported
        value=None,
        description="Credit score must pass multiple checks"
    )
    assert result == RuleEvaluationStatus.UNSUPPORTED, \
        f"Expected UNSUPPORTED, got {result}"
    print("✓ Test 4b: UNSUPPORTED for unsupported operator with partial components")


def test_invalid_numeric_op_with_string_value():
    """Test 5: INVALID when numeric operator used with non-numeric string value."""
    result = _classify_rule(
        field="credit_score",
        op=">=",
        value="excellent",  # Can't be coerced to number
        description="Credit score must be excellent"
    )
    assert result == RuleEvaluationStatus.INVALID, \
        f"Expected INVALID, got {result}"
    print("✓ Test 5: INVALID for numeric operator with non-numeric string value")


def test_invalid_numeric_op_with_bool():
    """Test 5b: INVALID when numeric operator used with boolean value."""
    result = _classify_rule(
        field="has_income",
        op=">=",
        value=True,
        description="Income check must be true"
    )
    assert result == RuleEvaluationStatus.INVALID, \
        f"Expected INVALID, got {result}"
    print("✓ Test 5b: INVALID for numeric operator with boolean value")


def test_invalid_numeric_op_with_list():
    """Test 5c: INVALID when numeric operator used with list value."""
    result = _classify_rule(
        field="income",
        op=">",
        value=[10000, 20000, 30000],
        description="Income must be greater than threshold list"
    )
    assert result == RuleEvaluationStatus.INVALID, \
        f"Expected INVALID, got {result}"
    print("✓ Test 5c: INVALID for numeric operator with list value")


def test_idempotency():
    """Test 6: Idempotency — multiple calls with same inputs always produce same output."""
    test_cases = [
        ("credit_score", ">=", 700, "Credit score threshold"),
        (None, None, None, "Policy text"),
        ("loan_amount", ">=", None, "Incomplete extraction"),
        ("age", "beyond", 65, "Unsupported operator"),
    ]
    
    for field, op, value, desc in test_cases:
        results = [
            _classify_rule(field, op, value, desc),
            _classify_rule(field, op, value, desc),
            _classify_rule(field, op, value, desc),
        ]
        assert len(set(results)) == 1, \
            f"Idempotency failed for {field}/{op}/{value}: got {results}"
    
    print("✓ Test 6: Idempotency verified across multiple calls")


def test_provenance_separation():
    """Test 7: Provenance separation — different rules don't contaminate each other."""
    # Rule 1: EVALUABLE
    rule1 = _classify_rule("credit_score", ">=", 700, "Rule 1: Credit check")
    # Rule 2: INFORMATIONAL
    rule2 = _classify_rule(None, None, None, "Rule 2: Policy text must be followed")
    # Rule 3: PARTIAL
    rule3 = _classify_rule("loan_amount", ">=", None, "Rule 3: Incomplete")
    # Rule 4: INVALID
    rule4 = _classify_rule("age", ">=", "young", "Rule 4: Bad extraction")
    
    # Call rule 1 again to ensure rule 2-4 didn't affect it
    rule1_again = _classify_rule("credit_score", ">=", 700, "Rule 1: Credit check")
    
    assert rule1 == rule1_again == RuleEvaluationStatus.EVALUABLE
    assert rule2 == RuleEvaluationStatus.INFORMATIONAL
    assert rule3 == RuleEvaluationStatus.PARTIAL
    assert rule4 == RuleEvaluationStatus.INVALID
    
    print("✓ Test 7: Provenance separation verified — no cross-contamination")


def test_non_evaluable_never_classified_as_evaluable():
    """Test 8: Non-EVALUABLE rules are NEVER misclassified as EVALUABLE."""
    non_evaluable_cases = [
        # INFORMATIONAL cases
        (None, None, None, "Policy text with must keyword"),
        (None, None, None, "Random description"),
        
        # PARTIAL cases
        ("field", None, None, "Field only"),
        (None, ">=", None, "Operator only"),
        (None, None, 100, "Value only"),
        ("field", ">=", None, "Field + op only"),
        
        # UNSUPPORTED cases
        ("field", "range", (1, 10), "Unsupported operator"),
        ("field", "composite", None, "Unsupported op, partial components"),
        
        # INVALID cases
        ("field", ">=", "text", "Non-numeric value with numeric op"),
        ("field", ">=", True, "Boolean value with numeric op"),
        ("field", ">", [1, 2, 3], "List value with numeric op"),
    ]
    
    for field, op, value, desc in non_evaluable_cases:
        result = _classify_rule(field, op, value, desc)
        assert result != RuleEvaluationStatus.EVALUABLE, \
            f"Rule MISCLASSIFIED as EVALUABLE: field={field}, op={op}, value={value}"
    
    print("✓ Test 8: Non-EVALUABLE rules NEVER misclassified as EVALUABLE")


def run_all_tests():
    """Run all test cases and report results."""
    tests = [
        test_evaluable_numeric_threshold,
        test_evaluable_with_integer_value,
        test_evaluable_with_string_numeric_value,
        test_evaluable_equality_operator,
        test_informational_all_nulls_with_keywords,
        test_informational_all_nulls_no_keywords,
        test_informational_various_keywords,
        test_partial_field_only,
        test_partial_field_and_op,
        test_partial_op_and_value,
        test_unsupported_operator,
        test_unsupported_with_partial_components,
        test_invalid_numeric_op_with_string_value,
        test_invalid_numeric_op_with_bool,
        test_invalid_numeric_op_with_list,
        test_idempotency,
        test_provenance_separation,
        test_non_evaluable_never_classified_as_evaluable,
    ]
    
    print("\n" + "="*70)
    print("RULE CLASSIFICATION TEST SUITE")
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
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
