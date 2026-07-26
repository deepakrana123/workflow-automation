from app.prompts import WORKFLOW_REPAIR_PROMPT


class WorkflowRepairService:

    def repair(
        self,
        raw_output,
        validation_errors,
        original_prompt,
    ):
        return WORKFLOW_REPAIR_PROMPT.format(
            original_prompt=original_prompt,
            raw_output=raw_output,
            validation_errors=validation_errors,
        )
