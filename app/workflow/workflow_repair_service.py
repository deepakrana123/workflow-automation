"""
app/workflow/workflow_repair_service.py

Builds a strict repair prompt when workflow generation fails validation.

Design decisions:
  1. The repair prompt is built in Python using plain string concatenation —
     NOT via PromptManager / template rendering. This avoids the crash where
     the already-rendered original prompt (which contains bare { and } from
     JSON examples) is passed as a template variable to a second str.format()
     call.

  2. The repair prompt does NOT repeat the original prompt. Repeating it
     doubles the token count and adds noise. The LLM already has the context
     from the original prompt in its recent history. The repair only needs to
     say: here is what you returned, here is what was wrong, here are the
     ONLY valid names you may use, fix it.

  3. The valid action and trigger name lists are injected directly so the LLM
     cannot claim it did not know which names were allowed.
"""


class WorkflowRepairService:

    def repair(
        self,
        raw_output: str,
        validation_errors: list | str,
        original_prompt: str,
        valid_action_names: list[str] | None = None,
        valid_trigger_names: list[str] | None = None,
    ) -> str:
        """
        Build a strict repair prompt for the LLM.

        Args:
            raw_output:          the invalid JSON string the LLM returned.
            validation_errors:   list of error strings from the validators.
            original_prompt:     kept for callers that pass it — not used in
                                 the output, prevents breaking call sites.
            valid_action_names:  the exact action name strings the LLM must use.
            valid_trigger_names: the exact trigger name strings the LLM must use.

        Returns:
            A self-contained repair prompt string, safe to send directly to
            the LLM without further template rendering.
        """
        errors_text = _format_errors(validation_errors)
        output_text = (raw_output or "").strip() or "(empty)"

        sections: list[str] = []

        sections.append(
            "Your previous workflow JSON failed validation. "
            "You must fix every error listed below and return corrected JSON."
        )

        sections.append(
            "VALIDATION ERRORS — fix ALL of these:\n"
            + errors_text
        )

        sections.append(
            "YOUR PREVIOUS OUTPUT (invalid):\n"
            + output_text
        )

        if valid_action_names:
            # Strip [Rule:] / [Actor:] annotations — repair prompt shows bare names only
            bare_actions = [_bare_name(n) for n in valid_action_names if n]
            sections.append(
                "VALID ACTION NAMES — use ONLY these, copied exactly:\n"
                + "\n".join(bare_actions)
            )

        if valid_trigger_names:
            bare_triggers = [_bare_name(n) for n in valid_trigger_names if n]
            sections.append(
                "VALID TRIGGER NAMES — use ONLY these, copied exactly:\n"
                + "\n".join(bare_triggers)
            )

        sections.append(
            "STRICT RULES:\n"
            "1. Action names must be copied EXACTLY from VALID ACTION NAMES above.\n"
            "2. Trigger name must be copied EXACTLY from VALID TRIGGER NAMES above.\n"
            "3. Do NOT invent, rename, or paraphrase any action or trigger name.\n"
            "4. Every action listed in dependencies must also exist in the actions list.\n"
            "5. No circular dependencies.\n"
            "6. Exactly one trigger.\n"
            "7. At least one action.\n"
            "8. Return JSON only — no markdown, no explanation, no commentary."
        )

        sections.append(
            "Return corrected JSON in this format:\n"
            '{\n'
            '  "workflow": {\n'
            '    "triggers": [{"name": "<exact_trigger_name>"}],\n'
            '    "actions": [\n'
            '      {"name": "<exact_action_name>", "dependencies": []},\n'
            '      {"name": "<exact_action_name>", "dependencies": ["<previous_action_name>"]}\n'
            '    ]\n'
            '  }\n'
            '}'
        )

        return "\n\n---\n\n".join(sections)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_errors(errors: list | str | None) -> str:
    if not errors:
        return "(none reported)"
    if isinstance(errors, str):
        return errors
    return "\n".join(f"  - {e}" for e in errors)


def _bare_name(name: str) -> str:
    """Strip [Rule:] / [Actor:] annotations from an enriched prompt line."""
    for sep in ("   ", " ["):
        idx = name.find(sep)
        if idx != -1:
            return name[:idx].strip()
    return name.strip()
