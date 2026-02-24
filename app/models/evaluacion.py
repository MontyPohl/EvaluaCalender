"""
app/models/evaluacion.py
Evaluaciones (solicitudes de agendamiento).
"""
from datetime import datetime, timezone, timedelta
from .. import db


ESTADOS = ("PENDIENTE", "CONFIRMADO", "RECHAZADO", "CANCELADO_AUTO")


class Evaluacion(db.Model):
    __tablename__ = "evaluaciones"

    id = db.Column(db.Integer, primary_key=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"), nullable=False)

    # Datos del solicitante (sin cuenta)
    nombre_solicitante = db.Column(db.String(150), nullable=False)
    email_solicitante = db.Column(db.String(255), nullable=False)
    telefono = db.Column(db.String(30), nullable=True)

    # Horario
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.String(5), nullable=False)   # "HH:MM"

    # Estado y tiempos
    estado = db.Column(db.String(20), nullable=False, default="PENDIENTE")
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime(timezone=True))   # created_at + 12h

    # Recordatorio
    recordatorio_enviado = db.Column(db.Boolean, default=False, nullable=False)

    __table_args__ = (
        db.Index("ix_eval_supervisor_fecha_hora", "supervisor_id", "fecha", "hora"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.expires_at is None and self.created_at:
            self.expires_at = self.created_at + timedelta(hours=12)

    @staticmethod
    def create(supervisor_id, challenge_id, nombre, email, telefono, fecha, hora):
        now = datetime.now(timezone.utc)
        return Evaluacion(
            supervisor_id=supervisor_id,
            challenge_id=challenge_id,
            nombre_solicitante=nombre,
            email_solicitante=email,
            telefono=telefono,
            fecha=fecha,
            hora=hora,
            estado="PENDIENTE",
            created_at=now,
            expires_at=now + timedelta(hours=12),
        )

    def confirmar(self):
        self.estado = "CONFIRMADO"

    def rechazar(self):
        self.estado = "RECHAZADO"

    def cancelar_auto(self):
        self.estado = "CANCELADO_AUTO"

    def is_pendiente(self):
        return self.estado == "PENDIENTE"

    def is_confirmado(self):
        return self.estado == "CONFIRMADO"

    def __repr__(self):
        return f"<Evaluacion id={self.id} {self.estado} {self.fecha} {self.hora}>"
