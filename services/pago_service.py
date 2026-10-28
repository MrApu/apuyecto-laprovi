from typing import List, Optional, Tuple, Dict, Any
from repositories.pago_repository import PagoRepository
from repositories.ticket_repository import TicketRepository
from repositories.auditoria_repository import AuditoriaRepository
from repositories.policia_pago_repository import PoliciaPagoRepository
from repositories.policia_repository import PoliciaRepository
from models.pago import PagoTicket
from models.policia_pago import PoliciaPagoTicket, ResumenDeudaPolicia

class PagoService:
    def __init__(
        self,
        pago_repo: Optional[PagoRepository] = None,
        ticket_repo: Optional[TicketRepository] = None,
        audit_repo: Optional[AuditoriaRepository] = None,
        policia_pago_repo: Optional[PoliciaPagoRepository] = None,
        policia_repo: Optional[PoliciaRepository] = None
    ):
        self.repo = pago_repo or PagoRepository()
        self.ticket_repo = ticket_repo or TicketRepository()
        self.audit_repo = audit_repo or AuditoriaRepository()
        self.policia_pago_repo = policia_pago_repo or PoliciaPagoRepository()
        self.policia_repo = policia_repo or PoliciaRepository()

    # --- Métodos Diarios (Compatibilidad) ---
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

    # --- Sistema de Cobranzas y Deudas por Policía (Nuevo) ---
    def get_resumen_deudas_policias(
        self,
        mes_id: int,
        busqueda: Optional[str] = None,
        solo_con_deuda: bool = False,
        precio_ticket: float = 12.0
    ) -> List[ResumenDeudaPolicia]:
        return self.policia_pago_repo.get_resumen_deudas_policias(
            mes_id=mes_id,
            busqueda=busqueda,
            solo_con_deuda=solo_con_deuda,
            precio_ticket=precio_ticket
        )

    def get_resumen_policia_individual(
        self,
        mes_id: int,
        policia_id: int,
        precio_ticket: float = 12.0
    ) -> Optional[ResumenDeudaPolicia]:
        return self.policia_pago_repo.get_resumen_deuda_policia_individual(
            mes_id=mes_id,
            policia_id=policia_id,
            precio_ticket=precio_ticket
        )

    def get_historial_pagos_policia(self, policia_id: int, mes_id: Optional[int] = None) -> List[PoliciaPagoTicket]:
        return self.policia_pago_repo.get_pagos_by_policia(policia_id, mes_id)

    def registrar_pago_policia(
        self,
        policia_id: int,
        mes_id: Optional[int],
        fecha: str,
        tickets_pagados: int,
        monto_pagado: float,
        medio_pago: str = "EFECTIVO",
        observacion: Optional[str] = None,
        usuario: str = "USUARIO"
    ) -> Tuple[bool, str, Optional[int]]:
        if tickets_pagados <= 0 and monto_pagado <= 0:
            return False, "Debe ingresar al menos la cantidad de tickets o el monto pagado.", None

        policia = self.policia_repo.get_by_id(policia_id)
        if not policia:
            return False, "Policía no encontrado.", None

        pago = PoliciaPagoTicket(
            policia_id=policia_id,
            mes_id=mes_id,
            fecha=fecha,
            tickets_pagados=tickets_pagados,
            monto_pagado=monto_pagado,
            medio_pago=medio_pago,
            observacion=observacion
        )
        pago_id = self.policia_pago_repo.registrar_pago(pago)

        self.audit_repo.registrar(
            accion="REGISTRAR_PAGO_TICKET_POLICIA",
            entidad="policias_pagos_tickets",
            entidad_id=str(pago_id),
            detalles=f"Policía: {policia.apellidos}, {policia.nombres} ({policia.codigo}) | Tickets: {tickets_pagados} | Monto: S/ {monto_pagado:.2f} ({medio_pago})",
            usuario=usuario
        )
        return True, f"Pago de {tickets_pagados} tickets (S/ {monto_pagado:.2f}) registrado con éxito.", pago_id

    def eliminar_pago_policia(self, pago_id: int, usuario: str = "USUARIO") -> Tuple[bool, str]:
        pago = self.policia_pago_repo.get_by_id(pago_id)
        if not pago:
            return False, "El registro de pago no existe."

        self.policia_pago_repo.eliminar_pago(pago_id)
        self.audit_repo.registrar(
            accion="ELIMINAR_PAGO_TICKET_POLICIA",
            entidad="policias_pagos_tickets",
            entidad_id=str(pago_id),
            detalles=f"Eliminado pago de {pago.tickets_pagados} tickets (S/ {pago.monto_pagado:.2f}) de fecha {pago.fecha}.",
            usuario=usuario
        )
        return True, "Pago eliminado correctamente."
