class DSLGenerator:
    def generate(self, workflow_type: str, workflow: dict):
        trigger = workflow["workflow"]["triggers"][0]["name"]
        actions = workflow["workflow"]["actions"]

        # build name → step index map first so deps can reference by name
        action_to_step = {action["name"]: idx for idx, action in enumerate(actions, start=1)}

        lines = []
        for idx, action in enumerate(actions, start=1):
            deps = action.get("dependencies", [])
            if deps:
                dep_ids = ",".join(f"@{action_to_step[dep]}" for dep in deps if dep in action_to_step)
                lines.append(f"@{idx} @depends({dep_ids}): {trigger} -> {action['name']}")
            else:
                lines.append(f"@{idx}: {trigger} -> {action['name']}")

        return "\n".join(lines)
