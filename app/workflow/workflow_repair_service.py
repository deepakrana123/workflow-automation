"""
app/workflow/workflow_repair_service.py

Builds a repair prompt to send back to the LLM when workflow generation
fails validation. The LLM receives the original prompt, its raw output,
and the validation errors, and is asked to fix the output.
"""

from app.prompting import PromptManager, PromptContext, PromptKey


class WorkflowRepairService:

    def __init__(self, prompt_manager: PromptManager | None = None):
        self._pm = prompt_manager or PromptManager()

    def repair(
        self,
        raw_output: str,
        validation_errors: list | str,
        original_prompt: str,
    ) -> str:
        """
        Build a repair prompt for the LLM.

        Falls back to simple string formatting if the repair template
        is not yet available via PromptManager.
        """
        try:
            return self._pm.build(
                PromptKey.WORKFLOW_REPAIR,
                PromptContext(variables={
                    "original_prompt": original_prompt,
                    "raw_output": raw_output,
                    "validation_errors": validation_errors,
                }),
            )
        except FileNotFoundError:
            # Fallback if repair.md template doesn't exist yet
            return (
                f"{original_prompt}\n\n"
                f"The previous output was invalid:\n{raw_output}\n\n"
                f"Errors: {validation_errors}\n\n"
                f"Fix the output and return valid JSON only."
            )
