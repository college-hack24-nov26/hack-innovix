"""Keeps an Excel copy of registered users (doctors and patients).

The database stays the source of truth. The workbook is rebuilt from it, so it
never drifts. Passwords and password hashes are never written.
"""
from pathlib import Path

from flask import current_app
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from app.extensions import db
from app.models import AuditLog, Patient, User

DOCTOR_COLUMNS = ["Doctor ID", "Full name", "Email", "Department", "Language", "Account active", "Registered", "Last login", "Total logins"]
PATIENT_COLUMNS = [
    "Patient ID", "Full name", "Age", "Gender", "Phone", "Language", "Department",
    "Hospital ID", "ABHA ID", "Login email", "Account active", "Registered", "Last login", "Total logins",
]


def login_info(patient_ids):
    """Patient login account details keyed by patient id. Never includes credentials."""
    info = {}
    if not patient_ids:
        return info
    users = User.query.filter(User.patient_id.in_(patient_ids)).all()
    by_user = {u.id: u for u in users}
    for u in users:
        info[u.patient_id] = {
            "email": u.email,
            "active": u.is_active,
            "registered": u.created_at,
            "last_login": None,
            "login_count": 0,
        }
    for user_id, last, count in _login_stats(list(by_user)):
        entry = info[by_user[user_id].patient_id]
        entry["last_login"] = last
        entry["login_count"] = count
    return info


def _login_stats(user_ids):
    if not user_ids:
        return []
    return (
        db.session.query(AuditLog.user_id, db.func.max(AuditLog.created_at), db.func.count(AuditLog.id))
        .filter(AuditLog.action == "login", AuditLog.user_id.in_(user_ids))
        .group_by(AuditLog.user_id)
        .all()
    )


def _fmt(value):
    return value.strftime("%Y-%m-%d %H:%M") if value else ""


def _sheet(ws, columns, rows):
    ws.append(columns)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2563EB")
        cell.alignment = Alignment(vertical="center")
    for row in rows:
        ws.append(row)
    ws.freeze_panes = "A2"
    for idx, col in enumerate(columns, start=1):
        width = max([len(str(col))] + [len(str(r[idx - 1])) for r in rows if r[idx - 1] is not None]) + 2
        ws.column_dimensions[get_column_letter(idx)].width = min(width, 40)


def build_workbook() -> Workbook:
    doctors = User.query.filter(User.role == "doctor").order_by(User.id).all()
    stats = {uid: (last, count) for uid, last, count in _login_stats([d.id for d in doctors])}
    doctor_rows = [
        [d.id, d.full_name, d.email, d.department or "", d.language or "", "Yes" if d.is_active else "No",
         _fmt(d.created_at), _fmt(stats.get(d.id, (None, 0))[0]), stats.get(d.id, (None, 0))[1]]
        for d in doctors
    ]

    patients = Patient.query.order_by(Patient.id).all()
    logins = login_info([p.id for p in patients])
    patient_rows = []
    for p in patients:
        lg = logins.get(p.id)
        patient_rows.append([
            p.id, p.full_name, p.age, p.gender or "", p.phone or "", p.language or "", p.department or "",
            p.hospital_patient_id or "", p.abha_id or "",
            lg["email"] if lg else "", ("Yes" if lg["active"] else "No") if lg else "",
            _fmt(lg["registered"]) if lg else _fmt(p.created_at),
            _fmt(lg["last_login"]) if lg else "", lg["login_count"] if lg else 0,
        ])

    wb = Workbook()
    _sheet(wb.active, DOCTOR_COLUMNS, doctor_rows)
    wb.active.title = "Doctors"
    _sheet(wb.create_sheet("Patients"), PATIENT_COLUMNS, patient_rows)
    return wb


def export_path() -> Path:
    folder = Path(current_app.instance_path) / "exports"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "medikiosk_users.xlsx"


def sync_users_workbook():
    """Rebuild the Excel file from the database. Never raises: sign-up must not fail over a spreadsheet."""
    try:
        path = export_path()
        build_workbook().save(path)
        return path
    except Exception:  # e.g. file open in Excel on Windows
        current_app.logger.exception("Could not update users Excel file")
        return None
