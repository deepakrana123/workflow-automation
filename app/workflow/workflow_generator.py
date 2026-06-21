class WorkflowGenerator:

    def __init__(self, llm_manager, response_parse):
        self.llm_manager = llm_manager
        self.response_parser = response_parse

    def generate(self, prompt: str) -> dict:
        """
        Generate a workflow using the default provider order (ollama → gemini).
        """
        result = self.llm_manager.generate(prompt)
        if not result["success"]:
            raise RuntimeError(result.get("error", "llm_generation_failed"))
        return self.response_parser.parse(result["output"])

    def generate_with_provider(self, prompt: str, provider: str) -> dict:
        """
        Generate a workflow forcing a specific provider.
        Used by the fallback path in NLPWorkflowService after max retries.
        """
        result = self.llm_manager.generate_with_provider(prompt, provider)
        if not result["success"]:
            raise RuntimeError(
                f"provider '{provider}' failed: {result.get('error', 'unknown')}"
            )
        return self.response_parser.parse(result["output"])
