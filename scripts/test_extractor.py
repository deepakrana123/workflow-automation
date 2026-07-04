from pathlib import Path

from app.knowledge_ingestions.extractor import DocumentExtractor

extractor = DocumentExtractor()

for pdf in [
    r"C:\Users\Devendra\Downloads\sample_text.pdf",
    r"C:\Users\Devendra\Downloads\sample_scanned.pdf",
]:
    print("=" * 80)
    print(pdf)

    text = extractor.extract(Path(pdf))

    print(text[:500])