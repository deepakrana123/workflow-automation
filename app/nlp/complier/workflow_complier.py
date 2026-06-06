from app.nlp.ast.schema import WorkflowAST


class WorkflowComplier:
    def compile(self, ast: WorkflowAST) -> dict:
        return {
            "version": "v2",
            "trigger": {"event_type": ast.trigger.event},
            "steps": [
                {
                    "id": step.id,
                    "action": step.action,
                    "depends_on": step.depends_on,
                    "config": {},
                }
                for step in ast.steps
            ],
        }
