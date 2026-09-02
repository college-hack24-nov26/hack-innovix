from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.models import ClinicalSession, Document, Patient
from app.security.decorators import role_required
from app.services.consent_service import has_valid_consent, record_consent
from app.services.history_service import complete_session, start_session
from app.services.timeline_service import build_timeline

bp = Blueprint("patient", __name__, url_prefix="/patient")


def _patient() -> Patient:
    return Patient.query.get_or_404(current_user.patient_id)


def _require_consent():
    patient = _patient()
    if not has_valid_consent(patient):
        flash("Please review and provide consent before continuing.", "info")
        return redirect(url_for("patient.consent"))
    return None


@bp.route("/dashboard")
@role_required("patient")
def dashboard():
    patient = _patient()
    session = ClinicalSession.query.filter_by(patient_id=patient.id).order_by(ClinicalSession.created_at.desc()).first()
    progress = session.completion_percentage if session else 0
    return render_template("patient/dashboard.html", patient=patient, progress=progress, session=session)


@bp.route("/consent", methods=["GET", "POST"])
@role_required("patient")
def consent():
    patient = _patient()
    if request.method == "POST":
        granted = request.form.get("decision") == "give"
        record_consent(patient, granted, patient.language or "en", current_user.id)
        if granted:
            return redirect(url_for("patient.dashboard"))
        flash("Consent was declined. Clinical intake will not start.", "warning")
    return render_template("patient/consent.html", patient=patient)


@bp.route("/profile", methods=["GET", "POST"])
@role_required("patient")
def profile():
    patient = _patient()
    if request.method == "POST":
        patient.ayush_mode = request.form.get("ayush_mode") == "on"
        patient.department = request.form.get("department") or patient.department
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("patient.profile"))
    return render_template("patient/profile.html", patient=patient)


@bp.route("/interview")
@role_required("patient")
def interview():
    blocked = _require_consent()
    if blocked:
        return blocked
    patient = _patient()
    session = ClinicalSession.query.filter_by(patient_id=patient.id, status="in_progress").first()
    if not session:
        session = start_session(patient)
    return render_template("patient/interview.html", patient=patient, session=session)


@bp.route("/documents")
@role_required("patient")
def documents():
    blocked = _require_consent()
    if blocked:
        return blocked
    patient = _patient()
    docs = Document.query.filter_by(patient_id=patient.id).order_by(Document.created_at.desc()).all()
    return render_template("patient/documents.html", patient=patient, documents=docs)


@bp.route("/timeline")
@role_required("patient")
def timeline():
    patient = _patient()
    return render_template("patient/timeline.html", patient=patient, items=build_timeline(patient.id))


@bp.route("/review")
@role_required("patient")
def review():
    patient = _patient()
    session = ClinicalSession.query.filter_by(patient_id=patient.id).order_by(ClinicalSession.created_at.desc()).first()
    answers = session.answers if session else []
    return render_template("patient/review.html", patient=patient, session=session, answers=answers)


@bp.route("/submit", methods=["POST"])
@role_required("patient")
def submit():
    patient = _patient()
    session = ClinicalSession.query.filter_by(patient_id=patient.id, status="in_progress").first()
    if session:
        complete_session(session)
    flash("Your information has been submitted for clinician review.", "success")
    return redirect(url_for("patient.completed"))


@bp.route("/completed")
@role_required("patient")
def completed():
    return render_template("patient/completed.html", patient=_patient())
