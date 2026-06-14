class WorkflowGenerator:

    def __init__(self, llm_manager):
        self.llm_manager = llm_manager

    def generate(self, prompt):

        print("=" * 80)
        print("PROMPT SENT TO LLM")
        print(prompt)
        print("=" * 80)

        result = self.llm_manager.generate(prompt)

        print("=" * 80)
        print("RAW LLM RESPONSE")
        print(result)
        print("=" * 80)

        if not result["success"]:
            raise RuntimeError(result["error"])

        return result["output"]