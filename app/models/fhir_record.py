from app.extensions import db
from app.models.mixins import TimestampMixin


class FHIRRecord(TimestampMixin, db.Model):
    __tablename__ = "fhir_records"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    resource_type = db.Column(db.String(80), default="Bundle")
    payload = db.Column(db.JSON, default=dict)
    exported_at = db.Column(db.DateTime, server_default=db.func.now())
