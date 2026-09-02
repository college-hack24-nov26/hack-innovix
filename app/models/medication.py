from app.extensions import db
from app.models.mixins import TimestampMixin


class Medication(TimestampMixin, db.Model):
    __tablename__ = "medications"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"))
    name = db.Column(db.String(160), nullable=False)
    dose = db.Column(db.String(80))
    frequency = db.Column(db.String(80))
    duration = db.Column(db.String(80))
    source_note = db.Column(db.String(255))

    patient = db.relationship("Patient", back_populates="medications")
    document = db.relationship("Document")
