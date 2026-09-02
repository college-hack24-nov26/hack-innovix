from app.routes.admin import bp as admin_bp
from app.routes.ai import bp as ai_bp
from app.routes.api import bp as api_bp
from app.routes.auth import bp as auth_bp
from app.routes.doctor import bp as doctor_bp
from app.routes.documents import bp as documents_bp
from app.routes.kiosk import bp as kiosk_bp
from app.routes.main import bp as main_bp
from app.routes.patient import bp as patient_bp
from app.routes.triage import bp as triage_bp


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(triage_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(kiosk_bp)
