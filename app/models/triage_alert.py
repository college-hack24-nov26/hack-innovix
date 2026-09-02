from app.extensions import db
from app.models.mixins import TimestampMixin


class TriageAlert(TimestampMixin, db.Model):
    __tablename__ = "triage_alerts"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    session_id = db.Column(db.Integer, db.ForeignKey("clinical_sessions.id"))
    severity = db.Column(db.String(16), nullable=False, index=True)
    complaint = db.Column(db.String(255))
    message = db.Column(db.String(500))
    status = db.Column(db.String(32), default="open", index=True)
    acknowledged_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    acknowledged_at = db.Column(db.DateTime)

    patient = db.relationship("Patient", back_populates="alerts")
    acknowledger = db.relationship("User", foreign_keys=[acknowledged_by])
