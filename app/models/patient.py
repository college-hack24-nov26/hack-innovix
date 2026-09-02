from app.extensions import db
from app.models.mixins import TimestampMixin


class Patient(TimestampMixin, db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    hospital_patient_id = db.Column(db.String(64), unique=True, index=True)
    abha_id = db.Column(db.String(64), unique=True, index=True)
    simulated_id_type = db.Column(db.String(32))
    simulated_id_value = db.Column(db.String(64))
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(32))
    phone = db.Column(db.String(32))
    language = db.Column(db.String(8), default="en")
    department = db.Column(db.String(80), default="General Medicine")
    ayush_mode = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="patient", uselist=False)
    consents = db.relationship("Consent", back_populates="patient")
    sessions = db.relationship("ClinicalSession", back_populates="patient")
    documents = db.relationship("Document", back_populates="patient")
    medications = db.relationship("Medication", back_populates="patient")
    lab_results = db.relationship("LabResult", back_populates="patient")
    events = db.relationship("MedicalEvent", back_populates="patient")
    summaries = db.relationship("ClinicalSummary", back_populates="patient")
    alerts = db.relationship("TriageAlert", back_populates="patient")
    histories = db.relationship("ClinicalHistory", back_populates="patient")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
