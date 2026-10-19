import sqlite3
import os
import sys
import shutil
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple


def _resolve_default_db_path() -> str:
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        local_db = os.path.join(exe_dir, "control_policial.db")
        if os.path.exists(local_db):
            return local_db
        # If running from dist/LaProvincial/LaProvincial.exe inside project folder
        root_db = os.path.abspath(os.path.join(exe_dir, "..", "..", "control_policial.db"))
        if os.path.exists(root_db):
            return root_db
        return local_db
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "control_policial.db")


def _resolve_schema_path() -> str:
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql"),
    ]
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            candidates.append(os.path.join(meipass, "database", "schema.sql"))
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        candidates.append(os.path.join(exe_dir, "database", "schema.sql"))
        candidates.append(os.path.join(exe_dir, "_internal", "database", "schema.sql"))
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]


DEFAULT_DB_PATH = _resolve_default_db_path()

class DatabaseManager:
    _instance: Optional['DatabaseManager'] = None

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.environ.get("CONTROL_POLICIAL_DB", _resolve_default_db_path())
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
        schema_path = _resolve_schema_path()
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
        else:
            raise FileNotFoundError(f"schema.sql not found (buscado en {schema_path})")

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
