from datetime import datetime

from app.ai import get_ai_provider
from app.ai.mock_provider import NOT_REPORTED
from app.ai.prompts.summary import SUMMARY_SYSTEM
from app.extensions import db
from app.models import ClinicalHistory, ClinicalSession, ClinicalSummary, Patient
from app.services.audit_service import log_action
from app.services.timeline_service import build_timeline

SECTIONS = [
    "Patient Information",
    "Chief Complaint",
    "History of Present Illness",
    "Past Medical History",
    "Past Surgical History",
    "Drug History",
    "Allergy History",
    "Family History",
    "Personal History",
    "Review of Systems",
    "Previous Investigations",
    "Medical Timeline",
    "AYUSH Assessment",
]


def _val(data: dict, *keys) -> str:
    for k in keys:
        if data.get(k):
            return data[k]
    return NOT_REPORTED


def build_structured(patient: Patient) -> dict:
    session = (
        ClinicalSession.query.filter_by(patient_id=patient.id)
        .order_by(ClinicalSession.created_at.desc())
        .first()
    )
    history = (
        ClinicalHistory.query.filter_by(patient_id=patient.id)
        .order_by(ClinicalHistory.created_at.desc())
        .first()
    )
    answers = (history.structured_json if history else {}) or {}
    ayush = (history.ayush_json if history else {}) or {}
    hpi_parts = [
        _val(answers, "onset"),
        _val(answers, "location"),
        _val(answers, "character"),
        _val(answers, "severity"),
        _val(answers, "radiation"),
        _val(answers, "aggravating"),
        _val(answers, "relieving"),
        _val(answers, "associated"),
    ]
    timeline = build_timeline(patient.id)
    timeline_text = "; ".join(f"{i.get('date') or 'undated'}: {i['title']}" for i in timeline) or NOT_REPORTED
    ayush_text = "; ".join(f"{k}: {v}" for k, v in ayush.items() if v) or NOT_REPORTED
    return {
        "Patient Information": f"{patient.full_name}, age {patient.age or NOT_REPORTED}, {patient.gender or NOT_REPORTED}",
        "Chief Complaint": (session.chief_complaint if session else None) or _val(answers, "chief_complaint"),
        "History of Present Illness": " | ".join(hpi_parts),
        "Past Medical History": _val(answers, "past_medical"),
        "Past Surgical History": _val(answers, "past_surgical"),
        "Drug History": _val(answers, "medications"),
        "Allergy History": _val(answers, "allergies"),
        "Family History": _val(answers, "family"),
        "Personal History": f"Diet: {_val(answers, 'diet')}; Sleep: {_val(answers, 'sleep')}; Substance: {_val(answers, 'substance')}; Occupation: {_val(answers, 'occupation')}",
        "Review of Systems": _val(answers, "ros"),
        "Previous Investigations": _val(answers, "investigations"),
        "Medical Timeline": timeline_text,
        "AYUSH Assessment": ayush_text,
    }


def generate_summary(patient: Patient, user_id=None) -> ClinicalSummary:
    structured = build_structured(patient)
    lines = ["AI-generated draft — physician verification required.", ""]
    for heading in SECTIONS:
        lines.append(f"{heading}: {structured.get(heading, NOT_REPORTED)}")
    fact_block = "\n".join(lines)
    provider = get_ai_provider()
    narrative = provider.complete(SUMMARY_SYSTEM, fact_block)
    previous = (
        ClinicalSummary.query.filter_by(patient_id=patient.id)
        .order_by(ClinicalSummary.version.desc())
        .first()
    )
    version = (previous.version + 1) if previous else 1
    summary = ClinicalSummary(
        patient_id=patient.id,
        content_json=structured,
        content_text=narrative,
        status="DRAFT",
        version=version,
    )
    db.session.add(summary)
    db.session.commit()
    log_action(user_id, "ai_summary_generation", "clinical_summary", summary.id)
    return summary


def update_summary(summary: ClinicalSummary, content_json: dict, user_id=None) -> ClinicalSummary:
    summary.content_json = content_json
    summary.content_text = "\n".join(f"{k}: {v}" for k, v in content_json.items())
    summary.status = "DRAFT"
    db.session.commit()
    log_action(user_id, "summary_editing", "clinical_summary", summary.id)
    return summary


def verify_summary(summary: ClinicalSummary, user_id: int) -> ClinicalSummary:
    summary.status = "VERIFIED"
    summary.verified_by = user_id
    summary.verified_at = datetime.utcnow()
    db.session.commit()
    log_action(user_id, "summary_verification", "clinical_summary", summary.id)
    return summary
