from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from repositories.venta_repository import VentaRepository
from repositories.ticket_repository import TicketRepository
from repositories.vale_repository import ValeRepository
from repositories.pago_repository import PagoRepository
from repositories.mes_repository import MesRepository
from repositories.configuracion_repository import ConfiguracionRepository
from repositories.auditoria_repository import AuditoriaRepository
from models.venta import VentaDiaria

class VentaService:
    def __init__(
        self,
        venta_repo: Optional[VentaRepository] = None,
        ticket_repo: Optional[TicketRepository] = None,
        vale_repo: Optional[ValeRepository] = None,
        pago_repo: Optional[PagoRepository] = None,
        mes_repo: Optional[MesRepository] = None,
        config_repo: Optional[ConfiguracionRepository] = None,
        audit_repo: Optional[AuditoriaRepository] = None
    ):
        self.repo = venta_repo or VentaRepository()
        self.ticket_repo = ticket_repo or TicketRepository()
        self.vale_repo = vale_repo or ValeRepository()
        self.pago_repo = pago_repo or PagoRepository()
        self.mes_repo = mes_repo or MesRepository()
        self.config_repo = config_repo or ConfiguracionRepository()
        self.audit_repo = audit_repo or AuditoriaRepository()

    def get_by_fecha(self, fecha: str) -> Optional[VentaDiaria]:
        return self.repo.get_by_fecha(fecha)

    def get_by_mes(self, anio: int, mes: int) -> List[VentaDiaria]:
        return self.repo.get_by_mes(anio, mes)

    def get_resumen_mes(self, anio: int, mes: int) -> dict:
        return self.repo.get_resumen_mes(anio, mes)

    def get_precio_historico_periodo(self, anio: int, mes: int) -> float:
        """Gets the fixed price for this month/year, never mutating historical periods."""
        m = self.mes_repo.get_by_anio_mes(anio, mes)
        if m:
            return m.precio_menu_policial
        return self.config_repo.get_float("precio_menu_policial", 15.0)

    def registrar_venta_diaria(
        self,
        fecha: str,
        venta_total: float,
        menus_vendidos: int,
        usuario: str = "USUARIO"
    ) -> Tuple[bool, str, VentaDiaria]:
        if venta_total < 0 or menus_vendidos < 0:
            return False, "La venta total y los menús vendidos no pueden ser negativos.", None

        dt = datetime.strptime(fecha, "%Y-%m-%d")
        precio_periodo = self.get_precio_historico_periodo(dt.year, dt.month)

        # Pull automated values directly from related tables (Never ask user to copy)
        td = self.ticket_repo.get_ticket_diario_by_fecha(fecha)
        para_unidad = td.para_unidad if td else 0
        local = td.local if td else 0
        policias = para_unidad + local
        obs_ticket = td.observacion if td else ""

        vale = self.vale_repo.get_by_fecha(fecha)
        vales_canjeados = vale.vales_canjeados if vale else 0

        pago = self.pago_repo.get_by_fecha(fecha)
        tickets_pagados = pago.tickets_pagados if pago else 0
        tickets_debidos = pago.tickets_debidos if pago else 0
        obs_pago = pago.observacion if pago else ""

        obs_combinadas = " | ".join(filter(None, [obs_ticket, obs_pago]))

        venta = VentaDiaria(
            fecha=fecha,
            venta_total=venta_total,
            menus_vendidos=menus_vendidos,
            para_unidad=para_unidad,
            local=local,
            policias=policias,
            menus_sin_policias=menus_vendidos - policias,
            precio_policial_aplicado=precio_periodo,
            venta_policial_calculada=round(policias * precio_periodo, 2),
            venta_sin_policias=round(venta_total - (policias * precio_periodo), 2),
            vales_canjeados=vales_canjeados,
            tickets_pagados=tickets_pagados,
            tickets_debidos=tickets_debidos,
            observaciones=obs_combinadas or None
        )

        alertas = []
        if policias > menus_vendidos and menus_vendidos > 0:
            alertas.append("⚠️ Los tickets policiales registrados superan la cantidad de menús vendidos. Revise los datos.")
        if venta.venta_sin_policias < 0:
            alertas.append("⚠️ La venta calculada sin policías resulta negativa. Revise el importe de venta total.")

        self.repo.save(venta)

        self.audit_repo.registrar(
            accion="REGISTRAR_VENTA_DIARIA",
            entidad="ventas_diarias",
            entidad_id=fecha,
            detalles=f"Fecha {fecha}: VentaTotal=S/ {venta_total:.2f}, MenúsVendidos={menus_vendidos}, Policías={policias}, VentaPolicial=S/ {venta.venta_policial_calculada:.2f}, VentaSinPol=S/ {venta.venta_sin_policias:.2f}",
            usuario=usuario
        )

        msg = "Venta diaria registrada correctamente."
        if alertas:
            msg += " " + " ".join(alertas)

        return True, msg, venta

    def sincronizar_desde_calendario(self, fecha: str) -> Optional[VentaDiaria]:
        """Auto-updates existing sales record if tickets in calendar or payments changed."""
        venta = self.repo.get_by_fecha(fecha)
        if not venta:
            return None

        dt = datetime.strptime(fecha, "%Y-%m-%d")
        precio_periodo = self.get_precio_historico_periodo(dt.year, dt.month)

        td = self.ticket_repo.get_ticket_diario_by_fecha(fecha)
        if td:
            venta.para_unidad = td.para_unidad
            venta.local = td.local
            venta.policias = td.total_policias

        vale = self.vale_repo.get_by_fecha(fecha)
        if vale:
            venta.vales_canjeados = vale.vales_canjeados

        pago = self.pago_repo.get_by_fecha(fecha)
        if pago:
            venta.tickets_pagados = pago.tickets_pagados
            venta.tickets_debidos = pago.tickets_debidos

        venta.precio_policial_aplicado = precio_periodo
        venta.recalcular()
        self.repo.save(venta)
        return venta
