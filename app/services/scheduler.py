"""
app/services/scheduler.py
Tareas automáticas programadas con APScheduler:
  · Cancelación de evaluaciones pendientes a las 12 horas.
  · Recordatorio 1 hora antes de evaluaciones confirmadas.
"""
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler(timezone="UTC")


def _cancelar_pendientes_expiradas(app):
    """Cancela evaluaciones PENDIENTE cuyo expires_at ya pasó."""
    with app.app_context():
        from ..models import Evaluacion
        from .. import db
        from .email_service import enviar_cancelacion_auto

        ahora = datetime.now(timezone.utc)
        expiradas = Evaluacion.query.filter(
            Evaluacion.estado == "PENDIENTE",
            Evaluacion.expires_at <= ahora,
        ).all()

        for ev in expiradas:
            ev.cancelar_auto()
            # Liberar disponibilidad
            from ..models import Disponibilidad
            disp = Disponibilidad.query.filter_by(
                supervisor_id=ev.supervisor_id,
                fecha=ev.fecha,
                hora=ev.hora,
            ).first()
            if disp:
                disp.disponible = True
            db.session.commit()
            try:
                enviar_cancelacion_auto(ev)
            except Exception as e:
                logger.error(f"Error enviando email cancelación auto id={ev.id}: {e}")
            logger.info(f"Evaluacion id={ev.id} cancelada automáticamente.")


def _enviar_recordatorios(app):
    """Envía recordatorio 1 hora antes de evaluaciones CONFIRMADAS."""
    with app.app_context():
        from ..models import Evaluacion
        from .. import db
        from .email_service import enviar_recordatorio
        from datetime import date as date_type, time as time_type
        import datetime as dt

        ahora = datetime.now(timezone.utc)
        ventana_inicio = ahora + timedelta(minutes=55)
        ventana_fin = ahora + timedelta(minutes=65)

        confirmadas = Evaluacion.query.filter(
            Evaluacion.estado == "CONFIRMADO",
            Evaluacion.recordatorio_enviado == False,
        ).all()

        for ev in confirmadas:
            # Construir datetime de la evaluación
            hora_parts = ev.hora.split(":")
            eval_dt = datetime(
                ev.fecha.year, ev.fecha.month, ev.fecha.day,
                int(hora_parts[0]), int(hora_parts[1]),
                tzinfo=timezone.utc
            )
            if ventana_inicio <= eval_dt <= ventana_fin:
                try:
                    enviar_recordatorio(ev)
                    ev.recordatorio_enviado = True
                    db.session.commit()
                    logger.info(f"Recordatorio enviado para evaluacion id={ev.id}")
                except Exception as e:
                    logger.error(f"Error enviando recordatorio id={ev.id}: {e}")


def init_scheduler(app):
    """Inicializa y arranca el scheduler con la app Flask."""
    if scheduler.running:
        return

    scheduler.add_job(
        func=_cancelar_pendientes_expiradas,
        args=[app],
        trigger=IntervalTrigger(minutes=10),
        id="cancelar_pendientes",
        replace_existing=True,
        name="Cancelar evaluaciones pendientes expiradas",
    )

    scheduler.add_job(
        func=_enviar_recordatorios,
        args=[app],
        trigger=IntervalTrigger(minutes=5),
        id="enviar_recordatorios",
        replace_existing=True,
        name="Enviar recordatorios 1h antes",
    )

    scheduler.start()
    logger.info("Scheduler APScheduler iniciado correctamente.")
