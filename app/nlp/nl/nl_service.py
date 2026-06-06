"""
Natural Language → AST pipeline entry point.

Converts a natural language workflow sentence into a WorkflowAST
compatible with ASTValidator and WorkflowComplier.

Pipeline:
    Natural Language
        ↓
    IntentExtractor       (rule-based, no LLM)
        ↓
    List[ParseNode]
        ↓
    WorkflowASTBuilder
        ↓
    WorkflowAST
"""

from app.nlp.nl.intent_extractor import IntentExtractor
from app.nlp.models import ParseNode
from app.nlp.ast.builder import WorkflowASTBuilder
from app.nlp.ast.schema import WorkflowAST


class NLService:
    """
    Converts a natural language sentence into a WorkflowAST.

    The resulting AST is structurally identical to one produced from DSL input.
    ASTValidator and WorkflowComplier receive the same type regardless of input source.
    """

    def __init__(self):
        self._extractor = IntentExtractor()
        self._builder = WorkflowASTBuilder()

    def parse(self, sentence: str) -> WorkflowAST:
        """
        Parse a natural language sentence into a WorkflowAST.

        Args:
            sentence: e.g. "When payment is due send reminder then notify manager"

        Returns:
            WorkflowAST with trigger and sequentially-dependent steps

        Raises:
            ValueError: empty sentence
            UnknownTriggerError: trigger phrase not in registry
            UnknownActionError: action phrase not in registry
        """
        intent = self._extractor.extract(sentence)
        nodes = self._build_parsed_nodes(intent["trigger"], intent["actions"])
        return self._builder.build(nodes)

    def _build_parsed_nodes(
        self, trigger: str, actions: list[str]
    ) -> list[ParseNode]:
        """
        Convert trigger + action list into ParseNode objects.

        Actions form a sequential dependency chain:
            step 1 (no deps) → step 2 depends on 1 → step 3 depends on 2 → ...
        """
        nodes = []
        for i, action in enumerate(actions):
            step_id = str(i + 1)
            depends_on = [str(i)] if i > 0 else []
            nodes.append(
                ParseNode(
                    step_id=step_id,
                    event=trigger,
                    action=action,
                    depends_on=depends_on,
                )
            )
        return nodes
