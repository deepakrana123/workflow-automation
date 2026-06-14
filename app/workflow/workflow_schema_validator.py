from dataclasses import dataclass


@dataclass
class SchemaValidationResult:
    valid: bool
    errors: list[str]


class WorkflowSchemaValidator:
    def validate(self, workflow: dict) -> SchemaValidationResult:
        errors = []
        if "workflow" not in workflow:
            errors.append("workflow_missing")
            return SchemaValidationResult(False, errors)
        wf = workflow["workflow"]
        if "triggers" not in wf:
            errors.append("triggers_missing")
        if "actions" not in wf:
            errors.append("actions_missing")

        if errors:
            return SchemaValidationResult(False, errors)

        if not isinstance(wf["triggers"], list):
            errors.append("triggers_not_list")

        if not isinstance(wf["actions"], list):
            errors.append("actions_not_list")

        for triggers in wf["triggers"]:
            if "name" not in triggers:
                errors.append("trigger_name_missing")
        for actions in wf["actions"]:
            if "name" not in actions:
                errors.append("actions_name_missing")

            if "dependencies" not in actions:
                errors.append(f"dependecies_missing:{actions.get('name')}")
        return SchemaValidationResult(valid=len(errors) == 0, errors=errors)
