"""
app/routes/public.py
Rutas públicas: home, perfil supervisor, agendamiento.
No requieren autenticación.
"""
from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from ..models import User, Challenge, Evaluacion
from ..services import (
    get_disponibilidad_mes,
    slot_disponible,
    bloquear_slot,
    enviar_solicitud_recibida,
    enviar_nueva_solicitud_supervisor,
)
from .. import db

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    supervisores = User.query.filter_by(rol="SUPERVISOR", activo=True).order_by(User.nombre).all()
    return render_template("public/home.html", supervisores=supervisores)


@public_bp.route("/supervisor/<int:supervisor_id>")
def perfil_supervisor(supervisor_id):
    supervisor = User.query.filter_by(id=supervisor_id, rol="SUPERVISOR", activo=True).first_or_404()

    # Mes actual o el solicitado
    try:
        year = int(request.args.get("year", date.today().year))
        month = int(request.args.get("month", date.today().month))
    except (ValueError, TypeError):
        year, month = date.today().year, date.today().month

    # Ajuste de mes
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    disponibilidad = get_disponibilidad_mes(supervisor_id, year, month)
    challenges = Challenge.query.filter_by(activo=True).order_by(Challenge.nombre).all()

    return render_template(
        "public/perfil_supervisor.html",
        supervisor=supervisor,
        disponibilidad=disponibilidad,
        challenges=challenges,
        year=year,
        month=month,
    )


@public_bp.route("/agendar", methods=["POST"])
def agendar():
    """Procesa el formulario de agendamiento."""
    supervisor_id = request.form.get("supervisor_id", type=int)
    challenge_id = request.form.get("challenge_id", type=int)
    fecha_str = request.form.get("fecha", "").strip()
    hora = request.form.get("hora", "").strip()
    nombre = request.form.get("nombre", "").strip()
    email = request.form.get("email", "").strip().lower()
    telefono = request.form.get("telefono", "").strip()

    # ── Validaciones backend ───────────────────────────────────────
    errors = []
    if not supervisor_id:
        errors.append("Supervisor requerido.")
    if not challenge_id:
        errors.append("Challenge requerido.")
    if not fecha_str:
        errors.append("Fecha requerida.")
    if not hora:
        errors.append("Hora requerida.")
    if not nombre:
        errors.append("Nombre requerido.")
    if not email or "@" not in email:
        errors.append("Email válido requerido.")

    if errors:
        flash(" | ".join(errors), "danger")
        return redirect(url_for("public.perfil_supervisor", supervisor_id=supervisor_id))

    # Parsear fecha
    try:
        fecha = date.fromisoformat(fecha_str)
    except ValueError:
        flash("Fecha inválida.", "danger")
        return redirect(url_for("public.home"))

    # Verificar supervisor y challenge
    supervisor = User.query.filter_by(id=supervisor_id, rol="SUPERVISOR", activo=True).first()
    challenge = Challenge.query.filter_by(id=challenge_id, activo=True).first()
    if not supervisor or not challenge:
        abort(400)

    # Verificar disponibilidad en backend (CRÍTICO - no confiar en frontend)
    if not slot_disponible(supervisor_id, fecha, hora):
        flash("El horario seleccionado ya no está disponible. Por favor elige otro.", "warning")
        return redirect(url_for("public.perfil_supervisor", supervisor_id=supervisor_id))

    # Crear evaluación
    evaluacion = Evaluacion.create(
        supervisor_id=supervisor_id,
        challenge_id=challenge_id,
        nombre=nombre,
        email=email,
        telefono=telefono,
        fecha=fecha,
        hora=hora,
    )
    db.session.add(evaluacion)
    bloquear_slot(supervisor_id, fecha, hora)
    db.session.commit()

    # Enviar correos
    try:
        enviar_solicitud_recibida(evaluacion)
        enviar_nueva_solicitud_supervisor(evaluacion)
    except Exception:
        pass  # No interrumpir el flujo

    flash(
        f"¡Solicitud enviada! Recibirás una confirmación en {email}. "
        f"El supervisor tiene 12 horas para responder.",
        "success",
    )
    return redirect(url_for("public.home"))


@public_bp.route("/api/disponibilidad/<int:supervisor_id>")
def api_disponibilidad(supervisor_id):
    """API JSON para el calendario dinámico."""
    try:
        year = int(request.args.get("year", date.today().year))
        month = int(request.args.get("month", date.today().month))
    except (ValueError, TypeError):
        return jsonify({"error": "Parámetros inválidos"}), 400

    disponibilidad = get_disponibilidad_mes(supervisor_id, year, month)
    return jsonify(disponibilidad)
