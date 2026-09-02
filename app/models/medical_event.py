from app.extensions import db
from app.models.mixins import TimestampMixin


class MedicalEvent(TimestampMixin, db.Model):
    __tablename__ = "medical_events"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"))
    event_type = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    event_date = db.Column(db.Date, index=True)
    details = db.Column(db.Text)
    source_note = db.Column(db.String(255))

    patient = db.relationship("Patient", back_populates="events")
    document = db.relationship("Document")
