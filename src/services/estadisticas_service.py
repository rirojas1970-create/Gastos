from collections import defaultdict
from src.repositories.gasto_repository import GastoRepository

class EstadisticasService:
    def __init__(self, repository: GastoRepository):
        self.repository = repository

    def _filtrar(self, gastos, año=None, mes=None, categoria=None):
        resultado = []
        for g in gastos:
            if año and g.fecha.year != año:
                continue
            if mes and g.fecha.month != mes:
                continue
            if categoria and g.categoria.lower() != categoria.lower():
                continue
            resultado.append(g)
        return resultado

    def total_por_categoria(self, categoria: str, año: int = None, mes: int = None):
        """Total gastado en una categoría específica (ej. Combustible, Gas)"""
        gastos = self.repository.obtener_todos()
        filtrados = self._filtrar(gastos, año=año, mes=mes, categoria=categoria)
        total = sum(g.monto for g in filtrados)
        return {"categoria": categoria, "total": total, "cantidad": len(filtrados)}

    def resumen_por_categoria(self, año: int = None, mes: int = None):
        """Total agrupado por cada categoría (para comparar todas)"""
        gastos = self.repository.obtener_todos()
        filtrados = self._filtrar(gastos, año=año, mes=mes)
        resumen = defaultdict(float)
        for g in filtrados:
            resumen[g.categoria] += g.monto
        return dict(sorted(resumen.items(), key=lambda x: x[1], reverse=True))
    
    def detalle_por_categoria(self, categoria: str, año: int = None, mes: int = None):
        """Desglose de una categoría por nombre (lugar/producto), de mayor a menor"""
        gastos = self.repository.obtener_todos()
        filtrados = self._filtrar(gastos, año=año, mes=mes, categoria=categoria)

        totales = defaultdict(float)
        cantidades = defaultdict(int)
        etiquetas = {}
        for g in filtrados:
            clave = g.nombre.strip().lower()
            totales[clave] += g.monto
            cantidades[clave] += 1
            etiquetas.setdefault(clave, g.nombre.strip())

        total_categoria = sum(totales.values())
        detalle = []
        for clave, total in sorted(totales.items(), key=lambda x: x[1], reverse=True):
            detalle.append({
                "nombre": etiquetas[clave],
                "total": total,
                "cantidad": cantidades[clave],
                "porcentaje": (total / total_categoria * 100) if total_categoria else 0,
            })
        return detalle

    def resumen_por_mes(self, año: int = None):
        """Total agrupado por mes (para ver la evolución mensual)"""
        gastos = self.repository.obtener_todos()
        filtrados = self._filtrar(gastos, año=año)
        resumen = defaultdict(float)
        for g in filtrados:
            clave = f"{g.fecha.year}-{g.fecha.month:02d}"
            resumen[clave] += g.monto
        return dict(sorted(resumen.items()))

    def total_general(self, año: int = None, mes: int = None):
        """Total de todos los gastos en el período"""
        gastos = self.repository.obtener_todos()
        filtrados = self._filtrar(gastos, año=año, mes=mes)
        return sum(g.monto for g in filtrados)

    def ultimo_mes_con_datos(self):
        """(año, mes) del gasto más reciente, o None si no hay gastos"""
        gastos = self.repository.obtener_todos()
        if not gastos:
            return None
        ultimo = max(g.fecha for g in gastos)
        return (ultimo.year, ultimo.month)

    def comparar_periodos(self, desde_a, hasta_a, desde_b, hasta_b):
        """Compara dos períodos por categoría. Cada extremo es una tupla (año, mes)."""
        gastos = self.repository.obtener_todos()

        def indice(año_mes):
            # convierte (año, mes) a un número para poder comparar rangos
            return año_mes[0] * 12 + año_mes[1]

        def resumir(desde, hasta):
            ini, fin = indice(desde), indice(hasta)
            totales = defaultdict(float)
            cantidades = defaultdict(int)
            for g in gastos:
                if ini <= g.fecha.year * 12 + g.fecha.month <= fin:
                    totales[g.categoria] += g.monto
                    cantidades[g.categoria] += 1
            return totales, cantidades, sum(totales.values()), fin - ini + 1

        tot_a, cant_a, suma_a, meses_a = resumir(desde_a, hasta_a)
        tot_b, cant_b, suma_b, meses_b = resumir(desde_b, hasta_b)

        filas = []
        for cat in set(tot_a) | set(tot_b):
            a = tot_a.get(cat, 0.0)
            b = tot_b.get(cat, 0.0)
            filas.append({
                "categoria": cat,
                "total_a": a,
                "total_b": b,
                "variacion": ((b - a) / a * 100) if a else None,
                "pct_a": (a / suma_a * 100) if suma_a else 0,
                "pct_b": (b / suma_b * 100) if suma_b else 0,
                "cant_a": cant_a.get(cat, 0),
                "cant_b": cant_b.get(cat, 0),
            })
        filas.sort(key=lambda f: f["total_b"], reverse=True)

        return {
            "filas": filas,
            "suma_a": suma_a,
            "suma_b": suma_b,
            "meses_a": meses_a,
            "meses_b": meses_b,
            "prom_a": suma_a / meses_a,
            "prom_b": suma_b / meses_b,
            "variacion_total": ((suma_b - suma_a) / suma_a * 100) if suma_a else None,
        }