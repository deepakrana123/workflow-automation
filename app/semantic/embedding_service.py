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
            trigger.description or "",
            aliases,
        ]
        return " ".join(p for p in parts if p).strip()

    def build_action_text(self, action) -> str:
        aliases = " ".join(action.aliases or [])
        parts = [
            action.name.replace("_", " "),
            action.display_name or "",
            action.description or "",
            aliases,
        ]
        return " ".join(p for p in parts if p).strip()
