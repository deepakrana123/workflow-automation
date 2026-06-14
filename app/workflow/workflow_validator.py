from dataclasses import dataclass


@dataclass
class WorkflowValidationResult:
    valid: bool
    errors: list[str]


class WorkflowValidator:
    def validate(self, workflow: dict):
        errors = []
        wf = workflow["workflow"]
        triggers = wf["triggers"]
        actions = wf["actions"]

        if len(triggers) != 1:
            errors.append("exactly_one_trigger_required")
        if len(actions) == 0:
            errors.append("at_least_one_action_required")

        action_names = [action["name"] for action in action_names]

        for action in actions:
            for dep in action["dependencies"]:
                if dep not in action_names:
                    errors.append(f"dependency_not_found:{dep}")
        return WorkflowValidationResult(valid=len(errors) == 0, errors=errors)
