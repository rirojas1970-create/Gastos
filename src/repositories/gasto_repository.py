from src.models.gasto import Gasto
from datetime import date


class GastoRepository:
    def __init__(self, session):
        self.session = session

    def guardar(self, gasto: Gasto):
        self.session.add(gasto)
        self.session.commit()
        return gasto

    def obtener_todos(self):
        return self.session.query(Gasto).all()
    
    def obtener_por_mes(self, año: int, mes: int):
        desde = date(año, mes, 1)
        hasta = date(año + 1, 1, 1) if mes == 12 else date(año, mes + 1, 1)
        return (
            self.session.query(Gasto)
            .filter(Gasto.fecha >= desde, Gasto.fecha < hasta)
            .order_by(Gasto.fecha.desc(), Gasto.id.desc())
            .all()
        )

    def obtener_por_id(self, gasto_id: int):
        return self.session.get(Gasto, gasto_id)

    def actualizar(self, gasto_id: int, **campos):
        gasto = self.session.get(Gasto, gasto_id)
        if gasto is None:
            return None
        for campo, valor in campos.items():
            if valor is not None and hasattr(gasto, campo):
                setattr(gasto, campo, valor)
        self.session.commit()
        return gasto

    def eliminar(self, gasto_id: int):
        gasto = self.session.get(Gasto, gasto_id)
        if gasto:
            self.session.delete(gasto)
            self.session.commit()
        return gasto