from flask import request
from flask_login import current_user

from app.extensions import db
from app.models import AuditLog


def log_action(user_id, action, resource_type=None, resource_id=None, meta=None):
    uid = user_id
    if uid is None and current_user and getattr(current_user, "is_authenticated", False):
        uid = current_user.id
    entry = AuditLog(
        user_id=uid,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        ip_address=request.remote_addr if request else None,
        meta=meta,
    )
    db.session.add(entry)
    db.session.commit()
