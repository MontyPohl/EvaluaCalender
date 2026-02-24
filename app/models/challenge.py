"""
app/models/challenge.py
Modelo de challenges (evaluaciones disponibles).
"""
from datetime import datetime, timezone
from .. import db


class Challenge(db.Model):
    __tablename__ = "challenges"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relaciones
    evaluaciones = db.relationship("Evaluacion", backref="challenge", lazy="dynamic")

    def __repr__(self):
        return f"<Challenge {self.nombre}>"
