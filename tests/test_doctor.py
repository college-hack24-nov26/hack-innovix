from app.extensions import db
from app.models import AuditLog, Patient, User

DOCTOR_FORM = {
    "full_name": "Dr. Test Doctor",
    "email": "Doc@Example.com",
    "department": "Cardiology",
    "language": "en",
    "password": "password1",
    "confirm": "password1",
}


def _make_patient(email="pat@example.com"):
    patient = Patient(first_name="Pat", last_name="Ient", age=40)
    db.session.add(patient)
    db.session.flush()
    user = User(email=email, full_name="Pat Ient", role="patient", patient_id=patient.id)
    user.set_password("password1")
    db.session.add(user)
    db.session.commit()
    return patient, user


def test_doctor_login_page(client):
    assert client.get("/doctor/login").status_code == 200


def test_doctor_register_then_dashboard(client):
    res = client.post("/doctor/register", data=DOCTOR_FORM)
    assert res.status_code == 302
    user = User.query.filter_by(email="doc@example.com").one()
    assert user.role == "doctor" and user.department == "Cardiology"
    assert client.get("/doctor/dashboard").status_code == 200


def test_doctor_login_rejects_patient(client):
    _make_patient()
    res = client.post("/doctor/login", data={"email": "pat@example.com", "password": "password1"})
    assert res.status_code == 200
    assert client.get("/doctor/dashboard").status_code in (302, 403)


def test_doctor_sees_patient_login_info(client):
    patient, user = _make_patient()
    db.session.add(AuditLog(user_id=user.id, action="login", resource_type="user", resource_id=str(user.id)))
    db.session.commit()
    client.post("/doctor/register", data=DOCTOR_FORM)

    listing = client.get("/doctor/patients")
    assert listing.status_code == 200
    assert b"pat@example.com" in listing.data

    found = client.get("/doctor/patients?q=pat@example")
    assert b"pat@example.com" in found.data

    detail = client.get(f"/doctor/patient/{patient.id}")
    assert detail.status_code == 200
    assert b"Patient login information" in detail.data
    assert b"Total logins:</strong> 1" in detail.data
    assert user.password_hash.encode() not in detail.data


def test_registration_writes_excel_without_passwords(client, tmp_path):
    from openpyxl import load_workbook

    client.application.instance_path = str(tmp_path)
    client.post("/doctor/register", data=DOCTOR_FORM)
    path = tmp_path / "exports" / "medikiosk_users.xlsx"
    assert path.exists()
    wb = load_workbook(path)
    assert wb.sheetnames == ["Doctors", "Patients"]
    doctors = [[c.value for c in row] for row in wb["Doctors"].iter_rows(min_row=2)]
    assert doctors[0][1:3] == ["Dr. Test Doctor", "doc@example.com"]
    flat = " ".join(str(c.value) for ws in wb for row in ws.iter_rows() for c in row)
    assert "pbkdf2" not in flat and "scrypt" not in flat and "password1" not in flat


def test_doctor_can_download_excel(client, tmp_path):
    client.application.instance_path = str(tmp_path)
    client.post("/doctor/register", data=DOCTOR_FORM)
    res = client.get("/doctor/export/users.xlsx")
    assert res.status_code == 200
    assert res.data[:2] == b"PK"


def test_patient_cannot_download_excel(client):
    _make_patient()
    client.post("/login", data={"email": "pat@example.com", "password": "password1"})
    assert client.get("/doctor/export/users.xlsx").status_code in (302, 403)
