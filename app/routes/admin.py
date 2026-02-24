"""
app/routes/admin.py
Rutas del panel administrador.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from ..models import User, Challenge, Evaluacion
from .. import db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _require_admin():
    if not current_user.is_authenticated or not current_user.is_admin():
        abort(403)


# ── Dashboard ──────────────────────────────────────────────────────

@admin_bp.route("/")
@login_required
def dashboard():
    _require_admin()
    total_supervisores = User.query.filter_by(rol="SUPERVISOR", activo=True).count()
    total_challenges = Challenge.query.filter_by(activo=True).count()
    total_evaluaciones = Evaluacion.query.count()
    pendientes = Evaluacion.query.filter_by(estado="PENDIENTE").count()
    confirmadas = Evaluacion.query.filter_by(estado="CONFIRMADO").count()
    rechazadas = Evaluacion.query.filter_by(estado="RECHAZADO").count()
    canceladas = Evaluacion.query.filter_by(estado="CANCELADO_AUTO").count()

    recientes = Evaluacion.query.order_by(Evaluacion.created_at.desc()).limit(10).all()

    return render_template(
        "admin/dashboard.html",
        stats={
            "supervisores": total_supervisores,
            "challenges": total_challenges,
            "evaluaciones": total_evaluaciones,
            "pendientes": pendientes,
            "confirmadas": confirmadas,
            "rechazadas": rechazadas,
            "canceladas": canceladas,
        },
        recientes=recientes,
    )


# ── Challenges ─────────────────────────────────────────────────────

@admin_bp.route("/challenges")
@login_required
def challenges():
    _require_admin()
    lista = Challenge.query.order_by(Challenge.created_at.desc()).all()
    return render_template("admin/challenges.html", challenges=lista)


@admin_bp.route("/challenges/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_challenge():
    _require_admin()
    error = None
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        if not nombre:
            error = "El nombre es obligatorio."
        else:
            c = Challenge(nombre=nombre, descripcion=descripcion, activo=True)
            db.session.add(c)
            db.session.commit()
            flash(f"Challenge '{nombre}' creado exitosamente.", "success")
            return redirect(url_for("admin.challenges"))
    return render_template("admin/challenge_form.html", challenge=None, error=error)


@admin_bp.route("/challenges/<int:challenge_id>/editar", methods=["GET", "POST"])
@login_required
def editar_challenge(challenge_id):
    _require_admin()
    c = Challenge.query.get_or_404(challenge_id)
    error = None
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        if not nombre:
            error = "El nombre es obligatorio."
        else:
            c.nombre = nombre
            c.descripcion = descripcion
            db.session.commit()
            flash("Challenge actualizado.", "success")
            return redirect(url_for("admin.challenges"))
    return render_template("admin/challenge_form.html", challenge=c, error=error)


@admin_bp.route("/challenges/<int:challenge_id>/toggle", methods=["POST"])
@login_required
def toggle_challenge(challenge_id):
    _require_admin()
    c = Challenge.query.get_or_404(challenge_id)
    c.activo = not c.activo
    db.session.commit()
    estado = "activado" if c.activo else "desactivado"
    flash(f"Challenge '{c.nombre}' {estado}.", "success")
    return redirect(url_for("admin.challenges"))


# ── Supervisores ───────────────────────────────────────────────────

@admin_bp.route("/supervisores")
@login_required
def supervisores():
    _require_admin()
    lista = User.query.filter_by(rol="SUPERVISOR").order_by(User.nombre).all()
    return render_template("admin/supervisores.html", supervisores=lista)


@admin_bp.route("/supervisores/<int:user_id>/eliminar", methods=["POST"])
@login_required
def eliminar_supervisor(user_id):
    _require_admin()
    sup = User.query.filter_by(id=user_id, rol="SUPERVISOR").first_or_404()
    # Soft delete
    sup.activo = False
    db.session.commit()
    flash(f"Supervisor '{sup.nombre}' desactivado.", "warning")
    return redirect(url_for("admin.supervisores"))


@admin_bp.route("/supervisores/<int:user_id>/restaurar", methods=["POST"])
@login_required
def restaurar_supervisor(user_id):
    _require_admin()
    sup = User.query.filter_by(id=user_id, rol="SUPERVISOR").first_or_404()
    sup.activo = True
    db.session.commit()
    flash(f"Supervisor '{sup.nombre}' restaurado.", "success")
    return redirect(url_for("admin.supervisores"))


# ── Evaluaciones globales ──────────────────────────────────────────

@admin_bp.route("/evaluaciones")
@login_required
def evaluaciones():
    _require_admin()
    estado = request.args.get("estado", "")
    q = Evaluacion.query
    if estado in ("PENDIENTE", "CONFIRMADO", "RECHAZADO", "CANCELADO_AUTO"):
        q = q.filter_by(estado=estado)
    evaluaciones = q.order_by(Evaluacion.created_at.desc()).limit(200).all()
    return render_template("admin/evaluaciones.html", evaluaciones=evaluaciones, filtro_estado=estado)
