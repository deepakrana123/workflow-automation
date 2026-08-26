"""
app/workflow/skill_file_generator.py

SkillFileGenerator — deterministic generation of skill.md from a published workflow.

No LLM. No new DB tables. Sources:
  - Workflow.parsed_rule_json     (DAG: steps, routing, actions)
  - ActionDefinition              (display_name, description)
  - BusinessRuleDefinition        (rule descriptions, allowed_roles)
  - WorkflowActor                 (escalation contacts)
  - WorkflowKnowledge             (source BRD names)
  - resolve_skipped_steps()       (what happens if a branch is not taken)

Output structure:
  # Skill Guide: {workflow.name}
  ## Roles in this workflow
  ## Step-by-step process
     ### Step N: {action display name}
         Who does this | What to do | Rules that apply | If blocked / routing
  ## Escalation contacts
  ## What can go wrong

Stored via FileStorageService → file_id + path written to Workflow.skill_file_id
and Workflow.skill_file_path.
"""

from __future__ import annotations

import textwrap
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.workflow import Workflow
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workflow_actor import WorkflowActor
from app.models.action_definitions import ActionDefinition
from app.rbac.rule_inheritance import resolve_effective_rules
from app.execution.rules.routing import resolve_activated_children, resolve_skipped_steps
from app.storage.service import FileStorageService
from app.execution.python.base.generate_model import GeneratedFile
from app.repositories.audit_repo import create as audit_create
from app.models.audit_log import AUDIT_EVENT_SKILL_FILE_GENERATED
from app.core.logger import logger


class SkillFileGenerator:
    """Generates and stores a skill.md guide for a published workflow."""

    def __init__(self, storage: FileStorageService | None = None):
        self._storage = storage or FileStorageService()

    def generate(self, workflow_id: int, db: Session) -> str:
        """Build, store, and return the skill.md content.

        Side effects:
          - Writes file via FileStorageService
          - Updates Workflow.skill_file_id and .skill_file_path
          - Writes audit log entry

        Args:
            workflow_id: ID of the published workflow.
            db: SQLAlchemy session.

        Returns:
            The Markdown content string.

        Raises:
            ValueError: If workflow not found.
        """
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if workflow is None:
            raise ValueError(f"Workflow {workflow_id} not found")

        content = self.build(workflow, db)

        # Store via FileStorageService
        generated = GeneratedFile(
            file_name=f"skill-{workflow_id}.md",
            mime_type="text/markdown",
            content=content.encode("utf-8"),
            extension=".md",
            size=len(content.encode("utf-8")),
        )
        stored = self._storage.store(generated, workspace_id=workflow.workspace_id)

        # Write references back to the workflow row
        workflow.skill_file_id = stored.file_id
        workflow.skill_file_path = stored.storage_path
        db.commit()

        # Audit
        audit_create(
            db=db,
            workflow_id=workflow_id,
            action="skill_file:generate",
            status="success",
            event_type=AUDIT_EVENT_SKILL_FILE_GENERATED,
            request_payload=None,
            response_payload=str({"file_id": stored.file_id, "path": stored.storage_path}),
        )

        logger.info(
            "skill_file_generated",
            extra={"extra_data": {
                "workflow_id": workflow_id,
                "file_id": stored.file_id,
                "storage_path": stored.storage_path,
            }},
        )

        return content

    # ── Pure builder (no DB side effects — fully testable) ────────────────────

    def build(self, workflow: Workflow, db: Session) -> str:
        """Build the Markdown string without storing it."""
        dag        = workflow.parsed_rule_json or {}
        steps      = dag.get("steps", [])
        trigger    = dag.get("trigger", {})
        workspace_id = workflow.workspace_id

        # Collect supporting data
        action_map   = self._load_actions(steps, db)
        actors       = self._load_actors(workflow, db)
        eff_rules    = resolve_effective_rules(workspace_id, db) if workspace_id else []
        steps_by_id  = {s["id"]: s for s in steps}

        # Topological order is already the step list order (the compiler guarantees it)
        ordered_steps = steps

        # Build role → step mapping for header table
        role_steps: dict[str, list[str]] = {}
        for step in ordered_steps:
            roles = self._step_roles(step, eff_rules)
            for role in roles:
                role_steps.setdefault(role, []).append(
                    action_map.get(step.get("action", ""), step.get("action", ""))
                )

        sections: list[str] = []

        # ── Header ────────────────────────────────────────────────────────────
        sections.append(self._header(workflow, trigger))

        # ── Roles table ───────────────────────────────────────────────────────
        sections.append(self._roles_table(role_steps, actors))

        # ── Step-by-step ──────────────────────────────────────────────────────
        sections.append("---\n\n## Step-by-step process\n")
        for idx, step in enumerate(ordered_steps, 1):
            sections.append(
                self._step_section(idx, step, action_map, eff_rules, steps, steps_by_id)
            )

        # ── Escalation contacts ───────────────────────────────────────────────
        sections.append(self._escalation_table(actors, eff_rules))

        # ── What can go wrong ─────────────────────────────────────────────────
        sections.append(self._risk_table(ordered_steps, eff_rules, action_map))

        return "\n".join(sections)

    # ── Section builders (pure) ───────────────────────────────────────────────

    def _header(self, workflow: Workflow, trigger: dict) -> str:
        from app.models.workspace import Workspace
        published = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        trigger_event = trigger.get("event_type", "unknown")
        return textwrap.dedent(f"""\
            # Skill Guide: {workflow.name}

            **Published:** {published}
            **Trigger:** {trigger_event}
            **Domain:** {workflow.domain}
            **Workflow ID:** {workflow.id}

        """)

    def _roles_table(
        self,
        role_steps: dict[str, list[str]],
        actors: list[WorkflowActor],
    ) -> str:
        lines = ["## Roles in this workflow\n", "| Role | Responsible for |", "|---|---|"]

        # Roles derived from rules
        for role, step_names in sorted(role_steps.items()):
            lines.append(f"| `{role}` | {', '.join(step_names)} |")

        # Actors from BRD that did not map to rules
        actor_roles = {a.role or a.name for a in actors}
        for ar in sorted(actor_roles):
            if ar not in role_steps:
                lines.append(f"| {ar} | (see BRD source) |")

        lines.append("")
        return "\n".join(lines)

    def _step_section(
        self,
        idx: int,
        step: dict,
        action_map: dict[str, str],
        eff_rules: list,
        all_steps: list[dict],
        steps_by_id: dict[str, dict],
    ) -> str:
        action       = step.get("action", "")
        display_name = action_map.get(action, action.replace("_", " ").title())
        step_roles   = self._step_roles(step, eff_rules)
        who          = ", ".join(f"`{r}`" for r in step_roles) if step_roles else "_(automated)_"

        lines = [f"### Step {idx}: {display_name}\n"]
        lines.append(f"**Who does this:** {who}  ")

        # Desc from ActionDefinition (stored in action_map descriptions if loaded)
        lines.append(f"**Action:** `{action}`\n")

        # Rules that apply
        step_rules = self._matching_rules(action, eff_rules) + (step.get("business_rules") or [])
        if step_rules:
            lines.append("**Rules that apply:**")
            for r in step_rules:
                desc = r.description if hasattr(r, "description") else r.get("description", "")
                lines.append(f"- {desc}")
            lines.append("")

        # If blocked
        if step_rules:
            lines.append("**If this step is blocked:**")
            for r in step_rules:
                desc = r.description if hasattr(r, "description") else r.get("description", "")
                roles = (
                    list(r.allowed_roles or [])
                    if hasattr(r, "allowed_roles")
                    else r.get("allowed_roles") or []
                )
                contact = ", ".join(f"`{ro}`" for ro in roles) if roles else "escalation contact"
                lines.append(f"- Rule: _{desc}_ — contact: {contact}")
            lines.append("")

        # Routing outcomes
        routing = step.get("routing")
        if routing:
            lines.append("**Routing decision:**")
            field = routing.get("field", "?")
            for branch in routing.get("branches", []):
                when = branch.get("when", {})
                activate = branch.get("activate", [])
                targets = [
                    action_map.get(steps_by_id.get(t, {}).get("action", t), t)
                    for t in activate
                ]
                lines.append(
                    f"- If `{field}` `{when.get('op', '?')}` `{when.get('value', '?')}`: "
                    f"→ {', '.join(targets) or '_(none)_'}"
                )
            default = routing.get("default", [])
            if default:
                targets = [
                    action_map.get(steps_by_id.get(t, {}).get("action", t), t)
                    for t in default
                ]
                lines.append(f"- Otherwise: → {', '.join(targets)}")

            # What happens if a branch is NOT taken
            dummy_outputs_pass = {field: routing["branches"][0]["when"]["value"]}
            activated_branch   = resolve_activated_children(routing, dummy_outputs_pass)
            skipped            = resolve_skipped_steps(all_steps, step["id"], activated_branch)
            if skipped:
                lines.append("")
                lines.append("**⚠ What is skipped if this branch is not taken:**")
                for sid in sorted(skipped):
                    skipped_action = steps_by_id.get(sid, {}).get("action", sid)
                    skipped_name   = action_map.get(skipped_action, skipped_action)
                    lines.append(f"- `{skipped_name}` is skipped")
            lines.append("")

        lines.append("---\n")
        return "\n".join(lines)

    def _escalation_table(
        self,
        actors: list[WorkflowActor],
        eff_rules: list,
    ) -> str:
        lines = [
            "## Escalation contacts\n",
            "| Situation | Contact | Escalation if unavailable |",
            "|---|---|---|",
        ]
        # Derive from actors
        for actor in actors:
            role = actor.role or actor.name
            lines.append(f"| Task assigned to {role} | {actor.name} | Contact branch manager |")

        # Derive from rules with allowed_roles
        for rule in eff_rules:
            roles = rule.allowed_roles or []
            if roles:
                contact = ", ".join(f"`{r}`" for r in roles)
                lines.append(
                    f"| {rule.description[:60]}... | {contact} | escalate to next level |"
                )

        lines.append("")
        return "\n".join(lines)

    def _risk_table(
        self,
        steps: list[dict],
        eff_rules: list,
        action_map: dict[str, str],
    ) -> str:
        lines = [
            "## ⚠ What can go wrong\n",
            "| Problem | Impact | Who to call |",
            "|---|---|---|",
        ]

        # One row per evaluable rule
        for rule in eff_rules:
            if not (hasattr(rule, "field") and rule.field):
                continue
            roles   = rule.allowed_roles or []
            contact = ", ".join(roles) if roles else "escalation contact"
            lines.append(
                f"| `{rule.field}` does not meet threshold "
                f"(`{rule.op}` `{rule.value}`) "
                f"| Step blocked (RULE\\_BLOCKED) "
                f"| {contact} |"
            )

        # One row per routing step (field missing in context)
        for step in steps:
            routing = step.get("routing")
            if routing:
                field  = routing.get("field", "?")
                action = step.get("action", "")
                name   = action_map.get(action, action)
                lines.append(
                    f"| `{field}` missing from context "
                    f"| `{name}` routing cannot proceed "
                    f"| Check previous step outputs |"
                )

        lines.append("")
        return "\n".join(lines)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _load_actions(self, steps: list[dict], db: Session) -> dict[str, str]:
        """Map action name → display_name from ActionDefinition."""
        names  = {s.get("action") for s in steps if s.get("action")}
        rows   = (
            db.query(ActionDefinition)
            .filter(ActionDefinition.name.in_(names))
            .all()
        )
        return {r.name: r.display_name for r in rows}

    def _load_actors(self, workflow: Workflow, db: Session) -> list[WorkflowActor]:
        """Load WorkflowActor rows for the workflow's BRD knowledge."""
        wk = (
            db.query(WorkflowKnowledge)
            .filter(WorkflowKnowledge.workflow_name == workflow.name)
            .first()
        )
        if wk is None:
            return []
        return db.query(WorkflowActor).filter(
            WorkflowActor.workflow_knowledge_id == wk.id
        ).all()

    def _step_roles(self, step: dict, eff_rules: list) -> list[str]:
        """Collect roles responsible for a step, from embedded rules + effective rules."""
        roles: set[str] = set()
        # From step-embedded business_rules
        for br in step.get("business_rules") or []:
            roles.update(br.get("allowed_roles") or [])
        # From effective rules matching this step's action
        for rule in self._matching_rules(step.get("action", ""), eff_rules):
            roles.update(rule.allowed_roles or [])
        return sorted(roles)

    def _matching_rules(self, action_name: str, eff_rules: list) -> list:
        """Return effective rules that are relevant to a given action.

        Currently all evaluable rules apply to all steps. In a future version
        rules could carry an action_name filter. For now return all evaluable
        ones (those with a field) so skill.md is comprehensive.
        """
        return [r for r in eff_rules if r.field]
