from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from pathlib import Path
import uuid

from app.extensions import csrf, db
from app.i18n import translate
from app.integrations.fhir import export_patient_bundle
from app.integrations.mock_abdm import MockABDMClient
from app.models import ClinicalSession, ClinicalSummary, Document, Patient, TriageAlert
from app.ocr.extractor import process_document
from app.routes.documents import _validate_file
from app.security.decorators import role_required
from app.services.audit_service import log_action
from app.services.history_service import complete_session, question_payload, record_answer, start_session
from app.services.summary_service import generate_summary, update_summary, verify_summary
from app.services.timeline_service import build_timeline

bp = Blueprint("api", __name__, url_prefix="/api")


def _patient_for_user():
    if current_user.role == "patient":
        return Patient.query.get_or_404(current_user.patient_id)
    pid = request.args.get("patient_id") or request.json.get("patient_id") if request.is_json else request.form.get("patient_id")
    if pid:
        return Patient.query.get_or_404(int(pid))
    return None


@bp.route("/interview/start", methods=["POST"])
@login_required
def interview_start():
    patient = _patient_for_user()
    kiosk = bool(request.json.get("kiosk")) if request.is_json else False
    session = start_session(patient, kiosk_mode=kiosk)
    payload = question_payload(session, translate)
    payload["session_id"] = session.id
    return jsonify(payload)


@bp.route("/interview/<int:session_id>/answer", methods=["POST"])
@login_required
def interview_answer(session_id):
    session = ClinicalSession.query.get_or_404(session_id)
    data = request.get_json(force=True)
    payload = record_answer(session, data.get("question_key"), data.get("value") or "", data.get("source") or "text", translate)
    payload["session_id"] = session.id
    if payload.get("emergency"):
        payload["patient_message"] = translate("emergency_notice")
    return jsonify(payload)


@bp.route("/interview/<int:session_id>/next-question")
@login_required
def next_question(session_id):
    session = ClinicalSession.query.get_or_404(session_id)
    payload = question_payload(session, translate)
    payload["session_id"] = session.id
    return jsonify(payload)


@bp.route("/interview/<int:session_id>/complete", methods=["POST"])
@login_required
def interview_complete(session_id):
    session = ClinicalSession.query.get_or_404(session_id)
    complete_session(session)
    return jsonify({"status": "completed"})


@bp.route("/documents/upload", methods=["POST"])
@login_required
def upload_document():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file"}), 400
    err = _validate_file(file)
    if err:
        return jsonify({"error": err}), 400
    patient = _patient_for_user()
    if not patient:
        return jsonify({"error": "Patient required"}), 400
    filename = secure_filename(file.filename)
    stored = f"{uuid.uuid4().hex}_{filename}"
    dest_dir = Path(current_app.config["UPLOAD_FOLDER"]) / "documents"
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / stored
    file.save(path)
    if path.stat().st_size > current_app.config["MAX_CONTENT_LENGTH"]:
        path.unlink(missing_ok=True)
        return jsonify({"error": "File too large"}), 400
    doc = Document(
        patient_id=patient.id,
        filename=filename,
        stored_path=str(path),
        mime_type=file.mimetype,
        size_bytes=path.stat().st_size,
        status="uploaded",
    )
    db.session.add(doc)
    db.session.commit()
    log_action(current_user.id, "document_upload", "document", doc.id)
    return jsonify({"id": doc.id, "filename": filename, "status": doc.status})


@bp.route("/documents/<int:doc_id>")
@login_required
def get_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    log_action(current_user.id, "document_view", "document", doc.id)
    return jsonify(
        {
            "id": doc.id,
            "filename": doc.filename,
            "category": doc.category,
            "status": doc.status,
            "ocr_text": doc.ocr_text,
            "extractions": [{"id": e.id, "field": e.field_name, "value": e.field_value, "confirmed": e.confirmed} for e in doc.extractions],
        }
    )


@bp.route("/documents/<int:doc_id>/process", methods=["POST"])
@login_required
def process_doc(doc_id):
    doc = Document.query.get_or_404(doc_id)
    process_document(doc)
    return jsonify({"id": doc.id, "status": doc.status, "category": doc.category})


@bp.route("/patient/<int:patient_id>/timeline")
@login_required
def timeline(patient_id):
    return jsonify({"items": build_timeline(patient_id)})


@bp.route("/summary/<int:patient_id>/generate", methods=["POST"])
@role_required("doctor", "admin")
def summary_generate(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    summary = generate_summary(patient, current_user.id)
    return jsonify({"id": summary.id, "status": summary.status, "version": summary.version, "content": summary.content_json})


@bp.route("/summary/<int:patient_id>", methods=["GET"])
@login_required
def summary_get(patient_id):
    summary = ClinicalSummary.query.filter_by(patient_id=patient_id).order_by(ClinicalSummary.version.desc()).first()
    if not summary:
        return jsonify({"error": "Not available"}), 404
    return jsonify({"id": summary.id, "status": summary.status, "content": summary.content_json, "disclaimer": summary.disclaimer})


@bp.route("/summary/<int:summary_id>", methods=["PUT"])
@role_required("doctor", "admin")
def summary_put(summary_id):
    summary = ClinicalSummary.query.get_or_404(summary_id)
    update_summary(summary, request.get_json(force=True), current_user.id)
    return jsonify({"id": summary.id, "status": summary.status})


@bp.route("/summary/<int:summary_id>/verify", methods=["POST"])
@role_required("doctor", "admin")
def summary_verify(summary_id):
    summary = ClinicalSummary.query.get_or_404(summary_id)
    verify_summary(summary, current_user.id)
    return jsonify({"id": summary.id, "status": summary.status})


@bp.route("/triage/alerts")
@role_required("triage", "doctor", "admin")
def triage_alerts():
    items = TriageAlert.query.order_by(TriageAlert.created_at.desc()).limit(50).all()
    return jsonify(
        {
            "alerts": [
                {
                    "id": a.id,
                    "patient": a.patient.full_name if a.patient else "",
                    "age": a.patient.age if a.patient else None,
                    "complaint": a.complaint,
                    "severity": a.severity,
                    "status": a.status,
                    "message": a.message,
                    "time": a.created_at.isoformat() if a.created_at else None,
                    "patient_id": a.patient_id,
                }
                for a in items
            ]
        }
    )


@bp.route("/triage/alerts/<int:alert_id>/acknowledge", methods=["POST"])
@role_required("triage", "doctor", "admin")
def ack_alert(alert_id):
    from datetime import datetime

    alert = TriageAlert.query.get_or_404(alert_id)
    alert.status = "acknowledged"
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"ok": True})


@bp.route("/fhir/export/<int:patient_id>", methods=["POST"])
@role_required("doctor", "admin")
def fhir_export(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return jsonify(export_patient_bundle(patient, current_user.id))


@bp.route("/abdm/sync/<int:patient_id>", methods=["POST"])
@role_required("doctor", "admin")
def abdm_sync(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return jsonify(MockABDMClient().sync_patient(patient, current_user.id))


@bp.route("/notifications")
@login_required
def notifications():
    from app.models import Notification

    items = Notification.query.filter(
        db.or_(Notification.user_id == current_user.id, Notification.role_target == current_user.role)
    ).order_by(Notification.created_at.desc()).limit(20).all()
    return jsonify({"items": [{"id": n.id, "title": n.title, "body": n.body, "link": n.link} for n in items]})
