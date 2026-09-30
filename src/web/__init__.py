import os
from flask import Flask

from src.config.database import Base, engine  # esto también carga el .env


def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "cambiar-en-produccion")

    Base.metadata.create_all(engine)

    from .routes import bp, cerrar_sesion
    app.register_blueprint(bp)
    app.teardown_appcontext(cerrar_sesion)

    return app