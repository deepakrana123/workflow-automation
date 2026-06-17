from app.semantic.embedding_provider import EmbeddingProvider



class EmbeddingService:
    def __init__(self):
        self.provider=EmbeddingProvider()

    
    def generate_embedding(self,text:str)->list[float]:
        return self.provider.embed(text)
    
    def build_trigger_text(self,trigger)->str:
        aliases=" ".join(trigger.aliases or [])
        return f"""
       {trigger.name}
        {trigger.display_name}
        {trigger.description}
        {aliases}
    """
    
    def build_action_text(self,action)->str:
        aliases=" ".join(action.aliases or [])
        return f"""
        {action.name}
        {action.display_name}
        {action.description}
        {aliases}
        """
        