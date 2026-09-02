from datetime import datetime

from flask import current_app

from app.extensions import db
from app.models import Consent, Notification
from app.services.audit_service import log_action


def has_valid_consent(patient) -> bool:
    version = current_app.config.get("CONSENT_VERSION", "1.0")
    latest = (
        Consent.query.filter_by(patient_id=patient.id, granted=True, consent_version=version)
        .order_by(Consent.consent_timestamp.desc())
        .first()
    )
    return latest is not None


def record_consent(patient, granted: bool, language: str, user_id=None) -> Consent:
    item = Consent(
        patient_id=patient.id,
        consent_version=current_app.config.get("CONSENT_VERSION", "1.0"),
        consent_type="clinical_intake",
        granted=granted,
        language=language,
        consent_timestamp=datetime.utcnow(),
    )
    db.session.add(item)
    db.session.commit()
    log_action(user_id, "consent", "patient", patient.id, {"granted": granted})
    return item
