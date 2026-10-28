from typing import List, Optional, Tuple, Dict, Any
from repositories.cuenta_ticket_repository import CuentaTicketRepository
from repositories.policia_repository import PoliciaRepository
from repositories.auditoria_repository import AuditoriaRepository
from models.cuenta_ticket import MovimientoTicket, ResumenCuentaPolicia

class CuentaTicketService:
    def __init__(
        self,
        repo: Optional[CuentaTicketRepository] = None,
        policia_repo: Optional[PoliciaRepository] = None,
        audit_repo: Optional[AuditoriaRepository] = None
    ):
        self.repo = repo or CuentaTicketRepository()
        self.policia_repo = policia_repo or PoliciaRepository()
        self.audit_repo = audit_repo or AuditoriaRepository()

    def registrar_deuda(
        self,
        policia_id: int,
        fecha: str,
        cantidad_tickets: int,
        precio_unitario: float = 12.0,
        monto_total: Optional[float] = None,
        observacion: Optional[str] = None,
        usuario: str = "USUARIO"
    ) -> Tuple[bool, str, Optional[int]]:
        if cantidad_tickets <= 0:
            return False, "La cantidad de tickets debe ser mayor a 0.", None

        policia = self.policia_repo.get_by_id(policia_id)
        if not policia:
            return False, "Policía no encontrado.", None

        if monto_total is None or monto_total <= 0:
            monto_total = round(cantidad_tickets * precio_unitario, 2)

        mov = MovimientoTicket(
            policia_id=policia_id,
            fecha=fecha,
            tipo_movimiento="DEBE",
            cantidad_tickets=cantidad_tickets,
            precio_unitario=precio_unitario,
            monto_total=monto_total,
            medio_pago=None,
            observacion=observacion
        )
        mov_id = self.repo.registrar_movimiento(mov)

        self.audit_repo.registrar(
            accion="REGISTRAR_DEUDA_TICKETS",
            entidad="policias_cuentas_tickets",
            entidad_id=str(mov_id),
            detalles=f"Policía: {policia.apellidos}, {policia.nombres} ({policia.codigo}) DEBE {cantidad_tickets} tickets (S/ {monto_total:.2f}) en fecha {fecha}.",
            usuario=usuario
        )
        return True, f"Deuda de {cantidad_tickets} tickets (S/ {monto_total:.2f}) registrada a {policia.apellidos}.", mov_id

    def registrar_pago(
        self,
        policia_id: int,
        fecha: str,
        cantidad_tickets: int,
        monto_total: float,
        medio_pago: str = "EFECTIVO",
        observacion: Optional[str] = None,
        usuario: str = "USUARIO"
    ) -> Tuple[bool, str, Optional[int]]:
        if cantidad_tickets <= 0 and monto_total <= 0:
            return False, "Debe ingresar al menos tickets pagados o monto.", None

        policia = self.policia_repo.get_by_id(policia_id)
        if not policia:
            return False, "Policía no encontrado.", None

        precio_unitario = round(monto_total / cantidad_tickets, 2) if cantidad_tickets > 0 else 12.0

        mov = MovimientoTicket(
            policia_id=policia_id,
            fecha=fecha,
            tipo_movimiento="PAGO",
            cantidad_tickets=cantidad_tickets,
            precio_unitario=precio_unitario,
            monto_total=monto_total,
            medio_pago=medio_pago,
            observacion=observacion
        )
        mov_id = self.repo.registrar_movimiento(mov)

        self.audit_repo.registrar(
            accion="REGISTRAR_PAGO_TICKETS",
            entidad="policias_cuentas_tickets",
            entidad_id=str(mov_id),
            detalles=f"Policía: {policia.apellidos}, {policia.nombres} ({policia.codigo}) PAGÓ {cantidad_tickets} tickets (S/ {monto_total:.2f}) vía {medio_pago}.",
            usuario=usuario
        )
        return True, f"Pago de {cantidad_tickets} tickets (S/ {monto_total:.2f}) registrado con éxito.", mov_id

    def eliminar_movimiento(self, mov_id: int, usuario: str = "USUARIO") -> Tuple[bool, str]:
        mov = self.repo.get_by_id(mov_id)
        if not mov:
            return False, "El registro de movimiento no existe."

        self.repo.eliminar_movimiento(mov_id)
        self.audit_repo.registrar(
            accion="ELIMINAR_MOVIMIENTO_TICKETS",
            entidad="policias_cuentas_tickets",
            entidad_id=str(mov_id),
            detalles=f"Eliminado movimiento {mov.tipo_movimiento} de {mov.cantidad_tickets} tickets (S/ {mov.monto_total:.2f}) de policía ID {mov.policia_id}.",
            usuario=usuario
        )
        return True, "Registro eliminado correctamente."

    def get_resumen_cuentas(self, busqueda: Optional[str] = None, solo_deudores: bool = False) -> List[ResumenCuentaPolicia]:
        return self.repo.get_resumen_cuentas(busqueda=busqueda, solo_deudores=solo_deudores)

    def get_resumen_policia_individual(self, policia_id: int) -> Optional[ResumenCuentaPolicia]:
        return self.repo.get_resumen_policia_individual(policia_id)

    def get_movimientos_by_policia(self, policia_id: int) -> List[MovimientoTicket]:
        return self.repo.get_movimientos_by_policia(policia_id)

    def get_movimientos_pagos(self, busqueda: Optional[str] = None) -> List[MovimientoTicket]:
        return self.repo.get_movimientos_todos(tipo="PAGO", busqueda=busqueda)

    def get_movimientos_deudas(self, busqueda: Optional[str] = None) -> List[MovimientoTicket]:
        return self.repo.get_movimientos_todos(tipo="DEBE", busqueda=busqueda)
