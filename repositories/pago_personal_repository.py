from typing import List, Optional
from database.connection import DatabaseManager
from models.pago_personal import PagoPersonal
from models.local import LOCAL_CONSOLIDADO

class PagoPersonalRepository:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager.get_instance()

    def get_by_id(self, pago_id: int) -> Optional[PagoPersonal]:
        rows = self.db.execute_query("SELECT * FROM pagos_personal WHERE id = ?", (pago_id,))
        return self._row_to_entity(rows[0]) if rows else None

    def get_by_mes(self, anio: int, mes: int, local_id: Optional[str] = None) -> List[PagoPersonal]:
        prefix = f"{anio:04d}-{mes:02d}-%"
        if local_id and local_id != LOCAL_CONSOLIDADO:
            query = "SELECT * FROM pagos_personal WHERE fecha LIKE ? AND local_id = ? ORDER BY fecha ASC, id ASC"
            rows = self.db.execute_query(query, (prefix, local_id))
        else:
            query = "SELECT * FROM pagos_personal WHERE fecha LIKE ? ORDER BY fecha ASC, id ASC"
            rows = self.db.execute_query(query, (prefix,))
        return [self._row_to_entity(r) for r in rows]

    def get_by_fecha(self, fecha: str, local_id: Optional[str] = None) -> List[PagoPersonal]:
        if local_id and local_id != LOCAL_CONSOLIDADO:
            query = "SELECT * FROM pagos_personal WHERE fecha = ? AND local_id = ? ORDER BY id ASC"
            rows = self.db.execute_query(query, (fecha, local_id))
        else:
            query = "SELECT * FROM pagos_personal WHERE fecha = ? ORDER BY id ASC"
            rows = self.db.execute_query(query, (fecha,))
        return [self._row_to_entity(r) for r in rows]

    def create(self, p: PagoPersonal) -> int:
        query = """
            INSERT INTO pagos_personal (fecha, local_id, trabajador, cargo, concepto, monto, medio_pago, observacion, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        params = (
            p.fecha,
            p.local_id,
            p.trabajador.strip().upper(),
            p.cargo.strip().upper(),
            p.concepto.strip().upper(),
            p.monto or 0.0,
            p.medio_pago.strip().upper(),
            p.observacion
        )
        return self.db.execute_non_query(query, params)

    def save(self, p: PagoPersonal) -> int:
        return self.create(p)

    def update(self, p: PagoPersonal) -> bool:
        query = """
            UPDATE pagos_personal
            SET fecha = ?, local_id = ?, trabajador = ?, cargo = ?, concepto = ?, monto = ?, medio_pago = ?, observacion = ?
            WHERE id = ?
        """
        params = (
            p.fecha,
            p.local_id,
            p.trabajador.strip().upper(),
            p.cargo.strip().upper(),
            p.concepto.strip().upper(),
            p.monto or 0.0,
            p.medio_pago.strip().upper(),
            p.observacion,
            p.id
        )
        self.db.execute_non_query(query, params)
        return True

    def delete(self, pago_id: int) -> bool:
        self.db.execute_non_query("DELETE FROM pagos_personal WHERE id = ?", (pago_id,))
        return True

    def get_total_mes(self, anio: int, mes: int, local_id: Optional[str] = None) -> float:
        prefix = f"{anio:04d}-{mes:02d}-%"
        if local_id and local_id != LOCAL_CONSOLIDADO:
            query = "SELECT SUM(monto) as tot FROM pagos_personal WHERE fecha LIKE ? AND local_id = ?"
            rows = self.db.execute_query(query, (prefix, local_id))
        else:
            query = "SELECT SUM(monto) as tot FROM pagos_personal WHERE fecha LIKE ?"
            rows = self.db.execute_query(query, (prefix,))
        return float(rows[0]["tot"] or 0.0) if rows else 0.0

    def get_total_fecha(self, fecha: str, local_id: Optional[str] = None) -> float:
        if local_id and local_id != LOCAL_CONSOLIDADO:
            query = "SELECT SUM(monto) as tot FROM pagos_personal WHERE fecha = ? AND local_id = ?"
            rows = self.db.execute_query(query, (fecha, local_id))
        else:
            query = "SELECT SUM(monto) as tot FROM pagos_personal WHERE fecha = ?"
            rows = self.db.execute_query(query, (fecha,))
        return float(rows[0]["tot"] or 0.0) if rows else 0.0

    @staticmethod
    def _row_to_entity(r) -> PagoPersonal:
        return PagoPersonal(
            id=r["id"],
            fecha=r["fecha"],
            local_id=r["local_id"],
            trabajador=r["trabajador"],
            cargo=r["cargo"],
            concepto=r["concepto"],
            monto=float(r["monto"] or 0.0),
            medio_pago=r["medio_pago"],
            observacion=r["observacion"],
            fecha_creacion=r["fecha_creacion"]
        )
