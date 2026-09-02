from app.extensions import db
from app.models.mixins import TimestampMixin


class ClinicalHistory(TimestampMixin, db.Model):
    __tablename__ = "clinical_histories"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    session_id = db.Column(db.Integer, db.ForeignKey("clinical_sessions.id"))
    structured_json = db.Column(db.JSON, default=dict)
    ayush_json = db.Column(db.JSON, default=dict)

    patient = db.relationship("Patient", back_populates="histories")
