from typing import List, Optional, Tuple, Dict, Any
from repositories.pago_repository import PagoRepository
from repositories.ticket_repository import TicketRepository
from repositories.auditoria_repository import AuditoriaRepository
from models.pago import PagoTicket

class PagoService:
    def __init__(
        self,
        pago_repo: Optional[PagoRepository] = None,
        ticket_repo: Optional[TicketRepository] = None,
        audit_repo: Optional[AuditoriaRepository] = None
    ):
        self.repo = pago_repo or PagoRepository()
        self.ticket_repo = ticket_repo or TicketRepository()
        self.audit_repo = audit_repo or AuditoriaRepository()

    def get_by_fecha(self, fecha: str) -> Optional[PagoTicket]:
        return self.repo.get_by_fecha(fecha)

    def get_by_mes(self, anio: int, mes: int) -> List[PagoTicket]:
        return self.repo.get_by_mes(anio, mes)

    def get_resumen_mes(self, anio: int, mes: int) -> dict:
        return self.repo.get_resumen_mes(anio, mes)

    def guardar_pago(
        self,
        fecha: str,
        total_tickets: Optional[int],
        tickets_pagados: int,
        tickets_debidos: int,
        monto_pagado: float = 0.0,
        monto_pendiente: float = 0.0,
        observacion: Optional[str] = None,
        usuario: str = "USUARIO"
    ) -> Tuple[bool, str, PagoTicket]:
        if tickets_pagados < 0 or tickets_debidos < 0 or monto_pagado < 0 or monto_pendiente < 0:
            return False, "Las cantidades y montos no pueden ser negativos.", None

        # If total_tickets is None, check tickets_diarios
        if total_tickets is None:
            td = self.ticket_repo.get_ticket_diario_by_fecha(fecha)
            total_tickets = td.total_policias if td else (tickets_pagados + tickets_debidos)

        pago = PagoTicket(
            fecha=fecha,
            total_tickets=total_tickets,
            tickets_pagados=tickets_pagados,
            tickets_debidos=tickets_debidos,
            monto_pagado=monto_pagado,
            monto_pendiente=monto_pendiente,
            observacion=observacion
        )
        pago.calcular_estado()

        advertencia = ""
        if (tickets_pagados + tickets_debidos) != total_tickets:
            advertencia = f" ⚠️ Advertencia: La suma de pagados ({tickets_pagados}) + debidos ({tickets_debidos}) no coincide con el total de tickets ({total_tickets})."

        self.repo.save(pago)

        self.audit_repo.registrar(
            accion="GUARDAR_PAGO_TICKET",
            entidad="pagos_tickets",
            entidad_id=fecha,
            detalles=f"Fecha {fecha}: Total={total_tickets}, Pagados={tickets_pagados}, Debidos={tickets_debidos}, Estado={pago.estado}",
            usuario=usuario
        )

        return True, f"Control de pago guardado.{advertencia}", pago

    def registrar_pago(
        self,
        fecha: str,
        total_tickets: Optional[int],
        tickets_pagados: int,
        tickets_debidos: int,
        monto_pagado: float = 0.0,
        monto_pendiente: float = 0.0,
        observacion: Optional[str] = None,
        usuario: str = "USUARIO"
    ) -> Tuple[bool, str, PagoTicket]:
        return self.guardar_pago(fecha, total_tickets, tickets_pagados, tickets_debidos, monto_pagado, monto_pendiente, observacion, usuario)
