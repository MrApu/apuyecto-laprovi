from typing import List, Optional, Dict, Tuple
from database.connection import DatabaseManager
from models.ticket import TicketPolicia, TicketDiario, DIAS_SEMANA_ES
from models.local import LOCAL_CONSOLIDADO, LOCAL_RESTAURANTE, LOCAL_FAST_FOOD
import calendar
from datetime import datetime

class TicketRepository:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager.get_instance()

    # --- Individual Officer Daily Tickets ---
    def set_ticket_policia(self, mes_id: int, policia_id: int, dia: int, valor: int, local_id: str = "restaurante") -> bool:
        if valor not in (0, 1):
            valor = 1 if valor else 0
        query = """
            INSERT INTO tickets_por_policia (mes_id, policia_id, local_id, dia, valor, fecha_registro)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(mes_id, policia_id, local_id, dia) DO UPDATE SET
                valor = excluded.valor,
                fecha_registro = CURRENT_TIMESTAMP
        """
        self.db.execute_non_query(query, (mes_id, policia_id, local_id, dia, valor))
        return True

    def set_tickets_policia_batch(self, tickets: List[Tuple]) -> bool:
        """Batch insert/update for (mes_id, policia_id, local_id, dia, valor) or (mes_id, policia_id, dia, valor)."""
        normalized = []
        for t in tickets:
            if len(t) == 4:
                # (mes_id, policia_id, dia, valor) -> local_id = 'restaurante'
                normalized.append((t[0], t[1], 'restaurante', t[2], t[3]))
            elif len(t) >= 5:
                normalized.append((t[0], t[1], t[2], t[3], t[4]))
        if not normalized:
            return True

        query = """
            INSERT INTO tickets_por_policia (mes_id, policia_id, local_id, dia, valor, fecha_registro)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(mes_id, policia_id, local_id, dia) DO UPDATE SET
                valor = excluded.valor,
                fecha_registro = CURRENT_TIMESTAMP
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, normalized)
            conn.commit()
        return True

    def get_tickets_matriz_mes(self, mes_id: int, local_id: Optional[str] = None) -> Dict[int, Dict[int, int]]:
        if local_id and local_id != LOCAL_CONSOLIDADO:
            query = "SELECT policia_id, dia, valor FROM tickets_por_policia WHERE mes_id = ? AND local_id = ?"
            rows = self.db.execute_query(query, (mes_id, local_id))
        else:
            query = "SELECT policia_id, dia, MAX(valor) as valor FROM tickets_por_policia WHERE mes_id = ? GROUP BY policia_id, dia"
            rows = self.db.execute_query(query, (mes_id,))

        matriz: Dict[int, Dict[int, int]] = {}
        for r in rows:
            p_id = r["policia_id"]
            if p_id not in matriz:
                matriz[p_id] = {}
            matriz[p_id][r["dia"]] = r["valor"]
        return matriz

    def get_historial_policia(self, policia_id: int) -> List[dict]:
        query = """
            SELECT m.anio, m.mes, m.nombre_mes, COUNT(t.id) as total_tickets,
                   GROUP_CONCAT(DISTINCT printf('%04d-%02d-%02d', m.anio, m.mes, t.dia)) as fechas_marcadas
            FROM meses m
            LEFT JOIN tickets_por_policia t ON m.id = t.mes_id AND t.policia_id = ? AND t.valor = 1
            GROUP BY m.id
            ORDER BY m.anio DESC, m.mes DESC
        """
        rows = self.db.execute_query(query, (policia_id,))
        return [dict(r) for r in rows]

    # --- Calendario Policial (Daily Summaries) ---
    def get_ticket_diario_by_fecha(self, fecha: str, local_id: str = "restaurante") -> Optional[TicketDiario]:
        if local_id == LOCAL_CONSOLIDADO:
            rows = self.db.execute_query("""
                SELECT NULL as id, fecha, 'consolidado' as local_id, anio, mes, dia, dia_semana,
                       SUM(para_unidad) as para_unidad, SUM(local) as local,
                       SUM(total_policias) as total_policias, SUM(vales_policiales) as vales_policiales,
                       GROUP_CONCAT(observacion, ' | ') as observacion, MAX(fecha_actualizacion) as fecha_actualizacion
                FROM tickets_diarios
                WHERE fecha = ?
                GROUP BY fecha
            """, (fecha,))
        else:
            rows = self.db.execute_query(
                "SELECT * FROM tickets_diarios WHERE fecha = ? AND local_id = ?",
                (fecha, local_id)
            )
        return self._row_to_diario(rows[0]) if rows else None

    def get_tickets_diarios_mes(self, anio: int, mes: int, local_id: str = "restaurante") -> List[TicketDiario]:
        if local_id == LOCAL_CONSOLIDADO:
            rows = self.db.execute_query("""
                SELECT NULL as id, fecha, 'consolidado' as local_id, anio, mes, dia, dia_semana,
                       SUM(para_unidad) as para_unidad, SUM(local) as local,
                       SUM(total_policias) as total_policias, SUM(vales_policiales) as vales_policiales,
                       GROUP_CONCAT(observacion, ' | ') as observacion, MAX(fecha_actualizacion) as fecha_actualizacion
                FROM tickets_diarios
                WHERE anio = ? AND mes = ?
                GROUP BY fecha
                ORDER BY dia ASC
            """, (anio, mes))
        else:
            rows = self.db.execute_query(
                "SELECT * FROM tickets_diarios WHERE anio = ? AND mes = ? AND local_id = ? ORDER BY dia ASC",
                (anio, mes, local_id)
            )
        return [self._row_to_diario(r) for r in rows]

    def save_ticket_diario(self, td: TicketDiario) -> int:
        total = (td.para_unidad or 0) + (td.local or 0)
        query = """
            INSERT INTO tickets_diarios (fecha, local_id, anio, mes, dia, dia_semana, para_unidad, local, total_policias, vales_policiales, observacion, fecha_actualizacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(fecha, local_id) DO UPDATE SET
                para_unidad = excluded.para_unidad,
                local = excluded.local,
                total_policias = excluded.total_policias,
                vales_policiales = excluded.vales_policiales,
                observacion = excluded.observacion,
                fecha_actualizacion = CURRENT_TIMESTAMP
        """
        params = (
            td.fecha,
            td.local_id or "restaurante",
            td.anio,
            td.mes,
            td.dia,
            td.dia_semana,
            td.para_unidad or 0,
            td.local or 0,
            total,
            td.vales_policiales or 0,
            td.observacion
        )
        return self.db.execute_non_query(query, params)

    def inicializar_dias_mes(self, anio: int, mes: int, local_id: str = "restaurante") -> int:
        num_dias = calendar.monthrange(anio, mes)[1]
        count = 0
        locales_to_init = [LOCAL_RESTAURANTE, LOCAL_FAST_FOOD] if local_id == LOCAL_CONSOLIDADO else [local_id]

        for loc in locales_to_init:
            for dia in range(1, num_dias + 1):
                fecha = f"{anio:04d}-{mes:02d}-{dia:02d}"
                dt = datetime(anio, mes, dia)
                dia_semana = DIAS_SEMANA_ES[dt.weekday()]
                query = """
                    INSERT OR IGNORE INTO tickets_diarios (fecha, local_id, anio, mes, dia, dia_semana, para_unidad, local, total_policias, vales_policiales, fecha_actualizacion)
                    VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, 0, CURRENT_TIMESTAMP)
                """
                self.db.execute_non_query(query, (fecha, loc, anio, mes, dia, dia_semana))
                count += 1
        return count

    @staticmethod
    def _row_to_diario(r) -> TicketDiario:
        return TicketDiario(
            id=r["id"],
            fecha=r["fecha"],
            local_id=r["local_id"],
            anio=r["anio"],
            mes=r["mes"],
            dia=r["dia"],
            dia_semana=r["dia_semana"],
            para_unidad=int(r["para_unidad"] or 0),
            local=int(r["local"] or 0),
            total_policias=int(r["total_policias"] or 0),
            vales_policiales=int(r["vales_policiales"] or 0),
            observacion=r["observacion"],
            fecha_actualizacion=r["fecha_actualizacion"]
        )
