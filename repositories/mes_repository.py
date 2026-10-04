from typing import List, Optional
from database.connection import DatabaseManager
from models.mes import Mes, PoliciaMes, NOMBRES_MESES

class MesRepository:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager.get_instance()

    def get_all(self) -> List[Mes]:
        rows = self.db.execute_query(
            "SELECT id, anio, mes, nombre_mes, estado, precio_ticket_policial, fecha_creacion FROM meses ORDER BY anio DESC, mes DESC"
        )
        return [self._row_to_entity(r) for r in rows]

    def get_by_id(self, mes_id: int) -> Optional[Mes]:
        rows = self.db.execute_query(
            "SELECT id, anio, mes, nombre_mes, estado, precio_ticket_policial, fecha_creacion FROM meses WHERE id = ?",
            (mes_id,)
        )
        return self._row_to_entity(rows[0]) if rows else None

    def get_by_anio_mes(self, anio: int, mes: int) -> Optional[Mes]:
        rows = self.db.execute_query(
            "SELECT id, anio, mes, nombre_mes, estado, precio_ticket_policial, fecha_creacion FROM meses WHERE anio = ? AND mes = ?",
            (anio, mes)
        )
        return self._row_to_entity(rows[0]) if rows else None

    def create(self, mes: Mes) -> int:
        query = """
            INSERT INTO meses (anio, mes, nombre_mes, estado, precio_ticket_policial, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        nombre = mes.nombre_mes or f"{NOMBRES_MESES[mes.mes]} {mes.anio}"
        return self.db.execute_non_query(query, (mes.anio, mes.mes, nombre, mes.estado, mes.precio_ticket_policial))

    def update_estado(self, mes_id: int, estado: str) -> bool:
        self.db.execute_non_query("UPDATE meses SET estado = ? WHERE id = ?", (estado.upper(), mes_id))
        return True

    def update_precio(self, mes_id: int, precio: float) -> bool:
        self.db.execute_non_query("UPDATE meses SET precio_ticket_policial = ? WHERE id = ?", (precio, mes_id))
        return True

    def sincronizar_policias_mes(self, mes_id: int) -> int:
        """Loads all ACTIVO policias from master DB into policias_mes if not already present."""
        query = """
            INSERT OR IGNORE INTO policias_mes (mes_id, policia_id, area_historica, estado_en_mes)
            SELECT ?, id, area, 'ACTIVO'
            FROM policias
            WHERE estado = 'ACTIVO'
        """
        return self.db.execute_non_query(query, (mes_id,))

    def get_policias_en_mes(self, mes_id: int, solo_activos: bool = False) -> List[dict]:
        query = """
            SELECT pm.id as pm_id, pm.mes_id, pm.policia_id, pm.area_historica, pm.estado_en_mes,
                   p.codigo, p.apellidos, p.nombres, p.sa_pnp, p.area as area_actual, p.estado as estado_general
            FROM policias_mes pm
            JOIN policias p ON pm.policia_id = p.id
            WHERE pm.mes_id = ?
        """
        if solo_activos:
            query += " AND pm.estado_en_mes = 'ACTIVO'"
        query += " ORDER BY pm.area_historica ASC, p.codigo ASC"
        rows = self.db.execute_query(query, (mes_id,))
        return [dict(r) for r in rows]

    @staticmethod
    def _row_to_entity(r) -> Mes:
        return Mes(
            id=r["id"],
            anio=r["anio"],
            mes=r["mes"],
            nombre_mes=r["nombre_mes"],
            estado=r["estado"],
            precio_ticket_policial=float(r["precio_ticket_policial"] or 12.0),
            fecha_creacion=r["fecha_creacion"]
        )
