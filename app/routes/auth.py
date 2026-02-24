"""
app/routes/auth.py
Rutas de autenticación: login, registro de supervisor, logout.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from ..models import User
from .. import db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            error = "Todos los campos son obligatorios."
        else:
            user = User.query.filter_by(email=email, activo=True).first()
            if user and user.check_password(password):
                login_user(user, remember=True)
                next_page = request.args.get("next")
                return redirect(next_page or _redirect_url_by_role(user))
            else:
                error = "Credenciales incorrectas."

    return render_template("auth/login.html", error=error)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Registro público de nuevos supervisores."""
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    error = None
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not all([nombre, email, password, confirm]):
            error = "Todos los campos son obligatorios."
        elif len(password) < 8:
            error = "La contraseña debe tener al menos 8 caracteres."
        elif password != confirm:
            error = "Las contraseñas no coinciden."
        elif User.query.filter_by(email=email).first():
            error = "Ya existe una cuenta con ese email."
        else:
            user = User(nombre=nombre, email=email, rol="SUPERVISOR")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("¡Cuenta creada exitosamente! Bienvenido/a a EvaluaCalender.", "success")
            return redirect(url_for("supervisor.dashboard"))

    return render_template("auth/register.html", error=error)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("auth.login"))


# ── Helpers ────────────────────────────────────────────────────────

def _redirect_by_role(user):
    return redirect(_redirect_url_by_role(user))


def _redirect_url_by_role(user):
    if user.is_admin():
        return url_for("admin.dashboard")
    return url_for("supervisor.dashboard")
