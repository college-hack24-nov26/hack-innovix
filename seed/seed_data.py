"""Load users, including a clinician account for local use."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.extensions import db
from app.models import LabResult, MedicalEvent, Patient, User
from app.services.excel_service import export_path, sync_users_workbook

DOCTOR_EMAIL = "dr.sharma@medikiosk.com"
DOCTOR_PASSWORD = "Clinic@2026"


def _ensure_user(email, full_name, role, password, **kwargs):
    user = User.query.filter_by(email=email.lower()).first()
    if user is None:
        user = User(email=email.lower(), full_name=full_name, role=role, **kwargs)
        user.set_password(password)
        db.session.add(user)
        return user
    user.full_name = full_name
    user.role = role
    for key, value in kwargs.items():
        setattr(user, key, value)
    user.set_password(password)
    return user


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()
        _ensure_user("admin@medikiosk.com", "System Admin", "admin", "Admin123!")
        _ensure_user(
            DOCTOR_EMAIL,
            "Dr. Ananya Sharma",
            "doctor",
            DOCTOR_PASSWORD,
            department="General Medicine",
        )
        _ensure_user("triage@medikiosk.com", "Triage Desk", "triage", "Triage123!")

        patient = Patient.query.filter_by(hospital_patient_id="HOSP-1001").first()
        if patient is None:
            patient = Patient(
                first_name="Asha",
                last_name="Kulkarni",
                age=54,
                gender="female",
                language="en",
                hospital_patient_id="HOSP-1001",
                abha_id="12-3456-7890-1234",
            )
            db.session.add(patient)
            db.session.flush()
            db.session.add(
                MedicalEvent(
                    patient_id=patient.id,
                    event_type="diagnosis",
                    title="Type 2 diabetes mellitus",
                    details="Recorded from prior consultation notes.",
                    source_note="Prior record",
                )
            )
            db.session.add(
                LabResult(
                    patient_id=patient.id,
                    test_name="Hemoglobin",
                    result_value="10.2",
                    unit="g/dL",
                    reference_range="12-16 g/dL",
                    status_label="Outside supplied reference range",
                )
            )
        linked = User.query.filter_by(patient_id=patient.id).first()
        if linked:
            linked.set_password("Patient123!")
        else:
            _ensure_user(
                "patient@medikiosk.com",
                "Asha Kulkarni",
                "patient",
                "Patient123!",
                patient_id=patient.id,
            )
        db.session.commit()
        print("Accounts ready.")
        sync_users_workbook()
        print(f"Excel file: {export_path()}")
        print(f"Doctor login: {DOCTOR_EMAIL} / {DOCTOR_PASSWORD}  (sign in at /doctor/login)")


if __name__ == "__main__":
    seed()
