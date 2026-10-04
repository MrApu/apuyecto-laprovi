import sqlite3
import os
import shutil
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "control_policial.db")

class DatabaseManager:
    _instance: Optional['DatabaseManager'] = None

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.environ.get("CONTROL_POLICIAL_DB", DEFAULT_DB_PATH)
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        DatabaseManager._instance = self
        self._init_db()

    @classmethod
    def get_instance(cls, db_path: Optional[str] = None) -> 'DatabaseManager':
        if cls._instance is None or (db_path and cls._instance.db_path != db_path):
            cls._instance = DatabaseManager(db_path)
        return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _init_db(self):
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
        else:
            raise FileNotFoundError("schema.sql not found")

        with self.get_connection() as conn:
            conn.executescript(schema_sql)
            # Insert default configs if not present
            configs = [
                ('nombre_local_1', 'LA PROVINCIAL RESTAURANTE', 'STRING', 'Nombre oficial del local 1'),
                ('nombre_local_2', 'LA PROVINCIAL FAST FOOD', 'STRING', 'Nombre oficial del local 2'),
                ('precio_ticket_policial', '12.00', 'FLOAT', 'Precio unitario estándar por ticket policial en soles'),
                ('venta_incluye_tickets', 'NO', 'STRING', 'Indica si la venta en efectivo/yape ya incluye tickets (SI/NO)'),
                ('moneda', 'S/', 'STRING', 'Símbolo de moneda oficial'),
                ('empresa_ruc', '20600000000', 'STRING', 'RUC o identificación tributaria')
            ]
            for clave, valor, tipo_dato, desc in configs:
                conn.execute("""
                    INSERT OR IGNORE INTO configuracion (clave, valor, tipo_dato, descripcion, fecha_actualizacion)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (clave, valor, tipo_dato, desc))
            conn.commit()

    def execute_query(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_non_query(self, query: str, params: Tuple = ()) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid or cursor.rowcount

    def execute_transaction(self, operations: List[Tuple[str, Tuple]]) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                for query, params in operations:
                    cursor.execute(query, params)
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                raise e
