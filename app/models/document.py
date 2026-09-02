from app.extensions import db
from app.models.mixins import TimestampMixin


class Document(TimestampMixin, db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    stored_path = db.Column(db.String(500), nullable=False)
    mime_type = db.Column(db.String(80))
    category = db.Column(db.String(64), default="Other")
    document_date = db.Column(db.Date, index=True)
    status = db.Column(db.String(32), default="uploaded")
    ocr_text = db.Column(db.Text)
    size_bytes = db.Column(db.Integer)

    patient = db.relationship("Patient", back_populates="documents")
    extractions = db.relationship("DocumentExtraction", back_populates="document")
