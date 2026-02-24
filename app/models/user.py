"""
app/models/user.py
Modelo de usuarios (ADMIN y SUPERVISOR).
"""
from datetime import datetime, timezone
from flask_login import UserMixin
import bcrypt
from .. import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default="SUPERVISOR")  # ADMIN | SUPERVISOR
    activo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relaciones
    disponibilidades = db.relationship("Disponibilidad", backref="supervisor", lazy="dynamic", cascade="all, delete-orphan")
    evaluaciones = db.relationship("Evaluacion", backref="supervisor", lazy="dynamic")

    # ── Métodos de contraseña ──────────────────────────────────────
    def set_password(self, password: str) -> None:
        """Hashea y almacena la contraseña con bcrypt."""
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Verifica la contraseña contra el hash almacenado."""
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    # ── Helpers ────────────────────────────────────────────────────
    def is_admin(self) -> bool:
        return self.rol == "ADMIN"

    def is_supervisor(self) -> bool:
        return self.rol == "SUPERVISOR"

    def __repr__(self):
        return f"<User {self.email} [{self.rol}]>"
