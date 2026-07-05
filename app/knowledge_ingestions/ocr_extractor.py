from pathlib import Path
import pytesseract
from pdf2image import convert_from_path
from .exceptions import DocumentExtractionError
from app.core.setting import TESSERACT_PATH, POPPLER_PATH


class OCRExtractor:
    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_PATH)

    def extract(self, pdf_path: Path) -> str:
        if not pdf_path.exists():
            raise DocumentExtractionError(f"file not found: {pdf_path}")
        return self._extract_pdf(pdf_path)

    def _extract_pdf(self, file_path: Path) -> str:
        try:
            images = convert_from_path(file_path, poppler_path=POPPLER_PATH)
            page_texts = []
            for image in images:
                page_content = pytesseract.image_to_string(image, lang="eng").strip()
                if not page_content:
                    continue
                page_texts.append(page_content)
            if not page_texts:
                raise DocumentExtractionError(
                    f"Failed to extract text from PDF: {file_path}"
                )
            return "\n".join(page_texts)
        except DocumentExtractionError:
            raise
        except Exception as e:
            raise DocumentExtractionError(
                f"Failed to read PDF '{file_path.name}': {e}"
            ) from e
