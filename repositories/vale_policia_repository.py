from typing import List, Optional, Any
from database.connection import DatabaseManager
from models.vale_policia import ValePolicia

class ValePoliciaRepository:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager.get_instance()

    def registrar(self, vale: ValePolicia) -> int:
        query = """
            INSERT INTO vales_policias (
                policia_id, fecha, local_id, tipo_operacion, cantidad_vales, tickets_equivalentes, observacion, fecha_registro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        params = (
            vale.policia_id,
            vale.fecha,
            vale.local_id or "restaurante",
            vale.tipo_operacion or "ENTREGA",
            vale.cantidad_vales or 1,
            vale.tickets_equivalentes or 1,
            vale.observacion
        )
        return self.db.execute_non_query(query, params)

    def actualizar(self, vale: ValePolicia) -> bool:
        if not vale.id:
            return False
        query = """
            UPDATE vales_policias
            SET policia_id = ?, fecha = ?, local_id = ?, tipo_operacion = ?,
                cantidad_vales = ?, tickets_equivalentes = ?, observacion = ?
            WHERE id = ?
        """
        params = (
            vale.policia_id,
            vale.fecha,
            vale.local_id or "restaurante",
            vale.tipo_operacion or "ENTREGA",
            vale.cantidad_vales or 1,
            vale.tickets_equivalentes or 1,
            vale.observacion,
            vale.id
        )
        self.db.execute_non_query(query, params)
        return True

    def eliminar(self, vale_id: int) -> bool:
        self.db.execute_non_query("DELETE FROM vales_policias WHERE id = ?", (vale_id,))
        return True

    def get_by_id(self, vale_id: int) -> Optional[ValePolicia]:
        query = """
            SELECT vp.*, p.codigo as policia_codigo, p.apellidos as policia_apellidos,
                   p.nombres as policia_nombres, p.area as policia_area
            FROM vales_policias vp
            JOIN policias p ON vp.policia_id = p.id
            WHERE vp.id = ?
        """
        rows = self.db.execute_query(query, (vale_id,))
        return self._row_to_entity(rows[0]) if rows else None

    def get_all(self, busqueda: Optional[str] = None, mes_prefijo: Optional[str] = None) -> List[ValePolicia]:
        query = """
            SELECT vp.*, p.codigo as policia_codigo, p.apellidos as policia_apellidos,
                   p.nombres as policia_nombres, p.area as policia_area
            FROM vales_policias vp
            JOIN policias p ON vp.policia_id = p.id
            WHERE 1=1
        """
        params: List[Any] = []

        if mes_prefijo:
            query += " AND vp.fecha LIKE ?"
            params.append(f"{mes_prefijo}%")

        if busqueda:
            term = f"%{busqueda.strip()}%"
            query += " AND (p.codigo LIKE ? OR p.apellidos LIKE ? OR p.nombres LIKE ? OR p.area LIKE ? OR vp.observacion LIKE ?)"
            params.extend([term, term, term, term, term])

        query += " ORDER BY vp.fecha DESC, vp.id DESC"
        rows = self.db.execute_query(query, tuple(params))
        return [self._row_to_entity(r) for r in rows]

    def get_by_policia(self, policia_id: int) -> List[ValePolicia]:
        query = """
            SELECT vp.*, p.codigo as policia_codigo, p.apellidos as policia_apellidos,
                   p.nombres as policia_nombres, p.area as policia_area
            FROM vales_policias vp
            JOIN policias p ON vp.policia_id = p.id
            WHERE vp.policia_id = ?
            ORDER BY vp.fecha DESC, vp.id DESC
        """
        rows = self.db.execute_query(query, (policia_id,))
        return [self._row_to_entity(r) for r in rows]

    @staticmethod
    def _row_to_entity(r) -> ValePolicia:
        return ValePolicia(
            id=r["id"],
            policia_id=r["policia_id"],
            fecha=r["fecha"],
            local_id=r["local_id"],
            tipo_operacion=r["tipo_operacion"],
            cantidad_vales=int(r["cantidad_vales"] or 0),
            tickets_equivalentes=int(r["tickets_equivalentes"] or 0),
            observacion=r["observacion"],
            fecha_registro=r["fecha_registro"],
            policia_codigo=r["policia_codigo"] if "policia_codigo" in r.keys() else None,
            policia_apellidos=r["policia_apellidos"] if "policia_apellidos" in r.keys() else None,
            policia_nombres=r["policia_nombres"] if "policia_nombres" in r.keys() else None,
            policia_area=r["policia_area"] if "policia_area" in r.keys() else None
        )
