from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QTextEdit, QDateEdit, QMessageBox, QComboBox,
    QDialog, QFormLayout, QFrame
)
from PySide6.QtCore import QDate, Qt
from typing import Optional, List
from models.observacion import Observacion
from services.observacion_service import ObservacionService
from views.components.toast import ToastManager


class EditarObservacionDialog(QDialog):
    """Diálogo formal para editar una observación sin riesgo de sobreescritura accidental."""
    def __init__(self, obs: Observacion, parent=None):
        super().__init__(parent)
        self.obs = obs
        self.setWindowTitle(f"✏️ Editar Observación #{obs.id}")
        self.resize(450, 260)
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
            QDateEdit, QComboBox, QTextEdit {
                background-color: #141414;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QDateEdit:focus, QComboBox:focus, QTextEdit:focus {
                border: 1px solid #DC2626;
                background-color: #18181B;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        lbl_head = QLabel("✏️ EDITAR OBSERVACIÓN / NOTA")
        lbl_head.setStyleSheet("font-size: 15px; font-weight: 900; color: #FFFFFF;")
        layout.addWidget(lbl_head)

        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: #141414; border: 1px solid #262626; border-radius: 8px; padding: 10px;")
        form = QFormLayout(form_frame)
        form.setSpacing(10)

        try:
            dt = datetime.strptime(self.obs.fecha, "%Y-%m-%d")
            self.dt_picker = QDateEdit(QDate(dt.year, dt.month, dt.day))
        except Exception:
            self.dt_picker = QDateEdit(QDate.currentDate())
        self.dt_picker.setCalendarPopup(True)
        form.addRow("📅 Fecha:", self.dt_picker)

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["GENERAL", "DEUDA", "VALES", "AJUSTE", "PAGO", "IMPORTANTE"])
        idx_t = self.cmb_tipo.findText(self.obs.tipo)
        if idx_t >= 0:
            self.cmb_tipo.setCurrentIndex(idx_t)
        form.addRow("🏷️ Tipo:", self.cmb_tipo)

        self.txt_texto = QTextEdit()
        self.txt_texto.setText(self.obs.texto)
        self.txt_texto.setMaximumHeight(80)
        form.addRow("📝 Nota / Detalle:", self.txt_texto)

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

        btn_save = QPushButton("💾 Guardar Cambios")
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
        txt = self.txt_texto.toPlainText().strip()
        if not txt:
            QMessageBox.warning(self, "Campo Requerido", "Debe ingresar el texto de la observación.")
            self.txt_texto.setFocus()
            return
        self.obs.fecha = self.dt_picker.date().toString("yyyy-MM-dd")
        self.obs.tipo = self.cmb_tipo.currentText()
        self.obs.texto = txt
        self.accept()


class ObservacionesView(QWidget):
    """
    Vista de Observaciones y Notas Diarias (CRUD Completo):
    - Creación de notas
    - Visualización con NoEditTriggers (protección contra ediciones accidentales al hacer clic)
    - Edición formal mediante botón '✏️'
    - Eliminación mediante botón '🗑️'
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.obs_service = ObservacionService()
        self.current_anio = 2026
        self.current_mes = 9
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        header_box = QHBoxLayout()
        self.lbl_title = QLabel("📝 OBSERVACIONES Y NOTAS DIARIAS")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: 900; color: #FFFFFF;")
        header_box.addWidget(self.lbl_title)
        header_box.addStretch()

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

        # New Note Box
        new_box = QHBoxLayout()
        new_box.setSpacing(10)

        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setStyleSheet("""
            QDateEdit {
                background-color: #141414;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
        """)
        new_box.addWidget(self.date_picker)

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["GENERAL", "DEUDA", "VALES", "AJUSTE", "PAGO", "IMPORTANTE"])
        self.cmb_tipo.setStyleSheet("""
            QComboBox {
                background-color: #141414;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
        """)
        new_box.addWidget(self.cmb_tipo)

        self.txt_texto = QTextEdit()
        self.txt_texto.setMaximumHeight(50)
        self.txt_texto.setPlaceholderText("Escriba aquí la observación o nota del día...")
        self.txt_texto.setStyleSheet("""
            QTextEdit {
                background-color: #141414;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QTextEdit:focus {
                border: 1px solid #DC2626;
            }
        """)
        new_box.addWidget(self.txt_texto, 3)

        self.btn_agregar = QPushButton("➕ Agregar Nota")
        self.btn_agregar.setCursor(Qt.PointingHandCursor)
        self.btn_agregar.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #991B1B, stop:1 #DC2626);
                color: #FFFFFF;
                border: 1px solid #EF4444;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 800;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7F1D1D, stop:1 #B91C1C);
            }
        """)
        self.btn_agregar.clicked.connect(self._on_agregar)
        new_box.addWidget(self.btn_agregar)

        layout.addLayout(new_box)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Fecha", "Tipo", "Observación / Nota", "Acciones"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 90)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        layout.addWidget(self.table)

    def set_periodo(self, anio: int, mes: int):
        self.current_anio = anio
        self.current_mes = mes
        self.lbl_title.setText(f"📝 OBSERVACIONES Y NOTAS — {mes:02d}/{anio}")
        self.cargar_datos()

    def cargar_datos(self):
        obs_list = self.obs_service.get_by_mes(self.current_anio, self.current_mes)
        self.table.setRowCount(len(obs_list))

        for r, o in enumerate(obs_list):
            self.table.setItem(r, 0, QTableWidgetItem(o.fecha))
            self.table.setItem(r, 1, QTableWidgetItem(o.tipo))
            self.table.setItem(r, 2, QTableWidgetItem(o.texto))

            # Contenedor de botones de acción
            action_box = QWidget()
            action_layout = QHBoxLayout(action_box)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(4)

            btn_edit = QPushButton("✏️")
            btn_edit.setToolTip("Editar esta observación")
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setStyleSheet("""
                QPushButton {
                    background-color: #18181B;
                    color: #A1A1AA;
                    border: 1px solid #27272A;
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 2px 5px;
                }
                QPushButton:hover {
                    background-color: #27272A;
                    color: #FFFFFF;
                    border: 1px solid #DC2626;
                }
            """)
            o_id = o.id
            btn_edit.clicked.connect(lambda ch, oid=o_id: self._editar(oid))
            action_layout.addWidget(btn_edit)

            btn_del = QPushButton("🗑️")
            btn_del.setToolTip("Eliminar esta observación")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setStyleSheet("""
                QPushButton {
                    background-color: #271214;
                    color: #EF4444;
                    border: 1px solid #7F1D1D;
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 2px 5px;
                }
                QPushButton:hover {
                    background-color: #DC2626;
                    color: #FFFFFF;
                }
            """)
            btn_del.clicked.connect(lambda ch, oid=o_id: self._eliminar(oid))
            action_layout.addWidget(btn_del)

            self.table.setCellWidget(r, 3, action_box)

    def _on_cell_double_clicked(self, row: int, col: int):
        obs_list = self.obs_service.get_by_mes(self.current_anio, self.current_mes)
        if 0 <= row < len(obs_list):
            self._editar(obs_list[row].id)

    def _on_agregar(self):
        fecha = self.date_picker.date().toString("yyyy-MM-dd")
        texto = self.txt_texto.toPlainText().strip()
        tipo = self.cmb_tipo.currentText()

        if not texto:
            QMessageBox.warning(self, "Campo Vacío", "Debe ingresar un texto.")
            self.txt_texto.setFocus()
            return

        ok, msg, _ = self.obs_service.agregar_observacion(fecha, texto, tipo)
        if ok:
            ToastManager.show_success("Nota guardada", self)
            self.txt_texto.clear()
            self.cargar_datos()
        else:
            QMessageBox.warning(self, "Error", msg)

    def _editar(self, obs_id: int):
        obs = self.obs_service.get_by_id(obs_id)
        if not obs:
            return
        dlg = EditarObservacionDialog(obs, self)
        if dlg.exec() == QDialog.Accepted:
            ok, msg = self.obs_service.actualizar_observacion(obs)
            if ok:
                ToastManager.show_success("Observación actualizada", self)
                self.cargar_datos()
            else:
                QMessageBox.warning(self, "Error", msg)

    def _eliminar(self, obs_id: int):
        if QMessageBox.question(self, "Confirmar", "¿Desea eliminar esta observación?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            ok, msg = self.obs_service.eliminar_observacion(obs_id)
            if ok:
                ToastManager.show_info("Observación eliminada", self)
                self.cargar_datos()
            else:
                QMessageBox.warning(self, "Error", msg)
