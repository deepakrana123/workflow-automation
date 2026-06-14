class DSLGenerator:
    def generate(self, workflow_type: str, workflow: dict):
        lines = []
        lines.append(f"workflow {workflow_type}")
        lines.append("")
        trigger = workflow["workflow"]["triggers"][0]
        lines.append(f"trigger {trigger['name']}")

        lines.append("")

        for action in workflow["workflow"]["actions"]:
            lines.append(f"Action {action['name']}")

            for dep in action["dependencies"]:
                lines.append(f"DEPENDS_on {dep}")
            lines.append("")
        return "\n".join(lines)
