"""
app/routes/supervisor.py
Rutas del panel de supervisor.
"""

import json
from datetime import date
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    abort,
)
from flask_login import login_required, current_user
from ..models import Evaluacion, Disponibilidad
from ..services import (
    get_todos_slots_mes,
    guardar_disponibilidad_bulk,
    eliminar_slot,
    liberar_slot,
    enviar_confirmacion,
    enviar_rechazo,
)
from .. import db

supervisor_bp = Blueprint("supervisor", __name__, url_prefix="/supervisor")


def _require_supervisor():
    if not current_user.is_authenticated or not current_user.is_supervisor():
        abort(403)


@supervisor_bp.route("/dashboard")
@login_required
def dashboard():
    _require_supervisor()
    pendientes = (
        Evaluacion.query.filter_by(supervisor_id=current_user.id, estado="PENDIENTE")
        .order_by(Evaluacion.fecha, Evaluacion.hora)
        .all()
    )

    proximas = (
        Evaluacion.query.filter(
            Evaluacion.supervisor_id == current_user.id,
            Evaluacion.estado == "CONFIRMADO",
            Evaluacion.fecha >= date.today(),
        )
        .order_by(Evaluacion.fecha, Evaluacion.hora)
        .limit(20)
        .all()
    )

    return render_template(
        "supervisor/dashboard.html",
        pendientes=pendientes,
        proximas=proximas,
    )


@supervisor_bp.route("/evaluacion/<int:eval_id>/confirmar", methods=["POST"])
@login_required
@supervisor_bp.route("/evaluacion/<int:eval_id>/confirmar", methods=["POST"])
@login_required
def confirmar_evaluacion(eval_id):
    _require_supervisor()
    ev = Evaluacion.query.filter_by(
        id=eval_id, supervisor_id=current_user.id
    ).first_or_404()

    if ev.estado != "PENDIENTE":
        flash("Esta evaluación ya fue procesada.", "warning")
        return redirect(url_for("supervisor.dashboard"))

    ev.confirmar()
    db.session.commit()

    # Enviar correo en segundo plano
    from flask import current_app
    import threading

    _app = current_app._get_current_object()
    _eval_id = ev.id

    def enviar():
        with _app.app_context():
            from ..models import Evaluacion as Ev

            e = Ev.query.get(_eval_id)
            if e:
                try:
                    enviar_confirmacion(e)
                except Exception as ex:
                    _app.logger.error(f"Error enviando correo confirmacion: {ex}")

    threading.Thread(target=enviar, daemon=True).start()

    flash(f"Evaluación de {ev.nombre_solicitante} confirmada exitosamente.", "success")
    return redirect(url_for("supervisor.dashboard"))


@supervisor_bp.route("/evaluacion/<int:eval_id>/rechazar", methods=["POST"])
@login_required
def rechazar_evaluacion(eval_id):
    _require_supervisor()
    ev = Evaluacion.query.filter_by(
        id=eval_id, supervisor_id=current_user.id
    ).first_or_404()

    if ev.estado != "PENDIENTE":
        flash("Esta evaluación ya fue procesada.", "warning")
        return redirect(url_for("supervisor.dashboard"))

    ev.rechazar()
    liberar_slot(current_user.id, ev.fecha, ev.hora)
    db.session.commit()

    # Enviar correo en segundo plano
    from flask import current_app
    import threading

    _app = current_app._get_current_object()
    _eval_id = ev.id

    def enviar():
        with _app.app_context():
            from ..models import Evaluacion as Ev

            e = Ev.query.get(_eval_id)
            if e:
                try:
                    enviar_rechazo(e)
                except Exception as ex:
                    _app.logger.error(f"Error enviando correo rechazo: {ex}")

    threading.Thread(target=enviar, daemon=True).start()

    flash(
        f"Evaluación de {ev.nombre_solicitante} rechazada. El horario fue liberado.",
        "info",
    )
    return redirect(url_for("supervisor.dashboard"))


@supervisor_bp.route("/disponibilidad")
@login_required
def disponibilidad():
    _require_supervisor()
    try:
        year = int(request.args.get("year", date.today().year))
        month = int(request.args.get("month", date.today().month))
    except (ValueError, TypeError):
        year, month = date.today().year, date.today().month

    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    slots = get_todos_slots_mes(current_user.id, year, month)
    return render_template(
        "supervisor/disponibilidad.html",
        slots=slots,
        year=year,
        month=month,
    )


@supervisor_bp.route("/disponibilidad/guardar", methods=["POST"])
@login_required
def guardar_disponibilidad():
    """Guarda múltiples slots en bulk desde el formulario del calendario."""
    _require_supervisor()
    data = request.get_json()
    if not data or "slots" not in data:
        return jsonify({"error": "Datos inválidos"}), 400

    slots_validos = []
    for s in data["slots"]:
        try:
            slots_validos.append(
                {
                    "fecha": date.fromisoformat(s["fecha"]),
                    "hora": s["hora"],
                }
            )
        except (KeyError, ValueError):
            continue

    if not slots_validos:
        return jsonify({"error": "No hay slots válidos"}), 400

    guardar_disponibilidad_bulk(current_user.id, slots_validos)
    return jsonify({"ok": True, "guardados": len(slots_validos)})


@supervisor_bp.route("/disponibilidad/<int:slot_id>/eliminar", methods=["POST"])
@login_required
def eliminar_disponibilidad(slot_id):
    _require_supervisor()
    ok = eliminar_slot(current_user.id, slot_id)
    if ok:
        flash("Slot eliminado.", "success")
    else:
        flash(
            "No se puede eliminar: tiene una evaluación activa o no existe.", "danger"
        )
    return redirect(url_for("supervisor.disponibilidad"))


@supervisor_bp.route("/historial")
@login_required
def historial():
    _require_supervisor()
    evaluaciones = (
        Evaluacion.query.filter_by(supervisor_id=current_user.id)
        .order_by(Evaluacion.created_at.desc())
        .limit(100)
        .all()
    )
    return render_template("supervisor/historial.html", evaluaciones=evaluaciones)
