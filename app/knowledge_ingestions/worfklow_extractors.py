from pydantic import ValidationError
from app.nlp.llm_manager.providers.gemini_rest import try_call_gemini_rest
from app.knowledge_ingestions.prompts import WORKFLOW_EXTRACTION_PROMPT
from app.knowledge_ingestions.schemas import WorkflowExtraction
from app.knowledge_ingestions.exceptions import WorkflowExtractionError


class WorkflowExtractor:
    def extract(self, document_text: str) -> WorkflowExtraction:
        if not document_text.strip():
            raise WorkflowExtractionError("Document text is empty.")
        prompt = WORKFLOW_EXTRACTION_PROMPT.format(
            schema = WorkflowExtraction.model_json_schema(), text=document_text
        )

        result = try_call_gemini_rest(prompt)
        if not result["success"]:
            raise WorkflowExtractionError(result["error"])

        try:
            return WorkflowExtraction.model_validate_json(result["output"])

        except ValidationError as e:
            raise WorkflowExtractionError(f"Invalid workflow extraction: {e}") from e
