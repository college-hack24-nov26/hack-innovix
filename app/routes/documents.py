from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename
from pathlib import Path
import uuid

from app.extensions import db
from app.models import Document, DocumentExtraction
from app.ocr.extractor import process_document
from app.security.decorators import role_required
from app.services.audit_service import log_action

bp = Blueprint("documents", __name__)


def _validate_file(file) -> str | None:
    filename = secure_filename(file.filename or "")
    if not filename or "." not in filename:
        return "Unsafe or missing filename."
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in current_app.config["ALLOWED_EXTENSIONS"]:
        return "File extension not allowed."
    mime = file.mimetype or ""
    if mime and mime not in current_app.config["ALLOWED_MIME"] and mime not in ("application/octet-stream",):
        return "MIME type not allowed."
    return None


@bp.route("/uploads/<path:filename>")
@role_required("patient", "doctor", "admin", "triage")
def uploaded_file(filename):
    folder = current_app.config["UPLOAD_FOLDER"] / "documents"
    log_action(current_user.id, "document_view", "document", filename)
    return send_from_directory(folder, filename)


@bp.route("/patient/documents/<int:doc_id>/confirm", methods=["POST"])
@role_required("patient", "doctor", "admin")
def confirm_extraction(doc_id):
    doc = Document.query.get_or_404(doc_id)
    for ext in doc.extractions:
        ext.reviewed = True
        ext.confirmed = True
        if request.form.get(f"field_{ext.id}"):
            ext.field_value = request.form.get(f"field_{ext.id}")
    db.session.commit()
    flash("Extracted information confirmed.", "success")
    return redirect(request.referrer or url_for("patient.documents"))
