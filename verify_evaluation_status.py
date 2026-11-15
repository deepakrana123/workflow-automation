#!/usr/bin/env python3
"""Verify evaluation_status field in BusinessRuleDefinition."""

from app.models.business_rule_definition import BusinessRuleDefinition, RuleEvaluationStatus, _VALID_EVALUATION_STATUSES
from sqlalchemy.inspection import inspect

print('='*70)
print('VERIFICATION: evaluation_status field in BusinessRuleDefinition')
print('='*70)

# Check 1: All five statuses exist
print('\n[1] Five statuses defined:')
statuses = [s.value for s in RuleEvaluationStatus]
expected = ['EVALUABLE', 'INFORMATIONAL', 'PARTIAL', 'UNSUPPORTED', 'INVALID']
all_ok = True
for status in expected:
    exists = status in statuses
    all_ok = all_ok and exists
    marker = "OK" if exists else "MISSING"
    print(f'    {status}: {marker}')
print(f'    Result: {"PASS" if all_ok else "FAIL"}')

# Check 2: Column is nullable
print('\n[2] Column nullability:')
mapper = inspect(BusinessRuleDefinition)
eval_col = mapper.columns['evaluation_status']
nullable_ok = eval_col.nullable is True
print(f'    nullable: {eval_col.nullable}')
print(f'    Result: {"PASS" if nullable_ok else "FAIL"}')

# Check 3: No default marks rules as EVALUABLE
print('\n[3] Default value check:')
default_ok = eval_col.default is None and eval_col.server_default is None
print(f'    default: {eval_col.default}')
print(f'    server_default: {eval_col.server_default}')
print(f'    Result: {"PASS" if default_ok else "FAIL"}')

# Check 4: Existing columns preserved
print('\n[4] Existing columns preserved:')
existing_cols = ['field', 'op', 'value', 'description', 'allowed_roles', 'locked', 'active', 'created_at', 'updated_at']
col_names = [c.name for c in mapper.columns]
cols_ok = True
for col in existing_cols:
    exists = col in col_names
    cols_ok = cols_ok and exists
    marker = "OK" if exists else "MISSING"
    print(f'    {col}: {marker}')
print(f'    Result: {"PASS" if cols_ok else "FAIL"}')

# Check 5: Relationships preserved
print('\n[5] Relationships preserved:')
rel_names = [r.key for r in mapper.relationships]
rel_ok = "workflow_business_rule" in rel_names
marker = "OK" if rel_ok else "MISSING"
print(f'    workflow_business_rule: {marker}')
print(f'    Result: {"PASS" if rel_ok else "FAIL"}')

# Check 6: SQLAlchemy mapper succeeds
print('\n[6] SQLAlchemy mapper configuration:')
try:
    test_instance = BusinessRuleDefinition()
    mapper_ok = callable(test_instance.is_evaluable)
    print('    Instance creation: OK')
    print(f'    is_evaluable() method: {mapper_ok}')
    print(f'    Result: {"PASS" if mapper_ok else "FAIL"}')
except Exception as e:
    print(f'    Instance creation: FAILED - {e}')
    print('    Result: FAIL')
    mapper_ok = False

# Check 7: Column properties
print('\n[7] Column properties:')
print(f'    Type: {eval_col.type}')
print(f'    Index: {eval_col.index}')
print(f'    Indexed: {"OK" if eval_col.index else "MISSING"}')

# Check 8: Verify CHECK constraint
print('\n[8] CHECK constraint:')
try:
    # Get the actual Table object from the mapper
    table = BusinessRuleDefinition.__table__
    constraints = [c.name for c in table.constraints]
    has_ck = 'ck_business_rule_evaluation_status' in constraints
    marker = "OK" if has_ck else "MISSING"
    print(f'    ck_business_rule_evaluation_status: {marker}')
    print(f'    Constraints found: {constraints}')
    print(f'    Result: {"PASS" if has_ck else "FAIL"}')
except Exception as e:
    print(f'    Error checking constraints: {e}')
    has_ck = False
    print('    Result: FAIL')

# Summary
print('\n' + '='*70)
all_pass = all_ok and nullable_ok and default_ok and cols_ok and rel_ok and mapper_ok and has_ck
status = "PASS" if all_pass else "FAIL"
print(f'OVERALL VERIFICATION: {status}')
print('='*70)
