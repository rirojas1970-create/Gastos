from datetime import date

from flask import (
    Blueprint, g, render_template, request, redirect, url_for, flash
)

from src.config.database import SessionLocal
from src.repositories.gasto_repository import GastoRepository
from src.services.gasto_service import GastoService
from src.services.estadisticas_service import EstadisticasService

bp = Blueprint("gastos", __name__)


# ---------- Menú de inicio ----------

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

MENU = [
    {
        "titulo": "Registro de gastos",
        "descripcion": "Cargá nuevos gastos y administrá los que ya anotaste.",
        "botones": [
            {"texto": "Anotar gasto", "endpoint": "gastos.nuevo"},
            {"texto": "Ver gastos",   "endpoint": "gastos.listar"},
        ],
    },
    {
        "titulo": "Estadísticas",
        "descripcion": "Totales por categoría y por mes, con filtros por período.",
        "botones": [
            {"texto": "Ver estadísticas", "endpoint": "gastos.estadisticas"},
        ],
    },
    {
        "titulo": "Comparaciones",
        "descripcion": "Compará períodos y visualizá la evolución de tus gastos.",
        "botones": [
            {"texto": "Mes vs mes", "endpoint": None},
            {"texto": "Semanal",    "endpoint": None},
            {"texto": "Histograma", "endpoint": None},
        ],
    },
]


# ---------- Sesión y servicios (uno por request) ----------

def get_repo():
    if "repo" not in g:
        g.session = SessionLocal()
        g.repo = GastoRepository(g.session)
    return g.repo


def cerrar_sesion(exc=None):
    session = g.pop("session", None)
    g.pop("repo", None)
    if session is not None:
        session.close()


def gasto_service():
    return GastoService(get_repo())


def estadisticas_service():
    return EstadisticasService(get_repo())


def _entero_opcional(valor):
    """Convierte un query param a int, o None si está vacío o es inválido."""
    try:
        return int(valor) if valor else None
    except ValueError:
        return None


# ---------- Rutas ----------

@bp.route("/")
def inicio():
    return render_template("inicio.html", menu=MENU)


@bp.route("/gastos")
def listar():
    hoy = date.today()
    año = _entero_opcional(request.args.get("año")) or hoy.year
    mes = _entero_opcional(request.args.get("mes")) or hoy.month
    if not 1 <= mes <= 12:
        año, mes = hoy.year, hoy.month

    gastos = gasto_service().listar_por_mes(año, mes)
    total = sum(g.monto for g in gastos)

    anterior = (año - 1, 12) if mes == 1 else (año, mes - 1)
    siguiente = (año + 1, 1) if mes == 12 else (año, mes + 1)

    return render_template(
        "gastos_list.html",
        gastos=gastos,
        total=total,
        año=año,
        mes=mes,
        nombre_mes=MESES[mes - 1],
        anterior=anterior,
        siguiente=siguiente,
    )


@bp.route("/gastos/nuevo", methods=["GET", "POST"])
def nuevo():
    if request.method == "POST":
        try:
            gasto_service().registrar_gasto(
                nombre=request.form["nombre"].strip(),
                categoria=request.form["categoria"].strip(),
                monto=float(request.form["monto"]),
                fecha=date.fromisoformat(request.form["fecha"]),
            )
            flash("Gasto registrado correctamente", "ok")
            return redirect(url_for("gastos.listar"))
        except ValueError as e:
            flash(str(e), "error")
    return render_template("gasto_form.html", gasto=None, hoy=date.today().isoformat())


@bp.route("/gastos/<int:gasto_id>/editar", methods=["GET", "POST"])
def editar(gasto_id):
    service = gasto_service()
    try:
        gasto = service.obtener_gasto(gasto_id)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("gastos.listar"))

    if request.method == "POST":
        try:
            service.actualizar_gasto(
                gasto_id,
                nombre=request.form["nombre"].strip(),
                categoria=request.form["categoria"].strip(),
                monto=float(request.form["monto"]),
                fecha=date.fromisoformat(request.form["fecha"]),
            )
            flash("Gasto actualizado", "ok")
            return redirect(url_for("gastos.listar"))
        except ValueError as e:
            flash(str(e), "error")

    return render_template("gasto_form.html", gasto=gasto, hoy=date.today().isoformat())


@bp.route("/gastos/<int:gasto_id>/eliminar", methods=["POST"])
def eliminar(gasto_id):
    try:
        gasto_service().eliminar_gasto(gasto_id)
        flash("Gasto eliminado", "ok")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("gastos.listar"))


@bp.route("/estadisticas")
def estadisticas():
    año = _entero_opcional(request.args.get("año"))
    mes = _entero_opcional(request.args.get("mes"))

    stats = estadisticas_service()
    return render_template(
        "estadisticas.html",
        total=stats.total_general(año=año, mes=mes),
        por_categoria=stats.resumen_por_categoria(año=año, mes=mes),
        por_mes=stats.resumen_por_mes(año=año),
        año=año,
        mes=mes,
    )