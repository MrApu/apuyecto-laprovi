from typing import List, Optional
from database.connection import DatabaseManager
from models.gasto import Gasto
from models.local import LOCAL_CONSOLIDADO

class GastoRepository:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager.get_instance()

    def get_by_id(self, gasto_id: int) -> Optional[Gasto]:
        rows = self.db.execute_query("SELECT * FROM gastos WHERE id = ?", (gasto_id,))
        return self._row_to_entity(rows[0]) if rows else None

    def get_by_mes(self, anio: int, mes: int, local_id: Optional[str] = None) -> List[Gasto]:
        prefix = f"{anio:04d}-{mes:02d}-%"
        if local_id and local_id != LOCAL_CONSOLIDADO:
            query = "SELECT * FROM gastos WHERE fecha LIKE ? AND local_id = ? ORDER BY fecha ASC, id ASC"
            rows = self.db.execute_query(query, (prefix, local_id))
        else:
            query = "SELECT * FROM gastos WHERE fecha LIKE ? ORDER BY fecha ASC, id ASC"
            rows = self.db.execute_query(query, (prefix,))
        return [self._row_to_entity(r) for r in rows]

    def get_by_fecha(self, fecha: str, local_id: Optional[str] = None) -> List[Gasto]:
        if local_id and local_id != LOCAL_CONSOLIDADO:
            query = "SELECT * FROM gastos WHERE fecha = ? AND local_id = ? ORDER BY id ASC"
            rows = self.db.execute_query(query, (fecha, local_id))
        else:
            query = "SELECT * FROM gastos WHERE fecha = ? ORDER BY id ASC"
            rows = self.db.execute_query(query, (fecha,))
        return [self._row_to_entity(r) for r in rows]

    def create(self, g: Gasto) -> int:
        query = """
            INSERT INTO gastos (fecha, local_id, categoria, descripcion, monto, medio_pago, observacion, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        params = (
            g.fecha,
            g.local_id,
            g.categoria.strip().upper(),
            g.descripcion.strip(),
            g.monto or 0.0,
            g.medio_pago.strip().upper(),
            g.observacion
        )
        return self.db.execute_non_query(query, params)

    def save(self, g: Gasto) -> int:
        return self.create(g)

    def update(self, g: Gasto) -> bool:
        query = """
            UPDATE gastos
            SET fecha = ?, local_id = ?, categoria = ?, descripcion = ?, monto = ?, medio_pago = ?, observacion = ?
            WHERE id = ?
        """
        params = (
            g.fecha,
            g.local_id,
            g.categoria.strip().upper(),
            g.descripcion.strip(),
            g.monto or 0.0,
            g.medio_pago.strip().upper(),
            g.observacion,
            g.id
        )
        self.db.execute_non_query(query, params)
        return True

    def delete(self, gasto_id: int) -> bool:
        self.db.execute_non_query("DELETE FROM gastos WHERE id = ?", (gasto_id,))
        return True

    def get_total_mes(self, anio: int, mes: int, local_id: Optional[str] = None) -> float:
        prefix = f"{anio:04d}-{mes:02d}-%"
        if local_id and local_id != LOCAL_CONSOLIDADO:
            query = "SELECT SUM(monto) as tot FROM gastos WHERE fecha LIKE ? AND local_id = ?"
            rows = self.db.execute_query(query, (prefix, local_id))
        else:
            query = "SELECT SUM(monto) as tot FROM gastos WHERE fecha LIKE ?"
            rows = self.db.execute_query(query, (prefix,))
        return float(rows[0]["tot"] or 0.0) if rows else 0.0

    def get_total_fecha(self, fecha: str, local_id: Optional[str] = None) -> float:
        if local_id and local_id != LOCAL_CONSOLIDADO:
            query = "SELECT SUM(monto) as tot FROM gastos WHERE fecha = ? AND local_id = ?"
            rows = self.db.execute_query(query, (fecha, local_id))
        else:
            query = "SELECT SUM(monto) as tot FROM gastos WHERE fecha = ?"
            rows = self.db.execute_query(query, (fecha,))
        return float(rows[0]["tot"] or 0.0) if rows else 0.0

    @staticmethod
    def _row_to_entity(r) -> Gasto:
        return Gasto(
            id=r["id"],
            fecha=r["fecha"],
            local_id=r["local_id"],
            categoria=r["categoria"],
            descripcion=r["descripcion"],
            monto=float(r["monto"] or 0.0),
            medio_pago=r["medio_pago"],
            observacion=r["observacion"],
            fecha_creacion=r["fecha_creacion"]
        )
