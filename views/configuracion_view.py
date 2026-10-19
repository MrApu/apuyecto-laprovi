from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDoubleSpinBox,
    QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGroupBox, QFormLayout, QDialog, QFrame, QScrollArea
)
from PySide6.QtCore import Qt
from typing import Optional
from repositories.configuracion_repository import ConfiguracionRepository
from repositories.auditoria_repository import AuditoriaRepository
from views.components.toast import ToastManager


class EditarParametroDialog(QDialog):
    """Diálogo modal seguro para editar valores de configuración sin permitir cambios accidentales."""
    def __init__(self, clave: str, valor_actual: str, descripcion: str = "", es_nuevo: bool = False, parent=None):
        super().__init__(parent)
        self.clave = clave
        self.valor_actual = valor_actual
        self.descripcion = descripcion
        self.es_nuevo = es_nuevo

        self.setWindowTitle("➕ Nuevo Parámetro" if es_nuevo else f"✏️ Modificar Parámetro: {clave}")
        self.resize(460, 280)
        self.setStyleSheet("""
            QDialog {
                background-color: #0A0A0A;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 12px;
                font-weight: 700;
            }
            QLineEdit, QTextEdit {
                background-color: #141414;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #DC2626;
                background-color: #18181B;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title_text = "NUEVO PARÁMETRO / TARIFA" if self.es_nuevo else f"MODIFICAR {self.clave.upper()}"
        lbl_head = QLabel(f"⚙️ {title_text}")
        lbl_head.setStyleSheet("font-size: 15px; font-weight: 900; color: #FFFFFF;")
        layout.addWidget(lbl_head)

        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: #141414; border: 1px solid #262626; border-radius: 8px; padding: 10px;")
        form = QFormLayout(form_frame)
        form.setSpacing(10)

        self.txt_clave = QLineEdit(self.clave)
        self.txt_clave.setReadOnly(not self.es_nuevo)
        if not self.es_nuevo:
            self.txt_clave.setStyleSheet("background-color: #1C1C1F; color: #A1A1AA; border: 1px solid #27272A;")
        form.addRow("🔑 Clave:", self.txt_clave)

        if not self.es_nuevo:
            lbl_ant = QLabel(f"<b>{self.valor_actual}</b>")
            lbl_ant.setStyleSheet("color: #EF4444; font-size: 13px;")
            form.addRow("Valor Anterior:", lbl_ant)

        self.txt_valor = QLineEdit(self.valor_actual if not self.es_nuevo else "")
        self.txt_valor.setPlaceholderText("Ej: 15.00, NOMBRE, SI...")
        form.addRow("Valor Nuevo (*):", self.txt_valor)

        self.txt_motivo = QLineEdit()
        self.txt_motivo.setPlaceholderText("Motivo del cambio para auditoría...")
        form.addRow("📝 Motivo (*):", self.txt_motivo)

        layout.addWidget(form_frame)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        btn_cancel = QPushButton("✕ Cancelar")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #18181B;
                color: #A1A1AA;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 7px 16px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #27272A;
                color: #FFFFFF;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Guardar y Aplicar")
        btn_save.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #991B1B, stop:1 #DC2626);
                color: #FFFFFF;
                border: 1px solid #EF4444;
                border-radius: 6px;
                padding: 8px 18px;
                font-weight: 900;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7F1D1D, stop:1 #B91C1C);
            }
        """)
        btn_save.clicked.connect(self._on_guardar)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)

    def _on_guardar(self):
        clave = self.txt_clave.text().strip()
        valor = self.txt_valor.text().strip()
        motivo = self.txt_motivo.text().strip()

        if not clave:
            QMessageBox.warning(self, "Atención", "Debe ingresar una clave válida.")
            self.txt_clave.setFocus()
            return
        if not valor:
            QMessageBox.warning(self, "Atención", "Debe ingresar un valor.")
            self.txt_valor.setFocus()
            return
        if not motivo:
            QMessageBox.warning(self, "Atención", "Debe registrar un motivo para la trazabilidad y auditoría.")
            self.txt_motivo.setFocus()
            return

        self.accept()

    def get_data(self):
        return self.txt_clave.text().strip(), self.txt_valor.text().strip(), self.txt_motivo.text().strip()


class ConfiguracionView(QWidget):
    """
    Vista de Configuración del Sistema y Auditoría (La Provincial - Rojo, Blanco y Negro):
    - CRUD completo de parámetros y tarifas con protección NoEditTriggers (solo editable mediante botón formal).
    - Historial de modificaciones de precios con trazabilidad.
    - Registro de auditoría de acciones recientes.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_repo = ConfiguracionRepository()
        self.audit_repo = AuditoriaRepository()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Header Title
        header_box = QHBoxLayout()
        self.lbl_title = QLabel("⚙️ CONFIGURACIÓN DEL SISTEMA Y AUDITORÍA")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: 900; color: #FFFFFF;")
        header_box.addWidget(self.lbl_title)

        header_box.addStretch()

        btn_add_param = QPushButton("➕ Agregar Parámetro / Tarifa")
        btn_add_param.setCursor(Qt.PointingHandCursor)
        btn_add_param.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #991B1B, stop:1 #DC2626);
                color: #FFFFFF;
                border: 1px solid #EF4444;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 800;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7F1D1D, stop:1 #B91C1C);
            }
        """)
        btn_add_param.clicked.connect(self._on_agregar_parametro)
        header_box.addWidget(btn_add_param)

        btn_refresh = QPushButton("🔄 Refrescar")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 6px 12px;
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

        # -------------------------------------------------------------
        # 1. Tabla de Parámetros y Tarifas Configurables (CRUD)
        # -------------------------------------------------------------
        lbl_sec1 = QLabel("<b>📋 Parámetros y Tarifas del Sistema (Edición protegida mediante botón):</b>")
        lbl_sec1.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 800;")
        layout.addWidget(lbl_sec1)

        self.table_params = QTableWidget()
        self.table_params.setColumnCount(5)
        self.table_params.setHorizontalHeaderLabels(["Clave del Sistema", "Valor Actual", "Tipo", "Descripción", "Acción"])
        self.table_params.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_params.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_params.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_params.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table_params.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.table_params.setColumnWidth(4, 110)
        self.table_params.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_params.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_params.setMaximumHeight(180)
        layout.addWidget(self.table_params)

        # -------------------------------------------------------------
        # 2. Historial de Modificaciones de Precios
        # -------------------------------------------------------------
        lbl_sec2 = QLabel("<b>📈 Historial de Modificaciones de Precios y Tarifas:</b>")
        lbl_sec2.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 800;")
        layout.addWidget(lbl_sec2)

        self.table_hist_precio = QTableWidget()
        self.table_hist_precio.setColumnCount(5)
        self.table_hist_precio.setHorizontalHeaderLabels(["Fecha Cambio", "Clave", "Valor Anterior", "Nuevo Valor", "Motivo / Usuario"])
        self.table_hist_precio.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_hist_precio.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_hist_precio.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_hist_precio.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_hist_precio.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table_hist_precio.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_hist_precio.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_hist_precio.setMaximumHeight(150)
        layout.addWidget(self.table_hist_precio)

        # -------------------------------------------------------------
        # 3. Registro de Auditoría de Acciones Recientes
        # -------------------------------------------------------------
        lbl_sec3 = QLabel("<b>🛡️ Registro de Auditoría de Acciones Recientes:</b>")
        lbl_sec3.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 800;")
        layout.addWidget(lbl_sec3)

        self.table_audit = QTableWidget()
        self.table_audit.setColumnCount(5)
        self.table_audit.setHorizontalHeaderLabels(["Fecha", "Usuario", "Acción", "Entidad", "Detalles"])
        self.table_audit.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_audit.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_audit.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_audit.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_audit.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table_audit.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_audit.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table_audit)

        self.cargar_datos()

    def cargar_datos(self):
        # 1. Load Parameters CRUD table
        params = self.config_repo.get_all()
        self.table_params.setRowCount(len(params))
        for r, p in enumerate(params):
            self.table_params.setItem(r, 0, QTableWidgetItem(p.clave))
            self.table_params.setItem(r, 1, QTableWidgetItem(p.valor))
            self.table_params.setItem(r, 2, QTableWidgetItem(p.tipo_dato or "STRING"))
            self.table_params.setItem(r, 3, QTableWidgetItem(p.descripcion or "-"))

            # Botón Editar dedicado (CRUD)
            btn_edit = QPushButton("✏️ Editar")
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setStyleSheet("""
                QPushButton {
                    background-color: #18181B;
                    color: #FFFFFF;
                    border: 1px solid #27272A;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 700;
                    padding: 3px 8px;
                }
                QPushButton:hover {
                    background-color: #27272A;
                    border: 1px solid #DC2626;
                    color: #EF4444;
                }
            """)
            clave_val = p.clave
            valor_val = p.valor
            desc_val = p.descripcion or ""
            btn_edit.clicked.connect(lambda ch, c=clave_val, v=valor_val, d=desc_val: self._on_editar_parametro(c, v, d))
            self.table_params.setCellWidget(r, 4, btn_edit)

        # 2. Load Price History
        hist = self.config_repo.get_historial()
        self.table_hist_precio.setRowCount(len(hist))
        for r, h in enumerate(hist):
            self.table_hist_precio.setItem(r, 0, QTableWidgetItem(h.fecha_cambio or ""))
            self.table_hist_precio.setItem(r, 1, QTableWidgetItem(h.clave))
            val_ant_str = f"S/ {float(h.valor_anterior or 0):.2f}" if (h.valor_anterior or "").replace(".", "").isdigit() else (h.valor_anterior or "-")
            val_nue_str = f"S/ {float(h.valor_nuevo or 0):.2f}" if (h.valor_nuevo or "").replace(".", "").isdigit() else (h.valor_nuevo or "-")
            self.table_hist_precio.setItem(r, 2, QTableWidgetItem(val_ant_str))
            self.table_hist_precio.setItem(r, 3, QTableWidgetItem(val_nue_str))
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

    def _on_editar_parametro(self, clave: str, valor_actual: str, descripcion: str = ""):
        dlg = EditarParametroDialog(clave=clave, valor_actual=valor_actual, descripcion=descripcion, es_nuevo=False, parent=self)
        if dlg.exec() == QDialog.Accepted:
            k, v, m = dlg.get_data()
            self.config_repo.set_valor(k, v, usuario="ADMIN", motivo=m)
            ToastManager.show_success(f"Parámetro {k} actualizado a '{v}'", self)
            self.cargar_datos()

    def _on_agregar_parametro(self):
        dlg = EditarParametroDialog(clave="", valor_actual="", descripcion="", es_nuevo=True, parent=self)
        if dlg.exec() == QDialog.Accepted:
            k, v, m = dlg.get_data()
            self.config_repo.set_valor(k, v, usuario="ADMIN", motivo=m)
            ToastManager.show_success(f"Parámetro {k} creado correctamente", self)
            self.cargar_datos()
