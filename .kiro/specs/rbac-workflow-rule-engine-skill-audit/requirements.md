# Requirements Document

## Introduction

This document specifies the design and audit requirements for four interrelated systems in MFlows — the banking workflow AI platform built on FastAPI, PostgreSQL, and Redis. The four systems are:

1. **Role-Based Access Control (RBAC)** — a hierarchical, workspace-level permission system tied to the bank's organisational structure.
2. **Business-Rules-Driven Workflow Building** — a step authoring model where every workflow step carries explicit business rules that govern transitions and approvals.
3. **Multi-Level Rule Engine** — a four-tier rule hierarchy (Global → Region → Zone → Branch) with strict downward-only restriction inheritance.
4. **Skill File Generation** — deterministic generation of `skill.md` files from published workflows so employees can receive guided help.

This is a **design and audit spec** — no production code changes are implied unless a separate implementation spec is created. The existing `evaluate_condition`, `routing`, and `detect_rule_conflicts` primitives are reused without modification.

---

## Glossary

- **MFlows**: The banking workflow AI platform (FastAPI + PostgreSQL + Redis) that is the subject of this spec.
- **Workspace**: A PostgreSQL row in the `workspaces` table representing a scoped organisational unit. Extended in this spec to carry `level` and `parent_id`.
- **Workspace Level**: One of four values — `global`, `region`, `zone`, or `branch` — that places a Workspace in the bank's hierarchy.
- **RBAC**: Role-Based Access Control. A permission model that grants or denies API operations based on a user's assigned role within a specific Workspace.
- **Role**: A named permission set (e.g., `global_admin`, `region_manager`, `zone_manager`, `branch_manager`, `branch_officer`, `auditor`, `read_only`) assigned to a user in the context of one Workspace.
- **Permission**: An atomic capability string (e.g., `workflow:publish`, `rule:override`, `humantask:resolve`) that a Role grants.
- **Principal**: An authenticated user identity represented by a `user_id` and the set of Role assignments across Workspaces.
- **Rule Scope**: The Workspace Level at which a business rule is declared (`global`, `region`, `zone`, `branch`).
- **Inherited Rule**: A rule declared at a higher Workspace Level that applies automatically to all descendant Workspaces.
- **Override Rule**: A rule declared at a lower Workspace Level that may only add additional restrictions on top of inherited rules.
- **Workflow Step**: A single node in a compiled workflow DAG carrying an `action`, optional `routing`, optional `human_task` spec, and (new) optional `business_rules` array.
- **Step Business Rule**: A condition-action pair attached to a Workflow Step declaring the rule(s) that must be satisfied before that step executes or before a HumanTask resolves.
- **Rule Engine**: The subsystem that evaluates Step Business Rules against WorkflowContext outputs, applying the four-level inheritance chain.
- **Skill File**: A static Markdown file (`skill.md`) generated and stored when a workflow is published, containing step-by-step guidance for the employees who perform or approve steps.
- **Workflow Publication**: The act of marking a workflow as `published`, which triggers immutable compilation and Skill File generation.
- **HumanTask**: A pending human decision on a suspended workflow step, represented by the existing `HumanTask` model.
- **Escalation**: Automatic reassignment of an unresolved HumanTask to a higher-level Role when a deadline passes.
- **AuditLog**: The existing `audit_logs` table extended to record RBAC decisions and rule evaluations.
- **WorkflowActor**: An extracted role/person from a BRD document stored in `workflow_actors`, used as a source for Skill File guidance.
- **DAG**: Directed Acyclic Graph. The compiled runtime representation of a workflow's steps and dependencies.
- **Conflict**: A condition where two rules at the same or different scope levels specify incompatible thresholds or outcomes for the same subject — detected by the existing `detect_rule_conflicts` function.

---

## Requirements

### Requirement 1 — Workspace Hierarchy Extension

**User Story:** As a platform architect, I want each Workspace to declare its position in the bank's four-level hierarchy, so that RBAC and rule inheritance can traverse parent–child relationships deterministically.

#### Acceptance Criteria

1. THE Workspace model SHALL carry a `level` field constrained to the enumerated values `global`, `region`, `zone`, and `branch`.
2. THE Workspace model SHALL carry a `parent_id` self-referential foreign key to `workspaces.id`, nullable only for Workspaces with `level = global`.
3. WHEN a Workspace is created with `level` other than `global`, THE Workspace model SHALL require a non-null `parent_id` that references a Workspace at the immediately superior level (`region` → `global`, `zone` → `region`, `branch` → `zone`).
4. IF a `parent_id` references a Workspace whose `level` is not the immediate superior, THEN THE Workspace model SHALL reject the record with a constraint violation.
5. THE Workspace model SHALL enforce that exactly one Workspace exists with `level = global` per deployment (enforced via a partial unique index).
6. WHEN a Workspace is deactivated (`active = false`), THE Workspace model SHALL cascade deactivation to all descendant Workspaces.

---

### Requirement 2 — Role Definitions

**User Story:** As a security designer, I want a fixed set of named roles that correspond to the bank's organisational levels, so that every permission assignment maps unambiguously to an organisational position.

#### Acceptance Criteria

1. THE Role Catalogue SHALL define the following roles: `global_admin`, `region_manager`, `zone_manager`, `branch_manager`, `branch_officer`, `auditor`, and `read_only`.
2. THE Role Catalogue SHALL associate each role with a minimum required Workspace Level: `global_admin` requires `global`; `region_manager` requires `region`; `zone_manager` requires `zone`; `branch_manager` and `branch_officer` require `branch`; `auditor` and `read_only` are valid at any level.
3. IF a role assignment attempts to bind `global_admin` to a non-`global` Workspace, THEN THE RBAC System SHALL reject the assignment with a validation error.
4. THE Role Catalogue SHALL define the permission set for each role as documented in the design document, covering at minimum: `workflow:read`, `workflow:create`, `workflow:publish`, `workflow:delete`, `rule:read`, `rule:create`, `rule:override`, `humantask:resolve`, `humantask:escalate`, `audit:read`, and `admin:manage_roles`.
5. THE Role Catalogue SHALL be static configuration — roles are not user-definable at runtime.

---

### Requirement 3 — Role Assignment

**User Story:** As a platform administrator, I want to assign roles to users within specific Workspaces, so that a Branch Manager has authority only within the Branch Workspace assigned to them.

#### Acceptance Criteria

1. THE RBAC System SHALL represent a role assignment as a tuple `(user_id, role, workspace_id)` stored in a dedicated `role_assignments` table.
2. THE RBAC System SHALL enforce that a user may hold at most one role per Workspace.
3. WHEN a role assignment is created, THE RBAC System SHALL validate that the target Workspace's `level` is compatible with the role as defined in Requirement 2.2.
4. THE RBAC System SHALL allow a user to hold different roles in different Workspaces (e.g., `region_manager` in Region A, `read_only` in Region B).
5. WHEN a Workspace is deactivated, THE RBAC System SHALL mark all role assignments for that Workspace as inactive.
6. THE RBAC System SHALL record every role assignment creation and deletion in the AuditLog with `event_type = rbac_assignment`.

---

### Requirement 4 — Permission Enforcement

**User Story:** As a security designer, I want every API operation to be guarded by a permission check, so that users cannot perform actions beyond their assigned role's capabilities.

#### Acceptance Criteria

1. WHEN an API request arrives, THE RBAC System SHALL resolve the caller's effective permissions by loading all active role assignments for the caller and computing the union of permissions.
2. WHEN an operation requires a permission that the caller does not hold in any active role assignment, THE RBAC System SHALL return HTTP 403 with a structured error body containing the missing permission and the workspace context.
3. WHEN an operation targets a resource in a specific Workspace, THE RBAC System SHALL check that the caller holds the required permission in that Workspace or in an ancestor Workspace.
4. THE RBAC System SHALL enforce that `workflow:publish` requires the caller's role assignment to be in the same Workspace or an ancestor Workspace of the workflow's Workspace.
5. THE RBAC System SHALL enforce that `rule:override` is only grantable to roles at `branch` level or above (i.e., not to `read_only`).
6. WHEN a permission check is performed, THE RBAC System SHALL write a record to the AuditLog with `event_type = permission_check`, `action` = the operation, and `status` = `allowed` or `denied`.

---

### Requirement 5 — HumanTask Role Assignment and Escalation

**User Story:** As a workflow designer, I want each HumanTask step to declare the roles permitted to resolve it and an escalation chain, so that unresolved tasks are automatically promoted up the hierarchy.

#### Acceptance Criteria

1. THE HumanTask model SHALL carry an `allowed_roles` field (JSONB array of role names) specifying which roles may resolve the task.
2. THE HumanTask model SHALL carry an `escalation_policy` field (JSONB) declaring: `timeout_minutes` (integer), `escalate_to_role` (string), and `max_escalation_levels` (integer).
3. WHEN a HumanTask is created, THE HumanTask model SHALL default `status` to `PENDING` and `escalation_level` to `0`.
4. WHEN a user attempts to resolve a HumanTask, THE RBAC System SHALL verify that the user holds one of the roles in `allowed_roles` within the HumanTask's Workspace.
5. IF a user attempts to resolve a HumanTask without a permitted role, THEN THE RBAC System SHALL return HTTP 403 and write a denied `permission_check` record to the AuditLog.
6. WHEN `timeout_at` is reached and the HumanTask remains `PENDING`, THE HumanTask Escalation Service SHALL increment `escalation_level`, update `allowed_roles` to include `escalate_to_role`, and extend `timeout_at` by `timeout_minutes`.
7. WHEN `escalation_level` reaches `max_escalation_levels` and the HumanTask remains `PENDING`, THE HumanTask Escalation Service SHALL fall back to the existing `on_timeout` (approve/reject) behaviour.

---

### Requirement 6 — Business Rules on Workflow Steps

**User Story:** As a workflow author, I want to attach explicit business rules to individual workflow steps, so that the platform enforces banking policy conditions before a step executes or a HumanTask resolves.

#### Acceptance Criteria

1. THE Workflow Step schema SHALL accept an optional `business_rules` array where each element is a rule object containing: `field` (string), `op` (one of the operators supported by `evaluate_condition`), `value`, and `description` (human-readable string).
2. WHEN a workflow is compiled, THE Workflow Compiler SHALL validate that every `field` referenced in a `business_rules` entry is declared in the preceding step's `output_schema` or is a WorkflowContext key.
3. WHEN a step is about to execute, THE Rule Engine SHALL evaluate all `business_rules` entries for that step using the existing `evaluate_condition` function against the current `WorkflowContext` outputs.
4. IF any `business_rules` condition evaluates to `false`, THEN THE Rule Engine SHALL suspend the step, record the failing rule in the step's `ExecutionStep.metadata`, and emit an `execution_step_rule_blocked` event to the AuditLog.
5. THE Rule Engine SHALL evaluate all `business_rules` entries for a step in declaration order; the first failing condition SHALL halt further evaluation for that step.
6. WHEN all `business_rules` conditions for a step evaluate to `true`, THE Rule Engine SHALL proceed with normal step execution without writing a blocked entry.

---

### Requirement 7 — Multi-Level Rule Scoping

**User Story:** As a compliance officer, I want rules to be declared at a specific level (Global, Region, Zone, Branch) and applied to descendant Workspaces, so that policy set at the Global level is never softened by lower levels.

#### Acceptance Criteria

1. THE Rule Store SHALL persist each business rule with a `scope_workspace_id` foreign key identifying the Workspace at which the rule was declared.
2. WHEN the Rule Engine resolves the effective rule set for a Workspace, THE Rule Engine SHALL collect all rules whose `scope_workspace_id` is in the ancestor chain of the target Workspace (inclusive of the target Workspace itself).
3. THE Rule Engine SHALL apply inherited rules from higher levels before rules declared at the target Workspace's own level, in descending order: `global` → `region` → `zone` → `branch`.
4. WHEN a lower-level rule references the same `field` and `op` as an inherited rule, THE Rule Engine SHALL only accept the lower-level rule if its threshold is strictly more restrictive (i.e., a lower upper-bound or higher lower-bound on a numeric field, or a reduced `in` set).
5. IF a lower-level rule attempts to relax a constraint established by an inherited rule (e.g., raising an approval threshold), THEN THE Rule Store SHALL reject the rule with a conflict error at write time and record a `rule_conflict` entry in the AuditLog.
6. THE Rule Engine SHALL reuse the existing `detect_rule_conflicts` function to detect threshold conflicts across rules in the same effective rule set.
7. THE Rule Engine SHALL make rule evaluation total — a malformed rule SHALL evaluate to `false` without raising an exception, consistent with the existing `evaluate_condition` contract.

---

### Requirement 8 — Rule Conflict Detection and Surfacing

**User Story:** As a compliance officer, I want cross-level rule conflicts surfaced explicitly, so that I can adjudicate them before a workflow is published.

#### Acceptance Criteria

1. WHEN a rule is created or updated in the Rule Store, THE Rule Engine SHALL run `detect_rule_conflicts` across all rules in the affected Workspace's effective rule set (ancestor chain + own level).
2. IF `detect_rule_conflicts` returns one or more conflicts, THEN THE Rule Store SHALL persist each conflict as a `rule_conflict` record linked to the affected rules and the affected Workspace.
3. THE Rule Store SHALL prevent publication of any workflow whose effective rule set contains unresolved `rule_conflict` records.
4. WHEN a conflict is resolved by deleting or modifying a conflicting rule, THE Rule Store SHALL mark the conflict record as `resolved` and allow workflow publication to proceed.
5. THE Rule Conflict API SHALL expose an endpoint that returns all unresolved conflicts for a given Workspace, including: conflict type, subject, conflicting rules, source Workspace levels, and source documents.

---

### Requirement 9 — Workflow Publication Gate

**User Story:** As a branch manager, I want the platform to prevent publishing a workflow that has unresolved rule conflicts or missing role assignments on HumanTask steps, so that workflows entering production are policy-compliant.

#### Acceptance Criteria

1. WHEN a `workflow:publish` operation is requested, THE Workflow Publication Service SHALL verify that the caller holds the `workflow:publish` permission in the workflow's Workspace.
2. WHEN a `workflow:publish` operation is requested, THE Workflow Publication Service SHALL verify that all HumanTask steps in the workflow carry a non-empty `allowed_roles` list.
3. WHEN a `workflow:publish` operation is requested, THE Workflow Publication Service SHALL verify that the workflow's effective rule set contains zero unresolved `rule_conflict` records.
4. IF any pre-publication check fails, THEN THE Workflow Publication Service SHALL return a structured error listing each failed check by step ID and check type.
5. WHEN all pre-publication checks pass, THE Workflow Publication Service SHALL atomically set the workflow's `status` to `published`, record a `workflow_published` entry in the AuditLog, and trigger Skill File generation (Requirement 11).
6. WHEN a workflow is published, THE Workflow Publication Service SHALL set the compiled `parsed_rule_json` to immutable — no further edits to steps or rules are permitted without creating a new workflow version.

---

### Requirement 10 — Audit Logging Coverage

**User Story:** As an auditor, I want every RBAC decision, rule evaluation outcome, and workflow lifecycle event recorded in the AuditLog, so that a complete, tamper-evident trail is available for regulatory review.

#### Acceptance Criteria

1. THE AuditLog model SHALL be extended to carry `user_id` (nullable string) and `workspace_id` (nullable foreign key) in addition to the existing fields.
2. THE AuditLog model SHALL support the following `event_type` values in addition to those already defined: `rbac_assignment`, `permission_check`, `rule_created`, `rule_updated`, `rule_deleted`, `rule_conflict`, `execution_step_rule_blocked`, `workflow_published`, `skill_file_generated`, `humantask_escalated`.
3. WHEN any of the above events occurs, THE AuditLog Service SHALL write a record within the same database transaction as the triggering operation.
4. THE AuditLog SHALL be append-only — no update or delete operations on existing records are permitted.
5. WHEN an `auditor` role user requests audit logs for a Workspace, THE AuditLog API SHALL return all log records whose `workspace_id` is in the Workspace's descendant-or-self set, ordered by `created_at` descending.
6. THE AuditLog API SHALL support filtering by `event_type`, `user_id`, `workspace_id`, and date range.

---

### Requirement 11 — Skill File Generation

**User Story:** As a branch employee, I want a plain-language guidance document generated for every published workflow, so that I can follow step-by-step instructions when executing or approving a workflow task.

#### Acceptance Criteria

1. WHEN a workflow transitions to `published` status, THE Skill File Generator SHALL produce a `skill.md` file for that workflow.
2. THE Skill File Generator SHALL produce the `skill.md` content deterministically from the workflow's compiled `parsed_rule_json`, the step `description` fields, the `WorkflowActor` records linked to the workflow's `WorkflowKnowledge`, and the step `business_rules` descriptions.
3. THE `skill.md` file SHALL contain, for each step in DAG execution order: the step name, the actor role responsible (from `allowed_roles` or `WorkflowActor`), a plain-language description of the step's purpose, the business rules that apply (using the `description` field of each rule), and the routing outcome descriptions.
4. THE `skill.md` file SHALL include a header section with: workflow name, publication timestamp, effective Workspace Level, and a list of all roles with responsibilities in the workflow.
5. THE Skill File Generator SHALL persist the generated `skill.md` content via the existing `FileStorageService.store()` interface, recording the returned `file_id` and `storage_path` on the workflow record.
6. WHEN a `skill.md` file is successfully stored, THE Skill File Generator SHALL write a `skill_file_generated` entry to the AuditLog with the `file_id` and `workflow_id`.
7. THE Skill File Generator SHALL NOT make any LLM calls — all content SHALL be derived deterministically from structured workflow data.
8. THE Skill File Generator SHALL NOT regenerate `skill.md` after publication unless a new workflow version is explicitly created and published.

---

### Requirement 12 — Skill File Retrieval

**User Story:** As a branch employee, I want to retrieve the `skill.md` guidance file for any published workflow I have access to, so that I can review the process steps before executing a task.

#### Acceptance Criteria

1. THE Skill File API SHALL expose an endpoint `GET /api/workflows/{workflow_id}/skill` that returns the `skill.md` content for a published workflow.
2. WHEN the endpoint is called, THE RBAC System SHALL verify that the caller holds at least `workflow:read` permission in the workflow's Workspace or an ancestor Workspace.
3. IF the workflow is not in `published` status, THEN THE Skill File API SHALL return HTTP 404 with a message indicating the skill file is not available for unpublished workflows.
4. IF no `skill.md` has been generated for the requested workflow, THEN THE Skill File API SHALL return HTTP 404 with a message indicating the skill file is missing.
5. THE Skill File API SHALL return the `skill.md` content as `text/markdown` with the filename `skill-{workflow_id}.md` in the `Content-Disposition` header.

---

### Requirement 13 — Rule Engine Observability

**User Story:** As a platform engineer, I want each rule evaluation outcome recorded on the execution step, so that debugging and auditing of rule-gated step transitions are straightforward.

#### Acceptance Criteria

1. WHEN THE Rule Engine evaluates `business_rules` for a step, THE Rule Engine SHALL append a `rule_evaluation` entry to `ExecutionStep.metadata` containing: the rule `description`, `field`, `op`, `value`, the `actual` value from WorkflowContext, the `result` (true/false), and the `scope_workspace_id` of the rule.
2. WHEN a step is blocked by a rule, THE Rule Engine SHALL set `ExecutionStep.status` to `RULE_BLOCKED` rather than `FAILED`, to distinguish policy blocks from execution errors.
3. WHILE a step is in `RULE_BLOCKED` status, THE DAG Executor SHALL NOT retry the step using the standard retry logic — the step SHALL remain blocked until an authorised user overrides the rule or the workflow is cancelled.
4. THE Rule Engine SHALL record the total count of passing and failing rules for each step in `ExecutionStep.metadata` under `rule_evaluation_summary`.

---

### Requirement 14 — Read-Only and Auditor Access

**User Story:** As a regulator or internal auditor, I want read-only access to workflows, rules, audit logs, and skill files across all Workspaces I am assigned to, without the ability to modify any data.

#### Acceptance Criteria

1. THE RBAC System SHALL ensure that the `read_only` role grants only `workflow:read`, `rule:read`, and `audit:read` permissions.
2. THE RBAC System SHALL ensure that the `auditor` role grants `workflow:read`, `rule:read`, `audit:read`, and `humantask:read` permissions, and no mutation permissions.
3. WHEN a `read_only` or `auditor` user attempts any mutation operation (create, update, delete, publish, resolve), THE RBAC System SHALL return HTTP 403 without performing the mutation.
4. WHERE the `auditor` role is assigned at a `region` Workspace level, THE RBAC System SHALL grant that auditor `audit:read` access to all `zone` and `branch` descendant Workspaces of that region.
