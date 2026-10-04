from typing import List, Optional
from database.connection import DatabaseManager
from models.observacion import Observacion

class ObservacionRepository:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager.get_instance()

    def get_by_fecha(self, fecha: str) -> List[Observacion]:
        rows = self.db.execute_query(
            "SELECT id, fecha, texto, tipo, fecha_creacion FROM observaciones WHERE fecha = ? ORDER BY fecha_creacion ASC",
            (fecha,)
        )
        return [self._row_to_entity(r) for r in rows]

    def get_by_mes(self, anio: int, mes: int) -> List[Observacion]:
        prefix = f"{anio:04d}-{mes:02d}-%"
        rows = self.db.execute_query(
            "SELECT id, fecha, texto, tipo, fecha_creacion FROM observaciones WHERE fecha LIKE ? ORDER BY fecha ASC, fecha_creacion ASC",
            (prefix,)
        )
        return [self._row_to_entity(r) for r in rows]

    def create(self, obs: Observacion) -> int:
        query = "INSERT INTO observaciones (fecha, texto, tipo, fecha_creacion) VALUES (?, ?, ?, CURRENT_TIMESTAMP)"
        return self.db.execute_non_query(query, (obs.fecha, obs.texto, obs.tipo))

    def delete(self, obs_id: int) -> bool:
        self.db.execute_non_query("DELETE FROM observaciones WHERE id = ?", (obs_id,))
        return True

    @staticmethod
    def _row_to_entity(r) -> Observacion:
        return Observacion(
            id=r["id"],
            fecha=r["fecha"],
            texto=r["texto"],
            tipo=r["tipo"],
            fecha_creacion=r["fecha_creacion"]
        )
