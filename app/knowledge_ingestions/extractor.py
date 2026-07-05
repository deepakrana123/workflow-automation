from pathlib import Path
from pypdf import PdfReader
from .exceptions import DocumentExtractionError
from .ocr_extractor import OCRExtractor


class DocumentExtractor:
    """
    Extract plain text from supported document types.
    """

    def __init__(self):
        self.ocr_extractor = OCRExtractor()

    def extract(self, file_path: Path) -> str:
        if not file_path.exists():
            raise DocumentExtractionError(f"file not found :{file_path}")
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return self._extract_pdf(file_path)
        raise DocumentExtractionError(f"Unsupported file type: {suffix}")

    def _extract_pdf(self, file_path: Path) -> str:
        try:
            reader = PdfReader(file_path)
            page_texts = []
            for page in reader.pages:
                page_content = page.extract_text()
                if not page_content:
                    continue
                page_texts.append(page_content)
            if not page_texts:
                return self.ocr_extractor.extract(file_path)
            return "\n".join(page_texts)
        except Exception as e:
            raise DocumentExtractionError(
                f"Failed to read PDF '{file_path.name}': {e}"
            ) from e
