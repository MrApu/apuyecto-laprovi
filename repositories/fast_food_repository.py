from typing import List, Optional
from database.connection import DatabaseManager
from models.fast_food_consumo import FastFoodConsumo

class FastFoodRepository:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager.get_instance()

    def get_by_fecha(self, fecha: str) -> Optional[FastFoodConsumo]:
        rows = self.db.execute_query(
            "SELECT id, fecha, tickets_local, vales_local, total_consumido, observacion, fecha_actualizacion FROM fast_food_consumos WHERE fecha = ?",
            (fecha,)
        )
        return self._row_to_entity(rows[0]) if rows else None

    def get_by_mes(self, anio: int, mes: int) -> List[FastFoodConsumo]:
        prefix = f"{anio:04d}-{mes:02d}-%"
        rows = self.db.execute_query(
            "SELECT id, fecha, tickets_local, vales_local, total_consumido, observacion, fecha_actualizacion FROM fast_food_consumos WHERE fecha LIKE ? ORDER BY fecha ASC",
            (prefix,)
        )
        return [self._row_to_entity(r) for r in rows]

    def save(self, ffc: FastFoodConsumo) -> int:
        tot = (ffc.tickets_local or 0) + (ffc.vales_local or 0)
        query = """
            INSERT INTO fast_food_consumos (fecha, tickets_local, vales_local, total_consumido, observacion, fecha_actualizacion)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(fecha) DO UPDATE SET
                tickets_local = excluded.tickets_local,
                vales_local = excluded.vales_local,
                total_consumido = excluded.total_consumido,
                observacion = excluded.observacion,
                fecha_actualizacion = CURRENT_TIMESTAMP
        """
        params = (
            ffc.fecha,
            ffc.tickets_local or 0,
            ffc.vales_local or 0,
            tot,
            ffc.observacion
        )
        return self.db.execute_non_query(query, params)

    def get_resumen_mes(self, anio: int, mes: int) -> dict:
        prefix = f"{anio:04d}-{mes:02d}-%"
        rows = self.db.execute_query("""
            SELECT SUM(tickets_local) as tot_tickets_ff,
                   SUM(vales_local) as tot_vales_ff,
                   SUM(total_consumido) as tot_consumo_ff
            FROM fast_food_consumos
            WHERE fecha LIKE ?
        """, (prefix,))
        if rows and rows[0]["tot_tickets_ff"] is not None:
            r = rows[0]
            t = int(r["tot_tickets_ff"] or 0)
            v = int(r["tot_vales_ff"] or 0)
            tot = int(r["tot_consumo_ff"] or 0)
            return {
                "tickets_local_ff": t,
                "vales_local_ff": v,
                "total_consumido_ff": tot,
                "total_tickets_local": t,
                "total_vales_local": v,
                "total_consumido": tot
            }
        return {
            "tickets_local_ff": 0, "vales_local_ff": 0, "total_consumido_ff": 0,
            "total_tickets_local": 0, "total_vales_local": 0, "total_consumido": 0
        }

    @staticmethod
    def _row_to_entity(r) -> FastFoodConsumo:
        return FastFoodConsumo(
            id=r["id"],
            fecha=r["fecha"],
            tickets_local=r["tickets_local"] or 0,
            vales_local=r["vales_local"] or 0,
            total_consumido=r["total_consumido"] or 0,
            observacion=r["observacion"],
            fecha_actualizacion=r["fecha_actualizacion"]
        )
