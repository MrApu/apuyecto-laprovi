from typing import List, Optional, Tuple, Dict, Any
import calendar
from datetime import datetime
from repositories.ticket_repository import TicketRepository
from repositories.mes_repository import MesRepository
from repositories.auditoria_repository import AuditoriaRepository
from models.ticket import TicketPolicia, TicketDiario, DIAS_SEMANA_ES

class TicketService:
    def __init__(
        self,
        ticket_repo: Optional[TicketRepository] = None,
        mes_repo: Optional[MesRepository] = None,
        audit_repo: Optional[AuditoriaRepository] = None
    ):
        self.repo = ticket_repo or TicketRepository()
        self.mes_repo = mes_repo or MesRepository()
        self.audit_repo = audit_repo or AuditoriaRepository()

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

    def toggle_ticket(self, mes_id: int, policia_id: int, dia: int, valor: int, usuario: str = "USUARIO") -> bool:
        res = self.repo.set_ticket_policia(mes_id, policia_id, dia, valor)
        return res

    def get_historial_policia(self, policia_id: int) -> List[dict]:
        return self.repo.get_historial_policia(policia_id)

    # --- Calendario Policial ---
    def get_calendario_mes(self, anio: int, mes: int) -> List[TicketDiario]:
        self.repo.inicializar_dias_mes(anio, mes)
        return self.repo.get_tickets_diarios_mes(anio, mes)

    def guardar_ticket_diario(
        self,
        fecha: str,
        para_unidad: int,
        local: int,
        vales_policiales: int = 0,
        observacion: Optional[str] = None,
        usuario: str = "USUARIO",
        motivo_ajuste: Optional[str] = None
    ) -> Tuple[bool, str, TicketDiario]:
        if para_unidad < 0 or local < 0 or vales_policiales < 0:
            return False, "Las cantidades no pueden ser negativas.", None

        dt = datetime.strptime(fecha, "%Y-%m-%d")
        dia_semana = DIAS_SEMANA_ES[dt.weekday()]
        total = para_unidad + local

        actual = self.repo.get_ticket_diario_by_fecha(fecha)

        td = TicketDiario(
            fecha=fecha,
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
