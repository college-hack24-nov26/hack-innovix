from app.extensions import db
from app.models.mixins import TimestampMixin


class DoctorReview(TimestampMixin, db.Model):
    __tablename__ = "doctor_reviews"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    summary_id = db.Column(db.Integer, db.ForeignKey("clinical_summaries.id"))
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    notes = db.Column(db.Text)
    decision = db.Column(db.String(32), default="draft")

    doctor = db.relationship("User")
