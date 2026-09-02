from app.extensions import db
from app.models.mixins import TimestampMixin


class ClinicalSession(TimestampMixin, db.Model):
    __tablename__ = "clinical_sessions"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    status = db.Column(db.String(32), default="in_progress", index=True)
    current_section = db.Column(db.String(80))
    current_question_key = db.Column(db.String(80))
    chief_complaint = db.Column(db.String(255))
    ayush_enabled = db.Column(db.Boolean, default=False)
    completion_percentage = db.Column(db.Integer, default=0)
    red_flag_level = db.Column(db.String(16), default="LOW")
    missing_fields = db.Column(db.JSON, default=list)
    started_at = db.Column(db.DateTime, server_default=db.func.now())
    completed_at = db.Column(db.DateTime)
    kiosk_mode = db.Column(db.Boolean, default=False)

    patient = db.relationship("Patient", back_populates="sessions")
    answers = db.relationship("ClinicalAnswer", back_populates="session", cascade="all, delete-orphan")
