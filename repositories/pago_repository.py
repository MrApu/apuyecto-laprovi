from typing import List, Optional
from database.connection import DatabaseManager
from models.pago import PagoTicket
from models.local import LOCAL_CONSOLIDADO

class PagoRepository:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager.get_instance()

    def get_by_fecha(self, fecha: str, local_id: str = "restaurante") -> Optional[PagoTicket]:
        if local_id == LOCAL_CONSOLIDADO:
            rows = self.db.execute_query("""
                SELECT NULL as id, fecha, 'consolidado' as local_id,
                       SUM(total_tickets) as total_tickets,
                       SUM(tickets_pagados) as tickets_pagados,
                       SUM(tickets_debidos) as tickets_debidos,
                       'CONSOLIDADO' as estado,
                       SUM(monto_pagado) as monto_pagado,
                       SUM(monto_pendiente) as monto_pendiente,
                       GROUP_CONCAT(observacion, ' | ') as observacion,
                       MAX(fecha_actualizacion) as fecha_actualizacion
                FROM pagos_tickets
                WHERE fecha = ?
                GROUP BY fecha
            """, (fecha,))
        else:
            rows = self.db.execute_query(
                "SELECT * FROM pagos_tickets WHERE fecha = ? AND local_id = ?",
                (fecha, local_id)
            )
        return self._row_to_entity(rows[0]) if rows else None

    def get_by_mes(self, anio: int, mes: int, local_id: str = "restaurante") -> List[PagoTicket]:
        prefix = f"{anio:04d}-{mes:02d}-%"
        if local_id == LOCAL_CONSOLIDADO:
            rows = self.db.execute_query("""
                SELECT NULL as id, fecha, 'consolidado' as local_id,
                       SUM(total_tickets) as total_tickets,
                       SUM(tickets_pagados) as tickets_pagados,
                       SUM(tickets_debidos) as tickets_debidos,
                       'CONSOLIDADO' as estado,
                       SUM(monto_pagado) as monto_pagado,
                       SUM(monto_pendiente) as monto_pendiente,
                       GROUP_CONCAT(observacion, ' | ') as observacion,
                       MAX(fecha_actualizacion) as fecha_actualizacion
                FROM pagos_tickets
                WHERE fecha LIKE ?
                GROUP BY fecha
                ORDER BY fecha ASC
            """, (prefix,))
        else:
            rows = self.db.execute_query(
                "SELECT * FROM pagos_tickets WHERE fecha LIKE ? AND local_id = ? ORDER BY fecha ASC",
                (prefix, local_id)
            )
        return [self._row_to_entity(r) for r in rows]

    def save(self, pago: PagoTicket) -> int:
        pago.calcular_estado()
        query = """
            INSERT INTO pagos_tickets (fecha, local_id, total_tickets, tickets_pagados, tickets_debidos, estado, monto_pagado, monto_pendiente, observacion, fecha_actualizacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(fecha, local_id) DO UPDATE SET
                total_tickets = excluded.total_tickets,
                tickets_pagados = excluded.tickets_pagados,
                tickets_debidos = excluded.tickets_debidos,
                estado = excluded.estado,
                monto_pagado = excluded.monto_pagado,
                monto_pendiente = excluded.monto_pendiente,
                observacion = excluded.observacion,
                fecha_actualizacion = CURRENT_TIMESTAMP
        """
        params = (
            pago.fecha,
            pago.local_id or "restaurante",
            pago.total_tickets or 0,
            pago.tickets_pagados or 0,
            pago.tickets_debidos or 0,
            pago.estado,
            pago.monto_pagado or 0.0,
            pago.monto_pendiente or 0.0,
            pago.observacion
        )
        return self.db.execute_non_query(query, params)

    def get_resumen_mes(self, anio: int, mes: int, local_id: str = "restaurante") -> dict:
        prefix = f"{anio:04d}-{mes:02d}-%"
        if local_id == LOCAL_CONSOLIDADO:
            rows = self.db.execute_query("""
                SELECT SUM(total_tickets) as total_tickets,
                       SUM(tickets_pagados) as pagados,
                       SUM(tickets_debidos) as debidos,
                       SUM(monto_pagado) as monto_pagado,
                       SUM(monto_pendiente) as monto_pendiente
                FROM pagos_tickets
                WHERE fecha LIKE ?
            """, (prefix,))
        else:
            rows = self.db.execute_query("""
                SELECT SUM(total_tickets) as total_tickets,
                       SUM(tickets_pagados) as pagados,
                       SUM(tickets_debidos) as debidos,
                       SUM(monto_pagado) as monto_pagado,
                       SUM(monto_pendiente) as monto_pendiente
                FROM pagos_tickets
                WHERE fecha LIKE ? AND local_id = ?
            """, (prefix, local_id))

        if rows and rows[0]["total_tickets"] is not None:
            r = rows[0]
            return {
                "total_tickets": int(r["total_tickets"] or 0),
                "pagados": int(r["pagados"] or 0),
                "debidos": int(r["debidos"] or 0),
                "monto_pagado": float(r["monto_pagado"] or 0.0),
                "monto_pendiente": float(r["monto_pendiente"] or 0.0)
            }
        return {"total_tickets": 0, "pagados": 0, "debidos": 0, "monto_pagado": 0.0, "monto_pendiente": 0.0}

    @staticmethod
    def _row_to_entity(r) -> PagoTicket:
        return PagoTicket(
            id=r["id"],
            fecha=r["fecha"],
            local_id=r["local_id"],
            total_tickets=int(r["total_tickets"] or 0),
            tickets_pagados=int(r["tickets_pagados"] or 0),
            tickets_debidos=int(r["tickets_debidos"] or 0),
            estado=r["estado"] or "PENDIENTE",
            monto_pagado=float(r["monto_pagado"] or 0.0),
            monto_pendiente=float(r["monto_pendiente"] or 0.0),
            observacion=r["observacion"],
            fecha_actualizacion=r["fecha_actualizacion"]
        )
