from typing import List, Optional, Dict, Any
from database.connection import DatabaseManager
from models.policia_pago import PoliciaPagoTicket, ResumenDeudaPolicia

class PoliciaPagoRepository:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager.get_instance()

    def registrar_pago(self, pago: PoliciaPagoTicket) -> int:
        query = """
            INSERT INTO policias_pagos_tickets (
                policia_id, mes_id, fecha, tickets_pagados, monto_pagado, medio_pago, observacion, fecha_registro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        params = (
            pago.policia_id,
            pago.mes_id,
            pago.fecha,
            pago.tickets_pagados,
            pago.monto_pagado,
            pago.medio_pago or "EFECTIVO",
            pago.observacion
        )
        return self.db.execute_non_query(query, params)

    def get_by_id(self, pago_id: int) -> Optional[PoliciaPagoTicket]:
        query = """
            SELECT ppt.*, p.codigo as policia_codigo, (p.apellidos || ', ' || p.nombres) as policia_nombre
            FROM policias_pagos_tickets ppt
            JOIN policias p ON ppt.policia_id = p.id
            WHERE ppt.id = ?
        """
        rows = self.db.execute_query(query, (pago_id,))
        if not rows:
            return None
        return self._row_to_pago(rows[0])

    def eliminar_pago(self, pago_id: int) -> bool:
        self.db.execute_non_query("DELETE FROM policias_pagos_tickets WHERE id = ?", (pago_id,))
        return True

    def get_pagos_by_policia(self, policia_id: int, mes_id: Optional[int] = None) -> List[PoliciaPagoTicket]:
        if mes_id:
            query = """
                SELECT ppt.*, p.codigo as policia_codigo, (p.apellidos || ', ' || p.nombres) as policia_nombre
                FROM policias_pagos_tickets ppt
                JOIN policias p ON ppt.policia_id = p.id
                WHERE ppt.policia_id = ? AND ppt.mes_id = ?
                ORDER BY ppt.fecha DESC, ppt.id DESC
            """
            rows = self.db.execute_query(query, (policia_id, mes_id))
        else:
            query = """
                SELECT ppt.*, p.codigo as policia_codigo, (p.apellidos || ', ' || p.nombres) as policia_nombre
                FROM policias_pagos_tickets ppt
                JOIN policias p ON ppt.policia_id = p.id
                WHERE ppt.policia_id = ?
                ORDER BY ppt.fecha DESC, ppt.id DESC
            """
            rows = self.db.execute_query(query, (policia_id,))
        return [self._row_to_pago(r) for r in rows]

    def get_pagos_by_mes(self, mes_id: int) -> List[PoliciaPagoTicket]:
        query = """
            SELECT ppt.*, p.codigo as policia_codigo, (p.apellidos || ', ' || p.nombres) as policia_nombre
            FROM policias_pagos_tickets ppt
            JOIN policias p ON ppt.policia_id = p.id
            WHERE ppt.mes_id = ?
            ORDER BY ppt.fecha DESC, ppt.id DESC
        """
        rows = self.db.execute_query(query, (mes_id,))
        return [self._row_to_pago(r) for r in rows]

    def get_resumen_deudas_policias(
        self,
        mes_id: int,
        busqueda: Optional[str] = None,
        solo_con_deuda: bool = False,
        precio_ticket: float = 12.0
    ) -> List[ResumenDeudaPolicia]:
        """
        Calcula para cada policía en el mes:
        - tickets_totales (consumidos/asignados)
        - tickets_pagados (registrados en policias_pagos_tickets)
        - tickets_debidos (totales - pagados)
        - montos y estado (PAGADO, DEBE, PARCIAL, AL DÍA)
        """
        query = """
            SELECT 
                p.id as policia_id,
                p.codigo,
                p.apellidos,
                p.nombres,
                p.sa_pnp,
                p.area,
                COALESCE(tk.total_tickets, 0) as tickets_totales,
                COALESCE(pg.tickets_pagados, 0) as tickets_pagados,
                COALESCE(pg.monto_pagado, 0.0) as monto_pagado
            FROM policias p
            LEFT JOIN (
                SELECT policia_id, COUNT(*) as total_tickets
                FROM tickets_por_policia
                WHERE mes_id = ? AND valor = 1
                GROUP BY policia_id
            ) tk ON p.id = tk.policia_id
            LEFT JOIN (
                SELECT policia_id, SUM(tickets_pagados) as tickets_pagados, SUM(monto_pagado) as monto_pagado
                FROM policias_pagos_tickets
                WHERE mes_id = ?
                GROUP BY policia_id
            ) pg ON p.id = pg.policia_id
            WHERE p.estado = 'ACTIVO'
        """
        params: List[Any] = [mes_id, mes_id]

        if busqueda:
            term = f"%{busqueda.strip()}%"
            query += " AND (p.codigo LIKE ? OR p.apellidos LIKE ? OR p.nombres LIKE ? OR p.area LIKE ? OR p.sa_pnp LIKE ?)"
            params.extend([term, term, term, term, term])

        query += " ORDER BY p.apellidos ASC, p.nombres ASC"
        rows = self.db.execute_query(query, tuple(params))

        resultados: List[ResumenDeudaPolicia] = []
        for r in rows:
            tot = int(r["tickets_totales"] or 0)
            pag = int(r["tickets_pagados"] or 0)
            deb = max(0, tot - pag)
            monto_pag = float(r["monto_pagado"] or 0.0)
            monto_pend = round(deb * precio_ticket, 2)

            if tot == 0:
                estado = "AL DÍA"
            elif deb == 0:
                estado = "PAGADO"
            elif pag == 0:
                estado = "DEBE"
            else:
                estado = "PARCIAL"

            if solo_con_deuda and deb <= 0:
                continue

            resultados.append(ResumenDeudaPolicia(
                policia_id=r["policia_id"],
                codigo=r["codigo"],
                apellidos=r["apellidos"],
                nombres=r["nombres"],
                sa_pnp=r["sa_pnp"],
                area=r["area"],
                tickets_totales=tot,
                tickets_pagados=pag,
                tickets_debidos=deb,
                monto_pagado=monto_pag,
                monto_pendiente=monto_pend,
                estado=estado
            ))
        return resultados

    def get_resumen_deuda_policia_individual(
        self,
        mes_id: int,
        policia_id: int,
        precio_ticket: float = 12.0
    ) -> Optional[ResumenDeudaPolicia]:
        res = self.get_resumen_deudas_policias(mes_id=mes_id, precio_ticket=precio_ticket)
        for r in res:
            if r.policia_id == policia_id:
                return r
        return None

    @staticmethod
    def _row_to_pago(r) -> PoliciaPagoTicket:
        return PoliciaPagoTicket(
            id=r["id"],
            policia_id=r["policia_id"],
            mes_id=r["mes_id"],
            fecha=r["fecha"],
            tickets_pagados=int(r["tickets_pagados"] or 0),
            monto_pagado=float(r["monto_pagado"] or 0.0),
            medio_pago=r["medio_pago"] or "EFECTIVO",
            observacion=r["observacion"],
            fecha_registro=r["fecha_registro"],
            policia_codigo=r["policia_codigo"] if "policia_codigo" in r.keys() else None,
            policia_nombre=r["policia_nombre"] if "policia_nombre" in r.keys() else None
        )
