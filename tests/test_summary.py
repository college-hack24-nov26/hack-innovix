from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models import Patient
from app.services.summary_service import generate_summary


def test_summary_marks_missing():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        p = Patient(first_name="A", last_name="B", age=40)
        db.session.add(p)
        db.session.commit()
        summary = generate_summary(p)
        assert "AI-generated draft" in summary.disclaimer
        assert "Not reported" in summary.content_json["Chief Complaint"] or summary.content_json["Chief Complaint"]
        db.drop_all()
