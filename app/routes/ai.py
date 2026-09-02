from flask import Blueprint, jsonify
from flask_login import login_required

from app.ai import get_ai_provider

bp = Blueprint("ai_routes", __name__, url_prefix="/ai")


@bp.route("/status")
@login_required
def status():
    provider = get_ai_provider()
    return jsonify({"provider": provider.__class__.__name__, "demo": True})
