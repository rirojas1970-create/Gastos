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