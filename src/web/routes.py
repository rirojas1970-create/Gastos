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
            {"texto": "Comparar períodos", "endpoint": "gastos.comparar_periodos"},
            {"texto": "Evolución mensual", "endpoint": None},
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

def _resolver_periodo(año, mes):
    """Si se elige un mes sin año, se usa el año actual."""
    if mes and not año:
        año = date.today().year
    return año, mes

def _texto_periodo(año, mes):
    """Describe el período que se está mostrando, para mostrarlo en pantalla."""
    mes = mes if mes and 1 <= mes <= 12 else None
    if año and mes:
        return f"{MESES[mes - 1]} de {año}"
    if año:
        return f"todo el año {año}"
    if mes:
        return f"{MESES[mes - 1]} de todos los años"
    return "todo el período registrado"

def _leer_periodo(prefijo, defecto):
    """Lee desde/hasta (mes y año) de un período. 'defecto' es ((año, mes), (año, mes))."""
    d_mes = _entero_opcional(request.args.get(f"{prefijo}_desde_mes"))
    d_año = _entero_opcional(request.args.get(f"{prefijo}_desde_año"))
    h_mes = _entero_opcional(request.args.get(f"{prefijo}_hasta_mes"))
    h_año = _entero_opcional(request.args.get(f"{prefijo}_hasta_año"))
    if None in (d_mes, d_año, h_mes, h_año):
        return defecto
    if not (1 <= d_mes <= 12 and 1 <= h_mes <= 12):
        return defecto
    desde, hasta = (d_año, d_mes), (h_año, h_mes)
    if hasta < desde:  # si los pusiste al revés, se corrigen solos
        desde, hasta = hasta, desde
    return desde, hasta


def _etiqueta_periodo(desde, hasta):
    (a1, m1), (a2, m2) = desde, hasta
    if desde == hasta:
        return f"{MESES[m1 - 1]} de {a1}"
    if a1 == a2:
        return f"{MESES[m1 - 1]} a {MESES[m2 - 1]} de {a1}"
    return f"{MESES[m1 - 1]} de {a1} a {MESES[m2 - 1]} de {a2}"


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
    año, mes = _resolver_periodo(año, mes)

    stats = estadisticas_service()
    return render_template(
        "estadisticas.html",
        total=stats.total_general(año=año, mes=mes),
        por_categoria=stats.resumen_por_categoria(año=año, mes=mes),
        por_mes=stats.resumen_por_mes(año=año),
        año=año,
        mes=mes,
        meses=MESES,
    )

@bp.route("/estadisticas/categoria/<categoria>")
def detalle_categoria(categoria):
    año = _entero_opcional(request.args.get("año"))
    mes = _entero_opcional(request.args.get("mes"))
    año, mes = _resolver_periodo(año, mes)

    detalle = estadisticas_service().detalle_por_categoria(categoria, año=año, mes=mes)
    total = sum(d["total"] for d in detalle)

    # Para el gráfico: los 10 mayores y el resto agrupado en "Otros"
    etiquetas = [d["nombre"] for d in detalle[:10]]
    valores = [d["total"] for d in detalle[:10]]
    resto = sum(d["total"] for d in detalle[10:])
    if resto:
        etiquetas.append("Otros")
        valores.append(resto)

    return render_template(
        "estadistica_categoria.html",
        categoria=categoria,
        detalle=detalle,
        total=total,
        etiquetas=etiquetas,
        valores=valores,
        año=año,
        mes=mes,
        periodo=_texto_periodo(año, mes),
        meses=MESES,
    )

@bp.route("/comparaciones/periodos")
def comparar_periodos():
    stats = estadisticas_service()
    hoy = date.today()

    # Por defecto: el último mes con datos contra el mes anterior
    base = stats.ultimo_mes_con_datos() or (hoy.year, hoy.month)
    anterior = (base[0] - 1, 12) if base[1] == 1 else (base[0], base[1] - 1)

    desde_a, hasta_a = _leer_periodo("a", (anterior, anterior))
    desde_b, hasta_b = _leer_periodo("b", (base, base))

    datos = stats.comparar_periodos(desde_a, hasta_a, desde_b, hasta_b)
    return render_template(
        "comparar_periodos.html",
        datos=datos,
        desde_a=desde_a, hasta_a=hasta_a,
        desde_b=desde_b, hasta_b=hasta_b,
        etiqueta_a=_etiqueta_periodo(desde_a, hasta_a),
        etiqueta_b=_etiqueta_periodo(desde_b, hasta_b),
        meses=MESES,
    )