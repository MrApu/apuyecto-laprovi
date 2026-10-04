from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt
from typing import Optional
from backups.backup_manager import BackupManager

class BackupView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.backup_mgr = BackupManager()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        header_box = QHBoxLayout()
        self.lbl_title = QLabel("Copias de Seguridad y Restauración")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1F4E78;")
        header_box.addWidget(self.lbl_title)
        header_box.addStretch()

        self.btn_crear = QPushButton("💾 Crear Backup Ahora")
        self.btn_crear.setProperty("class", "PrimaryBtn")
        self.btn_crear.clicked.connect(self._on_crear_backup)
        header_box.addWidget(self.btn_crear)

        layout.addLayout(header_box)

        # Info Box
        info = QLabel("ℹ️ Las copias de seguridad se generan en formato SQLite nativo (.db). Antes de cualquier restauración, el sistema crea automáticamente un backup de seguridad preventivo.")
        info.setStyleSheet("background-color: #EBF5FB; color: #1B4F72; padding: 8px; border-radius: 4px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Nombre de Archivo", "Tamaño", "Fecha de Creación", "Ruta Completa", "Restaurar"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
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

            btn_rest = QPushButton("🔄 Restaurar")
            btn_rest.setProperty("class", "DangerBtn")
            btn_rest.clicked.connect(lambda _, b_name=b["nombre"]: self._on_restaurar_backup(b_name))
            self.table.setCellWidget(r, 4, btn_rest)

    def _on_crear_backup(self):
        ok, msg, path = self.backup_mgr.crear_backup(usuario="USUARIO")
        if ok:
            QMessageBox.information(self, "Backup Exitoso", msg)
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
                QMessageBox.information(self, "Restauración Completada", msg)
                self.cargar_datos()
            else:
                QMessageBox.warning(self, "Error al Restaurar", msg)
