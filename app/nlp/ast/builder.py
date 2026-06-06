from app.nlp.ast.schema import WorkflowAST, StepNode, TriggerNode
from app.nlp.models import ParseNode


class WorkflowASTBuilder:
    def build(self, parsed_nodes: list[ParseNode]) -> WorkflowAST:
        if not parsed_nodes:
            raise ValueError("No parsed nodes provided")

        trigger_event = parsed_nodes[0].event
        steps = [
            StepNode(
                id=node.step_id,
                action=node.action,
                depends_on=node.depends_on,
            )
            for node in parsed_nodes
        ]
        return WorkflowAST(
            trigger=TriggerNode(event=trigger_event),
            steps=steps,
        )
