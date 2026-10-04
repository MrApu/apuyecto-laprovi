from typing import List, Optional, Dict, Any
from database.connection import DatabaseManager
from models.policia import Policia

class PoliciaRepository:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager.get_instance()

    def get_all(self, solo_activos: bool = False, busqueda: Optional[str] = None, area: Optional[str] = None) -> List[Policia]:
        query = "SELECT id, codigo, apellidos, nombres, sa_pnp, area, estado, observaciones, fecha_creacion, fecha_actualizacion FROM policias WHERE 1=1"
        params = []
        if solo_activos:
            query += " AND estado = 'ACTIVO'"
        if area and area.upper() != "TODAS":
            query += " AND UPPER(area) = UPPER(?)"
            params.append(area)
        if busqueda:
            term = f"%{busqueda.strip()}%"
            query += " AND (codigo LIKE ? OR apellidos LIKE ? OR nombres LIKE ? OR sa_pnp LIKE ? OR area LIKE ?)"
            params.extend([term, term, term, term, term])

        query += " ORDER BY area ASC, codigo ASC"
        rows = self.db.execute_query(query, tuple(params))
        return [self._row_to_entity(r) for r in rows]

    def get_by_id(self, policia_id: int) -> Optional[Policia]:
        rows = self.db.execute_query(
            "SELECT id, codigo, apellidos, nombres, sa_pnp, area, estado, observaciones, fecha_creacion, fecha_actualizacion FROM policias WHERE id = ?",
            (policia_id,)
        )
        return self._row_to_entity(rows[0]) if rows else None

    def get_by_codigo(self, codigo: str) -> Optional[Policia]:
        rows = self.db.execute_query(
            "SELECT id, codigo, apellidos, nombres, sa_pnp, area, estado, observaciones, fecha_creacion, fecha_actualizacion FROM policias WHERE UPPER(TRIM(codigo)) = UPPER(TRIM(?))",
            (codigo,)
        )
        return self._row_to_entity(rows[0]) if rows else None

    def create(self, policia: Policia) -> int:
        query = """
            INSERT INTO policias (codigo, apellidos, nombres, sa_pnp, area, estado, observaciones, fecha_creacion, fecha_actualizacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        params = (
            policia.codigo.strip().upper(),
            policia.apellidos.strip().upper(),
            policia.nombres.strip().upper(),
            policia.sa_pnp.strip() if policia.sa_pnp else None,
            policia.area.strip().upper(),
            policia.estado.strip().upper(),
            policia.observaciones
        )
        return self.db.execute_non_query(query, params)

    def update(self, policia: Policia) -> bool:
        query = """
            UPDATE policias
            SET codigo = ?, apellidos = ?, nombres = ?, sa_pnp = ?, area = ?, estado = ?, observaciones = ?, fecha_actualizacion = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        params = (
            policia.codigo.strip().upper(),
            policia.apellidos.strip().upper(),
            policia.nombres.strip().upper(),
            policia.sa_pnp.strip() if policia.sa_pnp else None,
            policia.area.strip().upper(),
            policia.estado.strip().upper(),
            policia.observaciones,
            policia.id
        )
        self.db.execute_non_query(query, params)
        return True

    def set_estado(self, policia_id: int, estado: str) -> bool:
        query = "UPDATE policias SET estado = ?, fecha_actualizacion = CURRENT_TIMESTAMP WHERE id = ?"
        self.db.execute_non_query(query, (estado.strip().upper(), policia_id))
        return True

    def get_areas(self) -> List[str]:
        rows = self.db.execute_query("SELECT DISTINCT area FROM policias WHERE area IS NOT NULL AND area != '' ORDER BY area ASC")
        return [r["area"] for r in rows]

    def count(self, solo_activos: bool = False) -> int:
        query = "SELECT COUNT(*) as c FROM policias" + (" WHERE estado = 'ACTIVO'" if solo_activos else "")
        rows = self.db.execute_query(query)
        return rows[0]["c"] if rows else 0

    @staticmethod
    def _row_to_entity(r) -> Policia:
        return Policia(
            id=r["id"],
            codigo=r["codigo"],
            apellidos=r["apellidos"],
            nombres=r["nombres"],
            sa_pnp=r["sa_pnp"],
            area=r["area"],
            estado=r["estado"],
            observaciones=r["observaciones"],
            fecha_creacion=r["fecha_creacion"],
            fecha_actualizacion=r["fecha_actualizacion"]
        )
