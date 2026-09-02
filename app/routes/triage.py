from datetime import datetime

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user

from app.extensions import db
from app.models import TriageAlert
from app.security.decorators import role_required
from app.services.audit_service import log_action

bp = Blueprint("triage", __name__, url_prefix="/triage")


@bp.route("/dashboard")
@role_required("triage", "doctor", "admin")
def dashboard():
    open_alerts = TriageAlert.query.filter_by(status="open").order_by(TriageAlert.created_at.desc()).all()
    return render_template("triage/dashboard.html", alerts=open_alerts)


@bp.route("/alerts")
@role_required("triage", "doctor", "admin")
def alerts():
    items = TriageAlert.query.order_by(TriageAlert.created_at.desc()).all()
    return render_template("triage/alerts.html", alerts=items)


@bp.route("/alerts/<int:alert_id>/acknowledge", methods=["POST"])
@role_required("triage", "doctor", "admin")
def acknowledge(alert_id):
    alert = TriageAlert.query.get_or_404(alert_id)
    alert.status = "acknowledged"
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    db.session.commit()
    log_action(current_user.id, "triage_alert_ack", "triage_alert", alert.id)
    return redirect(url_for("triage.alerts"))


@bp.route("/alerts/<int:alert_id>/resolve", methods=["POST"])
@role_required("triage", "doctor", "admin")
def resolve(alert_id):
    alert = TriageAlert.query.get_or_404(alert_id)
    alert.status = "resolved"
    db.session.commit()
    return redirect(url_for("triage.alerts"))
