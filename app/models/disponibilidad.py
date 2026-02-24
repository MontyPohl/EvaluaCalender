"""
app/models/disponibilidad.py
Bloques de disponibilidad horaria por supervisor.
"""
from .. import db


class Disponibilidad(db.Model):
    __tablename__ = "disponibilidades"

    id = db.Column(db.Integer, primary_key=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.String(5), nullable=False)   # "HH:MM"
    disponible = db.Column(db.Boolean, default=True, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("supervisor_id", "fecha", "hora", name="uq_supervisor_fecha_hora"),
        db.Index("ix_disp_supervisor_fecha", "supervisor_id", "fecha"),
    )

    def __repr__(self):
        return f"<Disponibilidad sup={self.supervisor_id} {self.fecha} {self.hora}>"
