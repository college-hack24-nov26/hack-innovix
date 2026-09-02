from pathlib import Path

from flask import Flask, render_template, request, url_for
from flask_login import current_user

from app.config import Config
from app.extensions import csrf, db, login_manager, migrate
from app.i18n import get_locale, translate
from app.routes import register_blueprints


def create_app(config_object=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_object or Config)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    for sub in ("documents", "temporary", "processed"):
        (Path(app.config["UPLOAD_FOLDER"]) / sub).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes.api import bp as api_bp

    csrf.exempt(api_bp)

    register_blueprints(app)

    @app.context_processor
    def inject_helpers():
        role_dashboards = {
            "patient": "patient.dashboard",
            "doctor": "doctor.dashboard",
            "triage": "triage.dashboard",
            "admin": "admin.dashboard",
        }
        dashboard_url = url_for("main.index")
        if current_user.is_authenticated:
            dashboard_url = url_for(role_dashboards.get(current_user.role, "main.index"))
        return {
            "_": translate,
            "current_user": current_user,
            "locale": get_locale(),
            "request": request,
            "dashboard_url": dashboard_url,
        }

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("errors/500.html"), 500

    return app
