# System Design Interview Questions: Business Rule Evaluability & Runtime Safety

## Context
This session focused on investigating and implementing rule evaluability classification in a banking workflow system that extracts business rules from BRDs (Business Requirements Documents) and evaluates them at runtime.

---

## Section 1: Problem Understanding & Analysis

### Q1: What were the three critical issues discovered in the rule evaluation system?

**Expected Answer:**
1. **Non-evaluable rules silently pass** — Description-only rules (e.g., "Applicant must have proof of address") never block applicants because they lack field/operator/value; they're treated as "pass by default"
2. **Partial rules create gaps in policy enforcement** — Multi-condition rules get partially extracted (e.g., CIBIL extracted but FOIR missed), causing incomplete validation
3. **No audit distinction between evaluable and non-evaluable** — The system treats "rule couldn't be evaluated" the same as "rule was evaluated and passed," making it impossible to audit what policies were actually enforced

---

### Q2: Explain the five categories of business rules identified in the investigation.

**Expected Answer:**

| Category | Example | Field/Op/Value | Runtime Behavior (Before Fix) | Risk Level |
|----------|---------|---|---|---|
| **EVALUABLE** | "CIBIL >= 700" | Present ✅ | Evaluated deterministically | 🟢 None |
| **INFORMATIONAL** | "Proof of address required" | All NULL | Logged as "evaluable=false, result=true" → passes | 🔴 Silently unenforced |
| **PARTIAL** | "Employment >= 2 years" (no field hint) | Some NULL | Falls to non-evaluable → passes | 🔴 Incomplete policy |
| **UNSUPPORTED** | "CIBIL in range [700,800]" | Has value but operator unknown | `evaluate_condition()` returns False | 🔴 Auto-rejects |
| **INVALID** | Type mismatch (value="abc" for numeric op) | Present but malformed | Type coercion fails → False | 🔴 False rejections |

---

### Q3: Walk through a concrete failure scenario: "Applicant must submit 2 years of tax returns."

**Expected Answer:**

**Extraction Phase:**
- LLM output: `rule="Applicant must submit 2 years of tax returns"`, `threshold=None`, `condition=None`
- Heuristic extraction: `_infer_field()` finds no match (no numeric keyword) → `field=None`
- `extract_amounts()` finds no monetary threshold → `value=None`
- Result: `field=None, op=None, value=None`

**Persistence Phase:**
- `BusinessRuleDefinition` created with:
  - `description="Applicant must submit 2 years of tax returns"`
  - `field=NULL, op=NULL, value=NULL`
  - `is_evaluable()=False`

**Runtime Evaluation:**
```python
if not rule.is_evaluable():
    decisions.append({"evaluable": False, "result": True})
    continue  # ← NEVER BLOCKS
```

**Consequence:**
- Applicant with **zero documents** passes the rule ❌
- Policy is silently not enforced
- No audit trail distinguishes this from a properly evaluated rule

---

### Q4: What was the root cause of the "Type Mismatch" issue?

**Expected Answer:**

The `evaluate_condition()` function treats type conversion failure as rule failure:

```python
if op in _NUMERIC_OPS:  # e.g., ">="
    a = _as_number(actual)        # Tries to convert applicant's value
    e = _as_number(expected)      # Tries to convert threshold
    if a is None or e is None:
        return False  # ← Ambiguous: is it bad data or bad applicant?
    return a >= e
```

**Problem:** If the extracted value is stored as `"twelve percent"` instead of `12.0`, and the applicant submitted `"12%"`, both conversions fail, and the rule fails — not because the applicant didn't meet the threshold, but because the system couldn't parse the values.

**Impact:** False rejections. A valid applicant is blocked due to format mismatch, not policy violation.

---

## Section 2: Design & Implementation

### Q5: Why was a `String(32)` column chosen for `evaluation_status` instead of a PostgreSQL enum type?

**Expected Answer:**

1. **Backward compatibility:** Nullable string column allows existing rules (created before this field) to have `NULL` values without migration issues
2. **Application flexibility:** New statuses can be added in application code without a schema migration (just update the enum in Python)
3. **Consistency with project patterns:** Mirrors existing status fields like `IngestionStatus`, `VersionStatus`, and `AttemptStatus` which use `(str, enum.Enum)` pattern
4. **CHECK constraint safety:** The CHECK constraint `evaluation_status IS NULL OR evaluation_status IN (...)` enforces valid values at the database level without requiring a PostgreSQL enum type

---

### Q6: Explain the five RuleEvaluationStatus enum values and when each would be assigned.

**Expected Answer:**

| Value | Assigned When | Example | Runtime Action |
|-------|---|---|---|
| `EVALUABLE` | field, op, value all present and valid | "CIBIL >= 700" | Evaluate deterministically |
| `INFORMATIONAL` | Policy text exists but no execution condition | "Proof of residence required" | Log for reference, never block |
| `PARTIAL` | Some components present but not all | "DPD = 0" (no field hint for DPD) | Escalate for manual review |
| `UNSUPPORTED` | Recognizable pattern but evaluator can't handle it | "CIBIL in range [700, 800]" | Escalate for manual review |
| `INVALID` | Malformed extraction or contradictions | field="score", op=">=", value="text" | Escalate for manual review |

---

### Q7: Why is the `evaluation_status` field nullable instead of defaulting to a specific value?

**Expected Answer:**

1. **Backward compatibility:** Existing rules created before this field was added have no status value. Setting a default would incorrectly classify legacy rules
2. **Explicit classification:** Null represents "unknown/legacy" — forcing a choice (e.g., defaulting to EVALUABLE) could silently misclassify a rule
3. **Migration safety:** Allows the database schema change to be applied without data modifications
4. **Gradual rollout:** New rules get classified; old rules are left alone until explicitly classified by a backfill process

---

### Q8: Describe the CHECK constraint added to the migration and why it's important.

**Expected Answer:**

```sql
CHECK (evaluation_status IS NULL OR evaluation_status IN ('EVALUABLE','INFORMATIONAL','PARTIAL','UNSUPPORTED','INVALID'))
```

**Importance:**
- **Database-level enforcement:** Prevents invalid values from being inserted (e.g., "UNKNOWN" or typos)
- **Data integrity:** Guarantees that if a record has a non-NULL status, it's one of the 5 valid values
- **Application safety:** No need to trust application-layer validation; the DB is the source of truth
- **NULL-safe:** Allows NULL for backward compat with existing records

---

## Section 3: Impact & Architecture

### Q9: How does adding `evaluation_status` fix the "informational rules silently pass" problem?

**Expected Answer:**

**Before:**
```python
for rule in inherited:
    if not rule.is_evaluable():
        decisions.append({"evaluable": False, "result": True})  # ← Passes
        continue
```

**After:**
```python
for rule in inherited:
    status = rule.evaluation_status  # NEW
    
    if status == "INFORMATIONAL":
        # OK — log for reference
        decisions.append({"evaluable": False, "result": True, "reason": "informational"})
    elif status in ("PARTIAL", "UNSUPPORTED", "INVALID"):
        # Requires review — block
        failed_rules.append({
            "rule_id": rule.id,
            "code": f"REQUIRES_REVIEW:{status}",
            "message": rule.description,
        })
        return RuleEvaluationResult(allowed=False, ...)
    elif status == "EVALUABLE":
        # Normal evaluation
        passed = evaluate_condition(rule.op, actual, rule.value)
        # ... rest of logic ...
```

**Result:** Only intentional informational rules pass; everything else escalates for review.

---

### Q10: What files are involved in the complete rule lifecycle, and what does each do?

**Expected Answer:**

| Phase | File | Responsibility |
|-------|------|---|
| **Extraction** | `app/knowledge_ingestions/schemas.py` | LLM output schema (BusinessRule class) |
| **Persistence** | `app/knowledge_ingestions/service.py` | Store raw rule in `WorkflowBusinessRule` |
| **Parsing** | `app/rbac/rule_extractor.py` | Heuristic extraction (field, op, value) + **Classification (NEW)** |
| **Model** | `app/models/business_rule_definition.py` | Structured rule definition + `evaluation_status` (NEW) |
| **Runtime** | `app/runtime/rule_engine.py` | Fetch rules + decision logic + **Routing by status (NEW)** |
| **Evaluation** | `app/execution/rules/evaluator.py` | Condition evaluation (total function, no crashes) |

---

### Q11: What is the contract of `is_evaluable()` and why was it left unchanged?

**Expected Answer:**

**Contract:**
```python
def is_evaluable(self) -> bool:
    """True if this rule can be evaluated by evaluate_condition at runtime."""
    return bool(self.field and self.op and self.value is not None)
```

**Why unchanged:**
1. **Narrow scope:** Only checks if the three components exist and are not None — pure data check
2. **Distinction from status:** `is_evaluable()` answers "does this rule have the necessary pieces?" whereas `evaluation_status` answers "how should this rule be treated at runtime?"
3. **No runtime logic:** Adding status classification to `is_evaluable()` would couple data checking with policy decisions
4. **Backward compat:** Existing callers depend on the current behavior

**Example:**
- A rule with `field=NULL, op=NULL, value=NULL` is NOT evaluable (`is_evaluable()=False`)
- Same rule classified as `evaluation_status="INFORMATIONAL"` means "this is policy text for human reference"
- These are different concerns

---

## Section 4: Testing & Verification

### Q12: Write pseudocode for a test that verifies "Informational rules never block applicants."

**Expected Answer:**

```python
def test_informational_rule_never_blocks():
    # Arrange
    rule = BusinessRuleDefinition(
        field=None,
        op=None,
        value=None,
        description="Applicant must provide proof of address.",
        evaluation_status="INFORMATIONAL",  # Explicitly informational
        active=True,
    )
    db.add(rule)
    db.commit()
    
    ctx = RuleEvaluationContext(
        workspace_id=1,
        user_id="user123",
        facts={},  # No address proof provided
    )
    
    # Act
    engine = RuntimeRuleEngine(db)
    result = engine.evaluate(ctx)
    
    # Assert
    assert result.allowed == True, "Informational rule should never block"
    assert len(result.failed_rules) == 0, "No failed rules"
    assert result.decisions[0]["reason"] == "informational"
```

---

### Q13: Write pseudocode for a test that verifies "Partial rules escalate for manual review."

**Expected Answer:**

```python
def test_partial_rule_escalates():
    # Arrange
    rule = BusinessRuleDefinition(
        field=None,  # Not extractable
        op=None,
        value=None,
        description="DPD = 0 for past 12 months",
        evaluation_status="PARTIAL",  # Recognizable but incomplete
        active=True,
    )
    db.add(rule)
    db.commit()
    
    ctx = RuleEvaluationContext(
        workspace_id=1,
        user_id="user456",
        facts={},
    )
    
    # Act
    engine = RuntimeRuleEngine(db)
    result = engine.evaluate(ctx)
    
    # Assert
    assert result.allowed == False, "Partial rules block (escalate)"
    assert result.failed_rules[0]["code"] == "REQUIRES_REVIEW:PARTIAL"
    assert "DPD" in result.failed_rules[0]["message"]
```

---

## Section 5: Trade-offs & Decisions

### Q14: Why not auto-classify all non-evaluable rules as INFORMATIONAL during extraction?

**Expected Answer:**

Because we don't know the intent:
- Document requirement ("proof of address") → should be INFORMATIONAL
- Failed extraction ("DPD = 0" with no field hint) → should be PARTIAL (needs human review)
- Unsupported pattern ("CIBIL in range X..Y") → should be UNSUPPORTED (known limitation)

Auto-classifying all as INFORMATIONAL would hide bugs in extraction and mask policy gaps. Better to require explicit classification by the extraction service or a human reviewer.

---

### Q15: What are the trade-offs of storing status in the DB vs. computing it at runtime?

**Expected Answer:**

| Approach | Pros | Cons |
|----------|------|------|
| **Store in DB** (chosen) | Immutable audit trail; quick queries by status; explicit intent captured | Extra schema column; requires migration; classification logic must be trusted |
| **Compute at runtime** | Schema-unchanged; classification logic centralized | Repeated computation; no audit trail; inconsistent if logic changes |

**Decision rationale:** Audit trail is more important than schema simplicity. Banking domain requires immutable records.

---

## Section 6: Future Roadmap

### Q16: What are the next three tasks after this change?

**Expected Answer:**

1. **Create Alembic migration** — Apply the schema change to production database
2. **Update RuleExtractionService** — Classify each extracted rule (EVALUABLE / INFORMATIONAL / PARTIAL / UNSUPPORTED / INVALID)
3. **Update RuntimeRuleEngine.evaluate()** — Route non-evaluable rules appropriately (escalate vs. pass)

---

### Q17: How would you implement classification logic in RuleExtractionService?

**Expected Answer:**

```python
def _classify_rule(self, field, op, value, description):
    # Check if fully evaluable
    if field and op and value is not None:
        # Validate type compatibility
        if op in [">=", "<=", ">", "<"]:
            if isinstance(value, (int, float)) or _is_numeric(value):
                return "EVALUABLE"
        else:
            return "EVALUABLE"
        return "INVALID"  # Type mismatch
    
    # Check if informational (pure policy text)
    if not field and not op and not value:
        keywords = ["must", "should", "requirement", "policy", "need"]
        if any(kw in description.lower() for kw in keywords):
            return "INFORMATIONAL"
        return "PARTIAL"  # Unclear what failed
    
    # Partial extraction (some pieces present)
    if (field and not op) or (op and not value) or (value and not field):
        return "PARTIAL"
    
    # Known unsupported pattern
    if op and op not in SUPPORTED_OPERATORS:
        return "UNSUPPORTED"
    
    return None  # Unclassified
```

---

### Q18: How would the audit trail use `evaluation_status` for compliance reporting?

**Expected Answer:**

```python
# Compliance report: "Which policies were actually enforced for this applicant?"

def get_enforced_policies(workflow_execution_id):
    decisions = (
        db.query(RuleDecision)
        .filter(RuleDecision.execution_id == workflow_execution_id)
        .all()
    )
    
    # Evaluated and passed ✅
    passed = [d for d in decisions if d.rule.evaluation_status == "EVALUABLE" and d.result == True]
    
    # Evaluated and failed ❌
    failed = [d for d in decisions if d.rule.evaluation_status == "EVALUABLE" and d.result == False]
    
    # Informational (for reference) 📌
    info = [d for d in decisions if d.rule.evaluation_status == "INFORMATIONAL"]
    
    # Escalated (requires review) ⚠️
    escalated = [d for d in decisions if d.rule.evaluation_status in ("PARTIAL", "UNSUPPORTED", "INVALID")]
    
    return {
        "passed_rules": len(passed),
        "failed_rules": len(failed),
        "informational": len(info),
        "escalated": len(escalated),
        "fully_evaluated": len(passed) + len(failed),
    }
```

This provides clear audit evidence of what was evaluated vs. what required human review.

---

## Section 7: System Design Principles

### Q19: How does this change reflect the "fail closed" principle in banking systems?

**Expected Answer:**

**Fail Closed Principle:** When in doubt, deny (don't auto-approve).

**Before:** Non-evaluable rules were silently passing applicants (fail open ❌)

**After:** Non-evaluable rules are escalated for manual review or block applicant (fail closed ✅)

This is critical for banking:
- A document requirement you couldn't evaluate should escalate, not auto-pass
- An unsupported rule pattern should escalate, not auto-pass
- Only explicitly classified informational rules auto-pass

---

### Q20: Explain the separation of concerns between extraction, classification, and evaluation.

**Expected Answer:**

| Concern | Responsibility | Input | Output |
|---------|---|---|---|
| **Extraction** | Parse unstructured text → structured fields | Raw rule text | field, op, value |
| **Classification** | Determine how to treat the rule at runtime | field, op, value + description | evaluation_status |
| **Evaluation** | Execute the rule logic against applicant facts | evaluation_status + facts | allowed/blocked decision |

**Benefits:**
- Each layer has a single responsibility
- Classification logic is independent of evaluation logic
- Extraction can improve without changing evaluation
- New statuses can be added without modifying evaluation code

---

## Summary Questions

### Q21: In one paragraph, explain what problem this session solved.

**Expected Answer:**

The system was extracting business rules from documents and evaluating them at runtime, but it couldn't distinguish between rules that were fully evaluated vs. rules that couldn't be evaluated. This caused three problems: informational policies were silently unenforced, partial extractions missed policy conditions entirely, and unsupported rules auto-rejected all applicants. We added an `evaluation_status` field to classify each rule's evaluability and runtime behavior (EVALUABLE, INFORMATIONAL, PARTIAL, UNSUPPORTED, INVALID), enabling the runtime engine to escalate unclear rules for manual review instead of silently passing or falsely rejecting applicants.

---

### Q22: What is the most important invariant that `evaluation_status` preserves?

**Expected Answer:**

**Invariant:** "A rule can only block an applicant if its evaluation_status is EVALUABLE and it was deterministically evaluated."

This ensures that:
- Applicants aren't falsely rejected due to malformed extractions
- Policies aren't silently ignored due to incomplete information
- Every block decision is traceable to either a failed condition or an explicit escalation
