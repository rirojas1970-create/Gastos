import os
from flask import Flask

from src.config.database import Base, engine  # esto también carga el .env


def formato_pesos(valor):
    # 60000 -> $60.000,00
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"${texto}"


def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "cambiar-en-produccion")

    Base.metadata.create_all(engine)

    from .routes import bp, cerrar_sesion
    app.register_blueprint(bp)
    app.teardown_appcontext(cerrar_sesion)

    app.add_template_filter(formato_pesos, "pesos")

    return app