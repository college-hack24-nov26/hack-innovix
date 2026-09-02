from datetime import datetime

from app.extensions import db
from app.models import TriageAlert
from app.services.audit_service import log_action
from app.services.notification_service import notify_role

EMERGENCY_PATTERNS = (
    ("loss of consciousness", "EMERGENCY"),
    ("unconscious", "EMERGENCY"),
    ("severe bleeding", "EMERGENCY"),
    ("sudden facial weakness", "EMERGENCY"),
    ("sudden speech", "EMERGENCY"),
    ("cannot speak", "EMERGENCY"),
)

HIGH_PATTERNS = (
    ("severe chest pain", "HIGH"),
    ("chest pain", "HIGH"),
    ("breathing difficulty", "HIGH"),
    ("shortness of breath", "HIGH"),
    ("severe breath", "HIGH"),
)

MEDIUM_PATTERNS = (
    ("fever", "MEDIUM"),
    ("cough", "MEDIUM"),
    ("pain", "MEDIUM"),
)


class RedFlagEngine:
    def evaluate(self, answers: dict[str, str]) -> tuple[str, str]:
        blob = " ".join((v or "").lower() for v in answers.values())
        complaint = (answers.get("chief_complaint") or "").lower()
        combined = f"{complaint} {blob}"

        if "chest pain" in combined and any(k in combined for k in ("breath", "dyspnea", "shortness")):
            return "EMERGENCY", "Chest pain with breathing difficulty"

        for phrase, level in EMERGENCY_PATTERNS:
            if phrase in combined:
                return level, phrase
        for phrase, level in HIGH_PATTERNS:
            if phrase in combined:
                return level, phrase
        for phrase, level in MEDIUM_PATTERNS:
            if phrase in combined:
                return level, phrase
        return "LOW", "no_red_flag"


def apply_red_flags(session, answers: dict, user_id=None) -> str:
    level, reason = RedFlagEngine().evaluate(answers)
    session.red_flag_level = level
    if level in ("HIGH", "EMERGENCY"):
        existing = TriageAlert.query.filter_by(session_id=session.id, status="open").first()
        if not existing:
            alert = TriageAlert(
                patient_id=session.patient_id,
                session_id=session.id,
                severity=level,
                complaint=session.chief_complaint,
                message=reason,
                status="open",
            )
            db.session.add(alert)
            notify_role(
                "triage",
                f"{level} triage alert",
                f"Patient {session.patient_id}: {reason}",
                "/triage/alerts",
            )
            log_action(user_id, "triage_alert", "clinical_session", session.id, {"severity": level})
    db.session.commit()
    return level
