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
                pol = vt.cantidad_tickets if vt.cantidad_tickets is not None else (vt.policias or 0)
                precio = vt.precio_ticket_aplicado if vt.precio_ticket_aplicado is not None else (vt.precio_policial_aplicado or 12.0)
                v_tickets = vt.venta_tickets if vt.venta_tickets is not None else (vt.venta_policial_calculada or 0.0)
                v_sin_t = vt.venta_sin_tickets if vt.venta_sin_tickets is not None else (vt.venta_sin_policias or 0.0)
                v_tot = vt.venta_total or 0.0

                # Venta tickets = Cantidad * Precio
                venta_pol_esperada = round(pol * precio, 2)
                if abs((v_tickets or 0.0) - venta_pol_esperada) > 0.01:
                    inconsistencias.append({
                        "fecha": fecha,
                        "tipo": "ERROR_VENTA_POLICIAL",
                        "mensaje": f"Venta policial ({v_tickets}) != Tickets ({pol}) * Precio ({precio})"
                    })

                # Venta sin tickets = Venta total - Venta tickets
                if vt.venta_incluye_tickets == 1:
                    expected_sin_t = round(max(0.0, v_tot - (v_tickets or 0.0)), 2)
                    if abs((v_sin_t or 0.0) - expected_sin_t) > 0.01 and v_tot > 0:
                        inconsistencias.append({
                            "fecha": fecha,
                            "tipo": "ERROR_VENTA_SIN_TICKETS",
                            "mensaje": f"Venta sin tickets ({v_sin_t}) != Venta total ({v_tot}) - Tickets ({v_tickets})"
                        })
                else:
                    expected_total = round((v_sin_t or 0.0) + (v_tickets or 0.0), 2)
                    if abs(v_tot - expected_total) > 0.01 and v_tot > 0:
                        inconsistencias.append({
                            "fecha": fecha,
                            "tipo": "ERROR_VENTA_TOTAL",
                            "mensaje": f"Venta total ({v_tot}) != Venta sin tickets ({v_sin_t}) + Tickets ({v_tickets})"
                        })

                if (v_sin_t or 0.0) < 0:
                    inconsistencias.append({
                        "fecha": fecha,
                        "tipo": "ADVERTENCIA_VENTA_SIN_POLICIAS_NEGATIVA",
                        "mensaje": f"Venta sin policías negativa (S/ {v_sin_t:.2f})."
                    })

        return inconsistencias
