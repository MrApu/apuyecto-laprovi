from typing import List, Optional
from database.connection import DatabaseManager
from models.auditoria import Auditoria

class AuditoriaRepository:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager.get_instance()

    def registrar(self, accion: str, entidad: str, entidad_id: Optional[str] = None, detalles: Optional[str] = None, usuario: str = "USUARIO", local_id: Optional[str] = None) -> int:
        query = """
            INSERT INTO auditoria (fecha, usuario, accion, entidad, entidad_id, local_id, detalles)
            VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?)
        """
        return self.db.execute_non_query(query, (usuario, accion, entidad, str(entidad_id) if entidad_id is not None else None, local_id, detalles))

    def get_recientes(self, limit: int = 100) -> List[Auditoria]:
        rows = self.db.execute_query(
            "SELECT id, fecha, usuario, accion, entidad, entidad_id, detalles FROM auditoria ORDER BY fecha DESC LIMIT ?",
            (limit,)
        )
        return [
            Auditoria(
                id=r["id"],
                fecha=r["fecha"],
                usuario=r["usuario"],
                accion=r["accion"],
                entidad=r["entidad"],
                entidad_id=r["entidad_id"],
                detalles=r["detalles"]
            )
            for r in rows
        ]
