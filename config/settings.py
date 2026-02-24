import os


class Config:
    SECRET_KEY = "EvaluaCalender2025xK9mP2qL8nR5vT"
    WTF_CSRF_ENABLED = True

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:admin1234@localhost:5433/evaluacalender"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "montypohl20@gmail.com"
    MAIL_PASSWORD = "h z b y t t m z u g u y l w a a"
    MAIL_DEFAULT_SENDER = "EvaluaCalender <montypohl20@gmail.com>"

    BASE_URL = "http://localhost:5000"
    EVAL_EXPIRY_HOURS = 12
    REMINDER_MINUTES_BEFORE = 60


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
