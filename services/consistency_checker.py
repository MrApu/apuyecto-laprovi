from typing import List, Dict, Any, Optional
from repositories.ticket_repository import TicketRepository
from repositories.vale_repository import ValeRepository
from repositories.pago_repository import PagoRepository
from repositories.venta_repository import VentaRepository
from repositories.mes_repository import MesRepository

class ConsistencyChecker:
    """Verifies all 11 consistency rules described in the system specification."""

    def __init__(
        self,
        ticket_repo: Optional[TicketRepository] = None,
        vale_repo: Optional[ValeRepository] = None,
        pago_repo: Optional[PagoRepository] = None,
        venta_repo: Optional[VentaRepository] = None,
        mes_repo: Optional[MesRepository] = None
    ):
        self.ticket_repo = ticket_repo or TicketRepository()
        self.vale_repo = vale_repo or ValeRepository()
        self.pago_repo = pago_repo or PagoRepository()
        self.venta_repo = venta_repo or VentaRepository()
        self.mes_repo = mes_repo or MesRepository()

    def verificar_mes(self, anio: int, mes: int) -> List[Dict[str, Any]]:
        inconsistencias: List[Dict[str, Any]] = []

        m = self.mes_repo.get_by_anio_mes(anio, mes)
        precio_periodo = m.precio_menu_policial if m else 15.0

        tickets_diarios = self.ticket_repo.get_tickets_diarios_mes(anio, mes)
        vales = {v.fecha: v for v in self.vale_repo.get_by_mes(anio, mes)}
        pagos = {p.fecha: p for p in self.pago_repo.get_by_mes(anio, mes)}
        ventas = {v.fecha: v for v in self.venta_repo.get_by_mes(anio, mes)}

        for td in tickets_diarios:
            fecha = td.fecha

            # 1. Total tickets = para_unidad + local
            if td.total_policias != (td.para_unidad + td.local):
                inconsistencias.append({
                    "fecha": fecha,
                    "tipo": "ERROR_SUMA_TICKETS",
                    "mensaje": f"Total tickets ({td.total_policias}) != Unidad ({td.para_unidad}) + Local ({td.local})"
                })

            # 6. Saldo vales = entregados - canjeados & No negative
            vl = vales.get(fecha)
            if vl:
                if vl.saldo != (vl.vales_entregados - vl.vales_canjeados):
                    inconsistencias.append({
                        "fecha": fecha,
                        "tipo": "ERROR_SALDO_VALES",
                        "mensaje": f"Saldo de vales ({vl.saldo}) != Entregados ({vl.vales_entregados}) - Canjeados ({vl.vales_canjeados})"
                    })
                if vl.saldo < 0:
                    inconsistencias.append({
                        "fecha": fecha,
                        "tipo": "ADVERTENCIA_VALES_NEGATIVOS",
                        "mensaje": f"Saldo de vales negativo ({vl.saldo})."
                    })

            # 5. Pagados + Debidos = Total tickets
            pg = pagos.get(fecha)
            if pg:
                if (pg.tickets_pagados + pg.tickets_debidos) != pg.total_tickets:
                    inconsistencias.append({
                        "fecha": fecha,
                        "tipo": "ADVERTENCIA_PAGOS_NO_CUADRAN",
                        "mensaje": f"Pagados ({pg.tickets_pagados}) + Debidos ({pg.tickets_debidos}) != Total tickets ({pg.total_tickets})"
                    })

            # Ventas checks
            vt = ventas.get(fecha)
            if vt:
                # 2. Menús sin policías = Menús vendidos - Policías
                if vt.menus_sin_policias != (vt.menus_vendidos - vt.policias):
                    inconsistencias.append({
                        "fecha": fecha,
                        "tipo": "ERROR_MENUS_SIN_POLICIAS",
                        "mensaje": f"Menús sin policías ({vt.menus_sin_policias}) != Menús vendidos ({vt.menus_vendidos}) - Policías ({vt.policias})"
                    })

                if vt.policias > vt.menus_vendidos and vt.menus_vendidos > 0:
                    inconsistencias.append({
                        "fecha": fecha,
                        "tipo": "ADVERTENCIA_POLICIAS_SUPERAN_MENUS",
                        "mensaje": f"Tickets policiales ({vt.policias}) superan menús vendidos ({vt.menus_vendidos})."
                    })

                # 3. Venta policial = Policías * Precio
                venta_pol_esperada = round(vt.policias * vt.precio_policial_aplicado, 2)
                if abs(vt.venta_policial_calculada - venta_pol_esperada) > 0.01:
                    inconsistencias.append({
                        "fecha": fecha,
                        "tipo": "ERROR_VENTA_POLICIAL",
                        "mensaje": f"Venta policial ({vt.venta_policial_calculada}) != Policías ({vt.policias}) * Precio ({vt.precio_policial_aplicado})"
                    })

                # 4. Venta sin policías = Venta total - Venta policial
                venta_sin_pol_esperada = round(vt.venta_total - vt.venta_policial_calculada, 2)
                if abs(vt.venta_sin_policias - venta_sin_pol_esperada) > 0.01:
                    inconsistencias.append({
                        "fecha": fecha,
                        "tipo": "ERROR_VENTA_SIN_POLICIAS",
                        "mensaje": f"Venta sin policías ({vt.venta_sin_policias}) != Venta total ({vt.venta_total}) - Venta policial ({vt.venta_policial_calculada})"
                    })

                if vt.venta_sin_policias < 0:
                    inconsistencias.append({
                        "fecha": fecha,
                        "tipo": "ADVERTENCIA_VENTA_SIN_POLICIAS_NEGATIVA",
                        "mensaje": f"Venta sin policías negativa (S/ {vt.venta_sin_policias:.2f})."
                    })

        return inconsistencias
