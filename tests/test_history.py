from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models import Patient
from app.services.history_service import record_answer, start_session


def _patient():
    p = Patient(first_name="A", last_name="B")
    db.session.add(p)
    db.session.commit()
    return p


def test_chief_complaint_flow():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        session = start_session(_patient())
        payload = record_answer(session, "chief_complaint", "Chest Pain", translate=lambda k: k)
        assert session.chief_complaint == "Chest Pain"
        assert "chest pain" in payload["question"]["prompt"].lower()
        db.drop_all()


def test_questions_depend_on_complaint():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        chest = start_session(_patient())
        fever = start_session(_patient())
        cough = start_session(_patient())
        q_chest = record_answer(chest, "chief_complaint", "Chest Pain", translate=lambda k: k)["question"]
        q_fever = record_answer(fever, "chief_complaint", "Fever", translate=lambda k: k)["question"]
        q_cough = record_answer(cough, "chief_complaint", "Cough", translate=lambda k: k)["question"]
        assert q_chest["prompt"] != q_fever["prompt"]
        assert q_fever["prompt"] != q_cough["prompt"]
        assert "chest" in q_chest["prompt"].lower()
        assert "fever" in q_fever["prompt"].lower()
        assert "cough" in q_cough["prompt"].lower()
        assert "spread" not in q_fever["prompt"].lower()
        db.drop_all()


def test_followup_uses_previous_answer():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        session = start_session(_patient())
        record_answer(session, "chief_complaint", "Fever", translate=lambda k: k)
        record_answer(session, "onset", "A few days ago", translate=lambda k: k)
        third = record_answer(session, "fever_pattern", "With chills", translate=lambda k: k)
        prompt = third["question"]["prompt"].lower()
        assert "spread" not in prompt
        assert third["question"]["key"] != "radiation"
        db.drop_all()
