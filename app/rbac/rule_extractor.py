"""
app/rbac/rule_extractor.py

RuleExtractionService — parses raw WorkflowBusinessRule text into structured
BusinessRuleDefinition rows, and derives RoleAssignment shapes from WorkflowActor rows.

This is the bridge between what the LLM extracted from BRDs (unstructured text)
and the deterministic rule engine (structured field/op/value rows).

Key principle: the LLM extracts; this service structures. The rule engine only
ever touches BusinessRuleDefinition rows — never raw BRD text.

What it does:
  1. For each WorkflowBusinessRule in a workspace:
     a. Use extract_amounts() to detect numeric thresholds
     b. Pattern-match threshold direction words to determine operator
     c. Look for actor names in WorkflowActor for the same BRD
     d. Write a BusinessRuleDefinition row

  2. For each WorkflowActor in a workspace:
     a. Map actor name to a role using the actor→role catalogue
     b. Write a RoleAssignment row (user_id=None, to be assigned later)

Actor → Role mapping:
  The mapping is intentionally simple and configurable. It covers common
  banking actor names. Unmapped actors produce a 'read_only' role flagged
  for human review.
"""

from __future__ import annotations

import re
from sqlalchemy.orm import Session

from app.models.workflow_business_rule import WorkflowBusinessRule
from app.models.workflow_actor import WorkflowActor
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.business_rule_definition import BusinessRuleDefinition
from app.models.role_assignment import RoleAssignment, VALID_ROLES
from app.workflow.rule_conflicts import extract_amounts
from app.core.logger import logger


# ── Actor name → role catalogue ───────────────────────────────────────────────
# Keys are lowercase substrings to match against actor_name.lower().
# First match wins (ordered by specificity — longer strings first).
_ACTOR_ROLE_MAP: list[tuple[str, str]] = [
    ("global admin",        "global_admin"),
    ("global head",         "global_admin"),
    ("regional head",       "region_manager"),
    ("regional manager",    "region_manager"),
    ("region manager",      "region_manager"),
    ("region head",         "region_manager"),
    ("zonal head",          "zone_manager"),
    ("zone head",           "zone_manager"),
    ("zone manager",        "zone_manager"),
    ("zonal manager",       "zone_manager"),
    ("branch head",         "branch_manager"),
    ("branch manager",      "branch_manager"),
    ("branch in-charge",    "branch_manager"),
    ("head of branch",      "branch_manager"),
    ("loan officer",        "branch_officer"),
    ("credit officer",      "branch_officer"),
    ("branch officer",      "branch_officer"),
    ("field officer",       "branch_officer"),
    ("relationship manager","branch_officer"),
    ("auditor",             "auditor"),
    ("compliance",          "auditor"),
    ("regulator",           "auditor"),
    ("inspector",           "auditor"),
]

# Threshold direction words → operator
_UPPER_BOUND_WORDS = (
    "below", "less than", "under", "up to", "maximum", "max", "not exceed",
    "not more than",
)
_LOWER_BOUND_WORDS = (
    "above", "exceed", "exceeds", "exceeding", "greater", "more than", "over",
    "at least", "minimum", "min",
)

# Context words that indicate "field" category for the threshold
_FIELD_HINTS: list[tuple[str, str]] = [
    ("loan amount",     "loan_amount"),
    ("loan value",      "loan_amount"),
    ("disbursement",    "loan_amount"),
    ("credit limit",    "credit_limit"),
    ("credit score",    "credit_score"),
    ("cibil",           "credit_score"),
    ("transaction",     "transaction_amount"),
    ("payment",         "payment_amount"),
    ("transfer",        "transfer_amount"),
    ("fund",            "fund_amount"),
    ("penalty",         "penalty_amount"),
    ("interest",        "interest_rate"),
    ("emi",             "emi_amount"),
    ("income",          "annual_income"),
    ("salary",          "monthly_salary"),
    ("age",             "applicant_age"),
]


def _infer_operator(text: str) -> str:
    """Infer the comparison operator from threshold direction words in text."""
    low = text.lower()
    for phrase in _UPPER_BOUND_WORDS:
        if phrase in low:
            return "<="
    for phrase in _LOWER_BOUND_WORDS:
        if phrase in low:
            return ">="
    return ">="   # default: above-threshold rules are the most common


def _infer_field(text: str) -> str | None:
    """Infer the WorkflowContext field name from context words in the rule text."""
    low = text.lower()
    for hint, field in _FIELD_HINTS:
        if hint in low:
            return field
    return None


def map_actor_to_role(actor_name: str) -> str:
    """Map an actor name string to a role. Returns 'read_only' if no match."""
    low = (actor_name or "").lower().strip()
    for keyword, role in _ACTOR_ROLE_MAP:
        if keyword in low:
            return role
    return "read_only"


class RuleExtractionService:
    """
    Extracts structured BusinessRuleDefinition and RoleAssignment rows
    from a workspace's raw BRD data.

    Idempotent: skips rules and roles that have already been extracted
    for this workspace (checked by description dedup).
    """

    def extract_for_workspace(
        self,
        db: Session,
        workspace_id: int,
    ) -> dict:
        """
        Run extraction for all BRDs in a workspace.

        Returns a summary dict:
        {
          "rules_created": int,
          "rules_skipped": int,
          "roles_created": int,
          "roles_skipped": int,
        }
        """
        knowledge_rows = (
            db.query(WorkflowKnowledge)
            .filter(WorkflowKnowledge.workspace_id == workspace_id)
            .all()
        )

        rules_created = 0
        rules_skipped = 0
        roles_created = 0
        roles_skipped = 0

        for wk in knowledge_rows:
            r, s = self._extract_rules(db, wk, workspace_id)
            rules_created += r
            rules_skipped += s

            rc, rs = self._extract_roles(db, wk, workspace_id)
            roles_created += rc
            roles_skipped += rs

        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.error(
                "rule_extraction_commit_failed",
                extra={"extra_data": {"workspace_id": workspace_id, "error": str(exc)}},
            )
            raise

        logger.info(
            "rule_extraction_completed",
            extra={"extra_data": {
                "workspace_id": workspace_id,
                "rules_created": rules_created,
                "rules_skipped": rules_skipped,
                "roles_created": roles_created,
                "roles_skipped": roles_skipped,
            }},
        )

        return {
            "rules_created": rules_created,
            "rules_skipped": rules_skipped,
            "roles_created": roles_created,
            "roles_skipped": roles_skipped,
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _extract_rules(
        self,
        db: Session,
        wk: WorkflowKnowledge,
        workspace_id: int,
    ) -> tuple[int, int]:
        created = 0
        skipped = 0

        raw_rules = (
            db.query(WorkflowBusinessRule)
            .filter(WorkflowBusinessRule.workflow_knowledge_id == wk.id)
            .all()
        )

        # Collect actors for this BRD to populate allowed_roles
        actor_rows = (
            db.query(WorkflowActor)
            .filter(WorkflowActor.workflow_knowledge_id == wk.id)
            .all()
        )
        actor_roles = list({map_actor_to_role(a.name) for a in actor_rows})

        for raw in raw_rules:
            rule_text = raw.rule or ""

            # Idempotency check — skip if already extracted for this workspace
            existing = (
                db.query(BusinessRuleDefinition)
                .filter(
                    BusinessRuleDefinition.scope_workspace_id == workspace_id,
                    BusinessRuleDefinition.description == rule_text,
                )
                .first()
            )
            if existing:
                skipped += 1
                continue

            amounts = extract_amounts(rule_text)
            field   = _infer_field(rule_text) if amounts else None
            op      = _infer_operator(rule_text) if amounts else None
            value   = amounts[0] if amounts else None

            # Gap 6 fix: validate that the new rule does not relax any inherited
            # constraint before persisting it. Log violations but do not abort —
            # extraction is best-effort; a human admin resolves conflicts later.
            if field and op and value is not None:
                try:
                    from app.rbac.rule_inheritance import validate_new_rule
                    violations = validate_new_rule(
                        new_rule={"field": field, "op": op, "value": value, "description": rule_text},
                        workspace_id=workspace_id,
                        db=db,
                    )
                    if violations:
                        logger.warning(
                            "rule_extraction_restriction_violation",
                            extra={"extra_data": {
                                "workspace_id": workspace_id,
                                "rule": rule_text,
                                "violations": violations,
                            }},
                        )
                except Exception as val_exc:
                    logger.warning(
                        "rule_extraction_validation_error",
                        extra={"extra_data": {"error": str(val_exc)}},
                    )

            rule_def = BusinessRuleDefinition(
                scope_workspace_id=workspace_id,
                source_workflow_knowledge_id=wk.id,
                field=field,
                op=op,
                value=value,
                description=rule_text,
                allowed_roles=actor_roles or [],
                locked=False,
                active=True,
            )
            db.add(rule_def)
            created += 1

        return created, skipped

    def _extract_roles(
        self,
        db: Session,
        wk: WorkflowKnowledge,
        workspace_id: int,
    ) -> tuple[int, int]:
        created = 0
        skipped = 0

        actor_rows = (
            db.query(WorkflowActor)
            .filter(WorkflowActor.workflow_knowledge_id == wk.id)
            .all()
        )

        seen_roles: set[str] = set()
        for actor in actor_rows:
            role = map_actor_to_role(actor.name)
            if role in seen_roles:
                continue
            seen_roles.add(role)

            # Idempotency check — skip if role shape already exists for workspace
            existing = (
                db.query(RoleAssignment)
                .filter(
                    RoleAssignment.workspace_id == workspace_id,
                    RoleAssignment.role == role,
                    RoleAssignment.user_id.is_(None),
                )
                .first()
            )
            if existing:
                skipped += 1
                continue

            ra = RoleAssignment(
                user_id=None,   # to be mapped by HR/admin
                role=role,
                workspace_id=workspace_id,
                source_rule_id=None,
                active=True,
            )
            db.add(ra)
            created += 1

        return created, skipped
