from app.semantic.embedding_provider import EmbeddingProvider


class EmbeddingService:
    def __init__(self):
        self.provider = EmbeddingProvider()

    def generate_embedding(self, text: str) -> list[float]:
        return self.provider.embed(text)

    def build_trigger_text(self, trigger) -> str:
        aliases = " ".join(trigger.aliases or [])
        parts = [
            trigger.name.replace("_", " "),
            trigger.display_name or "",
            # trigger.description or "",
            aliases,
        ]
        return " ".join(p for p in parts if p).strip()

    def build_action_text(self, action) -> str:
        aliases = " ".join(action.aliases or [])
        parts = [
            action.name.replace("_", " "),
            action.display_name or "",
            # action.description or "",
            aliases,
        ]
        return " ".join(p for p in parts if p).strip()

    def build_rule_text(self, rule) -> str:
        """
        Construct searchable text from a WorkflowBusinessRule.
        
        Concatenates rule, condition, outcome, responsible_role, and threshold
        to build a rich semantic representation for embedding and retrieval.
        """
        parts = [
            rule.rule or "",
            rule.condition or "",
            rule.outcome or "",
            rule.responsible_role or "",
            rule.threshold or "",
        ]
        return " ".join(p for p in parts if p).strip()
