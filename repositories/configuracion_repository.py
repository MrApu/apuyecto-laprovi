from typing import List, Optional, Any
from database.connection import DatabaseManager
from models.configuracion import Configuracion, ConfiguracionHistorial

class ConfiguracionRepository:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager.get_instance()

    def get_valor(self, clave: str, default: str = "") -> str:
        rows = self.db.execute_query("SELECT valor FROM configuracion WHERE clave = ?", (clave,))
        return rows[0]["valor"] if rows else default

    def get_float(self, clave: str, default: float = 0.0) -> float:
        val = self.get_valor(clave, str(default))
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    def set_valor(self, clave: str, valor: str, usuario: str = "USUARIO", motivo: Optional[str] = None) -> bool:
        current = self.get_valor(clave)
        if current == valor:
            return True

        query_update = """
            INSERT INTO configuracion (clave, valor, fecha_actualizacion)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(clave) DO UPDATE SET
                valor = excluded.valor,
                fecha_actualizacion = CURRENT_TIMESTAMP
        """
        self.db.execute_non_query(query_update, (clave, valor))

        # Log to configuracion_historial
        query_hist = """
            INSERT INTO configuracion_historial (clave, valor_anterior, valor_nuevo, fecha_cambio, usuario, motivo)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
        """
        self.db.execute_non_query(query_hist, (clave, current, valor, usuario, motivo))
        return True

    def get_historial(self, clave: Optional[str] = None) -> List[ConfiguracionHistorial]:
        if clave:
            rows = self.db.execute_query(
                "SELECT id, clave, valor_anterior, valor_nuevo, fecha_cambio, usuario, motivo FROM configuracion_historial WHERE clave = ? ORDER BY fecha_cambio DESC",
                (clave,)
            )
        else:
            rows = self.db.execute_query(
                "SELECT id, clave, valor_anterior, valor_nuevo, fecha_cambio, usuario, motivo FROM configuracion_historial ORDER BY fecha_cambio DESC"
            )
        return [
            ConfiguracionHistorial(
                id=r["id"],
                clave=r["clave"],
                valor_anterior=r["valor_anterior"],
                valor_nuevo=r["valor_nuevo"],
                fecha_cambio=r["fecha_cambio"],
                usuario=r["usuario"],
                motivo=r["motivo"]
            )
            for r in rows
        ]
