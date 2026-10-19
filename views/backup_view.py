from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from typing import Optional
from backups.backup_manager import BackupManager
from views.components.toast import ToastManager

class BackupView(QWidget):
    """
    Vista de Copias de Seguridad y Restauración:
    - Gestión de backups con protección contra edición accidental de celdas (NoEditTriggers).
    - Acciones de Restauración y Eliminación controladas.
    - Estilo oficial La Provincial (Rojo, Blanco y Negro).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.backup_mgr = BackupManager()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        header_box = QHBoxLayout()
        self.lbl_title = QLabel("💾 COPIAS DE SEGURIDAD Y RESTAURACIÓN")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: 900; color: #FFFFFF;")
        header_box.addWidget(self.lbl_title)
        header_box.addStretch()

        self.btn_crear = QPushButton("💾 Crear Backup Ahora")
        self.btn_crear.setCursor(Qt.PointingHandCursor)
        self.btn_crear.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #991B1B, stop:1 #DC2626);
                color: #FFFFFF;
                border: 1px solid #EF4444;
                border-radius: 6px;
                padding: 7px 16px;
                font-weight: 800;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7F1D1D, stop:1 #B91C1C);
            }
        """)
        self.btn_crear.clicked.connect(self._on_crear_backup)
        header_box.addWidget(self.btn_crear)

        btn_refresh = QPushButton("🔄 Refrescar")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 7px 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #27272A;
                border: 1px solid #DC2626;
            }
        """)
        btn_refresh.clicked.connect(self.cargar_datos)
        header_box.addWidget(btn_refresh)

        layout.addLayout(header_box)

        # Info Box
        info = QLabel("ℹ️ Las copias de seguridad se generan en formato SQLite nativo (.db). Antes de cualquier restauración, el sistema crea automáticamente un backup preventivo de seguridad.")
        info.setStyleSheet("background-color: #141414; color: #A1A1AA; border-left: 4px solid #DC2626; padding: 10px; border-radius: 6px; border: 1px solid #262626;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Nombre de Archivo", "Tamaño", "Fecha de Creación", "Ruta Completa", "Acciones"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 170)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.cargar_datos()

    def cargar_datos(self):
        backups = self.backup_mgr.listar_backups()
        self.table.setRowCount(len(backups))

        for r, b in enumerate(backups):
            self.table.setItem(r, 0, QTableWidgetItem(b["nombre"]))
            self.table.setItem(r, 1, QTableWidgetItem(f"{b['tamano_kb']} KB"))
            self.table.setItem(r, 2, QTableWidgetItem(b["fecha_modificacion"]))
            self.table.setItem(r, 3, QTableWidgetItem(b["ruta"]))

            # Acciones: Restaurar y Eliminar
            action_box = QWidget()
            action_layout = QHBoxLayout(action_box)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(6)

            btn_rest = QPushButton("🔄 Restaurar")
            btn_rest.setCursor(Qt.PointingHandCursor)
            btn_rest.setStyleSheet("""
                QPushButton {
                    background-color: #1E1B4B;
                    color: #A5B4FC;
                    border: 1px solid #3730A3;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 700;
                    padding: 3px 8px;
                }
                QPushButton:hover {
                    background-color: #312E81;
                    color: #FFFFFF;
                }
            """)
            b_name = b["nombre"]
            btn_rest.clicked.connect(lambda ch, bn=b_name: self._on_restaurar_backup(bn))
            action_layout.addWidget(btn_rest)

            btn_del = QPushButton("🗑️")
            btn_del.setToolTip("Eliminar esta copia de seguridad")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setStyleSheet("""
                QPushButton {
                    background-color: #271214;
                    color: #EF4444;
                    border: 1px solid #7F1D1D;
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 3px 6px;
                }
                QPushButton:hover {
                    background-color: #DC2626;
                    color: #FFFFFF;
                }
            """)
            btn_del.clicked.connect(lambda ch, bn=b_name: self._on_eliminar_backup(bn))
            action_layout.addWidget(btn_del)

            self.table.setCellWidget(r, 4, action_box)

    def _on_crear_backup(self):
        ok, msg, path = self.backup_mgr.crear_backup(usuario="USUARIO")
        if ok:
            ToastManager.show_success("Copia de seguridad creada con éxito", self)
            self.cargar_datos()
        else:
            QMessageBox.warning(self, "Error", msg)

    def _on_restaurar_backup(self, backup_name: str):
        resp = QMessageBox.question(
            self,
            "Confirmar Restauración",
            f"¿Está seguro de restaurar la base de datos desde '{backup_name}'?\n\nSe creará una copia preventiva automática antes de restaurar.",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            ok, msg = self.backup_mgr.restaurar_backup(backup_name, usuario="USUARIO")
            if ok:
                ToastManager.show_success("Restauración completada exitosamente", self)
                self.cargar_datos()
            else:
                QMessageBox.warning(self, "Error al Restaurar", msg)

    def _on_eliminar_backup(self, backup_name: str):
        resp = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de eliminar permanentemente la copia '{backup_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            ok, msg = self.backup_mgr.eliminar_backup(backup_name, usuario="USUARIO")
            if ok:
                ToastManager.show_info("Copia eliminada", self)
                self.cargar_datos()
            else:
                QMessageBox.warning(self, "Error al Eliminar", msg)
