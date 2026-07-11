from enum import Enum
from pathlib import Path


class PromptKey(str, Enum):
    WORKFLOW_EXTRACTION = "workflow_extractor.md"

    # Future
    WORKFLOW_VALIDATION = "workflow_validation.md"
    WORKFLOW_REPAIR = "workflow_repair.md"
    DSL_GENERATION = "dsl_generator.md"
    EXECUTION_PLANNER = "planner.md"
    
    


class PromptRegistry:
    def __init__(self):
        self._prompt_root = Path(__file__).parent.parent / "prompts"

    def get(self, key: PromptKey) -> str:
        path = self._prompt_root / key.value

        if not path.exists():
            raise FileNotFoundError(f"Prompt template not found: {path}")

        return path.read_text(encoding="utf-8")