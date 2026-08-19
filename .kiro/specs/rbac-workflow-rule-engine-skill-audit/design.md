# Design Document — RBAC, Rule Engine, Multi-Level Rules, and Skill Files

## Overview

This document audits how four systems should be built and integrated into MFlows. The work is additive — every new layer wraps or extends what already exists, nothing in the execution core changes.

The key conceptual shift: **business rules are not just conditions, they are the source of RBAC**. When a BRD says "approval required above ₹5 lakh by Branch Manager", that sentence contains the rule (threshold), the actor (Branch Manager), and the permission boundary in a single clause. The rule engine extracts all three. RBAC is not a separate config file — it is derived from the rules the bank already wrote.

The flow end-to-end:

```
BRD upload
  → Gemini extraction (already exists)
  → WorkflowKnowledge + WorkflowBusinessRule + WorkflowActor (already exists)
        ↓
  RuleExtractionService  ← NEW: parses actors + thresholds from business rules
        ↓
  BusinessRuleDefinition rows (scoped to workspace level)
        ↓
  RoleAssignment rows (derived from actors in the rules)
        ↓
  Workspace-scoped workflow generation (already exists)
        ↓
  Compiled DAG — steps carry business_rules[] array  ← NEW layer in compiler
        ↓
  Workflow publication gate  ← NEW: RBAC check + conflict check + role coverage
        ↓
  skill.md generated deterministically  ← NEW: from DAG + actors + rules
        ↓
  FileStorageService.store() (already exists)
```

---

## Architecture Layers to Add

Four new layers sit on top of the existing stack. None of them touch the execution core.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Layer 4 — Skill File Generator                                         │
│  Reads published DAG + actors + rules → produces skill.md               │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 3 — Publication Gate                                             │
│  RBAC check + role coverage + conflict-free before status → published   │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 2 — Multi-Level Rule Engine                                      │
│  Ancestor-chain rule resolution. Inherited rules flow down.             │
│  Extracted RBAC roles stored as RoleAssignments.                        │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 1 — Workspace Hierarchy                                          │
│  workspaces gains level + parent_id. Single-table, self-referential.   │
├─────────────────────────────────────────────────────────────────────────┤
│  EXISTING — BRD ingestion, NLP pipeline, DAG compiler, executor stack   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Layer 1 — Workspace Hierarchy

### What needs to change

The `Workspace` model is currently flat. It needs two new columns:

| Column | Type | Notes |
|---|---|---|
| `level` | `String(20)` | Enum: `global`, `region`, `zone`, `branch` |
| `parent_id` | `Integer FK → workspaces.id` | Null only when `level = global` |

Constraint logic (enforced at service layer, not just DB):
- `region` parent must be `global`
- `zone` parent must be `region`
- `branch` parent must be `zone`
- Exactly one workspace may have `level = global` per deployment

Ancestor-chain traversal (pure function, no DB needed at call time):

```
get_ancestors(workspace_id, all_workspaces_dict) → [global_id, region_id, zone_id]
```

This is used by both the rule engine (to collect inherited rules) and RBAC (to resolve upstream permissions). It walks `parent_id` upward until `level = global`.

### Migration path

Alembic migration:
1. Add `level VARCHAR(20) DEFAULT 'branch'` (nullable initially)
2. Add `parent_id INTEGER REFERENCES workspaces(id)` (nullable)
3. Backfill existing workspaces as `level = branch`, `parent_id = NULL`
4. Add partial unique index: `WHERE level = 'global'` on the `level` column

Existing workspaces are unaffected at runtime — their `level = branch`, `parent_id = NULL`. No execution behavior changes.

---

## Layer 2 — Multi-Level Rule Engine + RBAC Extraction

This is the core architectural addition. It has three sub-components.

### 2a — Rule Extraction from Business Rules

Today, `WorkflowBusinessRule` stores raw text extracted by Gemini. The new `RuleExtractionService` parses these raw strings into structured `BusinessRuleDefinition` rows. It reuses the existing `extract_amounts` and `subject_key` utilities from `rule_conflicts.py`.

**New table: `business_rule_definitions`**

| Column | Type | Purpose |
|---|---|---|
| `id` | Integer PK | |
| `scope_workspace_id` | FK → workspaces.id | Level at which this rule was declared |
| `source_workflow_knowledge_id` | FK → workflow_knowledge.id | Which BRD it came from |
| `field` | String | The output field this rule checks (e.g. `loan_amount`) |
| `op` | String | Operator from `evaluate_condition`: `>=`, `<=`, `==`, `in`, etc. |
| `value` | JSONB | The threshold value (numeric, string, or list) |
| `description` | Text | Human-readable form of the rule (original BRD sentence) |
| `allowed_roles` | JSONB | Roles extracted from the same sentence (see 2b below) |
| `locked` | Boolean | If true, lower levels cannot narrow or reference this rule |
| `active` | Boolean | |
| `created_at` | DateTime | |

**What `RuleExtractionService` does:**

1. Takes `WorkflowBusinessRule` rows for a workspace
2. For each rule text, calls `extract_amounts()` to detect numeric thresholds
3. Uses a simple pattern match for role mentions: looks for actor names that appear in `WorkflowActor` rows for the same `WorkflowKnowledge`
4. Produces a `BusinessRuleDefinition` row per extractable rule
5. Rules that cannot be structured (no threshold, no field reference) are kept as description-only rows — they still flow into skill.md but are not evaluated at runtime

Example: BRD text `"Loan disbursement above ₹5 lakh requires Branch Manager approval"`

Extracted:
- `field`: `loan_amount`
- `op`: `>=`
- `value`: 500000
- `description`: "Loan disbursement above ₹5 lakh requires Branch Manager approval"
- `allowed_roles`: `["branch_manager"]`

### 2b — RBAC Extraction from Rules

RBAC is not configured manually. It is derived from the actors and rules extracted from BRDs.

**New table: `role_assignments`**

| Column | Type | Purpose |
|---|---|---|
| `id` | Integer PK | |
| `user_id` | String | The user this assignment belongs to (null = unassigned, pending HR mapping) |
| `role` | String | One of the 7 defined roles (see role catalogue below) |
| `workspace_id` | FK → workspaces.id | The workspace this role is scoped to |
| `source_rule_id` | FK → business_rule_definitions.id (nullable) | Which rule caused this role to be extracted |
| `active` | Boolean | |
| `created_at` | DateTime | |

**Role Catalogue (static, not user-configurable):**

| Role | Min workspace level | Key permissions |
|---|---|---|
| `global_admin` | global | all |
| `region_manager` | region | workflow:publish, rule:create, rule:override, humantask:resolve |
| `zone_manager` | zone | workflow:publish, rule:create, humantask:resolve |
| `branch_manager` | branch | workflow:publish, rule:create, humantask:resolve |
| `branch_officer` | branch | workflow:read, humantask:resolve |
| `auditor` | any | workflow:read, rule:read, audit:read, humantask:read |
| `read_only` | any | workflow:read, rule:read |

**Full permission matrix:**

| Permission | global_admin | region_manager | zone_manager | branch_manager | branch_officer | auditor | read_only |
|---|---|---|---|---|---|---|---|
| `workflow:read` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `workflow:create` | ✓ | ✓ | ✓ | ✓ | | | |
| `workflow:publish` | ✓ | ✓ | ✓ | ✓ | | | |
| `workflow:delete` | ✓ | ✓ | | | | | |
| `rule:read` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `rule:create` | ✓ | ✓ | ✓ | ✓ | | | |
| `rule:override` | ✓ | ✓ | ✓ | ✓ | | | |
| `humantask:resolve` | ✓ | ✓ | ✓ | ✓ | ✓ | | |
| `humantask:escalate` | ✓ | ✓ | ✓ | ✓ | | | |
| `humantask:read` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| `audit:read` | ✓ | ✓ | ✓ | ✓ | | ✓ | |
| `admin:manage_roles` | ✓ | | | | | | |

**How actor names map to roles:**

`WorkflowActor.actor_name` → fuzzy match to role catalogue:
- "branch manager" → `branch_manager`
- "zone officer" → `zone_manager`
- "regional head" → `region_manager`
- "compliance" / "auditor" → `auditor`

This mapping lives in a configurable dict in `RuleExtractionService`. Unmapped actors produce a `read_only` role assignment flagged for human review.

**Key design decision:** `role_assignments.user_id` starts as NULL. The platform creates the role shapes from rules; actual user mapping (connecting a real person's user ID to a role+workspace) is done separately, either via HR integration or admin UI. This means RBAC is "ready" as soon as BRDs are ingested — it just needs users assigned.

### 2c — Ancestor-Chain Rule Resolution

When the execution engine needs the effective rule set for a step in workspace W:

```
resolve_effective_rules(workspace_id, field) →
  1. Walk ancestors: [global_id, region_id, zone_id, branch_id = workspace_id]
  2. Query BusinessRuleDefinition WHERE scope_workspace_id IN (ancestor_ids)
     AND field = field AND active = true
  3. Order by level: global rules first, branch rules last
  4. Return ordered list
```

At runtime, the step evaluator applies rules in this order. A rule from global cannot be loosened by a rule at branch. If a branch rule references the same field as a global rule but with a less-restrictive threshold, the `RuleValidationService` rejects it at write time.

**Write-time restriction check (pure function):**

```
is_more_restrictive(new_rule, inherited_rule) → bool
  - For >=: new_value >= inherited_value   (higher lower-bound = more restrictive)
  - For <=: new_value <= inherited_value   (lower upper-bound = more restrictive)
  - For in: new_set ⊆ inherited_set        (smaller set = more restrictive)
  - For ==: must be same value
```

If `is_more_restrictive` returns False, the rule store rejects the write with a conflict error and logs it to `audit_logs`.

**Conflict detection across levels:**

The existing `detect_rule_conflicts()` function runs on the full effective rule set (all ancestor levels) when any rule is written. This catches cross-level threshold conflicts (e.g. global says `>= 500000`, zone says `>= 300000` — that's a relaxation, rejected). Within-level conflicts (two rules at the same level with different thresholds for the same subject) also surface as `review_flags`.

### 2d — HumanTask role extensions

The existing `HumanTask` model needs two new JSONB columns:

| Column | Type | Purpose |
|---|---|---|
| `allowed_roles` | JSONB array of strings | Roles that may resolve this task |
| `escalation_policy` | JSONB | `{timeout_minutes, escalate_to_role, max_escalation_levels}` |
| `escalation_level` | Integer | Current escalation depth, starts at 0 |

These are populated at HumanTask creation from the `allowed_roles` on the `BusinessRuleDefinition` that governs the step. The escalation reaper (already exists for timeout handling) is extended to increment `escalation_level` and update `allowed_roles` when `timeout_at` is reached.

---

## Layer 3 — Workflow Steps with Business Rules + Publication Gate

### 3a — Business Rules in the Compiled DAG

Today a compiled step looks like:

```json
{"id": "s1", "action": "approve_loan", "depends_on": [], "routing": {...}}
```

After this change, steps optionally carry:

```json
{
  "id": "s1",
  "action": "approve_loan",
  "depends_on": [],
  "routing": {...},
  "business_rules": [
    {
      "rule_id": 42,
      "field": "loan_amount",
      "op": ">=",
      "value": 500000,
      "description": "Loan disbursement above ₹5 lakh requires Branch Manager approval",
      "scope_workspace_id": 3,
      "allowed_roles": ["branch_manager"]
    }
  ]
}
```

**How rules get into steps:**

During workspace-scoped workflow generation (`generate_workspace_workflow_service`), the v2 prompt already receives business rules as text. After compilation, a new `RuleInjector` post-processes the compiled DAG:

1. For each step, look up `BusinessRuleDefinition` rows that match the step's action name or that reference fields in the action's `output_schema`
2. Attach matched rules to `step["business_rules"]`
3. The existing `ASTValidator` already checks `output_schema` fields — the new step validator also checks that every `field` in `business_rules` is resolvable from preceding step outputs or WorkflowContext

This is a post-compilation hook, not a change to the compiler itself. The compiler stays untouched.

### 3b — Rule Evaluation at Step Execution

Before a step executes, a new `StepRuleEvaluator` runs:

```
StepRuleEvaluator.evaluate(step, workflow_context) →
  for each rule in step["business_rules"]:
    actual = workflow_context.outputs.get(rule["field"])
    result = evaluate_condition(rule["op"], actual, rule["value"])  ← reused unchanged
    record to ExecutionStep.metadata["rule_evaluations"]
    if not result: return BLOCKED(rule)
  return PASS
```

On BLOCKED:
- `ExecutionStep.status` → `RULE_BLOCKED` (new status, not FAILED)
- Retry logic does NOT fire (a blocked step is a policy hold, not a transient error)
- AuditLog entry: `execution_step_rule_blocked` with rule_id, field, actual value, threshold
- DAG pauses at this step — downstream steps do not execute

On PASS:
- Normal execution continues, no extra log entry

`RULE_BLOCKED` is cleared only by:
1. An authorized user with `rule:override` overriding the rule (new API endpoint)
2. The workflow being cancelled

### 3c — Publication Gate

`WorkflowPublicationService.publish(workflow_id, caller_user_id)` runs three checks atomically before setting `status = published`:

**Check 1 — RBAC permission**
Caller must hold `workflow:publish` in the workflow's workspace or any ancestor workspace.

**Check 2 — HumanTask role coverage**
Every step with `execution_type = human_task` in `parsed_rule_json` must have at least one entry in `allowed_roles`. Empty `allowed_roles` = publication blocked.

**Check 3 — Zero unresolved rule conflicts**
`detect_rule_conflicts()` runs on the full effective rule set of the workspace. Any unresolved `threshold_conflict` = publication blocked.

If any check fails, the API returns a structured error:
```json
{
  "blocked": true,
  "reasons": [
    {"check": "human_task_roles", "step_id": "s3", "detail": "allowed_roles is empty"},
    {"check": "rule_conflict", "subject": "approval required", "rules": [...]}
  ]
}
```

On success:
1. `Workflow.status` → `published` (atomic DB write)
2. `parsed_rule_json` frozen — any edit attempt on a published workflow returns HTTP 409
3. Skill File generation triggered (Layer 4)
4. AuditLog: `workflow_published`

---

## Layer 4 — Skill File Generation

### What a skill.md file contains

A skill.md is a self-contained employee guide generated from the compiled, published workflow. No LLM involved — it is assembled deterministically from structured data.

**Sources used:**

| Data | Where it comes from |
|---|---|
| Step order | Topological sort of `parsed_rule_json.steps` (already done by DAG executor) |
| Step names | `step["action"]` → `ActionDefinition.display_name` |
| Responsible roles | `step["business_rules"][*].allowed_roles` + `WorkflowActor` records |
| Rule descriptions | `step["business_rules"][*].description` (the original BRD sentence) |
| Routing outcomes | `step["routing"]["branches"]` → plain language if/then |
| Missing path (what happens if something is absent) | SKIPPED branch analysis |
| Contacts | `WorkflowActor.actor_name` + `WorkflowExternalSystem.name` |

### Skill.md structure

```markdown
# Skill Guide: {workflow.name}
**Published:** {published_at}  
**Workspace:** {workspace.display_name} ({workspace.level})  
**Domain:** {workflow.domain}

## Roles in this workflow
| Role | Step |
|---|---|
| Branch Manager | Step 3: Approve Loan |
| Branch Officer | Step 1: Verify KYC |

---

## Step-by-step process

### Step 1: Verify KYC
**Who does this:** Branch Officer  
**What to do:** [ActionDefinition.description]  

**Rules that apply:**
- Customer must have valid PAN and Aadhaar (from: BRD_KYC_Policy.pdf)

**If this step is blocked:**
- Rule: "Customer must have valid PAN" — check the KYC system. Talk to: Branch Manager.
- If KYC is still missing after 24 hours, escalate to Zone Manager.

---

### Step 2: Check Credit Score  
**Who does this:** (automated — no human approval needed)  
**What to do:** System fetches credit score from credit bureau.

**Rules that apply:**
- Credit score must be >= 650 to proceed to disbursement

**If credit score < 650:**
→ Workflow routes to: Step 4 (Reject Application)  
→ Notify: Branch Officer, applicant

**If credit score >= 650:**
→ Workflow routes to: Step 3 (Approve Loan)

---

### Step 3: Approve Loan
**Who does this:** Branch Manager  
**What to do:** Review and approve loan application.

**Rules that apply:**
- Loan amount >= ₹5 lakh: Branch Manager approval required (from: Loan_Policy_BRD.pdf)
- Loan amount >= ₹25 lakh: Zone Manager co-approval required

**⚠ What happens if this step is skipped or missing:**
- Loan will not be disbursed. Workflow is paused in RULE_BLOCKED state.
- Contact: Branch Manager (primary), Zone Manager (escalation after 48 hours)
- System reference: workspace "South Zone Branch 12", rule ID #42

---

## Escalation contacts
| Situation | Contact | Escalation if unavailable |
|---|---|---|
| KYC missing | Branch Officer | Branch Manager → Zone Manager |
| Approval needed > ₹5L | Branch Manager | Zone Manager (after 48 hrs) |
| System integration failure | IT Help Desk | Region IT Manager |

## ⚠ What can go wrong
| Problem | Impact | Who to call |
|---|---|---|
| credit_score field missing from context | Step 2 RULE_BLOCKED | Check credit bureau integration |
| Branch Manager not assigned | HumanTask has no resolver | Zone Manager must assign via admin |
| Rule conflict across BRDs | Workflow cannot be published | Compliance officer must resolve |
```

### Generation algorithm

```
SkillFileGenerator.generate(workflow_id, db) →

1. Load: workflow, workspace, parsed_rule_json, WorkflowActor rows, 
         BusinessRuleDefinition rows for this workspace's effective rule set

2. Topological sort of steps (same order the DAG executor uses)

3. For each step:
   a. Resolve display_name from ActionDefinition
   b. Collect allowed_roles from step["business_rules"] — these are the "who does this"
   c. Collect rule descriptions for this step
   d. If routing: generate if/then language for each branch
      - activated branch → "If [field] [op] [value]: go to Step N ([action_display_name])"
      - default branch   → "Otherwise: go to Step N"
   e. For each non-activated (SKIPPED) branch: generate the "what can go wrong" entry
      - "If [field] is missing or [condition] not met: [step_name] is skipped. Contact: [roles]."

4. Build escalation contacts table from WorkflowActor + HumanTask escalation_policy

5. Build "what can go wrong" table:
   - Each RULE_BLOCKED possibility (one per business rule with a threshold)
   - Each HumanTask step where allowed_roles is populated
   - Each HTTP integration step (possible external system failure)

6. Render to Markdown string

7. FileStorageService.store(content=md_string, filename=f"skill-{workflow_id}.md")
   → returns {file_id, storage_path}

8. Write file_id + storage_path to Workflow.skill_file_id, Workflow.skill_file_path

9. AuditLog: skill_file_generated
```

### Retrieval

```
GET /api/workflows/{workflow_id}/skill
  → RBAC check: caller needs workflow:read in workflow's workspace or ancestor
  → If workflow.status != "published": 404
  → If workflow.skill_file_id is null: 404
  → FileStorageService.retrieve(file_id) → content
  → Response: text/markdown, Content-Disposition: attachment; filename="skill-{id}.md"
```

---

## Audit Logging Extension

The existing `audit_logs` table needs two new columns and new event types.

**New columns:**
- `user_id` (String, nullable) — who triggered the event
- `workspace_id` (Integer FK, nullable) — which workspace the event belongs to

**New event types:**

| Event | Triggered by |
|---|---|
| `rbac_assignment` | Role assigned or revoked |
| `permission_check` | Any RBAC gate evaluated (allowed or denied) |
| `rule_created` | BusinessRuleDefinition written |
| `rule_conflict` | detect_rule_conflicts returns a hit |
| `execution_step_rule_blocked` | Step blocked by rule evaluation |
| `workflow_published` | Workflow status → published |
| `skill_file_generated` | skill.md stored |
| `humantask_escalated` | HumanTask escalation_level incremented |

All entries are append-only. The AuditLog table never sees UPDATE or DELETE.

---

## What Already Exists vs. What to Build

### Already exists — reuse without changes

| Component | Location | Used for |
|---|---|---|
| `evaluate_condition` | `app/execution/rules/evaluator.py` | Step rule evaluation at runtime |
| `resolve_activated_children` + `resolve_skipped_steps` | `app/execution/rules/routing.py` | DAG branching, skill.md SKIPPED branch analysis |
| `detect_rule_conflicts` | `app/workflow/rule_conflicts.py` | Cross-level conflict detection, publication gate |
| `extract_amounts` + `subject_key` | `app/workflow/rule_conflicts.py` | Rule extraction from BRD text |
| `WorkspaceSynthesisService` | `app/workflow/workspace_synthesis.py` | Source of business rules + actors for extraction |
| `FileStorageService.store()/retrieve()` | `app/storage/` | skill.md persistence |
| `WorkflowActor` model | extracted in BRD pipeline | Actor → role mapping in skill.md |
| `WorkflowBusinessRule` model | extracted in BRD pipeline | Source text for `RuleExtractionService` |
| `HumanExecutor` + `HumanTask` model | `app/execution/executors/human_executor.py` | Extended with `allowed_roles` + escalation |
| Reaper worker | existing | Extended to handle escalation |
| `ExecutionStep.metadata` JSONB | `app/models/execution_step.py` | Rule evaluation results written here |
| Workspace CRUD routes | `app/routes/workspaces.py` | No change, hierarchy added at model level |

### New to build

| Component | Type | Purpose |
|---|---|---|
| `Workspace.level` + `Workspace.parent_id` | DB migration + model change | Hierarchy foundation |
| `BusinessRuleDefinition` table + model | New DB table | Structured, scoped rule store |
| `RoleAssignment` table + model | New DB table | RBAC extracted from rules |
| `RuleExtractionService` | New service | BRD text → structured rules + role shapes |
| `RuleInheritanceResolver` | New pure function | Ancestor-chain rule collection |
| `RuleValidationService` | New pure function | Write-time restriction check |
| `RuleInjector` | New post-compile hook | Attach rules to compiled DAG steps |
| `StepRuleEvaluator` | New pre-execute hook | Evaluate rules before step runs |
| `RULE_BLOCKED` status | New status constant | Distinct from FAILED, no retry |
| `WorkflowPublicationService` | New service | Publication gate (3 checks) |
| `SkillFileGenerator` | New service | Deterministic skill.md from DAG |
| `GET /workflows/{id}/skill` endpoint | New route | RBAC-gated skill file retrieval |
| `HumanTask.allowed_roles` + `escalation_policy` + `escalation_level` | DB migration | Role-aware human approval |
| `AuditLog.user_id` + `AuditLog.workspace_id` | DB migration | Full audit coverage |

---

## Integration Points — How the Layers Connect

```
BRD uploaded
    │
    ▼
WorkflowKnowledge created
WorkflowBusinessRule rows saved (raw text)        ← EXISTS
WorkflowActor rows saved                          ← EXISTS
    │
    ▼
RuleExtractionService.extract(workspace_id)       ← NEW
    → BusinessRuleDefinition rows (scoped to workspace's level)
    → RoleAssignment rows (user_id = NULL, role inferred from actor names)
    │
    ▼
Workflow generation (NL or deterministic)         ← EXISTS
    │
    ▼
RuleInjector.inject(compiled_dag, workspace_id)   ← NEW (post-compile hook)
    → Adds business_rules[] array to each step
    │
    ▼
WorkflowPublicationService.publish()              ← NEW
    → Check 1: RBAC (caller has workflow:publish)
    → Check 2: All HumanTask steps have allowed_roles
    → Check 3: No unresolved rule_conflicts
    → On pass: status = published → SkillFileGenerator.generate()
    │
    ▼
SkillFileGenerator.generate(workflow_id)          ← NEW
    → Topological step traversal
    → Rule descriptions + actor contacts + routing language + missing-path warnings
    → FileStorageService.store() → file_id saved on Workflow
    │
    ▼                                              At execution time:
ExecutionEngine runs DAG                          ← EXISTS
    │
    ▼
StepRuleEvaluator.evaluate(step, context)         ← NEW (called by step_executor)
    → evaluate_condition() for each rule          ← REUSED
    → BLOCKED → ExecutionStep.status = RULE_BLOCKED, AuditLog, DAG pauses
    → PASS    → normal executor.execute()
```

---

## Property-Based Testing Strategy

These pure functions must be tested without DB or LLM:

| Function | Property to test |
|---|---|
| `is_more_restrictive(new, inherited)` | Symmetry broken: `is_more_restrictive(A,B) ≠ is_more_restrictive(B,A)` for differing values |
| `RuleInheritanceResolver.resolve(workspace_id)` | Global rules always appear before branch rules in result |
| `SkillFileGenerator._build_step_section(step, ...)` | Every step with routing produces at least one "if" and one "otherwise" clause |
| `RuleExtractionService.extract_role(actor_name)` | All 7 role names are reachable from plausible actor name strings |
| `evaluate_condition` (already tested) | Total — never raises on any input combination |

Tests live in `tests/unit/` alongside existing `test_rule_conflicts.py` and `test_workspace_*.py`.

---

## What the Employee Experience Looks Like

This is what the `skill.md` enables at the employee level:

1. Employee opens a case or task notification in the bank's system
2. Looks up the workflow by name — e.g. "Home Loan Disbursement > ₹5 Lakh"
3. Downloads or views `GET /api/workflows/{id}/skill` → skill.md rendered in browser
4. Sees exactly:
   - Which step they are responsible for (their role is listed)
   - What conditions must be true before their step runs (the business rules)
   - Who to call if something is blocked (contacts table)
   - What happens downstream if they approve vs reject (routing outcomes)
   - What cannot happen if a required field is missing (missing-path warnings)
5. If something is wrong (step blocked, task not routing), the `⚠ What can go wrong` section shows the exact field, threshold, and escalation contact — no support ticket needed

The screenshot scenario: an employee sees a task stuck in `RULE_BLOCKED`. The skill.md tells them:
- "credit_score field missing → check credit bureau integration"
- "Contact: IT Help Desk, escalate to Region IT Manager after 4 hours"

That is the entire guidance loop, generated from the rules the bank already wrote in their BRD.
