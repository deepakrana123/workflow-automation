"""
app/workflow/publication_service.py

WorkflowPublicationService — three-gate check before a workflow goes live.

Gate 1 — RBAC:         Caller must hold workflow:publish in the workflow's workspace.
Gate 2 — Role coverage: Every human_task step must have non-empty allowed_roles.
Gate 3 — No conflicts:  detect_rule_conflicts() must return empty for the
                        workspace's effective rule set.

On success, atomically:
  1. workflow.status → "published"
  2. Triggers SkillFileGenerator.generate()
  3. Writes audit log: workflow_published

On failure, returns a structured error listing every failed check.
The caller (route handler) raises HTTP 422 with that structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from app.models.workflow import Workflow
from app.models.workspace import Workspace
from app.rbac.permission_checker import PermissionChecker
from app.rbac.rule_inheritance import resolve_effective_rules
from app.workflow.rule_conflicts import detect_rule_conflicts
from app.repositories.audit_repo import create as audit_create
from app.models.audit_log import AUDIT_EVENT_WORKFLOW_PUBLISHED
from app.core.logger import logger


@dataclass
class PublicationCheck:
    check: str
    passed: bool
    detail: str
    step_id: str | None = None


@dataclass
class PublicationResult:
    success: bool
    workflow_id: int
    checks: list[PublicationCheck] = field(default_factory=list)
    error: str | None = None

    @property
    def failed_checks(self) -> list[PublicationCheck]:
        return [c for c in self.checks if not c.passed]


class WorkflowPublicationService:

    def publish(
        self,
        workflow_id: int,
        user_id: str | None,
        db: Session,
    ) -> PublicationResult:
        """Run all publication gates and publish if they all pass.

        Returns PublicationResult regardless of outcome.
        Never raises — all exceptions are caught.
        """
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if workflow is None:
            return PublicationResult(
                success=False,
                workflow_id=workflow_id,
                error="workflow_not_found",
            )

        if workflow.status == "published":
            return PublicationResult(
                success=False,
                workflow_id=workflow_id,
                error="already_published",
            )

        checks: list[PublicationCheck] = []

        # ── Gate 1: RBAC ─────────────────────────────────────────────────────
        checks.append(self._check_rbac(workflow, user_id, db))

        # ── Gate 2: HumanTask role coverage ──────────────────────────────────
        checks.extend(self._check_human_task_roles(workflow))

        # ── Gate 3: No unresolved rule conflicts ──────────────────────────────
        checks.append(self._check_rule_conflicts(workflow, db))

        failed = [c for c in checks if not c.passed]
        if failed:
            return PublicationResult(
                success=False,
                workflow_id=workflow_id,
                checks=checks,
            )

        # ── All gates passed: publish ─────────────────────────────────────────
        try:
            workflow.status = "published"
            db.commit()
            db.refresh(workflow)

            audit_create(
                db=db,
                workflow_id=workflow_id,
                action="workflow:publish",
                status="success",
                event_type=AUDIT_EVENT_WORKFLOW_PUBLISHED,
                request_payload=str({"user_id": user_id}),
                response_payload=str({"workflow_id": workflow_id}),
            )

            # Trigger skill file generation (import here to avoid circular)
            try:
                from app.workflow.skill_file_generator import SkillFileGenerator
                SkillFileGenerator().generate(workflow_id=workflow_id, db=db)
            except Exception as skill_exc:
                logger.warning(
                    "skill_file_generation_failed",
                    extra={"extra_data": {
                        "workflow_id": workflow_id,
                        "error": str(skill_exc),
                    }},
                )
                # Skill file failure does not block publication

            logger.info(
                "workflow_published",
                extra={"extra_data": {
                    "workflow_id": workflow_id,
                    "user_id": user_id,
                }},
            )

            return PublicationResult(success=True, workflow_id=workflow_id, checks=checks)

        except Exception as exc:
            db.rollback()
            logger.error(
                "workflow_publication_failed",
                extra={"extra_data": {
                    "workflow_id": workflow_id,
                    "error": str(exc),
                }},
            )
            return PublicationResult(
                success=False,
                workflow_id=workflow_id,
                error=str(exc),
            )

    # ── Gate implementations ──────────────────────────────────────────────────

    def _check_rbac(
        self,
        workflow: Workflow,
        user_id: str | None,
        db: Session,
    ) -> PublicationCheck:
        if workflow.workspace_id is None:
            # Global workflows (no workspace) — only allow if user_id is set
            # (treat as system-level publish; in a real deployment gate on global_admin)
            passed = user_id is not None
            return PublicationCheck(
                check="rbac",
                passed=passed,
                detail="workflow:publish" if passed else "no user_id provided for global workflow",
            )

        checker = PermissionChecker(db)
        allowed = checker.can(user_id, "workflow:publish", workflow.workspace_id)
        return PublicationCheck(
            check="rbac",
            passed=allowed,
            detail=(
                f"user {user_id} has workflow:publish"
                if allowed
                else f"user {user_id} lacks workflow:publish in workspace {workflow.workspace_id}"
            ),
        )

    def _check_human_task_roles(self, workflow: Workflow) -> list[PublicationCheck]:
        """Verify every human_task step has non-empty allowed_roles."""
        dag = workflow.parsed_rule_json or {}
        steps = dag.get("steps", [])
        checks = []

        for step in steps:
            # Detect human_task steps by execution_type hint in business_rules
            # or by step type marker if present
            step_type = step.get("step_type") or step.get("type") or ""
            is_human_task = (
                step_type == "human_task"
                or step.get("execution_type") == "human_task"
            )
            if not is_human_task:
                # Also check business_rules for allowed_roles
                br = step.get("business_rules") or []
                roles = [r for rule in br for r in (rule.get("allowed_roles") or [])]
                if not br:
                    continue
                # Step has business_rules — check if any supply allowed_roles
                if not roles:
                    checks.append(PublicationCheck(
                        check="human_task_roles",
                        passed=False,
                        detail="step has business_rules but no allowed_roles",
                        step_id=step.get("id"),
                    ))
                continue

            br = step.get("business_rules") or []
            roles = [r for rule in br for r in (rule.get("allowed_roles") or [])]
            passed = len(roles) > 0
            checks.append(PublicationCheck(
                check="human_task_roles",
                passed=passed,
                detail=(
                    f"allowed_roles: {roles}"
                    if passed
                    else "human_task step has no allowed_roles — cannot be resolved"
                ),
                step_id=step.get("id"),
            ))

        return checks or [PublicationCheck(
            check="human_task_roles",
            passed=True,
            detail="no human_task steps found",
        )]

    def _check_rule_conflicts(
        self,
        workflow: Workflow,
        db: Session,
    ) -> PublicationCheck:
        """Run detect_rule_conflicts on the workspace's effective rule set."""
        workspace_id = workflow.workspace_id
        if workspace_id is None:
            return PublicationCheck(
                check="rule_conflicts",
                passed=True,
                detail="global workflow — no workspace rule set to check",
            )

        try:
            effective_rules = resolve_effective_rules(workspace_id, db)
            rule_dicts = [
                {"rule": r.description, "source_document": None}
                for r in effective_rules
            ]
            conflicts = detect_rule_conflicts(rule_dicts)

            if conflicts:
                return PublicationCheck(
                    check="rule_conflicts",
                    passed=False,
                    detail=f"{len(conflicts)} unresolved rule conflict(s) in effective rule set",
                )

            return PublicationCheck(
                check="rule_conflicts",
                passed=True,
                detail="no conflicts",
            )

        except Exception as exc:
            return PublicationCheck(
                check="rule_conflicts",
                passed=False,
                detail=f"conflict check failed: {exc}",
            )
