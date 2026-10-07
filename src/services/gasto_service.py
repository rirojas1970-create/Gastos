from src.repositories.gasto_repository import GastoRepository
from src.models.gasto import Gasto

class GastoService:
    def __init__(self, repository: GastoRepository):
        self.repository = repository

    def registrar_gasto(self, nombre, categoria, monto, fecha):
        if monto <= 0:
            raise ValueError("El monto debe ser mayor a cero")
        gasto = Gasto(nombre=nombre, categoria=categoria, monto=monto, fecha=fecha)
        return self.repository.guardar(gasto)

    def listar_gastos(self):
        return self.repository.obtener_todos()

    def listar_por_mes(self, año, mes):
        return self.repository.obtener_por_mes(año, mes)

    def obtener_gasto(self, gasto_id: int):
        gasto = self.repository.obtener_por_id(gasto_id)
        if gasto is None:
            raise ValueError(f"No existe un gasto con id {gasto_id}")
        return gasto

    def actualizar_gasto(self, gasto_id, nombre=None, categoria=None, monto=None, fecha=None):
        if monto is not None and monto <= 0:
            raise ValueError("El monto debe ser mayor a cero")
        gasto = self.repository.actualizar(
            gasto_id, nombre=nombre, categoria=categoria, monto=monto, fecha=fecha
        )
        if gasto is None:
            raise ValueError(f"No existe un gasto con id {gasto_id}")
        return gasto

    def eliminar_gasto(self, gasto_id: int):
        gasto = self.repository.eliminar(gasto_id)
        if gasto is None:
            raise ValueError(f"No existe un gasto con id {gasto_id}")
        return gasto