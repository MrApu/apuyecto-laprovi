from typing import List, Optional
from database.connection import DatabaseManager
from models.vale import Vale
from models.local import LOCAL_CONSOLIDADO

class ValeRepository:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager.get_instance()

    def get_by_fecha(self, fecha: str, local_id: str = "restaurante") -> Optional[Vale]:
        if local_id == LOCAL_CONSOLIDADO:
            rows = self.db.execute_query("""
                SELECT NULL as id, fecha, 'consolidado' as local_id,
                       SUM(vales_entregados) as vales_entregados,
                       SUM(vales_consumidos) as vales_consumidos,
                       (SUM(vales_entregados) - SUM(vales_consumidos)) as saldo,
                       GROUP_CONCAT(observacion, ' | ') as observacion,
                       MAX(fecha_actualizacion) as fecha_actualizacion
                FROM vales
                WHERE fecha = ?
                GROUP BY fecha
            """, (fecha,))
        else:
            rows = self.db.execute_query(
                "SELECT * FROM vales WHERE fecha = ? AND local_id = ?",
                (fecha, local_id)
            )
        return self._row_to_entity(rows[0]) if rows else None

    def get_by_mes(self, anio: int, mes: int, local_id: str = "restaurante") -> List[Vale]:
        prefix = f"{anio:04d}-{mes:02d}-%"
        if local_id == LOCAL_CONSOLIDADO:
            rows = self.db.execute_query("""
                SELECT NULL as id, fecha, 'consolidado' as local_id,
                       SUM(vales_entregados) as vales_entregados,
                       SUM(vales_consumidos) as vales_consumidos,
                       (SUM(vales_entregados) - SUM(vales_consumidos)) as saldo,
                       GROUP_CONCAT(observacion, ' | ') as observacion,
                       MAX(fecha_actualizacion) as fecha_actualizacion
                FROM vales
                WHERE fecha LIKE ?
                GROUP BY fecha
                ORDER BY fecha ASC
            """, (prefix,))
        else:
            rows = self.db.execute_query(
                "SELECT * FROM vales WHERE fecha LIKE ? AND local_id = ? ORDER BY fecha ASC",
                (prefix, local_id)
            )
        return [self._row_to_entity(r) for r in rows]

    def save(self, vale: Vale) -> int:
        saldo = (vale.vales_entregados or 0) - (vale.vales_consumidos or 0)
        query = """
            INSERT INTO vales (fecha, local_id, vales_entregados, vales_consumidos, saldo, observacion, fecha_actualizacion)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(fecha, local_id) DO UPDATE SET
                vales_entregados = excluded.vales_entregados,
                vales_consumidos = excluded.vales_consumidos,
                saldo = excluded.saldo,
                observacion = excluded.observacion,
                fecha_actualizacion = CURRENT_TIMESTAMP
        """
        params = (
            vale.fecha,
            vale.local_id or "restaurante",
            vale.vales_entregados or 0,
            vale.vales_consumidos or 0,
            saldo,
            vale.observacion
        )
        return self.db.execute_non_query(query, params)

    def get_resumen_mes(self, anio: int, mes: int, local_id: str = "restaurante") -> dict:
        prefix = f"{anio:04d}-{mes:02d}-%"
        if local_id == LOCAL_CONSOLIDADO:
            rows = self.db.execute_query("""
                SELECT SUM(vales_entregados) as total_entregados,
                       SUM(vales_consumidos) as total_consumidos,
                       (SUM(vales_entregados) - SUM(vales_consumidos)) as saldo_mes
                FROM vales
                WHERE fecha LIKE ?
            """, (prefix,))
        else:
            rows = self.db.execute_query("""
                SELECT SUM(vales_entregados) as total_entregados,
                       SUM(vales_consumidos) as total_consumidos,
                       (SUM(vales_entregados) - SUM(vales_consumidos)) as saldo_mes
                FROM vales
                WHERE fecha LIKE ? AND local_id = ?
            """, (prefix, local_id))

        if rows and rows[0]["total_entregados"] is not None:
            r = rows[0]
            return {
                "entregados": int(r["total_entregados"] or 0),
                "consumidos": int(r["total_consumidos"] or 0),
                "canjeados": int(r["total_consumidos"] or 0),
                "saldo": int(r["saldo_mes"] or 0)
            }
        return {"entregados": 0, "consumidos": 0, "canjeados": 0, "saldo": 0}

    @staticmethod
    def _row_to_entity(r) -> Vale:
        return Vale(
            id=r["id"],
            fecha=r["fecha"],
            local_id=r["local_id"],
            vales_entregados=int(r["vales_entregados"] or 0),
            vales_consumidos=int(r["vales_consumidos"] or 0),
            saldo=int(r["saldo"] or 0),
            observacion=r["observacion"],
            fecha_actualizacion=r["fecha_actualizacion"]
        )
