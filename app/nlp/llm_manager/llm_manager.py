from app.nlp.llm_manager.providers.gemini_rest import try_call_gemini_rest
from app.nlp.llm_manager.providers.ollama import try_call_ollama
class LLMManager:
    def __init__(self):
        self.providers=[
            ("ollama",try_call_ollama),
            ("gemini",try_call_gemini_rest)
        ]
    
    
    def generate(self,prompt:str):
        for provider_name , provider_fn in self.providers:
            result = provider_fn(prompt)
            if result["success"]:
                return result
        raise RuntimeError("All provider failed")
                
            