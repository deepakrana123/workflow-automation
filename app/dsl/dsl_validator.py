class DSLValidator:
    def validate(self, dsl: str):
        errors = []
        print(dsl,"dsl")
        normalized = dsl.upper()
        workflow_count = normalized.count("WORKFLOW")
        trigger_count = normalized.count("TRIGGER")

        if workflow_count != 1:
            errors.append("workflow_count_invalid")
        if trigger_count != 1:
            errors.append("trigger_count_invalid")
        return {"valid": len(errors) == 0, "errors": errors}
