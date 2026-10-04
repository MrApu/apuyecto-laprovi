from typing import List, Optional, Tuple, Dict, Any
from database.connection import DatabaseManager
from models.compra import Compra
from models.local import LOCAL_CONSOLIDADO

class CompraRepository:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager.get_instance()

    def get_by_id(self, compra_id: int) -> Optional[Compra]:
        rows = self.db.execute_query("SELECT * FROM compras WHERE id = ?", (compra_id,))
        return self._row_to_entity(rows[0]) if rows else None

    def get_by_mes(self, anio: int, mes: int, local_id: Optional[str] = None) -> List[Compra]:
        prefix = f"{anio:04d}-{mes:02d}-%"
        if local_id and local_id != LOCAL_CONSOLIDADO:
            query = "SELECT * FROM compras WHERE fecha LIKE ? AND local_id = ? ORDER BY fecha ASC, id ASC"
            rows = self.db.execute_query(query, (prefix, local_id))
        else:
            query = "SELECT * FROM compras WHERE fecha LIKE ? ORDER BY fecha ASC, id ASC"
            rows = self.db.execute_query(query, (prefix,))
        return [self._row_to_entity(r) for r in rows]

    def get_by_fecha(self, fecha: str, local_id: Optional[str] = None) -> List[Compra]:
        if local_id and local_id != LOCAL_CONSOLIDADO:
            query = "SELECT * FROM compras WHERE fecha = ? AND local_id = ? ORDER BY id ASC"
            rows = self.db.execute_query(query, (fecha, local_id))
        else:
            query = "SELECT * FROM compras WHERE fecha = ? ORDER BY id ASC"
            rows = self.db.execute_query(query, (fecha,))
        return [self._row_to_entity(r) for r in rows]

    def create(self, c: Compra) -> int:
        if (c.total or 0.0) > 0 and (c.precio_unitario or 0.0) == 0.0:
            total = float(c.total)
            precio_unitario = round(total / (c.cantidad or 1.0), 2)
        else:
            precio_unitario = c.precio_unitario or 0.0
            total = round((c.cantidad or 1.0) * precio_unitario, 2)
            if c.total and c.total > 0:
                total = c.total

        query = """
            INSERT INTO compras (fecha, local_id, proveedor, categoria, descripcion, cantidad, precio_unitario, total, medio_pago, nro_documento, observacion, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        params = (
            c.fecha,
            c.local_id,
            c.proveedor.strip().upper(),
            c.categoria.strip().upper(),
            c.descripcion.strip(),
            c.cantidad or 1.0,
            precio_unitario,
            total,
            c.medio_pago.strip().upper(),
            c.nro_documento,
            c.observacion
        )
        return self.db.execute_non_query(query, params)

    def save(self, c: Compra) -> int:
        return self.create(c)

    def update(self, c: Compra) -> bool:
        if (c.total or 0.0) > 0 and (c.precio_unitario or 0.0) == 0.0:
            total = float(c.total)
            precio_unitario = round(total / (c.cantidad or 1.0), 2)
        else:
            precio_unitario = c.precio_unitario or 0.0
            total = round((c.cantidad or 1.0) * precio_unitario, 2)
            if c.total and c.total > 0:
                total = c.total

        query = """
            UPDATE compras
            SET fecha = ?, local_id = ?, proveedor = ?, categoria = ?, descripcion = ?, cantidad = ?, precio_unitario = ?, total = ?, medio_pago = ?, nro_documento = ?, observacion = ?
            WHERE id = ?
        """
        params = (
            c.fecha,
            c.local_id,
            c.proveedor.strip().upper(),
            c.categoria.strip().upper(),
            c.descripcion.strip(),
            c.cantidad,
            c.precio_unitario,
            total,
            c.medio_pago.strip().upper(),
            c.nro_documento,
            c.observacion,
            c.id
        )
        self.db.execute_non_query(query, params)
        return True

    def delete(self, compra_id: int) -> bool:
        self.db.execute_non_query("DELETE FROM compras WHERE id = ?", (compra_id,))
        return True

    def get_total_mes(self, anio: int, mes: int, local_id: Optional[str] = None) -> float:
        prefix = f"{anio:04d}-{mes:02d}-%"
        if local_id and local_id != LOCAL_CONSOLIDADO:
            query = "SELECT SUM(total) as tot FROM compras WHERE fecha LIKE ? AND local_id = ?"
            rows = self.db.execute_query(query, (prefix, local_id))
        else:
            query = "SELECT SUM(total) as tot FROM compras WHERE fecha LIKE ?"
            rows = self.db.execute_query(query, (prefix,))
        return float(rows[0]["tot"] or 0.0) if rows else 0.0

    def get_total_fecha(self, fecha: str, local_id: Optional[str] = None) -> float:
        if local_id and local_id != LOCAL_CONSOLIDADO:
            query = "SELECT SUM(total) as tot FROM compras WHERE fecha = ? AND local_id = ?"
            rows = self.db.execute_query(query, (fecha, local_id))
        else:
            query = "SELECT SUM(total) as tot FROM compras WHERE fecha = ?"
            rows = self.db.execute_query(query, (fecha,))
        return float(rows[0]["tot"] or 0.0) if rows else 0.0

    @staticmethod
    def _row_to_entity(r) -> Compra:
        return Compra(
            id=r["id"],
            fecha=r["fecha"],
            local_id=r["local_id"],
            proveedor=r["proveedor"],
            categoria=r["categoria"],
            descripcion=r["descripcion"],
            cantidad=float(r["cantidad"] or 1.0),
            precio_unitario=float(r["precio_unitario"] or 0.0),
            total=float(r["total"] or 0.0),
            medio_pago=r["medio_pago"],
            nro_documento=r["nro_documento"],
            observacion=r["observacion"],
            fecha_creacion=r["fecha_creacion"]
        )
