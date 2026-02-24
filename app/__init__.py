"""
app/__init__.py
Application factory de EvaluaCalender.
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect

from config.settings import config

# ── Extensiones (sin app vinculada) ───────────────────────────────
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()


def create_app(config_name: str = None) -> Flask:
    """Crea y configura la aplicación Flask."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config[config_name])

    # ── Inicializar extensiones ────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # ── Flask-Login config ─────────────────────────────────────────
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Debes iniciar sesión para acceder."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    # ── Registrar blueprints ───────────────────────────────────────
    from .routes import auth_bp, public_bp, supervisor_bp, admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(supervisor_bp)
    app.register_blueprint(admin_bp)

    # ── Inicializar scheduler ──────────────────────────────────────
    from .services.scheduler import init_scheduler
    with app.app_context():
        init_scheduler(app)

    # ── Context processor global ───────────────────────────────────
    @app.context_processor
    def inject_globals():
        from datetime import date
        return {"today": date.today()}

    # ── Manejo de errores ──────────────────────────────────────────
    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template("errors/500.html"), 500

    return app
