from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError

from app.extensions import db
from app.models import Patient, User
from app.services.audit_service import log_action

bp = Blueprint("auth", __name__)


def _email_ok(_form, field):
    value = (field.data or "").strip()
    if "@" not in value or "." not in value.split("@")[-1]:
        raise ValidationError("Enter a valid email address.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), _email_ok])
    password = PasswordField("Password", validators=[DataRequired()])


class RegisterForm(FlaskForm):
    first_name = StringField("First name", validators=[DataRequired(), Length(max=80)])
    last_name = StringField("Last name", validators=[DataRequired(), Length(max=80)])
    email = StringField("Email", validators=[DataRequired(), _email_ok])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField("Confirm", validators=[EqualTo("password")])
    age = StringField("Age")
    gender = SelectField("Gender", choices=[("female", "Female"), ("male", "Male"), ("other", "Other"), ("unspecified", "Prefer not to say")])
    language = SelectField("Language", choices=[("en", "English"), ("hi", "Hindi"), ("mr", "Marathi")])
    id_type = SelectField(
        "Identification",
        choices=[
            ("new", "New Patient"),
            ("hospital", "Hospital Patient ID"),
            ("abha", "ABHA ID"),
            ("simulated_aadhaar", "Other hospital ID"),
        ],
    )
    id_value = StringField("ID value")


@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user)
            session["language"] = user.language or "en"
            log_action(user.id, "login", "user", user.id)
            dest = {
                "doctor": "doctor.dashboard",
                "triage": "triage.dashboard",
                "admin": "admin.dashboard",
                "patient": "patient.dashboard",
            }.get(user.role, "main.index")
            return redirect(url_for(dest))
        flash("Invalid email or password.", "danger")
    return render_template("auth/login.html", form=form)


@bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash("An account with that email already exists.", "warning")
            return render_template("auth/register.html", form=form)
        patient = Patient(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            age=int(form.age.data) if (form.age.data or "").isdigit() else None,
            gender=form.gender.data,
            language=form.language.data,
            simulated_id_type=form.id_type.data,
            simulated_id_value=form.id_value.data,
        )
        if form.id_type.data == "abha":
            patient.abha_id = form.id_value.data or None
        elif form.id_type.data == "hospital":
            patient.hospital_patient_id = form.id_value.data or None
        db.session.add(patient)
        db.session.flush()
        user = User(
            email=form.email.data.lower(),
            full_name=f"{form.first_name.data} {form.last_name.data}",
            role="patient",
            language=form.language.data,
            patient_id=patient.id,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        session["language"] = form.language.data
        log_action(user.id, "register", "user", user.id)
        return redirect(url_for("patient.consent"))
    return render_template("auth/register.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    log_action(current_user.id, "logout", "user", current_user.id)
    logout_user()
    return redirect(url_for("main.index"))


@bp.route("/language/<code>")
def set_language(code):
    if code in ("en", "hi", "mr"):
        session["language"] = code
        if current_user.is_authenticated:
            current_user.language = code
            db.session.commit()
    return redirect(request.referrer or url_for("main.index"))
