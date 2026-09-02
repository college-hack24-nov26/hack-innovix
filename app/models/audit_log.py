from app.extensions import db
from app.models.mixins import TimestampMixin


class AuditLog(TimestampMixin, db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    action = db.Column(db.String(80), nullable=False, index=True)
    resource_type = db.Column(db.String(80))
    resource_id = db.Column(db.String(64))
    ip_address = db.Column(db.String(64))
    meta = db.Column(db.JSON)

    user = db.relationship("User")
