from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDoubleSpinBox,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt
from typing import Optional
from repositories.configuracion_repository import ConfiguracionRepository
from repositories.auditoria_repository import AuditoriaRepository
from views.dialogs.ajuste_dialog import AjusteDialog

class ConfiguracionView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_repo = ConfiguracionRepository()
        self.audit_repo = AuditoriaRepository()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        header_box = QHBoxLayout()
        self.lbl_title = QLabel("Configuración del Sistema y Auditoría")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1F4E78;")
        header_box.addWidget(self.lbl_title)
        header_box.addStretch()
        layout.addLayout(header_box)

        # Price Config Card
        grp_precio = QGroupBox("Parámetros Principales de Precios")
        l_form = QFormLayout(grp_precio)
        l_form.setSpacing(10)

        self.spin_precio_actual = QDoubleSpinBox()
        self.spin_precio_actual.setRange(1.0, 500.0)
        self.spin_precio_actual.setDecimals(2)
        self.spin_precio_actual.setPrefix("S/ ")
        self.spin_precio_actual.setValue(self.config_repo.get_float("precio_menu_policial", 15.0))

        btn_guardar_precio = QPushButton("💾 Actualizar Precio General")
        btn_guardar_precio.setProperty("class", "PrimaryBtn")
        btn_guardar_precio.clicked.connect(self._on_guardar_precio)

        l_precio_row = QHBoxLayout()
        l_precio_row.addWidget(self.spin_precio_actual)
        l_precio_row.addWidget(btn_guardar_precio)
        l_precio_row.addStretch()

        l_form.addRow("Precio Menú Policial Estándar:", l_precio_row)

        info_lbl = QLabel("ℹ️ <b>Regla histórica:</b> Modificar el precio actual NO altera los cálculos de meses pasados ya cerrados o registrados.")
        info_lbl.setStyleSheet("color: #595959; font-size: 11px;")
        l_form.addRow("", info_lbl)

        layout.addWidget(grp_precio)

        # Price History Table
        layout.addWidget(QLabel("<b>Historial de Modificaciones de Precios:</b>"))
        self.table_hist_precio = QTableWidget()
        self.table_hist_precio.setColumnCount(5)
        self.table_hist_precio.setHorizontalHeaderLabels(["Fecha Cambio", "Clave", "Valor Anterior", "Nuevo Valor", "Motivo / Usuario"])
        self.table_hist_precio.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_hist_precio.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_hist_precio.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_hist_precio.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_hist_precio.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table_hist_precio.setMaximumHeight(160)
        layout.addWidget(self.table_hist_precio)

        # Audit Table
        layout.addWidget(QLabel("<b>Registro de Auditoría de Acciones Recientes:</b>"))
        self.table_audit = QTableWidget()
        self.table_audit.setColumnCount(5)
        self.table_audit.setHorizontalHeaderLabels(["Fecha", "Usuario", "Acción", "Entidad", "Detalles"])
        self.table_audit.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_audit.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_audit.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_audit.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_audit.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        layout.addWidget(self.table_audit)

        self.cargar_datos()

    def cargar_datos(self):
        # 1. Load price
        precio = self.config_repo.get_float("precio_menu_policial", 15.0)
        self.spin_precio_actual.setValue(precio)

        # 2. Load Price History
        hist = self.config_repo.get_historial("precio_menu_policial")
        self.table_hist_precio.setRowCount(len(hist))
        for r, h in enumerate(hist):
            self.table_hist_precio.setItem(r, 0, QTableWidgetItem(h.fecha_cambio or ""))
            self.table_hist_precio.setItem(r, 1, QTableWidgetItem(h.clave))
            self.table_hist_precio.setItem(r, 2, QTableWidgetItem(f"S/ {float(h.valor_anterior or 0):.2f}"))
            self.table_hist_precio.setItem(r, 3, QTableWidgetItem(f"S/ {float(h.valor_nuevo or 0):.2f}"))
            self.table_hist_precio.setItem(r, 4, QTableWidgetItem(f"{h.motivo or '-'} (por {h.usuario})"))

        # 3. Load Audit Logs
        audits = self.audit_repo.get_recientes(100)
        self.table_audit.setRowCount(len(audits))
        for r, a in enumerate(audits):
            self.table_audit.setItem(r, 0, QTableWidgetItem(a.fecha or ""))
            self.table_audit.setItem(r, 1, QTableWidgetItem(a.usuario))
            self.table_audit.setItem(r, 2, QTableWidgetItem(a.accion))
            self.table_audit.setItem(r, 3, QTableWidgetItem(f"{a.entidad} #{a.entidad_id or ''}"))
            self.table_audit.setItem(r, 4, QTableWidgetItem(a.detalles or ""))

    def _on_guardar_precio(self):
        nuevo_precio = self.spin_precio_actual.value()
        precio_actual = self.config_repo.get_float("precio_menu_policial", 15.0)

        if nuevo_precio == precio_actual:
            QMessageBox.information(self, "Información", "El precio ingresado es igual al actual.")
            return

        dlg = AjusteDialog(self, titulo="Cambio de Precio Policial", detalle_cambio=f"De S/ {precio_actual:.2f} a S/ {nuevo_precio:.2f}")
        if dlg.exec():
            motivo = dlg.get_motivo()
            self.config_repo.set_valor("precio_menu_policial", f"{nuevo_precio:.2f}", usuario="ADMIN", motivo=motivo)
            QMessageBox.information(self, "Precio Actualizado", f"Precio configurado a S/ {nuevo_precio:.2f}.")
            self.cargar_datos()
