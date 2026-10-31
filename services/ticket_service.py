from typing import List, Optional, Tuple, Dict, Any
import calendar
from datetime import datetime
from repositories.ticket_repository import TicketRepository
from repositories.mes_repository import MesRepository
from repositories.auditoria_repository import AuditoriaRepository
from repositories.vale_repository import ValeRepository
from models.ticket import TicketPolicia, TicketDiario, DIAS_SEMANA_ES
from models.vale import Vale

class TicketService:
    def __init__(
        self,
        ticket_repo: Optional[TicketRepository] = None,
        mes_repo: Optional[MesRepository] = None,
        audit_repo: Optional[AuditoriaRepository] = None,
        vale_repo: Optional[ValeRepository] = None
    ):
        self.repo = ticket_repo or TicketRepository()
        self.mes_repo = mes_repo or MesRepository()
        self.audit_repo = audit_repo or AuditoriaRepository()
        self.vale_repo = vale_repo or ValeRepository()

    # --- Individual Ticket Matrix ---
    def get_matriz_tickets_mes(self, mes_id: int) -> Tuple[List[dict], int, Dict[int, Dict[int, int]]]:
        """
        Returns:
            - policias_list: list of dicts with officer details
            - num_dias: number of days in this month
            - matriz: dict[policia_id][dia] -> 1/0
        """
        mes = self.mes_repo.get_by_id(mes_id)
        if not mes:
            return [], 31, {}

        # Auto-sync active policias if any new was created
        self.mes_repo.sincronizar_policias_mes(mes_id)

        policias = self.mes_repo.get_policias_en_mes(mes_id)
        num_dias = calendar.monthrange(mes.anio, mes.mes)[1]
        matriz = self.repo.get_tickets_matriz_mes(mes_id)

        # Calculate totals per officer
        for p in policias:
            p_id = p["policia_id"]
            dias_map = matriz.get(p_id, {})
            p["total_tickets"] = sum(1 for d in range(1, num_dias + 1) if dias_map.get(d) == 1)

        return policias, num_dias, matriz

    def toggle_ticket(self, mes_id: int, policia_id: int, dia: int, valor: int, usuario: str = "USUARIO", local_id: str = "restaurante") -> bool:
        res = self.repo.set_ticket_policia(mes_id, policia_id, dia, valor, local_id=local_id)
        return res

    def get_historial_policia(self, policia_id: int) -> List[dict]:
        return self.repo.get_historial_policia(policia_id)

    # --- Calendario Policial ---
    def get_calendario_mes(self, anio: int, mes: int, local_id: str = "restaurante") -> List[TicketDiario]:
        self.repo.inicializar_dias_mes(anio, mes, local_id=local_id)
        return self.repo.get_tickets_diarios_mes(anio, mes, local_id=local_id)

    def guardar_ticket_diario(
        self,
        fecha: str,
        para_unidad: int,
        local: int,
        vales_policiales: int = 0,
        local_id: str = "restaurante",
        observacion: Optional[str] = None,
        usuario: str = "USUARIO",
        motivo_ajuste: Optional[str] = None
    ) -> Tuple[bool, str, TicketDiario]:
        if para_unidad < 0 or local < 0 or vales_policiales < 0:
            return False, "Las cantidades no pueden ser negativas.", None

        dt = datetime.strptime(fecha, "%Y-%m-%d")
        dia_semana = DIAS_SEMANA_ES[dt.weekday()]
        total = para_unidad + local

        actual = self.repo.get_ticket_diario_by_fecha(fecha, local_id=local_id)

        td = TicketDiario(
            fecha=fecha,
            local_id=local_id,
            anio=dt.year,
            mes=dt.month,
            dia=dt.day,
            dia_semana=dia_semana,
            para_unidad=para_unidad,
            local=local,
            total_policias=total,
            vales_policiales=vales_policiales,
            observacion=observacion
        )

        self.repo.save_ticket_diario(td)

        # Audit if modified
        if actual and (actual.para_unidad != para_unidad or actual.local != local or actual.vales_policiales != vales_policiales):
            det = f"Ajuste en {fecha}: Anterior (Unidad: {actual.para_unidad}, Local: {actual.local}, Total: {actual.total_policias}, Vales: {actual.vales_policiales}) -> Nuevo (Unidad: {para_unidad}, Local: {local}, Total: {total}, Vales: {vales_policiales})."
            if motivo_ajuste:
                det += f" Motivo: {motivo_ajuste}"
            self.audit_repo.registrar(
                accion="MODIFICAR_TICKET_DIARIO",
                entidad="tickets_diarios",
                entidad_id=fecha,
                detalles=det,
                usuario=usuario
            )

        return True, "Registro de tickets diario guardado correctamente.", td

    def get_resumen_totales_calendario(self, anio: int, mes: int) -> dict:
        diarios = self.get_calendario_mes(anio, mes)
        tot_unidad = sum(d.para_unidad for d in diarios)
        tot_local = sum(d.local for d in diarios)
        tot_policias = sum(d.total_policias for d in diarios)
        tot_vales = sum(d.vales_policiales for d in diarios)

        return {
            "para_unidad": tot_unidad,
            "local": tot_local,
            "total_policias": tot_policias,
            "vales_policiales": tot_vales
        }

    def asignar_cantidad_tickets_policia(
        self,
        mes_id: int,
        policia_id: int,
        cantidad: int,
        local_id: str = "restaurante",
        usuario: str = "USUARIO"
    ) -> Tuple[bool, str]:
        mes = self.mes_repo.get_by_id(mes_id)
        if not mes:
            return False, "Mes no encontrado."
        num_dias = calendar.monthrange(mes.anio, mes.mes)[1]
        if cantidad < 0 or cantidad > num_dias:
            return False, f"La cantidad de tickets debe estar entre 0 y {num_dias}."

        batch = []
        for d in range(1, num_dias + 1):
            val = 1 if d <= cantidad else 0
            batch.append((mes_id, policia_id, local_id, d, val))

        self.repo.set_tickets_policia_batch(batch)
        self.audit_repo.registrar(
            accion="ASIGNAR_CANTIDAD_TICKETS",
            entidad="tickets_por_policia",
            entidad_id=f"mes_{mes_id}_pol_{policia_id}",
            detalles=f"Asignación rápida directa de {cantidad} tickets para policía ID {policia_id}.",
            usuario=usuario
        )
        return True, f"Se asignaron {cantidad} tickets correctamente al policía."

    # --- Control Integral de Tickets y Vales Diarios ---
    def get_calendario_con_vales(self, anio: int, mes: int, local_id: str = "restaurante") -> List[Dict[str, Any]]:
        """
        Retorna la matriz diaria integrando tickets para unidad, en local,
        vales entregados, vales canjeados y saldo de vales en circulación.
        """
        diarios = self.get_calendario_mes(anio, mes, local_id=local_id)
        vales_list = self.vale_repo.get_by_mes(anio, mes, local_id=local_id)
        vales_map = {v.fecha: v for v in vales_list}

        res = []
        saldo_acumulado = 0
        for td in diarios:
            vl = vales_map.get(td.fecha)
            v_ent = vl.vales_entregados if vl else 0
            v_canj = vl.vales_consumidos if vl else (td.vales_policiales or 0)
            saldo_dia = v_ent - v_canj
            saldo_acumulado += saldo_dia

            res.append({
                "fecha": td.fecha,
                "anio": td.anio,
                "mes": td.mes,
                "dia": td.dia,
                "dia_semana": td.dia_semana,
                "para_unidad": td.para_unidad,
                "local": td.local,
                "total_policias": td.total_policias,
                "vales_entregados": v_ent,
                "vales_canjeados": v_canj,
                "saldo_dia": saldo_dia,
                "saldo_acumulado": saldo_acumulado,
                "observacion": td.observacion or (vl.observacion if vl else "") or "",
                "ticket_diario": td,
                "vale": vl
            })
        return res

    def guardar_ticket_y_vales(
        self,
        fecha: str,
        para_unidad: int,
        local: int,
        vales_entregados: int,
        vales_canjeados: int,
        local_id: str = "restaurante",
        observacion: Optional[str] = None,
        usuario: str = "USUARIO",
        motivo_ajuste: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Guarda atómicamente los tickets para unidad, en local, y los vales entregados y canjeados,
        recalculando el saldo restante descontado en tiempo real.
        """
        if para_unidad < 0 or local < 0 or vales_entregados < 0 or vales_canjeados < 0:
            return False, "Las cantidades no pueden ser negativas."

        # 1. Guardar ticket diario (vales_policiales = vales_canjeados para compatibilidad histórica)
        ok, msg, td = self.guardar_ticket_diario(
            fecha=fecha,
            para_unidad=para_unidad,
            local=local,
            vales_policiales=vales_canjeados,
            local_id=local_id,
            observacion=observacion,
            usuario=usuario,
            motivo_ajuste=motivo_ajuste
        )
        if not ok:
            return False, msg

        # 2. Guardar vale (descuento exacto de canjeados sobre entregados)
        saldo = vales_entregados - vales_canjeados
        v = Vale(
            fecha=fecha,
            local_id=local_id,
            vales_entregados=vales_entregados,
            vales_consumidos=vales_canjeados,
            saldo=saldo,
            observacion=observacion
        )
        self.vale_repo.save(v)

        return True, "Ticket y vales guardados exitosamente."

