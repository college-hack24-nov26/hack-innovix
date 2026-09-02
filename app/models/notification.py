from app.extensions import db
from app.models.mixins import TimestampMixin


class Notification(TimestampMixin, db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    role_target = db.Column(db.String(32), index=True)
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.String(500))
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(255))
