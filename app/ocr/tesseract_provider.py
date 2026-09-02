from pathlib import Path

from app.ocr.base import OCRProvider
from app.ocr.mock_provider import MockOCRProvider


class TesseractOCRProvider(OCRProvider):
    def extract_text(self, file_path: str) -> str:
        suffix = Path(file_path).suffix.lower()
        if suffix == ".pdf":
            from PyPDF2 import PdfReader

            reader = PdfReader(file_path)
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages).strip()
            return text or MockOCRProvider().extract_text(file_path)
        try:
            import pytesseract
            from PIL import Image

            return pytesseract.image_to_string(Image.open(file_path))
        except Exception:
            return MockOCRProvider().extract_text(file_path)
