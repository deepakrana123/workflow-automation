class DSLValidator:
    def validate(self, dsl: str):
        errors = []

        workflow_count = dsl.count("WORKFLOW")
        trigger_count = dsl.count("TRIGGER")

        if workflow_count != 1:
            errors.append("workflow_count_invalid")
        if trigger_count != 1:
            errors.append("trigger_count_invalid")
        return {"valid": len(errors) == 0, "errors": errors}
