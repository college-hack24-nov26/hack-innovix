from app.extensions import db
from app.models import Patient, User


def test_patient_dashboard_requires_login(client):
    res = client.get("/patient/dashboard")
    assert res.status_code in (302, 401)
