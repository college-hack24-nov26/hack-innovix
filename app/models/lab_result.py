from app.extensions import db
from app.models.mixins import TimestampMixin


class LabResult(TimestampMixin, db.Model):
    __tablename__ = "lab_results"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"))
    test_name = db.Column(db.String(160), nullable=False)
    result_value = db.Column(db.String(80))
    unit = db.Column(db.String(40))
    reference_range = db.Column(db.String(80))
    status_label = db.Column(db.String(80))
    collected_on = db.Column(db.Date)

    patient = db.relationship("Patient", back_populates="lab_results")
    document = db.relationship("Document")
