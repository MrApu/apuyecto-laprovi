from typing import List, Optional, Dict, Any, Tuple
import calendar
from datetime import datetime
from database.connection import DatabaseManager
from repositories.venta_repository import VentaRepository
from repositories.compra_repository import CompraRepository
from repositories.gasto_repository import GastoRepository
from repositories.pago_personal_repository import PagoPersonalRepository
from repositories.ticket_repository import TicketRepository
from repositories.vale_repository import ValeRepository
from repositories.pago_repository import PagoRepository
from repositories.mes_repository import MesRepository
from repositories.configuracion_repository import ConfiguracionRepository
from repositories.cuenta_ticket_repository import CuentaTicketRepository
from models.local import LOCAL_CONSOLIDADO, LOCAL_RESTAURANTE, LOCAL_FAST_FOOD
from models.ticket import DIAS_SEMANA_ES

class FinancieroService:
    def __init__(
        self,
        venta_repo: Optional[VentaRepository] = None,
        compra_repo: Optional[CompraRepository] = None,
        gasto_repo: Optional[GastoRepository] = None,
        pago_pers_repo: Optional[PagoPersonalRepository] = None,
        ticket_repo: Optional[TicketRepository] = None,
        vale_repo: Optional[ValeRepository] = None,
        pago_repo: Optional[PagoRepository] = None,
        mes_repo: Optional[MesRepository] = None,
        config_repo: Optional[ConfiguracionRepository] = None,
        cuenta_ticket_repo: Optional[CuentaTicketRepository] = None
    ):
        self.venta_repo = venta_repo or VentaRepository()
        self.compra_repo = compra_repo or CompraRepository()
        self.gasto_repo = gasto_repo or GastoRepository()
        self.pago_pers_repo = pago_pers_repo or PagoPersonalRepository()
        self.ticket_repo = ticket_repo or TicketRepository()
        self.vale_repo = vale_repo or ValeRepository()
        self.pago_repo = pago_repo or PagoRepository()
        self.mes_repo = mes_repo or MesRepository()
        self.config_repo = config_repo or ConfiguracionRepository()
        self.cuenta_ticket_repo = cuenta_ticket_repo or CuentaTicketRepository()

    def get_calendario_financiero_mes(self, anio: int, mes: int, local_id: str = "restaurante") -> List[Dict[str, Any]]:
        """
        Returns complete day-by-day financial rows:
        Fecha, Dia, DiaSemana, Efectivo, Yape, VentaTickets, VentaTotal, Compras, Gastos, Personal, TotalEgresos, Saldo
        """
        num_dias = calendar.monthrange(anio, mes)[1]
        ventas = {v.fecha: v for v in self.venta_repo.get_by_mes(anio, mes, local_id)}
        
        # Aggregate daily egresos
        compras_list = self.compra_repo.get_by_mes(anio, mes, local_id)
        gastos_list = self.gasto_repo.get_by_mes(anio, mes, local_id)
        pagos_pers_list = self.pago_pers_repo.get_by_mes(anio, mes, local_id)

        compras_map: Dict[str, float] = {}
        for c in compras_list:
            compras_map[c.fecha] = round(compras_map.get(c.fecha, 0.0) + (c.total or 0.0), 2)

        gastos_map: Dict[str, float] = {}
        for g in gastos_list:
            gastos_map[g.fecha] = round(gastos_map.get(g.fecha, 0.0) + (g.monto or 0.0), 2)

        pagos_pers_map: Dict[str, float] = {}
        for p in pagos_pers_list:
            pagos_pers_map[p.fecha] = round(pagos_pers_map.get(p.fecha, 0.0) + (p.monto or 0.0), 2)

        # Precio estándar del ticket para el mes
        mes_obj = self.mes_repo.get_by_anio_mes(anio, mes)
        precio_ticket_base = mes_obj.precio_ticket_policial if mes_obj else self.config_repo.get_float("precio_ticket_policial", 12.0)
        if not precio_ticket_base or precio_ticket_base <= 0:
            precio_ticket_base = 12.0

        # Tickets diarios del calendario policial para complementar si ventas_diarias no tiene datos
        tickets_diarios_list = self.ticket_repo.get_tickets_diarios_mes(anio, mes, local_id)
        tickets_diarios_map = {td.fecha: td for td in tickets_diarios_list}

        # Movimientos de cuentas (quiénes deben y quiénes pagaron tickets en cada fecha)
        movimientos_mes = self.cuenta_ticket_repo.get_movimientos_todos(
            fecha_desde=f"{anio:04d}-{mes:02d}-01",
            fecha_hasta=f"{anio:04d}-{mes:02d}-{num_dias:02d}"
        )
        pagaron_map: Dict[str, List[Dict[str, Any]]] = {}
        deben_map: Dict[str, List[Dict[str, Any]]] = {}
        for m in movimientos_mes:
            f = m.fecha
            pol_info = {
                "policia_id": m.policia_id,
                "codigo": m.policia_codigo or "",
                "nombre": m.policia_nombre_completo,
                "tickets": m.cantidad_tickets,
                "monto": m.monto_total,
                "medio": m.medio_pago or "EFECTIVO",
                "obs": m.observacion or ""
            }
            if m.tipo_movimiento == "PAGO":
                pagaron_map.setdefault(f, []).append(pol_info)
            else:
                deben_map.setdefault(f, []).append(pol_info)

        dias = []
        for dia in range(1, num_dias + 1):
            fecha_str = f"{anio:04d}-{mes:02d}-{dia:02d}"
            dt = datetime(anio, mes, dia)
            dia_sem = DIAS_SEMANA_ES[dt.weekday()]

            v = ventas.get(fecha_str)
            td = tickets_diarios_map.get(fecha_str)

            efectivo = v.efectivo if v else 0.0
            yape = v.yape if v else 0.0
            
            # Cantidad y venta de tickets: usar ventas_diarias o complementar con tickets_diarios
            if v and (v.cantidad_tickets > 0 or v.venta_tickets > 0):
                cant_tickets = v.cantidad_tickets
                venta_tickets = v.venta_tickets
                precio_tk = v.precio_ticket_aplicado or precio_ticket_base
            elif td and td.total_policias > 0:
                cant_tickets = td.total_policias
                precio_tk = precio_ticket_base
                venta_tickets = round(cant_tickets * precio_tk, 2)
            else:
                cant_tickets = 0
                precio_tk = precio_ticket_base
                venta_tickets = 0.0

            # Venta del local (exclusivamente efectivo + yape sin incluir tickets policiales)
            venta_local = round(efectivo + yape, 2)

            # Venta total del día: si v tiene venta_total la usamos; si no, calculamos venta_local + venta_tickets
            if v and v.venta_total > 0:
                venta_total = v.venta_total
            else:
                venta_total = round(venta_local + venta_tickets, 2)

            compra_dia = compras_map.get(fecha_str, 0.0)
            gasto_dia = gastos_map.get(fecha_str, 0.0)
            personal_dia = pagos_pers_map.get(fecha_str, 0.0)
            total_egresos = round(compra_dia + gasto_dia + personal_dia, 2)
            saldo_dia = round(venta_total - total_egresos, 2)

            dias.append({
                "fecha": fecha_str,
                "dia": dia,
                "dia_semana": dia_sem,
                "efectivo": efectivo,
                "yape": yape,
                "venta_local": venta_local,
                "cantidad_tickets": cant_tickets,
                "precio_ticket": precio_tk,
                "venta_tickets": venta_tickets,
                "venta_total": venta_total,
                "compras": compra_dia,
                "gastos": gasto_dia,
                "personal": personal_dia,
                "total_egresos": total_egresos,
                "saldo": saldo_dia,
                "policias_pagaron": pagaron_map.get(fecha_str, []),
                "policias_deben": deben_map.get(fecha_str, [])
            })
        return dias

    def get_resumen_financiero_mes(self, anio: int, mes: int, local_id: str = "restaurante") -> Dict[str, Any]:
        """Summary metrics for the given month and branch/consolidated."""
        res_ventas = self.venta_repo.get_resumen_mes(anio, mes, local_id)
        tot_compras = self.compra_repo.get_total_mes(anio, mes, local_id)
        tot_gastos = self.gasto_repo.get_total_mes(anio, mes, local_id)
        tot_personal = self.pago_pers_repo.get_total_mes(anio, mes, local_id)

        # Si no hay ventas en ventas_diarias pero sí hay en tickets_diarios, complementar
        tot_tickets_repo = res_ventas.get("cantidad_tickets", 0)
        tot_venta_tk_repo = res_ventas.get("venta_tickets", 0.0)

        if tot_tickets_repo == 0:
            mes_obj = self.mes_repo.get_by_anio_mes(anio, mes)
            precio_tk = mes_obj.precio_ticket_policial if mes_obj else 12.0
            diarios_tk = self.ticket_repo.get_tickets_diarios_mes(anio, mes, local_id)
            tot_tickets_repo = sum(d.total_policias for d in diarios_tk)
            tot_venta_tk_repo = round(tot_tickets_repo * precio_tk, 2)

        efectivo = res_ventas.get("efectivo", 0.0)
        yape = res_ventas.get("yape", 0.0)
        venta_local = round(efectivo + yape, 2)

        total_ventas = res_ventas.get("venta_total", 0.0)
        if total_ventas == 0.0 and (venta_local > 0 or tot_venta_tk_repo > 0):
            total_ventas = round(venta_local + tot_venta_tk_repo, 2)

        total_egresos = round(tot_compras + tot_gastos + tot_personal, 2)
        saldo_neto = round(total_ventas - total_egresos, 2)
        rentabilidad_pct = round((saldo_neto / total_ventas * 100.0), 2) if total_ventas > 0 else 0.0

        return {
            "total_ventas": total_ventas,
            "venta_local": venta_local,
            "efectivo": efectivo,
            "yape": yape,
            "venta_sin_tickets": res_ventas.get("venta_sin_tickets", 0.0),
            "cantidad_tickets": tot_tickets_repo,
            "venta_tickets": tot_venta_tk_repo,
            "total_compras": tot_compras,
            "total_gastos": tot_gastos,
            "total_personal": tot_personal,
            "total_egresos": total_egresos,
            "saldo_neto": saldo_neto,
            "rentabilidad_pct": rentabilidad_pct
        }

    def get_resumen_anual(self, anio: int, local_id: str = "restaurante") -> List[Dict[str, Any]]:
        """12-month breakdown for annual financial report."""
        resumen_12_meses = []
        nombres = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
        for m in range(1, 13):
            r = self.get_resumen_financiero_mes(anio, m, local_id)
            r["mes_num"] = m
            r["mes_nombre"] = nombres[m - 1]
            resumen_12_meses.append(r)
        return resumen_12_meses
