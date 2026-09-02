from app.extensions import db
from app.models.mixins import TimestampMixin


class DocumentExtraction(TimestampMixin, db.Model):
    __tablename__ = "document_extractions"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=False, index=True)
    field_name = db.Column(db.String(80), nullable=False)
    field_value = db.Column(db.Text)
    confidence = db.Column(db.Float, default=0.7)
    reviewed = db.Column(db.Boolean, default=False)
    confirmed = db.Column(db.Boolean, default=False)

    document = db.relationship("Document", back_populates="extractions")
