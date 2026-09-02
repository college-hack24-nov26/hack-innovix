from app.extensions import db
from app.models.mixins import TimestampMixin


class ClinicalAnswer(TimestampMixin, db.Model):
    __tablename__ = "clinical_answers"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("clinical_sessions.id"), nullable=False, index=True)
    question_key = db.Column(db.String(80), nullable=False, index=True)
    section = db.Column(db.String(80), nullable=False)
    value = db.Column(db.Text)
    source = db.Column(db.String(32), default="text")

    session = db.relationship("ClinicalSession", back_populates="answers")
