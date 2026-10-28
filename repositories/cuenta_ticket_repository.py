from typing import List, Optional, Any
from database.connection import DatabaseManager
from models.cuenta_ticket import MovimientoTicket, ResumenCuentaPolicia

class CuentaTicketRepository:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager.get_instance()

    def registrar_movimiento(self, mov: MovimientoTicket) -> int:
        if mov.monto_total <= 0:
            mov.monto_total = round(mov.cantidad_tickets * mov.precio_unitario, 2)

        query = """
            INSERT INTO policias_cuentas_tickets (
                policia_id, fecha, tipo_movimiento, cantidad_tickets,
                precio_unitario, monto_total, medio_pago, observacion, fecha_registro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        params = (
            mov.policia_id,
            mov.fecha,
            mov.tipo_movimiento.upper(),
            mov.cantidad_tickets,
            mov.precio_unitario,
            mov.monto_total,
            mov.medio_pago or "EFECTIVO",
            mov.observacion
        )
        return self.db.execute_non_query(query, params)

    def actualizar_movimiento(self, mov: MovimientoTicket) -> bool:
        if not mov.id:
            return False
        if mov.monto_total <= 0:
            mov.monto_total = round(mov.cantidad_tickets * mov.precio_unitario, 2)

        query = """
            UPDATE policias_cuentas_tickets
            SET policia_id = ?, fecha = ?, tipo_movimiento = ?,
                cantidad_tickets = ?, precio_unitario = ?, monto_total = ?,
                medio_pago = ?, observacion = ?
            WHERE id = ?
        """
        params = (
            mov.policia_id,
            mov.fecha,
            mov.tipo_movimiento.upper(),
            mov.cantidad_tickets,
            mov.precio_unitario,
            mov.monto_total,
            mov.medio_pago or "EFECTIVO",
            mov.observacion,
            mov.id
        )
        self.db.execute_non_query(query, params)
        return True

    def eliminar_movimiento(self, mov_id: int) -> bool:
        self.db.execute_non_query("DELETE FROM policias_cuentas_tickets WHERE id = ?", (mov_id,))
        return True

    def get_by_id(self, mov_id: int) -> Optional[MovimientoTicket]:
        query = """
            SELECT m.*, p.codigo as policia_codigo, p.apellidos as policia_apellidos,
                   p.nombres as policia_nombres, p.area as policia_area
            FROM policias_cuentas_tickets m
            JOIN policias p ON m.policia_id = p.id
            WHERE m.id = ?
        """
        rows = self.db.execute_query(query, (mov_id,))
        return self._row_to_movimiento(rows[0]) if rows else None

    def get_movimientos_by_policia(self, policia_id: int) -> List[MovimientoTicket]:
        query = """
            SELECT m.*, p.codigo as policia_codigo, p.apellidos as policia_apellidos,
                   p.nombres as policia_nombres, p.area as policia_area
            FROM policias_cuentas_tickets m
            JOIN policias p ON m.policia_id = p.id
            WHERE m.policia_id = ?
            ORDER BY m.fecha DESC, m.id DESC
        """
        rows = self.db.execute_query(query, (policia_id,))
        return [self._row_to_movimiento(r) for r in rows]

    def get_movimientos_todos(
        self,
        tipo: Optional[str] = None,
        busqueda: Optional[str] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None
    ) -> List[MovimientoTicket]:
        query = """
            SELECT m.*, p.codigo as policia_codigo, p.apellidos as policia_apellidos,
                   p.nombres as policia_nombres, p.area as policia_area
            FROM policias_cuentas_tickets m
            JOIN policias p ON m.policia_id = p.id
            WHERE 1=1
        """
        params: List[Any] = []

        if tipo and tipo.upper() != "TODOS":
            query += " AND m.tipo_movimiento = ?"
            params.append(tipo.upper())

        if fecha_desde:
            query += " AND m.fecha >= ?"
            params.append(fecha_desde)

        if fecha_hasta:
            query += " AND m.fecha <= ?"
            params.append(fecha_hasta)

        if busqueda:
            term = f"%{busqueda.strip()}%"
            query += " AND (p.codigo LIKE ? OR p.apellidos LIKE ? OR p.nombres LIKE ? OR p.area LIKE ? OR m.observacion LIKE ?)"
            params.extend([term, term, term, term, term])

        query += " ORDER BY m.fecha DESC, m.id DESC"
        rows = self.db.execute_query(query, tuple(params))
        return [self._row_to_movimiento(r) for r in rows]

    def get_resumen_cuentas(
        self,
        busqueda: Optional[str] = None,
        solo_deudores: bool = False,
        precio_ticket_defecto: float = 12.0
    ) -> List[ResumenCuentaPolicia]:
        """
        Calcula para cada policía en el sistema:
        - Total tickets que se le registraron como DEBE
        - Total tickets que ha PAGADO
        - Saldo de tickets que debe actualmente = Debe - Pagado
        - Total monto deuda y saldo en soles
        Totalmente independiente de la matriz policial.
        """
        query = """
            SELECT 
                p.id as policia_id,
                p.codigo,
                p.apellidos,
                p.nombres,
                p.area,
                p.sa_pnp,
                COALESCE(SUM(CASE WHEN m.tipo_movimiento = 'DEBE' THEN m.cantidad_tickets ELSE 0 END), 0) as tickets_debe_total,
                COALESCE(SUM(CASE WHEN m.tipo_movimiento = 'PAGO' THEN m.cantidad_tickets ELSE 0 END), 0) as tickets_pago_total,
                COALESCE(SUM(CASE WHEN m.tipo_movimiento = 'DEBE' THEN m.monto_total ELSE 0 END), 0.0) as monto_debe_total,
                COALESCE(SUM(CASE WHEN m.tipo_movimiento = 'PAGO' THEN m.monto_total ELSE 0 END), 0.0) as monto_pago_total
            FROM policias p
            LEFT JOIN policias_cuentas_tickets m ON p.id = m.policia_id
            WHERE p.estado = 'ACTIVO'
        """
        params: List[Any] = []

        if busqueda:
            term = f"%{busqueda.strip()}%"
            query += " AND (p.codigo LIKE ? OR p.apellidos LIKE ? OR p.nombres LIKE ? OR p.area LIKE ? OR p.sa_pnp LIKE ?)"
            params.extend([term, term, term, term, term])

        query += " GROUP BY p.id ORDER BY p.apellidos ASC, p.nombres ASC"
        rows = self.db.execute_query(query, tuple(params))

        resultados: List[ResumenCuentaPolicia] = []
        for r in rows:
            debe_t = int(r["tickets_debe_total"] or 0)
            pago_t = int(r["tickets_pago_total"] or 0)
            saldo_t = debe_t - pago_t

            monto_debe = float(r["monto_debe_total"] or 0.0)
            monto_pago = float(r["monto_pago_total"] or 0.0)
            saldo_monto = max(0.0, monto_debe - monto_pago)

            if saldo_t > 0:
                estado = "DEBE"
            elif saldo_t == 0:
                estado = "AL DÍA"
            else:
                estado = "A FAVOR"

            if solo_deudores and saldo_t <= 0:
                continue

            resultados.append(ResumenCuentaPolicia(
                policia_id=r["policia_id"],
                codigo=r["codigo"],
                apellidos=r["apellidos"],
                nombres=r["nombres"],
                area=r["area"],
                sa_pnp=r["sa_pnp"],
                tickets_debe_total=debe_t,
                tickets_pago_total=pago_t,
                saldo_tickets_debe=saldo_t,
                monto_debe_total=monto_debe,
                monto_pago_total=monto_pago,
                saldo_monto_debe=saldo_monto,
                estado=estado
            ))

        return resultados

    def get_resumen_policia_individual(
        self,
        policia_id: int,
        precio_ticket_defecto: float = 12.0
    ) -> Optional[ResumenCuentaPolicia]:
        res = self.get_resumen_cuentas(precio_ticket_defecto=precio_ticket_defecto)
        for r in res:
            if r.policia_id == policia_id:
                return r
        return None

    @staticmethod
    def _row_to_movimiento(r) -> MovimientoTicket:
        return MovimientoTicket(
            id=r["id"],
            policia_id=r["policia_id"],
            fecha=r["fecha"],
            tipo_movimiento=r["tipo_movimiento"],
            cantidad_tickets=int(r["cantidad_tickets"] or 0),
            precio_unitario=float(r["precio_unitario"] or 12.0),
            monto_total=float(r["monto_total"] or 0.0),
            medio_pago=r["medio_pago"] if "medio_pago" in r.keys() else "EFECTIVO",
            observacion=r["observacion"] if "observacion" in r.keys() else None,
            fecha_registro=r["fecha_registro"] if "fecha_registro" in r.keys() else None,
            policia_codigo=r["policia_codigo"] if "policia_codigo" in r.keys() else None,
            policia_apellidos=r["policia_apellidos"] if "policia_apellidos" in r.keys() else None,
            policia_nombres=r["policia_nombres"] if "policia_nombres" in r.keys() else None,
            policia_area=r["policia_area"] if "policia_area" in r.keys() else None
        )
