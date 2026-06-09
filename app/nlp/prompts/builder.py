from pathlib import Path


class PromptBuilder:

    def __init__(self):

        template_dir = (
            Path(__file__).parent / "templates"
        )

        self.workflow_generation = (
            template_dir / "workflow_generation.txt"
        ).read_text()

        self.generation_rules = (
            template_dir / "generation_rules.txt"
        ).read_text()

    def build(
        self,
        context,
    ) -> str:

        trigger_block = "\n".join(
            context.triggers
        )

        action_block = "\n".join(
            context.actions
        )

        return f"""
{self.workflow_generation}

------------------------------------------------

{self.generation_rules}

------------------------------------------------

Workflow Type:

{context.workflow_type}

------------------------------------------------

Available Triggers:

{trigger_block}

------------------------------------------------

Available Actions:

{action_block}

------------------------------------------------

User Request:

{context.user_request}

------------------------------------------------

Return JSON only.
""".strip()