from flask import Blueprint, render_template

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("landing.html")


@bp.route("/about")
def about():
    return render_template("about.html")


@bp.route("/help")
def help_page():
    return render_template("help.html")
