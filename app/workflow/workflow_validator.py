from dataclasses import dataclass


@dataclass
class WorkflowValidationResult:
    valid: bool
    errors: list[str]


class WorkflowValidator:

    def validate(
        self,
        workflow: dict,
        valid_action_names: set[str] | None = None,
        valid_trigger_names: set[str] | None = None,
    ) -> WorkflowValidationResult:
        """
        Validate the structure and catalog membership of a generated workflow.

        Args:
            workflow:            normalised workflow dict from WorkflowResponseParser
            valid_action_names:  set of bare action name strings from CatalogMatchResult.
                                 When provided, every action name in the LLM response
                                 must appear in this set. Hallucinated names are rejected.
            valid_trigger_names: same for trigger names.
        """
        errors = []
        wf = workflow["workflow"]
        triggers = wf["triggers"]
        actions  = wf["actions"]

        # ── Structural checks ────────────────────────────────────────────────
        if len(triggers) != 1:
            errors.append("exactly_one_trigger_required")
        if len(actions) == 0:
            errors.append("at_least_one_action_required")

        action_names_in_response = [a["name"] for a in actions]

        for action in actions:
            for dep in action["dependencies"]:
                if dep not in action_names_in_response:
                    errors.append(f"dependency_not_found:{dep}")

        # ── Catalog membership checks ────────────────────────────────────────
        # Strip enrichment annotations from valid name sets so bare names can
        # be compared. valid_action_names may contain lines like:
        #   "verify_property_title   [Rule: ...]   [Actor: ...]"
        # The bare name is everything before the first triple-space or [.
        if valid_action_names:
            bare_valid_actions = _bare_names(valid_action_names)
            for action in actions:
                bare = _bare_name(action["name"])
                if bare not in bare_valid_actions:
                    errors.append(
                        f"action_not_in_catalog:{action['name']}"
                    )

        if valid_trigger_names and len(triggers) == 1:
            bare_valid_triggers = _bare_names(valid_trigger_names)
            trigger_name = triggers[0].get("name", "")
            if _bare_name(trigger_name) not in bare_valid_triggers:
                errors.append(
                    f"trigger_not_in_catalog:{trigger_name}"
                )

        return WorkflowValidationResult(valid=len(errors) == 0, errors=errors)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _bare_name(name: str) -> str:
    """
    Extract the bare catalog name from a potentially annotated prompt line.

    "verify_property_title   [Rule: Title must be clean]   [Actor: Legal Officer]"
    → "verify_property_title"

    Also handles names the LLM may have copied with trailing spaces or
    annotation fragments.
    """
    # Split on first triple-space (annotation separator) or first [
    for sep in ("   ", " ["):
        idx = name.find(sep)
        if idx != -1:
            return name[:idx].strip()
    return name.strip()


def _bare_names(names: set[str] | list[str]) -> set[str]:
    """Apply _bare_name to a collection and return a set."""
    return {_bare_name(n) for n in names}
