"""
app/services/email_service.py
Envío de correos electrónicos transaccionales.
"""

from flask import current_app, render_template_string
from flask_mail import Message
from .. import mail


# ── Plantillas de correo (inline para portabilidad) ────────────────

_BASE = """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  body {{ font-family: 'Segoe UI', sans-serif; background:#f5f5f5; margin:0; padding:0; }}
  .container {{ max-width:600px; margin:30px auto; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 4px 20px rgba(0,0,0,.1); }}
  .header {{ background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%); padding:30px; text-align:center; }}
  .header h1 {{ color:#e94560; margin:0; font-size:24px; letter-spacing:2px; }}
  .header p {{ color:#a8b2d8; margin:5px 0 0; font-size:13px; }}
  .body {{ padding:30px; color:#333; }}
  .body h2 {{ color:#1a1a2e; border-left:4px solid #e94560; padding-left:12px; }}
  .detail-box {{ background:#f8f9ff; border-radius:8px; padding:20px; margin:20px 0; }}
  .detail-row {{ display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #eee; }}
  .detail-row:last-child {{ border-bottom:none; }}
  .label {{ font-weight:600; color:#666; }}
  .value {{ color:#1a1a2e; }}
  .badge {{ display:inline-block; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:700; }}
  .badge-pendiente {{ background:#fff3cd; color:#856404; }}
  .badge-confirmado {{ background:#d1e7dd; color:#0f5132; }}
  .badge-rechazado {{ background:#f8d7da; color:#842029; }}
  .badge-cancelado {{ background:#e2e3e5; color:#41464b; }}
  .footer {{ background:#f8f9ff; padding:15px 30px; text-align:center; font-size:12px; color:#999; }}
  .btn {{ display:inline-block; padding:12px 28px; background:#e94560; color:#fff !important; text-decoration:none; border-radius:8px; font-weight:700; margin-top:15px; }}
</style></head>
<body><div class="container">
  <div class="header"><h1>⚡ EvaluaCalender</h1><p>Plataforma profesional de evaluaciones</p></div>
  <div class="body">{content}</div>
  <div class="footer">© EvaluaCalender · Este correo fue generado automáticamente.</div>
</div></body></html>
"""


def _send(to: str | list, subject: str, html: str) -> None:
    """Envía un correo. Silencia errores para no romper flujo principal."""
    try:
        recipients = [to] if isinstance(to, str) else to
        msg = Message(subject=subject, recipients=recipients, html=html)
        mail.send(msg)
    except Exception as exc:
        current_app.logger.error(f"[EmailService] Error enviando correo: {exc}")


# ── Funciones públicas ─────────────────────────────────────────────


def enviar_solicitud_recibida(evaluacion) -> None:
    """Notifica al solicitante que su evaluación está PENDIENTE."""
    content = f"""
    <h2>Solicitud recibida ✅</h2>
    <p>Hola <strong>{evaluacion.nombre_solicitante}</strong>, tu solicitud de evaluación fue registrada correctamente.</p>
    <div class="detail-box">
      <div class="detail-row"><span class="label">Supervisor: </span><span class="value">{evaluacion.supervisor.nombre}</span></div>
      <div class="detail-row"><span class="label">Challenge: </span><span class="value">{evaluacion.challenge.nombre}</span></div>
      <div class="detail-row"><span class="label">Fecha: </span><span class="value">{evaluacion.fecha.strftime('%d/%m/%Y')}</span></div>
      <div class="detail-row"><span class="label">Hora: </span><span class="value">{evaluacion.hora}</span></div>
      <div class="detail-row"><span class="label">Estado:  </span><span class="value"><span class="badge badge-pendiente">PENDIENTE</span></span></div>
    </div>
    <p>El supervisor confirmará o rechazará tu solicitud en las próximas horas. Si no hay respuesta en 12 horas, la solicitud se cancelará automáticamente.</p>
    """
    _send(
        evaluacion.email_solicitante,
        "📋 Solicitud de evaluación recibida – EvaluaCalender",
        _BASE.format(content=content),
    )


def enviar_nueva_solicitud_supervisor(evaluacion) -> None:
    """Notifica al supervisor que tiene una nueva solicitud pendiente."""
    base_url = current_app.config.get("BASE_URL", "")
    content = f"""
    <h2>Nueva solicitud de evaluación 🔔</h2>
    <p>Hola <strong>{evaluacion.supervisor.nombre}</strong>, tienes una nueva solicitud pendiente de revisión.</p>
    <div class="detail-box">
      <div class="detail-row"><span class="label">Solicitante: </span><span class="value">{evaluacion.nombre_solicitante}</span></div>
      <div class="detail-row"><span class="label">Email: </span><span class="value">{evaluacion.email_solicitante}</span></div>
      <div class="detail-row"><span class="label">Teléfono: </span><span class="value">{evaluacion.telefono or 'No indicado'}</span></div>
      <div class="detail-row"><span class="label">Challenge: </span><span class="value">{evaluacion.challenge.nombre}</span></div>
      <div class="detail-row"><span class="label">Fecha: </span><span class="value">{evaluacion.fecha.strftime('%d/%m/%Y')}</span></div>
      <div class="detail-row"><span class="label">Hora: </span><span class="value">{evaluacion.hora}</span></div>
    </div>
    <p>⚠️ Tienes <strong>12 horas</strong> para confirmar o rechazar. Si no respondes, se cancelará automáticamente.</p>
    <a href="{base_url}/supervisor/dashboard" class="btn">Ver en el panel</a>
    """
    _send(
        evaluacion.supervisor.email,
        "🔔 Nueva solicitud de evaluación – EvaluaCalender",
        _BASE.format(content=content),
    )


def enviar_confirmacion(evaluacion) -> None:
    """Notifica al solicitante que su evaluación fue CONFIRMADA."""
    content = f"""
    <h2>Evaluación confirmada 🎉</h2>
    <p>Hola <strong>{evaluacion.nombre_solicitante}</strong>, tu evaluación ha sido <strong>confirmada</strong>.</p>
    <div class="detail-box">
      <div class="detail-row"><span class="label">Supervisor: </span><span class="value">{evaluacion.supervisor.nombre}</span></div>
      <div class="detail-row"><span class="label">Challenge: </span><span class="value">{evaluacion.challenge.nombre}</span></div>
      <div class="detail-row"><span class="label">Fecha: </span><span class="value">{evaluacion.fecha.strftime('%d/%m/%Y')}</span></div>
      <div class="detail-row"><span class="label">Hora: </span><span class="value">{evaluacion.hora} (duración: 1 hora)</span></div>
      <div class="detail-row"><span class="label">Estado: </span><span class="value"><span class="badge badge-confirmado">CONFIRMADO</span></span></div>
    </div>
    <p>¡Mucho éxito en tu evaluación! Recibirás un recordatorio 1 hora antes.</p>
    """
    _send(
        evaluacion.email_solicitante,
        "✅ Evaluación confirmada – EvaluaCalender",
        _BASE.format(content=content),
    )


def enviar_rechazo(evaluacion) -> None:
    """Notifica al solicitante que su evaluación fue RECHAZADA."""
    content = f"""
    <h2>Evaluación rechazada</h2>
    <p>Hola <strong>{evaluacion.nombre_solicitante}</strong>, lamentablemente tu solicitud de evaluación fue <strong>rechazada</strong>.</p>
    <div class="detail-box">
      <div class="detail-row"><span class="label">Supervisor: </span><span class="value">{evaluacion.supervisor.nombre}</span></div>
      <div class="detail-row"><span class="label">Challenge: </span><span class="value">{evaluacion.challenge.nombre}</span></div>
      <div class="detail-row"><span class="label">Fecha solicitada: </span><span class="value">{evaluacion.fecha.strftime('%d/%m/%Y')}</span></div>
      <div class="detail-row"><span class="label">Estado: </span><span class="value"><span class="badge badge-rechazado">RECHAZADO</span></span></div>
    </div>
    <p>Puedes intentar agendar un nuevo horario con otro supervisor o en una fecha diferente.</p>
    """
    _send(
        evaluacion.email_solicitante,
        "❌ Evaluación rechazada – EvaluaCalender",
        _BASE.format(content=content),
    )


def enviar_cancelacion_auto(evaluacion) -> None:
    """Notifica al solicitante que su evaluación fue cancelada automáticamente."""
    content = f"""
    <h2>Evaluación cancelada automáticamente</h2>
    <p>Hola <strong>{evaluacion.nombre_solicitante}</strong>, tu solicitud de evaluación fue <strong>cancelada automáticamente</strong> porque el supervisor no respondió en 12 horas.</p>
    <div class="detail-box">
      <div class="detail-row"><span class="label">Supervisor: </span><span class="value">{evaluacion.supervisor.nombre}</span></div>
      <div class="detail-row"><span class="label">Challenge: </span><span class="value">{evaluacion.challenge.nombre}</span></div>
      <div class="detail-row"><span class="label">Fecha solicitada: </span><span class="value">{evaluacion.fecha.strftime('%d/%m/%Y')}</span></div>
      <div class="detail-row"><span class="label">Estado: </span><span class="value"><span class="badge badge-cancelado">CANCELADO AUTOMÁTICAMENTE</span></span></div>
    </div>
    <p>Puedes agendar una nueva evaluación eligiendo otro horario disponible.</p>
    """
    _send(
        evaluacion.email_solicitante,
        "⏰ Evaluación cancelada automáticamente – EvaluaCalender",
        _BASE.format(content=content),
    )


def enviar_recordatorio(evaluacion) -> None:
    """Envía recordatorio 1 hora antes al supervisor y al solicitante."""
    content_solicitante = f"""
    <h2>⏰ Recordatorio: tu evaluación es en 1 hora</h2>
    <p>Hola <strong>{evaluacion.nombre_solicitante}</strong>, te recordamos que tienes una evaluación en <strong>1 hora</strong>.</p>
    <div class="detail-box">
      <div class="detail-row"><span class="label">Supervisor: </span><span class="value">{evaluacion.supervisor.nombre}</span></div>
      <div class="detail-row"><span class="label">Challenge: </span><span class="value">{evaluacion.challenge.nombre}</span></div>
      <div class="detail-row"><span class="label">Fecha: </span><span class="value">{evaluacion.fecha.strftime('%d/%m/%Y')}</span></div>
      <div class="detail-row"><span class="label">Hora: </span><span class="value">{evaluacion.hora}</span></div>
    </div>
    <p>¡Prepárate con anticipación!</p>
    """
    content_supervisor = f"""
    <h2>⏰ Recordatorio: evaluación en 1 hora</h2>
    <p>Hola <strong>{evaluacion.supervisor.nombre}</strong>, tienes una evaluación confirmada en <strong>1 hora</strong>.</p>
    <div class="detail-box">
      <div class="detail-row"><span class="label">Solicitante: </span><span class="value">{evaluacion.nombre_solicitante}</span></div>
      <div class="detail-row"><span class="label">Email: </span><span class="value">{evaluacion.email_solicitante}</span></div>
      <div class="detail-row"><span class="label">Teléfono: </span><span class="value">{evaluacion.telefono or 'No indicado'}</span></div>
      <div class="detail-row"><span class="label">Challenge: </span><span class="value">{evaluacion.challenge.nombre}</span></div>
      <div class="detail-row"><span class="label">Hora: </span><span class="value">{evaluacion.hora}</span></div>
    </div>
    """
    _send(
        evaluacion.email_solicitante,
        "⏰ Recordatorio: evaluación en 1 hora – EvaluaCalender",
        _BASE.format(content=content_solicitante),
    )
    _send(
        evaluacion.supervisor.email,
        "⏰ Recordatorio de evaluación – EvaluaCalender",
        _BASE.format(content=content_supervisor),
    )
