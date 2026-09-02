from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.integrations.fhir import export_patient_bundle
from app.models import Patient


def test_fhir_bundle():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        p = Patient(first_name="A", last_name="B")
        db.session.add(p)
        db.session.commit()
        bundle = export_patient_bundle(p)
        assert bundle["resourceType"] == "Bundle"
        db.drop_all()
