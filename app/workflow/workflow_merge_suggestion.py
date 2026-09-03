"""
app/workflow/workflow_merge_suggestion.py

WorkflowMergeSuggestionService — asks the LLM to suggest how 2–3 workflows
in a workspace could be merged into one coherent end-to-end workflow.

Design:
  - Prompt is built in Python (plain string concatenation, not template engine)
    to avoid the brace-crash issue.
  - The prompt contains only human-readable data: summaries, step display names,
    applicable rules, actors, and detected chain connections.
  - Raw compiled DAG JSON is never sent to the LLM.
  - The LLM returns a structured JSON suggestion.
  - Nothing is persisted here — the caller decides whether to accept.
"""

from __future__ import annotations

import json
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.workflow import Workflow
from app.models.workflow_action_mapping import WorkflowActionMapping, MappingStatus
from app.models.workflow_knowledge import WorkflowKnowledge
from app.models.workflow_chain import WorkflowChain
from app.core.logger import logger


class WorkflowMergeSuggestionService:

    def suggest(
        self,
        db: Session,
        workspace_id: int,
        workflow_ids: list[int],
    ) -> dict:
        """
        Build a merge suggestion for the given workflows.

        Args:
            db:            DB session
            workspace_id:  workspace scope
            workflow_ids:  2–3 workflow IDs to merge

        Returns:
            Suggestion dict with keys:
              merged_name, steps, deduplication_notes, handoff_points, warnings

        Raises:
            ValueError:   if any workflow_id is not found or not in workspace
            RuntimeError: if LLM call fails completely
        """
        workflows = self._load_workflows(db, workspace_id, workflow_ids)
        action_index = self._build_action_index(db, workspace_id)
        chains = self._load_relevant_chains(db, workspace_id, workflow_ids)
        duplicates = self._find_duplicates(workflows)

        prompt = self._build_prompt(workflows, action_index, chains, duplicates)

        raw = self._call_llm(prompt)
        suggestion = self._parse_suggestion(raw, workflows)

        return suggestion

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_workflows(
        self,
        db: Session,
        workspace_id: int,
        workflow_ids: list[int],
    ) -> list[Workflow]:
        workflows = (
            db.query(Workflow)
            .filter(
                Workflow.id.in_(workflow_ids),
                Workflow.workspace_id == workspace_id,
            )
            .all()
        )
        found_ids = {w.id for w in workflows}
        missing = set(workflow_ids) - found_ids
        if missing:
            raise ValueError(
                f"Workflow IDs not found in workspace {workspace_id}: {sorted(missing)}"
            )
        # Preserve the user's requested order
        id_order = {wid: idx for idx, wid in enumerate(workflow_ids)}
        return sorted(workflows, key=lambda w: id_order[w.id])

    def _build_action_index(
        self,
        db: Session,
        workspace_id: int,
    ) -> dict[str, WorkflowActionMapping]:
        """Map action_name → WorkflowActionMapping (with display_name, rules, actors)."""
        rows = (
            db.query(WorkflowActionMapping)
            .join(
                WorkflowKnowledge,
                WorkflowKnowledge.id == WorkflowActionMapping.workflow_knowledge_id,
            )
            .filter(
                WorkflowKnowledge.workspace_id == workspace_id,
                WorkflowActionMapping.status == MappingStatus.MAPPED,
                WorkflowActionMapping.action_name.isnot(None),
            )
            .all()
        )
        return {r.action_name: r for r in rows}

    def _load_relevant_chains(
        self,
        db: Session,
        workspace_id: int,
        workflow_ids: list[int],
    ) -> list[WorkflowChain]:
        """Load chains where both source and target are in the selected workflows."""
        return (
            db.query(WorkflowChain)
            .filter(
                WorkflowChain.workspace_id == workspace_id,
                WorkflowChain.source_workflow_id.in_(workflow_ids),
                WorkflowChain.target_workflow_id.in_(workflow_ids),
                WorkflowChain.status.in_(["auto", "accepted", "suggested"]),
            )
            .order_by(WorkflowChain.confidence.desc())
            .all()
        )

    def _find_duplicates(
        self,
        workflows: list[Workflow],
    ) -> dict[str, list[str]]:
        """Map action_name → list of workflow names that contain it."""
        action_to_wf: dict[str, list[str]] = defaultdict(list)
        for wf in workflows:
            dag = wf.parsed_rule_json or {}
            for step in dag.get("steps", []):
                action = step.get("action")
                if action:
                    action_to_wf[action].append(wf.name)
        return {k: v for k, v in action_to_wf.items() if len(v) > 1}

    # ── Prompt building ───────────────────────────────────────────────────────

    def _build_prompt(
        self,
        workflows: list[Workflow],
        action_index: dict[str, WorkflowActionMapping],
        chains: list[WorkflowChain],
        duplicates: dict[str, list[str]],
    ) -> str:
        label = {wf.id: chr(65 + i) for i, wf in enumerate(workflows)}  # A, B, C

        sections: list[str] = []

        sections.append(
            "You are a banking workflow architect. "
            "Suggest how to merge the following workflows into ONE coherent "
            "end-to-end workflow. Base your suggestion ONLY on the information below."
        )

        # Per-workflow summaries and steps
        for wf in workflows:
            lbl = label[wf.id]
            summary = ""
            if wf.explanation and isinstance(wf.explanation, dict):
                summary = wf.explanation.get("summary", "")

            dag = wf.parsed_rule_json or {}
            steps = dag.get("steps", [])

            # Topological sort for human-readable order
            step_lines = _topo_sort_steps(steps, action_index)

            # Mark duplicates
            marked: list[str] = []
            for line in step_lines:
                action_name = line.split("   ")[0].strip()
                if action_name in duplicates:
                    line += "   ← DUPLICATE (also in " + ", ".join(
                        n for n in duplicates[action_name] if n != wf.name
                    ) + ")"
                marked.append(line)

            wf_block = (
                f"WORKFLOW {lbl} — \"{wf.name}\"\n"
                + (f"Summary: {summary}\n" if summary else "")
                + "Steps:\n"
                + "\n".join(f"  {i+1}. {line}" for i, line in enumerate(marked))
            )
            sections.append(wf_block)

        # Detected connections
        if chains:
            chain_lines = []
            for c in chains:
                src_name = next((w.name for w in workflows if w.id == c.source_workflow_id), str(c.source_workflow_id))
                tgt_name = next((w.name for w in workflows if w.id == c.target_workflow_id), str(c.target_workflow_id))
                chain_lines.append(
                    f"  - Workflow \"{src_name}\" terminal step "
                    f"\"{c.source_action}\" → Workflow \"{tgt_name}\" "
                    f"trigger \"{c.target_trigger}\" "
                    f"(match: {c.match_type}, confidence: {round(c.confidence, 2)})"
                )
            sections.append(
                "DETECTED CONNECTIONS:\n" + "\n".join(chain_lines)
            )

        # Duplicate actions
        if duplicates:
            dup_lines = [
                f"  - {action}: appears in {', '.join(wf_names)} — keep once"
                for action, wf_names in duplicates.items()
            ]
            sections.append(
                "DUPLICATE ACTIONS (deduplicate in merged workflow):\n"
                + "\n".join(dup_lines)
            )

        # Valid action name list — LLM must not invent names
        all_actions = sorted({
            step["action"]
            for wf in workflows
            for step in (wf.parsed_rule_json or {}).get("steps", [])
            if step.get("action")
        })
        sections.append(
            "VALID ACTION NAMES — use ONLY these, copied exactly:\n"
            + "\n".join(f"  {a}" for a in all_actions)
        )

        sections.append(
            "MERGE RULES:\n"
            "1. Use ONLY action names from VALID ACTION NAMES above.\n"
            "2. Deduplicate actions that appear in multiple workflows — keep the instance with the most rules/actors.\n"
            "3. Respect DETECTED CONNECTIONS — chained workflows should be ordered accordingly.\n"
            "4. Preserve all business rules and actor assignments.\n"
            "5. Do NOT invent new actions.\n"
            "6. depends_on must reference action names only — not workflow names.\n"
            "7. No circular dependencies.\n"
            "8. Return JSON only — no markdown, no explanation."
        )

        sections.append(
            "Return JSON in this format:\n"
            '{\n'
            '  "merged_name": "...",\n'
            '  "steps": [\n'
            '    {"action": "...", "source_workflow": "A", "depends_on": [], "note": ""},\n'
            '    {"action": "...", "source_workflow": "B", "depends_on": ["previous_action"], "note": ""}\n'
            '  ],\n'
            '  "deduplication_notes": ["..."],\n'
            '  "handoff_points": [{"from": "A", "to": "B", "via": "..."}],\n'
            '  "warnings": ["..."]\n'
            '}'
        )

        return "\n\n---\n\n".join(sections)

    # ── LLM call ──────────────────────────────────────────────────────────────

    def _call_llm(self, prompt: str) -> str:
        from app.nlp.llm_manager.llm_manager import LLMManager
        manager = LLMManager()
        result = manager.generate(prompt)
        if not result.get("success"):
            raise RuntimeError(
                f"LLM merge suggestion failed: {result.get('error', 'unknown')}"
            )
        return result["output"]

    # ── Response parsing ──────────────────────────────────────────────────────

    def _parse_suggestion(self, raw: str, workflows: list[Workflow]) -> dict:
        """Extract and validate the LLM's JSON suggestion."""
        raw = raw.strip()
        start = raw.find("{")
        end   = raw.rfind("}")
        if start == -1 or end == -1:
            raise RuntimeError("LLM did not return valid JSON for merge suggestion")

        try:
            data = json.loads(raw[start: end + 1])
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"LLM merge suggestion JSON parse error: {exc}") from exc

        # Collect valid action names
        valid_actions = {
            step["action"]
            for wf in workflows
            for step in (wf.parsed_rule_json or {}).get("steps", [])
            if step.get("action")
        }

        # Validate and clean steps
        steps = data.get("steps") or []
        cleaned_steps = []
        warnings = list(data.get("warnings") or [])

        for step in steps:
            action = step.get("action", "").strip()
            if action not in valid_actions:
                warnings.append(
                    f"Action '{action}' not in valid action list — removed from suggestion"
                )
                continue
            cleaned_steps.append({
                "action":          action,
                "source_workflow": step.get("source_workflow", ""),
                "depends_on":      step.get("depends_on") or [],
                "note":            step.get("note", ""),
            })

        return {
            "merged_name":          data.get("merged_name", "Merged Workflow"),
            "steps":                cleaned_steps,
            "deduplication_notes":  data.get("deduplication_notes") or [],
            "handoff_points":       data.get("handoff_points") or [],
            "warnings":             warnings,
            # Label → workflow_id map so accept-merge can resolve the correct
            # trigger from the source workflow without relying on name matching
            "workflow_label_map":   {
                chr(65 + i): wf.id
                for i, wf in enumerate(workflows)
            },
        }


# ── Pure helpers ──────────────────────────────────────────────────────────────

def _topo_sort_steps(
    steps: list[dict],
    action_index: dict[str, WorkflowActionMapping],
) -> list[str]:
    """
    Return step prompt lines in topological execution order.
    Each line: "action_name   [Rule: ...]   [Actor: ...]"
    """
    from collections import deque

    if not steps:
        return []

    in_degree: dict[str, int] = {s["action"]: 0 for s in steps}
    dependents: dict[str, list[str]] = {s["action"]: [] for s in steps}

    for step in steps:
        for dep in (step.get("depends_on") or []):
            if dep in in_degree:
                in_degree[step["action"]] += 1
                dependents[dep].append(step["action"])

    queue = deque([a for a, d in in_degree.items() if d == 0])
    ordered: list[str] = []

    while queue:
        action = queue.popleft()
        mapping = action_index.get(action)
        parts = [action]
        if mapping:
            for rule in (mapping.applicable_rules or []):
                if rule:
                    parts.append(f"[Rule: {rule}]")
            for actor in (mapping.responsible_actors or []):
                if actor:
                    parts.append(f"[Actor: {actor}]")
        ordered.append("   ".join(parts))

        for child in dependents.get(action, []):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    # Append any steps that could not be sorted (cycles) at the end
    sorted_actions = {line.split("   ")[0] for line in ordered}
    for step in steps:
        if step["action"] not in sorted_actions:
            ordered.append(step["action"])

    return ordered
