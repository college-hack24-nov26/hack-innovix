import re
from datetime import date

from flask import current_app

from app.extensions import db
from app.models import Document, DocumentExtraction, LabResult, MedicalEvent, Medication
from app.ocr.mock_provider import MockOCRProvider
from app.ocr.tesseract_provider import TesseractOCRProvider


def get_ocr_provider():
    name = current_app.config.get("OCR_PROVIDER", "mock").lower()
    if name == "tesseract":
        return TesseractOCRProvider()
    return MockOCRProvider()


def classify_document(text: str) -> str:
    t = text.lower()
    if "hemoglobin" in t or "g/dl" in t or "laboratory" in t:
        return "Laboratory Report"
    if "metformin" in t or "mg" in t and "twice" in t:
        return "Prescription"
    if "discharge" in t:
        return "Discharge Summary"
    if "imaging" in t or "x-ray" in t:
        return "Imaging Report"
    if "surgery" in t or "procedure" in t:
        return "Surgery Record"
    return "Other"


def extract_entities(document: Document, text: str) -> None:
    med = re.search(r"Medication:\s*(.+)", text, re.I)
    if med:
        raw = med.group(1).strip()
        dose = re.search(r"(\d+\s*mg)", raw, re.I)
        freq = re.search(r"(once|twice|thrice|\d+\s*times).+", raw, re.I)
        duration = re.search(r"for\s+(.+)", raw, re.I)
        db.session.add(
            Medication(
                patient_id=document.patient_id,
                document_id=document.id,
                name=raw.split()[0],
                dose=dose.group(1) if dose else None,
                frequency=freq.group(0) if freq else None,
                duration=duration.group(1) if duration else None,
                source_note=f"Prescription uploaded on {document.created_at.strftime('%d %B %Y') if document.created_at else 'unknown date'}",
            )
        )
        _add_field(document, "medication", raw)

    lab = re.search(r"Hemoglobin\s+([0-9.]+)\s*g/dL.*?Reference\s+([0-9.\-–]+)\s*g/dL", text, re.I)
    if lab:
        value = float(lab.group(1))
        ref = lab.group(2).replace("–", "-")
        parts = ref.split("-")
        status = "Reference range unavailable."
        if len(parts) == 2:
            try:
                low, high = float(parts[0]), float(parts[1])
                status = "Outside supplied reference range" if value < low or value > high else "Within supplied reference range"
            except ValueError:
                status = "Reference range unavailable."
        db.session.add(
            LabResult(
                patient_id=document.patient_id,
                document_id=document.id,
                test_name="Hemoglobin",
                result_value=str(value),
                unit="g/dL",
                reference_range=f"{ref} g/dL",
                status_label=status,
                collected_on=document.document_date,
            )
        )
        _add_field(document, "investigation", f"Hemoglobin {value} g/dL")

    dx = re.search(r"Diagnosis as written:\s*(.+)", text, re.I)
    if dx:
        _add_field(document, "diagnosis", dx.group(1).strip())
        db.session.add(
            MedicalEvent(
                patient_id=document.patient_id,
                document_id=document.id,
                event_type="diagnosis",
                title=dx.group(1).strip(),
                event_date=document.document_date or date.today(),
                source_note=f"Document uploaded on {document.created_at.strftime('%d %B %Y') if document.created_at else 'unknown date'}",
            )
        )

    name = re.search(r"Patient:\s*(.+)", text, re.I)
    if name:
        _add_field(document, "patient_name", name.group(1).strip())


def _add_field(document: Document, field_name: str, field_value: str) -> None:
    db.session.add(
        DocumentExtraction(
            document_id=document.id,
            field_name=field_name,
            field_value=field_value,
            confidence=0.72,
        )
    )


def process_document(document: Document) -> str:
    provider = get_ocr_provider()
    text = provider.extract_text(document.stored_path)
    document.ocr_text = text
    document.category = classify_document(text)
    document.status = "processed"
    extract_entities(document, text)
    db.session.commit()
    return text
