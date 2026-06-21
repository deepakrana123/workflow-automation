class WorkflowRepairService:

    def repair(
        self,
        raw_output,
        validation_errors,
        original_prompt,
    ):
        repair_prompt = f"""
Original Prompt:

{original_prompt}

Previous Output:

{raw_output}

Validation Errors:

{validation_errors}

Fix the workflow.

Return JSON only.
"""
        return repair_prompt
