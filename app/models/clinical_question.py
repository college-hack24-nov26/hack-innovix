from app.extensions import db
from app.models.mixins import TimestampMixin


class ClinicalQuestion(TimestampMixin, db.Model):
    __tablename__ = "clinical_questions"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False, index=True)
    section = db.Column(db.String(80), nullable=False, index=True)
    prompt_key = db.Column(db.String(160), nullable=False)
    question_type = db.Column(db.String(32), default="text")
    options = db.Column(db.JSON)
    follow_up_map = db.Column(db.JSON)
    ayush_only = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
