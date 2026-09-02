from flask import Blueprint, redirect, render_template, session, url_for
from flask_login import current_user

from app.models import Patient
from app.security.decorators import role_required

bp = Blueprint("kiosk", __name__)


@bp.route("/kiosk")
def kiosk():
    return render_template("kiosk/index.html")


@bp.route("/kiosk/session")
@role_required("patient", "admin")
def kiosk_session():
    patient = Patient.query.get(current_user.patient_id) if current_user.role == "patient" else None
    return render_template("kiosk/session.html", patient=patient)
