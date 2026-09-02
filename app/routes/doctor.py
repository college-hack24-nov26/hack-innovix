from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.models import AuditLog, ClinicalSession, ClinicalSummary, Document, DoctorReview, Patient, TriageAlert
from app.security.decorators import role_required
from app.security.permissions import can_access_patient
from app.services.audit_service import log_action
from app.services.summary_service import generate_summary, update_summary, verify_summary
from app.services.timeline_service import build_timeline

bp = Blueprint("doctor", __name__, url_prefix="/doctor")


@bp.route("/dashboard")
@role_required("doctor", "admin")
def dashboard():
    from datetime import date

    today = date.today()
    patients_today = ClinicalSession.query.filter(db.func.date(ClinicalSession.created_at) == today).count()
    completed = ClinicalSession.query.filter_by(status="completed").count()
    pending = ClinicalSummary.query.filter_by(status="DRAFT").count()
    alerts = TriageAlert.query.filter_by(status="open").count()
    docs = Document.query.filter_by(status="processed").count()
    done = ClinicalSession.query.filter(ClinicalSession.completed_at.isnot(None)).all()
    if done:
        seconds = []
        for s in done:
            start = s.started_at or s.created_at
            if start and s.completed_at:
                seconds.append((s.completed_at - start).total_seconds())
        avg_intake = f"{int(sum(seconds) / len(seconds) / 60)} min" if seconds else "Not available"
    else:
        avg_intake = "Not available"
    return render_template(
        "doctor/dashboard.html",
        patients_today=patients_today,
        completed=completed,
        pending=pending,
        alerts=alerts,
        docs=docs,
        avg_intake=avg_intake,
    )


@bp.route("/documents")
@role_required("doctor", "admin")
def all_documents():
    documents = Document.query.order_by(Document.created_at.desc()).limit(120).all()
    return render_template("doctor/documents.html", documents=documents)


@bp.route("/histories")
@role_required("doctor", "admin")
def histories():
    sessions = ClinicalSession.query.order_by(ClinicalSession.created_at.desc()).limit(80).all()
    return render_template("doctor/histories.html", sessions=sessions)


@bp.route("/patients")
@role_required("doctor", "admin")
def patients():
    q = request.args.get("q", "").strip()
    query = Patient.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Patient.first_name.ilike(like),
                Patient.last_name.ilike(like),
                Patient.hospital_patient_id.ilike(like),
                Patient.abha_id.ilike(like),
            )
        )
    return render_template("doctor/patients.html", patients=query.order_by(Patient.created_at.desc()).all(), q=q)


@bp.route("/queue")
@role_required("doctor", "admin")
def queue():
    sessions = ClinicalSession.query.order_by(ClinicalSession.created_at.desc()).limit(50).all()
    return render_template("doctor/queue.html", sessions=sessions)


@bp.route("/patient/<int:patient_id>")
@role_required("doctor", "admin", "triage")
def patient_view(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if not can_access_patient(current_user, patient):
        abort(403)
    log_action(current_user.id, "patient_record_access", "patient", patient.id)
    summary = ClinicalSummary.query.filter_by(patient_id=patient.id).order_by(ClinicalSummary.version.desc()).first()
    return render_template(
        "doctor/patient.html",
        patient=patient,
        tab="overview",
        summary=summary,
        documents=patient.documents,
        items=build_timeline(patient.id),
        alerts=patient.alerts,
    )


@bp.route("/patient/<int:patient_id>/history")
@role_required("doctor", "admin")
def history(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    log_action(current_user.id, "patient_record_access", "patient", patient.id)
    session = ClinicalSession.query.filter_by(patient_id=patient.id).order_by(ClinicalSession.created_at.desc()).first()
    return render_template("doctor/patient.html", patient=patient, tab="history", session=session, documents=patient.documents, items=build_timeline(patient.id), summary=None)


@bp.route("/patient/<int:patient_id>/documents")
@role_required("doctor", "admin")
def documents(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template("doctor/patient.html", patient=patient, tab="documents", documents=patient.documents, items=build_timeline(patient.id), summary=None)


@bp.route("/patient/<int:patient_id>/timeline")
@role_required("doctor", "admin")
def timeline(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template("doctor/patient.html", patient=patient, tab="timeline", items=build_timeline(patient.id), documents=patient.documents, summary=None)


@bp.route("/patient/<int:patient_id>/review", methods=["GET", "POST"])
@role_required("doctor", "admin")
def review(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    summary = ClinicalSummary.query.filter_by(patient_id=patient.id).order_by(ClinicalSummary.version.desc()).first()
    if request.method == "POST" and summary:
        action = request.form.get("action")
        if action == "generate":
            summary = generate_summary(patient, current_user.id)
        elif action == "save":
            data = {k: request.form.get(k, "") for k in (summary.content_json or {})}
            update_summary(summary, data, current_user.id)
        elif action == "confirm":
            verify_summary(summary, current_user.id)
        elif action == "reject":
            summary.status = "REJECTED"
            db.session.commit()
        notes = request.form.get("notes")
        if notes:
            db.session.add(DoctorReview(patient_id=patient.id, summary_id=summary.id, doctor_id=current_user.id, notes=notes, decision=action or "draft"))
            db.session.commit()
        return redirect(url_for("doctor.review", patient_id=patient.id))
    if request.method == "POST" and not summary and request.form.get("action") == "generate":
        generate_summary(patient, current_user.id)
        return redirect(url_for("doctor.review", patient_id=patient.id))
    return render_template("doctor/patient.html", patient=patient, tab="review", summary=summary, documents=patient.documents, items=build_timeline(patient.id))


@bp.route("/patient/<int:patient_id>/notes", methods=["GET", "POST"])
@role_required("doctor", "admin")
def notes(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if request.method == "POST":
        db.session.add(
            DoctorReview(
                patient_id=patient.id,
                doctor_id=current_user.id,
                notes=request.form.get("notes"),
                decision="note",
            )
        )
        db.session.commit()
        log_action(current_user.id, "summary_editing", "doctor_review", patient.id)
        return redirect(url_for("doctor.notes", patient_id=patient.id))
    reviews = DoctorReview.query.filter_by(patient_id=patient.id).order_by(DoctorReview.created_at.desc()).all()
    return render_template(
        "doctor/patient.html",
        patient=patient,
        tab="notes",
        reviews=reviews,
        documents=patient.documents,
        items=build_timeline(patient.id),
        summary=None,
    )


@bp.route("/patient/<int:patient_id>/audit")
@role_required("doctor", "admin")
def patient_audit(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    logs = (
        AuditLog.query.filter(AuditLog.resource_type.in_(["patient", "document", "clinical_summary"]))
        .filter(AuditLog.resource_id == str(patient.id))
        .order_by(AuditLog.created_at.desc())
        .limit(80)
        .all()
    )
    return render_template(
        "doctor/patient.html",
        patient=patient,
        tab="audit",
        logs=logs,
        documents=patient.documents,
        items=build_timeline(patient.id),
        summary=None,
    )
