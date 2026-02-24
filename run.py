"""
run.py
Punto de entrada de EvaluaCalender.
"""

import os
from app import create_app, db
from app.models import User, Challenge, Disponibilidad, Evaluacion

app = create_app(os.environ.get("FLASK_ENV", "development"))


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "User": User,
        "Challenge": Challenge,
        "Disponibilidad": Disponibilidad,
        "Evaluacion": Evaluacion,
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
