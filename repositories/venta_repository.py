from typing import List, Optional
from database.connection import DatabaseManager
from models.venta import VentaDiaria
from models.local import LOCAL_CONSOLIDADO

class VentaRepository:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager.get_instance()

    def get_by_fecha(self, fecha: str, local_id: str = "restaurante") -> Optional[VentaDiaria]:
        if local_id == LOCAL_CONSOLIDADO:
            rows = self.db.execute_query("""
                SELECT NULL as id, fecha, 'consolidado' as local_id,
                       SUM(efectivo) as efectivo, SUM(yape) as yape,
                       SUM(venta_sin_tickets) as venta_sin_tickets,
                       SUM(cantidad_tickets) as cantidad_tickets,
                       AVG(precio_ticket_aplicado) as precio_ticket_aplicado,
                       SUM(venta_tickets) as venta_tickets,
                       SUM(venta_total) as venta_total,
                       MAX(venta_incluye_tickets) as venta_incluye_tickets,
                       SUM(para_unidad) as para_unidad, SUM(local) as local,
                       SUM(vales_consumidos) as vales_consumidos,
                       SUM(tickets_pagados) as tickets_pagados,
                       SUM(tickets_debidos) as tickets_debidos,
                       GROUP_CONCAT(observaciones, ' | ') as observaciones,
                       MAX(fecha_actualizacion) as fecha_actualizacion
                FROM ventas_diarias
                WHERE fecha = ?
                GROUP BY fecha
            """, (fecha,))
        else:
            rows = self.db.execute_query(
                "SELECT * FROM ventas_diarias WHERE fecha = ? AND local_id = ?",
                (fecha, local_id)
            )
        return self._row_to_entity(rows[0]) if rows else None

    def get_by_mes(self, anio: int, mes: int, local_id: str = "restaurante") -> List[VentaDiaria]:
        prefix = f"{anio:04d}-{mes:02d}-%"
        if local_id == LOCAL_CONSOLIDADO:
            rows = self.db.execute_query("""
                SELECT NULL as id, fecha, 'consolidado' as local_id,
                       SUM(efectivo) as efectivo, SUM(yape) as yape,
                       SUM(venta_sin_tickets) as venta_sin_tickets,
                       SUM(cantidad_tickets) as cantidad_tickets,
                       AVG(precio_ticket_aplicado) as precio_ticket_aplicado,
                       SUM(venta_tickets) as venta_tickets,
                       SUM(venta_total) as venta_total,
                       MAX(venta_incluye_tickets) as venta_incluye_tickets,
                       SUM(para_unidad) as para_unidad, SUM(local) as local,
                       SUM(vales_consumidos) as vales_consumidos,
                       SUM(tickets_pagados) as tickets_pagados,
                       SUM(tickets_debidos) as tickets_debidos,
                       GROUP_CONCAT(observaciones, ' | ') as observaciones,
                       MAX(fecha_actualizacion) as fecha_actualizacion
                FROM ventas_diarias
                WHERE fecha LIKE ?
                GROUP BY fecha
                ORDER BY fecha ASC
            """, (prefix,))
        else:
            rows = self.db.execute_query(
                "SELECT * FROM ventas_diarias WHERE fecha LIKE ? AND local_id = ? ORDER BY fecha ASC",
                (prefix, local_id)
            )
        return [self._row_to_entity(r) for r in rows]

    def save(self, venta: VentaDiaria) -> int:
        venta.recalcular()
        query = """
            INSERT INTO ventas_diarias (
                fecha, local_id, efectivo, yape, venta_sin_tickets, cantidad_tickets,
                precio_ticket_aplicado, venta_tickets, venta_total, venta_incluye_tickets,
                para_unidad, local, vales_consumidos, tickets_pagados, tickets_debidos,
                observaciones, fecha_actualizacion
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(fecha, local_id) DO UPDATE SET
                efectivo = excluded.efectivo,
                yape = excluded.yape,
                venta_sin_tickets = excluded.venta_sin_tickets,
                cantidad_tickets = excluded.cantidad_tickets,
                precio_ticket_aplicado = excluded.precio_ticket_aplicado,
                venta_tickets = excluded.venta_tickets,
                venta_total = excluded.venta_total,
                venta_incluye_tickets = excluded.venta_incluye_tickets,
                para_unidad = excluded.para_unidad,
                local = excluded.local,
                vales_consumidos = excluded.vales_consumidos,
                tickets_pagados = excluded.tickets_pagados,
                tickets_debidos = excluded.tickets_debidos,
                observaciones = excluded.observaciones,
                fecha_actualizacion = CURRENT_TIMESTAMP
        """
        params = (
            venta.fecha,
            venta.local_id or "restaurante",
            venta.efectivo or 0.0,
            venta.yape or 0.0,
            venta.venta_sin_tickets or 0.0,
            venta.cantidad_tickets or 0,
            venta.precio_ticket_aplicado or 12.0,
            venta.venta_tickets or 0.0,
            venta.venta_total or 0.0,
            venta.venta_incluye_tickets or 0,
            venta.para_unidad or 0,
            venta.local or 0,
            venta.vales_consumidos or 0,
            venta.tickets_pagados or 0,
            venta.tickets_debidos or 0,
            venta.observaciones
        )
        return self.db.execute_non_query(query, params)

    def get_resumen_mes(self, anio: int, mes: int, local_id: str = "restaurante") -> dict:
        prefix = f"{anio:04d}-{mes:02d}-%"
        if local_id == LOCAL_CONSOLIDADO:
            rows = self.db.execute_query("""
                SELECT SUM(efectivo) as tot_efectivo,
                       SUM(yape) as tot_yape,
                       SUM(venta_sin_tickets) as tot_sin_tickets,
                       SUM(cantidad_tickets) as tot_tickets,
                       SUM(venta_tickets) as tot_venta_tickets,
                       SUM(venta_total) as tot_venta_total,
                       SUM(para_unidad) as tot_para_unidad,
                       SUM(local) as tot_local,
                       SUM(vales_consumidos) as tot_vales,
                       SUM(tickets_pagados) as tot_pagados,
                       SUM(tickets_debidos) as tot_debidos
                FROM ventas_diarias
                WHERE fecha LIKE ?
            """, (prefix,))
        else:
            rows = self.db.execute_query("""
                SELECT SUM(efectivo) as tot_efectivo,
                       SUM(yape) as tot_yape,
                       SUM(venta_sin_tickets) as tot_sin_tickets,
                       SUM(cantidad_tickets) as tot_tickets,
                       SUM(venta_tickets) as tot_venta_tickets,
                       SUM(venta_total) as tot_venta_total,
                       SUM(para_unidad) as tot_para_unidad,
                       SUM(local) as tot_local,
                       SUM(vales_consumidos) as tot_vales,
                       SUM(tickets_pagados) as tot_pagados,
                       SUM(tickets_debidos) as tot_debidos
                FROM ventas_diarias
                WHERE fecha LIKE ? AND local_id = ?
            """, (prefix, local_id))

        if rows and rows[0]["tot_venta_total"] is not None:
            r = rows[0]
            vt = float(r["tot_venta_total"] or 0.0)
            st = float(r["tot_sin_tickets"] or 0.0)
            ct = int(r["tot_tickets"] or 0)
            v_tick = float(r["tot_venta_tickets"] or 0.0)
            return {
                "efectivo": float(r["tot_efectivo"] or 0.0),
                "yape": float(r["tot_yape"] or 0.0),
                "venta_sin_tickets": st,
                "cantidad_tickets": ct,
                "venta_tickets": v_tick,
                "venta_total": vt,
                "para_unidad": int(r["tot_para_unidad"] or 0),
                "local": int(r["tot_local"] or 0),
                "vales_consumidos": int(r["tot_vales"] or 0),
                "tickets_pagados": int(r["tot_pagados"] or 0),
                "tickets_debidos": int(r["tot_debidos"] or 0),
                # Legacy aliases
                "menus_vendidos": ct,
                "menus_sin_policias": 0,
                "venta_policial": v_tick,
                "venta_sin_policias": st,
                "canjeados": int(r["tot_vales"] or 0)
            }
        return {
            "efectivo": 0.0, "yape": 0.0, "venta_sin_tickets": 0.0, "cantidad_tickets": 0,
            "venta_tickets": 0.0, "venta_total": 0.0, "para_unidad": 0, "local": 0,
            "vales_consumidos": 0, "tickets_pagados": 0, "tickets_debidos": 0,
            "menus_vendidos": 0, "menus_sin_policias": 0, "venta_policial": 0.0, "venta_sin_policias": 0.0, "canjeados": 0
        }

    @staticmethod
    def _row_to_entity(r) -> VentaDiaria:
        return VentaDiaria(
            id=r["id"],
            fecha=r["fecha"],
            local_id=r["local_id"],
            efectivo=float(r["efectivo"] or 0.0),
            yape=float(r["yape"] or 0.0),
            venta_sin_tickets=float(r["venta_sin_tickets"] or 0.0),
            cantidad_tickets=int(r["cantidad_tickets"] or 0),
            precio_ticket_aplicado=float(r["precio_ticket_aplicado"] or 12.0),
            venta_tickets=float(r["venta_tickets"] or 0.0),
            venta_total=float(r["venta_total"] or 0.0),
            venta_incluye_tickets=int(r["venta_incluye_tickets"] or 0),
            para_unidad=int(r["para_unidad"] or 0),
            local=int(r["local"] or 0),
            vales_consumidos=int(r["vales_consumidos"] or 0),
            tickets_pagados=int(r["tickets_pagados"] or 0),
            tickets_debidos=int(r["tickets_debidos"] or 0),
            observaciones=r["observaciones"],
            fecha_actualizacion=r["fecha_actualizacion"]
        )
