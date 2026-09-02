from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.models import AuditLog, ClinicalSession, ClinicalSummary, Document, Patient, TriageAlert, User
from app.security.decorators import role_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/dashboard")
@role_required("admin")
def dashboard():
    stats = {
        "patients": Patient.query.count(),
        "sessions": ClinicalSession.query.count(),
        "completed": ClinicalSession.query.filter_by(status="completed").count(),
        "documents": Document.query.count(),
        "summaries": ClinicalSummary.query.count(),
        "alerts": TriageAlert.query.count(),
        "verified": ClinicalSummary.query.filter_by(status="VERIFIED").count(),
        "ocr_ok": Document.query.filter_by(status="processed").count(),
    }
    total_docs = max(stats["documents"], 1)
    stats["ocr_rate"] = round(100 * stats["ocr_ok"] / total_docs, 1) if stats["documents"] else 0
    stats["verify_rate"] = round(100 * stats["verified"] / max(stats["summaries"], 1), 1) if stats["summaries"] else 0
    return render_template("admin/dashboard.html", stats=stats)


@bp.route("/users", methods=["GET", "POST"])
@role_required("admin")
def users():
    if request.method == "POST":
        email = request.form.get("email", "").lower()
        if not User.query.filter_by(email=email).first():
            user = User(email=email, full_name=request.form.get("full_name"), role=request.form.get("role"))
            user.set_password(request.form.get("password") or "ChangeMe123!")
            db.session.add(user)
            db.session.commit()
            flash("User created.", "success")
        return redirect(url_for("admin.users"))
    return render_template("admin/users.html", users=User.query.order_by(User.created_at.desc()).all())


@bp.route("/analytics")
@role_required("admin")
def analytics():
    stats = {
        "patients": Patient.query.count(),
        "sessions": ClinicalSession.query.count(),
        "completed": ClinicalSession.query.filter_by(status="completed").count(),
        "documents": Document.query.count(),
        "summaries": ClinicalSummary.query.count(),
        "alerts": TriageAlert.query.count(),
        "verified": ClinicalSummary.query.filter_by(status="VERIFIED").count(),
        "ocr_ok": Document.query.filter_by(status="processed").count(),
    }
    stats["ocr_rate"] = round(100 * stats["ocr_ok"] / max(stats["documents"], 1), 1) if stats["documents"] else 0
    stats["verify_rate"] = round(100 * stats["verified"] / max(stats["summaries"], 1), 1) if stats["summaries"] else 0
    return render_template("admin/analytics.html", stats=stats)


@bp.route("/audit")
@role_required("admin")
def audit():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
    return render_template("admin/audit.html", logs=logs)


@bp.route("/settings", methods=["GET", "POST"])
@role_required("admin")
def settings():
    cfg = {
        "ai_provider": current_app.config.get("AI_PROVIDER"),
        "ocr_provider": current_app.config.get("OCR_PROVIDER"),
        "demo_mode": current_app.config.get("DEMO_MODE"),
        "consent_version": current_app.config.get("CONSENT_VERSION"),
    }
    return render_template("admin/settings.html", cfg=cfg)
