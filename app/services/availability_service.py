"""
app/services/availability_service.py
Lógica de negocio para disponibilidad y agendamiento.
"""
from datetime import date
from ..models import Disponibilidad, Evaluacion
from .. import db


def get_disponibilidad_mes(supervisor_id: int, year: int, month: int) -> dict:
    """
    Retorna la disponibilidad del mes como dict:
    { "2025-06-10": ["09:00", "10:00", ...], ... }
    Solo incluye slots con disponible=True.
    """
    from calendar import monthrange
    _, last_day = monthrange(year, month)
    fecha_inicio = date(year, month, 1)
    fecha_fin = date(year, month, last_day)

    slots = Disponibilidad.query.filter(
        Disponibilidad.supervisor_id == supervisor_id,
        Disponibilidad.fecha >= fecha_inicio,
        Disponibilidad.fecha <= fecha_fin,
        Disponibilidad.disponible == True,
    ).order_by(Disponibilidad.fecha, Disponibilidad.hora).all()

    resultado = {}
    for s in slots:
        key = s.fecha.strftime("%Y-%m-%d")
        resultado.setdefault(key, []).append(s.hora)
    return resultado


def get_todos_slots_mes(supervisor_id: int, year: int, month: int) -> list:
    """Retorna TODOS los slots del mes (disponibles e indisponibles)."""
    from calendar import monthrange
    _, last_day = monthrange(year, month)
    slots = Disponibilidad.query.filter(
        Disponibilidad.supervisor_id == supervisor_id,
        Disponibilidad.fecha >= date(year, month, 1),
        Disponibilidad.fecha <= date(year, month, last_day),
    ).order_by(Disponibilidad.fecha, Disponibilidad.hora).all()
    return slots


def slot_disponible(supervisor_id: int, fecha: date, hora: str) -> bool:
    """Verifica si un slot está disponible (sin evaluación activa)."""
    disp = Disponibilidad.query.filter_by(
        supervisor_id=supervisor_id,
        fecha=fecha,
        hora=hora,
        disponible=True,
    ).first()
    if not disp:
        return False

    # Verificar que no haya evaluación activa (pendiente o confirmada)
    eval_activa = Evaluacion.query.filter(
        Evaluacion.supervisor_id == supervisor_id,
        Evaluacion.fecha == fecha,
        Evaluacion.hora == hora,
        Evaluacion.estado.in_(["PENDIENTE", "CONFIRMADO"]),
    ).first()
    return eval_activa is None


def bloquear_slot(supervisor_id: int, fecha: date, hora: str) -> None:
    """Marca un slot como no disponible al agendar."""
    disp = Disponibilidad.query.filter_by(
        supervisor_id=supervisor_id, fecha=fecha, hora=hora
    ).first()
    if disp:
        disp.disponible = False


def liberar_slot(supervisor_id: int, fecha: date, hora: str) -> None:
    """Libera un slot al rechazar/cancelar una evaluación."""
    disp = Disponibilidad.query.filter_by(
        supervisor_id=supervisor_id, fecha=fecha, hora=hora
    ).first()
    if disp:
        disp.disponible = True


def guardar_disponibilidad_bulk(supervisor_id: int, slots: list) -> None:
    """
    slots = [{"fecha": date, "hora": "HH:MM"}, ...]
    Inserta o activa los slots. Ignora duplicados.
    """
    for s in slots:
        existing = Disponibilidad.query.filter_by(
            supervisor_id=supervisor_id,
            fecha=s["fecha"],
            hora=s["hora"],
        ).first()
        if existing:
            existing.disponible = True
        else:
            db.session.add(Disponibilidad(
                supervisor_id=supervisor_id,
                fecha=s["fecha"],
                hora=s["hora"],
                disponible=True,
            ))
    db.session.commit()


def eliminar_slot(supervisor_id: int, disponibilidad_id: int) -> bool:
    """Elimina un slot de disponibilidad si no tiene evaluación activa."""
    disp = Disponibilidad.query.filter_by(
        id=disponibilidad_id, supervisor_id=supervisor_id
    ).first()
    if not disp:
        return False
    eval_activa = Evaluacion.query.filter(
        Evaluacion.supervisor_id == supervisor_id,
        Evaluacion.fecha == disp.fecha,
        Evaluacion.hora == disp.hora,
        Evaluacion.estado.in_(["PENDIENTE", "CONFIRMADO"]),
    ).first()
    if eval_activa:
        return False
    db.session.delete(disp)
    db.session.commit()
    return True
