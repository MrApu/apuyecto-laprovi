import os
import shutil
import sqlite3
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
from database.connection import DatabaseManager
from repositories.auditoria_repository import AuditoriaRepository

class BackupManager:
    def __init__(self, backup_dir: Optional[str] = None, db: Optional[DatabaseManager] = None, db_path: Optional[str] = None):
        if db:
            self.db = db
        elif db_path:
            self.db = DatabaseManager.get_instance(db_path)
        else:
            self.db = DatabaseManager.get_instance()
        self.backup_dir = backup_dir or os.path.join(os.path.dirname(os.path.dirname(self.db.db_path)), "backups_db")
        os.makedirs(self.backup_dir, exist_ok=True)
        self.audit_repo = AuditoriaRepository(self.db)

    def verificar_integridad(self, backup_path: str) -> Tuple[bool, str]:
        """Checks if a SQLite database file has PRAGMA quick_check == 'ok'."""
        if not os.path.exists(backup_path):
            return False, "El archivo de respaldo no existe."
        try:
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA quick_check")
            res = cursor.fetchone()
            conn.close()
            if res and res[0] == "ok":
                return True, "Base de datos íntegra y válida."
            return False, f"Fallo de integridad: {res}"
        except Exception as e:
            return False, f"Error al verificar base de datos: {str(e)}"

    def crear_backup(self, usuario: str = "USUARIO", etiqueta: str = "manual") -> Tuple[bool, str, str]:
        """Creates backup_YYYY-MM-DD_HH-MM-SS.db using sqlite3 backup API."""
        now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"backup_{now_str}.db"
        if etiqueta and etiqueta != "manual":
            backup_filename = f"backup_{now_str}_{etiqueta}.db"
        backup_path = os.path.join(self.backup_dir, backup_filename)

        try:
            # Safe live SQLite backup
            with self.db.get_connection() as src_conn:
                dest_conn = sqlite3.connect(backup_path)
                src_conn.backup(dest_conn)
                dest_conn.close()

            file_size_kb = os.path.getsize(backup_path) / 1024

            self.audit_repo.registrar(
                accion="CREAR_BACKUP",
                entidad="sistema",
                entidad_id=backup_filename,
                detalles=f"Copia de seguridad generada ({file_size_kb:.1f} KB) en {backup_path}",
                usuario=usuario
            )
            return True, f"Copia de seguridad creada con éxito: {backup_filename} ({file_size_kb:.1f} KB)", backup_path
        except Exception as e:
            return False, f"Error al generar copia de seguridad: {str(e)}", ""

    def listar_backups(self) -> List[Dict[str, Any]]:
        backups = []
        if not os.path.exists(self.backup_dir):
            return []

        for f in os.listdir(self.backup_dir):
            if f.endswith(".db"):
                path = os.path.join(self.backup_dir, f)
                stat = os.stat(path)
                backups.append({
                    "nombre": f,
                    "ruta": path,
                    "tamano_kb": round(stat.st_size / 1024, 2),
                    "fecha_modificacion": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })

        backups.sort(key=lambda x: x["nombre"], reverse=True)
        return backups

    def restaurar_backup(self, backup_filename: str, usuario: str = "USUARIO") -> Tuple[bool, str]:
        """Creates a safety backup of the current database before restoring."""
        backup_path = os.path.join(self.backup_dir, backup_filename)
        if not os.path.exists(backup_path):
            return False, f"El archivo de copia {backup_filename} no existe."

        # 1. Automatic safety backup of current state
        ok_pre, msg_pre, _ = self.crear_backup(usuario=usuario, etiqueta="pre_restauracion")
        if not ok_pre:
            return False, f"No se pudo crear copia de seguridad previa de protección: {msg_pre}"

        try:
            # Perform restore via backup API
            src_conn = sqlite3.connect(backup_path)
            with self.db.get_connection() as dest_conn:
                src_conn.backup(dest_conn)
            src_conn.close()

            self.audit_repo.registrar(
                accion="RESTAURAR_BACKUP",
                entidad="sistema",
                entidad_id=backup_filename,
                detalles=f"Base de datos restaurada desde {backup_filename}",
                usuario=usuario
            )
            return True, f"Base de datos restaurada exitosamente desde {backup_filename}."
        except Exception as e:
            return False, f"Error durante la restauración: {str(e)}"
