from typing import Dict, Any, List, Optional
from repositories.venta_repository import VentaRepository
from repositories.ticket_repository import TicketRepository
from repositories.vale_repository import ValeRepository
from repositories.pago_repository import PagoRepository
from repositories.mes_repository import MesRepository
from repositories.compra_repository import CompraRepository
from repositories.gasto_repository import GastoRepository
from repositories.pago_personal_repository import PagoPersonalRepository
from models.local import LOCAL_CONSOLIDADO, LOCAL_RESTAURANTE

class DashboardService:
    def __init__(
        self,
        venta_repo: Optional[VentaRepository] = None,
        ticket_repo: Optional[TicketRepository] = None,
        vale_repo: Optional[ValeRepository] = None,
        pago_repo: Optional[PagoRepository] = None,
        mes_repo: Optional[MesRepository] = None,
        compra_repo: Optional[CompraRepository] = None,
        gasto_repo: Optional[GastoRepository] = None,
        personal_repo: Optional[PagoPersonalRepository] = None
    ):
        self.venta_repo = venta_repo or VentaRepository()
        self.ticket_repo = ticket_repo or TicketRepository()
        self.vale_repo = vale_repo or ValeRepository()
        self.pago_repo = pago_repo or PagoRepository()
        self.mes_repo = mes_repo or MesRepository()
        self.compra_repo = compra_repo or CompraRepository()
        self.gasto_repo = gasto_repo or GastoRepository()
        self.personal_repo = personal_repo or PagoPersonalRepository()

    def get_dashboard_data(self, anio: int, mes: int, local_id: str = "restaurante") -> Dict[str, Any]:
        if local_id == LOCAL_CONSOLIDADO:
            self.ticket_repo.inicializar_dias_mes(anio, mes, "restaurante")
            self.ticket_repo.inicializar_dias_mes(anio, mes, "fast_food")
        else:
            self.ticket_repo.inicializar_dias_mes(anio, mes, local_id)

        res_ventas = self.venta_repo.get_resumen_mes(anio, mes, local_id)
        res_vales = self.vale_repo.get_resumen_mes(anio, mes, local_id)
        res_pagos = self.pago_repo.get_resumen_mes(anio, mes, local_id)
        res_tickets = self.ticket_repo.get_tickets_diarios_mes(anio, mes, local_id)

        tot_compras = self.compra_repo.get_total_mes(anio, mes, local_id)
        tot_gastos = self.gasto_repo.get_total_mes(anio, mes, local_id)
        tot_personal = self.personal_repo.get_total_mes(anio, mes, local_id)
        tot_egresos = round(tot_compras + tot_gastos + tot_personal, 2)

        total_ventas = res_ventas.get("venta_total", 0.0)
        tot_efectivo = res_ventas.get("efectivo", 0.0)
        tot_yape = res_ventas.get("yape", 0.0)
        tot_venta_sin_t = res_ventas.get("venta_sin_tickets", 0.0)
        tot_venta_tickets = res_ventas.get("venta_tickets", 0.0)

        saldo_neto = round(total_ventas - tot_egresos, 2)
        rentabilidad = round((saldo_neto / total_ventas * 100.0), 2) if total_ventas > 0 else 0.0

        tot_unidad = sum(t.para_unidad for t in res_tickets)
        tot_local = sum(t.local for t in res_tickets)
        tot_policias = sum(t.total_policias for t in res_tickets)

        # Monto pendiente por cobrar
        monto_pendiente = res_pagos.get("monto_pendiente", 0.0)
        m = self.mes_repo.get_by_anio_mes(anio, mes)
        precio_unitario = m.precio_ticket_policial if m else 12.0
        debidos = res_pagos.get("debidos", 0)
        if monto_pendiente == 0.0 and debidos > 0:
            monto_pendiente = debidos * precio_unitario

        # Egresos maps per day
        compras_list = self.compra_repo.get_by_mes(anio, mes, local_id)
        gastos_list = self.gasto_repo.get_by_mes(anio, mes, local_id)
        personal_list = self.personal_repo.get_by_mes(anio, mes, local_id)

        compras_map: Dict[str, float] = {}
        for c in compras_list:
            compras_map[c.fecha] = round(compras_map.get(c.fecha, 0.0) + (c.total or 0.0), 2)

        gastos_map: Dict[str, float] = {}
        for g in gastos_list:
            gastos_map[g.fecha] = round(gastos_map.get(g.fecha, 0.0) + (g.monto or 0.0), 2)

        personal_map: Dict[str, float] = {}
        for p in personal_list:
            personal_map[p.fecha] = round(personal_map.get(p.fecha, 0.0) + (p.monto or 0.0), 2)

        # Daily series for charts
        dias_labels = []
        serie_ventas_total = []
        serie_efectivo = []
        serie_yape = []
        serie_venta_sin_pol = []
        serie_venta_tickets = []
        serie_egresos_total = []
        serie_compras = []
        serie_gastos = []
        serie_personal = []
        serie_saldos_netos = []
        serie_unidad = []
        serie_local = []
        serie_policias = []
        serie_vales_ent = []
        serie_vales_canj = []
        serie_pagados = []
        serie_debidos = []

        ventas_diarias_map = {v.fecha: v for v in self.venta_repo.get_by_mes(anio, mes, local_id)}
        vales_map = {v.fecha: v for v in self.vale_repo.get_by_mes(anio, mes, local_id)}
        pagos_map = {p.fecha: p for p in self.pago_repo.get_by_mes(anio, mes, local_id)}

        for td in res_tickets:
            dia_str = str(td.dia)
            dias_labels.append(dia_str)
            serie_unidad.append(td.para_unidad)
            serie_local.append(td.local)
            serie_policias.append(td.total_policias)

            vd = ventas_diarias_map.get(td.fecha)
            vt = vd.venta_total if vd else 0.0
            ef = vd.efectivo if vd else 0.0
            yp = vd.yape if vd else 0.0
            st = vd.venta_sin_tickets if vd else 0.0
            vtick = vd.venta_tickets if vd else round(td.total_policias * precio_unitario, 2)

            serie_ventas_total.append(vt)
            serie_efectivo.append(ef)
            serie_yape.append(yp)
            serie_venta_sin_pol.append(st)
            serie_venta_tickets.append(vtick)

            c_dia = compras_map.get(td.fecha, 0.0)
            g_dia = gastos_map.get(td.fecha, 0.0)
            p_dia = personal_map.get(td.fecha, 0.0)
            egr_dia = round(c_dia + g_dia + p_dia, 2)
            saldo_dia = round(vt - egr_dia, 2)

            serie_compras.append(c_dia)
            serie_gastos.append(g_dia)
            serie_personal.append(p_dia)
            serie_egresos_total.append(egr_dia)
            serie_saldos_netos.append(saldo_dia)

            vl = vales_map.get(td.fecha)
            serie_vales_ent.append(vl.vales_entregados if vl else 0)
            serie_vales_canj.append(vl.vales_consumidos if vl else 0)

            pg = pagos_map.get(td.fecha)
            serie_pagados.append(pg.tickets_pagados if pg else 0)
            serie_debidos.append(pg.tickets_debidos if pg else 0)

        return {
            "kpis": {
                "venta_total": total_ventas,
                "efectivo": tot_efectivo,
                "yape": tot_yape,
                "venta_sin_tickets": tot_venta_sin_t,
                "total_tickets_policiales": tot_policias,
                "tickets_para_unidad": tot_unidad,
                "tickets_local": tot_local,
                "total_compras": tot_compras,
                "total_gastos": tot_gastos,
                "total_personal": tot_personal,
                "total_egresos": tot_egresos,
                "saldo_neto": saldo_neto,
                "rentabilidad_pct": rentabilidad,
                "vales_entregados": res_vales.get("entregados", 0),
                "vales_canjeados": res_vales.get("canjeados", 0),
                "saldo_vales": res_vales.get("saldo", 0),
                "tickets_pagados": res_pagos.get("pagados", 0),
                "tickets_debidos": res_pagos.get("debidos", 0),
                "venta_policial_calculada": tot_venta_tickets or round(tot_policias * precio_unitario, 2),
                "venta_sin_policias": tot_venta_sin_t,
                "monto_pendiente": monto_pendiente,
                "precio_menu": precio_unitario,
                "menus_vendidos": tot_policias
            },
            "series": {
                "dias": dias_labels,
                "ventas_total": serie_ventas_total,
                "efectivo": serie_efectivo,
                "yape": serie_yape,
                "venta_sin_policias": serie_venta_sin_pol,
                "venta_tickets": serie_venta_tickets,
                "egresos_total": serie_egresos_total,
                "compras": serie_compras,
                "gastos": serie_gastos,
                "personal": serie_personal,
                "saldos_netos": serie_saldos_netos,
                "para_unidad": serie_unidad,
                "local": serie_local,
                "policias": serie_policias,
                "vales_entregados": serie_vales_ent,
                "vales_canjeados": serie_vales_canj,
                "tickets_pagados": serie_pagados,
                "tickets_debidos": serie_debidos
            }
        }
