"""
create_db.py
Script para crear la base de datos e insertar datos iniciales.

Uso:
    python create_db.py
"""
import os
from app import create_app, db
from app.models import User, Challenge


def create_database():
    app = create_app(os.environ.get("FLASK_ENV", "development"))

    with app.app_context():
        print("📦 Creando tablas...")
        db.create_all()
        print("✅ Tablas creadas.")

        # ── Admin por defecto ──────────────────────────────────────
        if not User.query.filter_by(email="admin@evaluacalender.com").first():
            admin = User(
                nombre="Administrador",
                email="admin@evaluacalender.com",
                rol="ADMIN",
            )
            admin.set_password("Admin1234!")
            db.session.add(admin)
            print("👤 Admin creado: admin@evaluacalender.com / Admin1234!")

        # ── Challenges de ejemplo ──────────────────────────────────
        if Challenge.query.count() == 0:
            challenges_demo = [
                Challenge(nombre="Challenge Python Básico", descripcion="Evaluación de fundamentos de Python.", activo=True),
                Challenge(nombre="Challenge SQL Intermedio", descripcion="Consultas avanzadas con SQL.", activo=True),
                Challenge(nombre="Challenge JavaScript ES6+", descripcion="Programación moderna con JavaScript.", activo=True),
                Challenge(nombre="Challenge Algoritmos", descripcion="Estructuras de datos y algoritmos.", activo=True),
            ]
            db.session.add_all(challenges_demo)
            print(f"🎯 {len(challenges_demo)} challenges de ejemplo creados.")

        db.session.commit()
        print("\n🚀 Base de datos lista. Puedes iniciar con: python run.py")
        print("   Admin: admin@evaluacalender.com | Contraseña: Admin1234!")
        print("   ⚠️  Cambia la contraseña del admin en producción.")


if __name__ == "__main__":
    create_database()
