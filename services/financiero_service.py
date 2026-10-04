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
        pago_repo: Optional[PagoRepository] = None
    ):
        self.venta_repo = venta_repo or VentaRepository()
        self.compra_repo = compra_repo or CompraRepository()
        self.gasto_repo = gasto_repo or GastoRepository()
        self.pago_pers_repo = pago_pers_repo or PagoPersonalRepository()
        self.ticket_repo = ticket_repo or TicketRepository()
        self.vale_repo = vale_repo or ValeRepository()
        self.pago_repo = pago_repo or PagoRepository()

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

        dias = []
        for dia in range(1, num_dias + 1):
            fecha_str = f"{anio:04d}-{mes:02d}-{dia:02d}"
            dt = datetime(anio, mes, dia)
            dia_sem = DIAS_SEMANA_ES[dt.weekday()]

            v = ventas.get(fecha_str)
            efectivo = v.efectivo if v else 0.0
            yape = v.yape if v else 0.0
            venta_tickets = v.venta_tickets if v else 0.0
            venta_total = v.venta_total if v else 0.0
            cant_tickets = v.cantidad_tickets if v else 0

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
                "cantidad_tickets": cant_tickets,
                "venta_tickets": venta_tickets,
                "venta_total": venta_total,
                "compras": compra_dia,
                "gastos": gasto_dia,
                "personal": personal_dia,
                "total_egresos": total_egresos,
                "saldo": saldo_dia
            })
        return dias

    def get_resumen_financiero_mes(self, anio: int, mes: int, local_id: str = "restaurante") -> Dict[str, Any]:
        """Summary metrics for the given month and branch/consolidated."""
        res_ventas = self.venta_repo.get_resumen_mes(anio, mes, local_id)
        tot_compras = self.compra_repo.get_total_mes(anio, mes, local_id)
        tot_gastos = self.gasto_repo.get_total_mes(anio, mes, local_id)
        tot_personal = self.pago_pers_repo.get_total_mes(anio, mes, local_id)

        total_ventas = res_ventas.get("venta_total", 0.0)
        total_egresos = round(tot_compras + tot_gastos + tot_personal, 2)
        saldo_neto = round(total_ventas - total_egresos, 2)
        rentabilidad_pct = round((saldo_neto / total_ventas * 100.0), 2) if total_ventas > 0 else 0.0

        return {
            "total_ventas": total_ventas,
            "efectivo": res_ventas.get("efectivo", 0.0),
            "yape": res_ventas.get("yape", 0.0),
            "venta_sin_tickets": res_ventas.get("venta_sin_tickets", 0.0),
            "cantidad_tickets": res_ventas.get("cantidad_tickets", 0),
            "venta_tickets": res_ventas.get("venta_tickets", 0.0),
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
