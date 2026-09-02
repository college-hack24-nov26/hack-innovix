from app.extensions import db
from app.models.mixins import TimestampMixin


class Consent(TimestampMixin, db.Model):
    __tablename__ = "consents"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    consent_version = db.Column(db.String(16), nullable=False)
    consent_type = db.Column(db.String(32), nullable=False)
    granted = db.Column(db.Boolean, nullable=False)
    consent_timestamp = db.Column(db.DateTime, server_default=db.func.now(), index=True)
    language = db.Column(db.String(8), default="en")

    patient = db.relationship("Patient", back_populates="consents")
