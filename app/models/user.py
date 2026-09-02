from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.mixins import TimestampMixin


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(160), nullable=False)
    role = db.Column(db.String(32), nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    language = db.Column(db.String(8), default="en")
    department = db.Column(db.String(80))
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), unique=True)

    patient = db.relationship("Patient", back_populates="user", uselist=False, foreign_keys=[patient_id])

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
