from datetime import datetime

from app.extensions import db
from app.models import ClinicalAnswer, ClinicalHistory, ClinicalSession
from app.services.interview_engine import AYUSH_FLOW, CHIEF, answers_map, next_question, progress_for
from app.services.triage_service import apply_red_flags

AYUSH_KEYS = tuple(q["key"] for q in AYUSH_FLOW)


def start_session(patient, kiosk_mode=False) -> ClinicalSession:
    session = ClinicalSession(
        patient_id=patient.id,
        status="in_progress",
        current_section=CHIEF["section"],
        current_question_key=CHIEF["key"],
        ayush_enabled=bool(patient.ayush_mode),
        kiosk_mode=kiosk_mode,
        completion_percentage=0,
        missing_fields={"pending": dict(CHIEF), "pathway": None},
    )
    db.session.add(session)
    db.session.commit()
    return session


def question_payload(session: ClinicalSession, translate) -> dict:
    answers = answers_map(session)
    question = next_question(session, answers)
    index, total, percent = progress_for(session, answers)
    if not question:
        session.completion_percentage = 100
        session.current_question_key = None
        db.session.commit()
        return {"done": True, "progress": 100, "question": None, "index": total, "total": total}

    session.current_question_key = question["key"]
    session.current_section = question["section"]
    session.completion_percentage = percent
    db.session.commit()

    prompt = question["prompt"]
    prompt_key = question.get("prompt_key")
    if prompt_key and callable(translate):
        localized = translate(prompt_key)
        if localized and localized != prompt_key:
            prompt = localized

    return {
        "done": False,
        "progress": session.completion_percentage,
        "index": index,
        "total": total,
        "question": {
            "key": question["key"],
            "section": question["section"],
            "prompt": prompt,
            "type": question.get("type") or "text",
            "options": question.get("options") or [],
        },
        "red_flag_level": session.red_flag_level,
        "emergency": session.red_flag_level == "EMERGENCY",
        "pathway": (session.missing_fields or {}).get("pathway") if isinstance(session.missing_fields, dict) else None,
    }


def record_answer(session: ClinicalSession, question_key: str, value: str, source="text", translate=None) -> dict:
    answers = answers_map(session)
    pending = (session.missing_fields or {}).get("pending") if isinstance(session.missing_fields, dict) else None
    current = pending if isinstance(pending, dict) and pending.get("key") == question_key else None
    if not current and question_key == session.current_question_key:
        current = {"key": question_key, "section": session.current_section or "History of Present Illness"}
    if not current and question_key not in answers and question_key != CHIEF["key"]:
        current = {"key": question_key, "section": session.current_section or "History of Present Illness"}
    if question_key == CHIEF["key"]:
        current = dict(CHIEF)

    if not current:
        return {"error": "Unknown question"}

    existing = ClinicalAnswer.query.filter_by(session_id=session.id, question_key=question_key).first()
    if existing:
        existing.value = value
        existing.source = source
    else:
        db.session.add(
            ClinicalAnswer(
                session_id=session.id,
                question_key=question_key,
                section=current.get("section") or "History of Present Illness",
                value=value,
                source=source,
            )
        )
    db.session.flush()
    if question_key == "chief_complaint":
        session.chief_complaint = value

    meta = session.missing_fields if isinstance(session.missing_fields, dict) else {}
    if meta.get("pending") and meta["pending"].get("key") == question_key:
        meta["pending"] = None
        session.missing_fields = meta

    amap = answers_map(session)
    amap[question_key] = value
    apply_red_flags(session, amap)
    next_question(session, amap)
    db.session.commit()
    return question_payload(session, translate or (lambda k: k))


def complete_session(session: ClinicalSession) -> ClinicalHistory:
    amap = answers_map(session)
    clinical = {k: v for k, v in amap.items() if k not in AYUSH_KEYS}
    ayush = {k: v for k, v in amap.items() if k in AYUSH_KEYS}
    history = ClinicalHistory(
        patient_id=session.patient_id,
        session_id=session.id,
        structured_json=clinical,
        ayush_json=ayush,
    )
    session.status = "completed"
    session.completed_at = datetime.utcnow()
    session.completion_percentage = 100
    db.session.add(history)
    db.session.commit()
    return history
