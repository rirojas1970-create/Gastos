"""
Genera gastos ficticios para mostrar las estadísticas y comparaciones de la app.

Uso (desde la raíz del proyecto, con el .env apuntando a una base de demo):

    python -m scripts.generar_datos_demo

Medidas de seguridad:
- Solo corre si el nombre de la base termina en "_demo" (ej: db_gastos_demo).
- No carga nada si la base ya tiene gastos.
"""
import random
import sys
from datetime import date, timedelta

from src.config.database import SessionLocal, Base, engine
from src.repositories.gasto_repository import GastoRepository
from src.services.gasto_service import GastoService

# ---------------------------------------------------------------------------
# AJUSTAR: categorías, lugares/productos (campo "nombre") y precio base
# (precio promedio a enero de 2025). Cambiá los nombres por los que uses vos.
# ---------------------------------------------------------------------------
CATALOGO = {
    "Supermercado": {
        "nombres": ["Carrefour", "Coto", "Día", "Verdulería", "Carnicería"],
        "precio_base": 28000,
        "compras_por_mes": 8,
    },
    "Transporte": {
        "nombres": ["SUBE", "Nafta", "Estacionamiento", "Peaje"],
        "precio_base": 9000,
        "compras_por_mes": 5,
    },
    "Servicios": {
        "nombres": ["Luz", "Gas", "Agua", "Internet", "Celular"],
        "precio_base": 18000,
        "compras_por_mes": 5,
    },
    "Salud": {
        "nombres": ["Farmacia", "Consulta médica", "Óptica"],
        "precio_base": 15000,
        "compras_por_mes": 2,
    },
    "Salidas": {
        "nombres": ["Restaurante", "Cine", "Café", "Heladería"],
        "precio_base": 12000,
        "compras_por_mes": 4,
    },
    "Hogar": {
        "nombres": ["Ferretería", "Librería", "Bazar"],
        "precio_base": 14000,
        "compras_por_mes": 2,
    },
}

INFLACION_MENSUAL = 0.03     # aumento de precios acumulado mes a mes
INICIO = date(2025, 1, 1)
FIN = date(2026, 9, 30)
SEMILLA = 42                 # misma semilla = mismos datos cada vez


def meses_del_periodo(inicio, fin):
    anio, mes = inicio.year, inicio.month
    while (anio, mes) <= (fin.year, fin.month):
        yield anio, mes
        mes += 1
        if mes == 13:
            anio, mes = anio + 1, 1


def dias_en_mes(anio, mes):
    primero = date(anio, mes, 1)
    siguiente = date(anio + (mes == 12), (mes % 12) + 1, 1)
    return (siguiente - primero).days


def main():
    base = engine.url.database or ""
    if not base.endswith("_demo"):
        print(f"❌ La base actual es '{base}'. Por seguridad, este script solo")
        print("   corre sobre una base cuyo nombre termine en '_demo'.")
        print("   Cambiá DB_NAME en tu .env (ej: DB_NAME=db_gastos_demo).")
        sys.exit(1)

    Base.metadata.create_all(engine)
    session = SessionLocal()
    service = GastoService(GastoRepository(session))

    if service.listar_gastos():
        print("❌ La base de demo ya tiene gastos. Vaciala o creá una nueva.")
        session.close()
        sys.exit(1)

    random.seed(SEMILLA)
    cargados = 0

    for indice, (anio, mes) in enumerate(meses_del_periodo(INICIO, FIN)):
        factor = (1 + INFLACION_MENSUAL) ** indice
        for categoria, datos in CATALOGO.items():
            for _ in range(datos["compras_por_mes"]):
                dia = random.randint(1, dias_en_mes(anio, mes))
                fecha = date(anio, mes, dia)
                variacion = random.uniform(0.6, 1.5)
                monto = round(datos["precio_base"] * factor * variacion, -1)
                service.registrar_gasto(
                    random.choice(datos["nombres"]),
                    categoria,
                    monto,
                    fecha,
                )
                cargados += 1

    session.close()
    print(f"✅ {cargados} gastos ficticios cargados en '{base}'.")


if __name__ == "__main__":
    main()
