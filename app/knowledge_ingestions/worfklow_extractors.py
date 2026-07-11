from pydantic import ValidationError

from app.nlp.llm_manager.providers.gemini_rest import try_call_gemini_rest
from app.knowledge_ingestions.schemas import WorkflowExtraction
from app.knowledge_ingestions.exceptions import WorkflowExtractionError

from app.prompting.prompt_manager import PromptManager
from app.prompting.prompt_context import PromptContext
from app.prompting.prompt_registry import PromptKey


class WorkflowExtractor:
    def __init__(self):
        self.prompt_manager = PromptManager()

    def extract(self, document_text: str) -> WorkflowExtraction:
        if not document_text.strip():
            raise WorkflowExtractionError("Document text is empty.")

        prompt = self.prompt_manager.build(
            PromptKey.WORKFLOW_EXTRACTION,
            PromptContext(
                variables={
                    "schema": WorkflowExtraction.model_json_schema(),
                    "text": document_text,
                }
            ),
        )

        result = try_call_gemini_rest(prompt)

        if not result["success"]:
            raise WorkflowExtractionError(result["error"])

        try:
            return WorkflowExtraction.model_validate_json(result["output"])

        except ValidationError as e:
            raise WorkflowExtractionError(
                f"Invalid workflow extraction: {e}"
            ) from e