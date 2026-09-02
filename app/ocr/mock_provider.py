from pathlib import Path

from app.ocr.base import OCRProvider

DEMO_TEXT = """
Patient: Demo Patient
Date: 12 March 2026
Hospital: Demo General Hospital
Diagnosis as written: Type 2 diabetes mellitus (as recorded on source document)
Medication: Metformin 500 mg twice daily for 30 days
Investigation: Hemoglobin 10.2 g/dL Reference 12-16 g/dL
Procedure: None recorded
"""


class MockOCRProvider(OCRProvider):
    def extract_text(self, file_path: str) -> str:
        name = Path(file_path).name
        return f"{DEMO_TEXT}\nSource file: {name}\n"
