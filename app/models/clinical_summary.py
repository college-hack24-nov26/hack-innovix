from app.extensions import db
from app.models.mixins import TimestampMixin


class ClinicalSummary(TimestampMixin, db.Model):
    __tablename__ = "clinical_summaries"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    session_id = db.Column(db.Integer, db.ForeignKey("clinical_sessions.id"))
    content_json = db.Column(db.JSON, default=dict)
    content_text = db.Column(db.Text)
    status = db.Column(db.String(32), default="DRAFT", index=True)
    version = db.Column(db.Integer, default=1)
    verified_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    verified_at = db.Column(db.DateTime)
    disclaimer = db.Column(
        db.String(255),
        default="AI-generated draft — physician verification required.",
    )

    patient = db.relationship("Patient", back_populates="summaries")
    verifier = db.relationship("User", foreign_keys=[verified_by])
