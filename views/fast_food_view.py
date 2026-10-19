from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QMessageBox, QSpinBox,
    QDialog, QFormLayout, QDialogButtonBox, QDateEdit, QLineEdit, QFrame
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor
from typing import Optional

from services.fast_food_service import FastFoodService
from services.mes_service import MesService
from models.fast_food_consumo import FastFoodConsumo
from views.components.toast import ToastManager


class EditarFastFoodDialog(QDialog):
    """Diálogo modal para registrar o modificar consumo de Fast Food sin editar celdas directamente."""
    def __init__(self, consumo: Optional[FastFoodConsumo] = None, fecha_default: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.consumo = consumo
        self.fecha_default = fecha_default
        self.setWindowTitle("✏️ Editar Consumo Fast Food" if consumo else "➕ Registrar Consumo Fast Food")
        self.resize(450, 280)
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
            QDateEdit, QSpinBox, QLineEdit {
                background-color: #141414;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QDateEdit:focus, QSpinBox:focus, QLineEdit:focus {
                border: 1px solid #DC2626;
                background-color: #18181B;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title_txt = "EDITAR CONSUMO FAST FOOD" if self.consumo else "REGISTRAR CONSUMO FAST FOOD"
        lbl_head = QLabel(f"🍔 {title_txt}")
        lbl_head.setStyleSheet("font-size: 15px; font-weight: 900; color: #FFFFFF;")
        layout.addWidget(lbl_head)

        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: #141414; border: 1px solid #262626; border-radius: 8px; padding: 10px;")
        form = QFormLayout(form_frame)
        form.setSpacing(10)

        # Fecha
        if self.consumo:
            try:
                dt = datetime.strptime(self.consumo.fecha, "%Y-%m-%d")
                self.dt_edit = QDateEdit(QDate(dt.year, dt.month, dt.day))
            except Exception:
                self.dt_edit = QDateEdit(QDate.currentDate())
            self.dt_edit.setReadOnly(True)
            self.dt_edit.setStyleSheet("background-color: #1C1C1F; color: #A1A1AA; border: 1px solid #27272A;")
        else:
            if self.fecha_default:
                try:
                    dt = datetime.strptime(self.fecha_default, "%Y-%m-%d")
                    self.dt_edit = QDateEdit(QDate(dt.year, dt.month, dt.day))
                except Exception:
                    self.dt_edit = QDateEdit(QDate.currentDate())
            else:
                self.dt_edit = QDateEdit(QDate.currentDate())
            self.dt_edit.setCalendarPopup(True)

        form.addRow("📅 Fecha:", self.dt_edit)

        # Tickets en Local
        self.spn_t = QSpinBox()
        self.spn_t.setRange(0, 9999)
        self.spn_t.setValue(self.consumo.tickets_local if self.consumo else 0)
        form.addRow("🎫 Tickets en Local:", self.spn_t)

        # Vales en Local
        self.spn_v = QSpinBox()
        self.spn_v.setRange(0, 9999)
        self.spn_v.setValue(self.consumo.vales_local if self.consumo else 0)
        form.addRow("🎟️ Vales en Local:", self.spn_v)

        # Observación
        self.txt_obs = QLineEdit(self.consumo.observacion if (self.consumo and self.consumo.observacion) else "")
        self.txt_obs.setPlaceholderText("Observaciones o notas del consumo...")
        form.addRow("📝 Observación:", self.txt_obs)

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

        btn_save = QPushButton("💾 Guardar Consumo")
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
        btn_save.clicked.connect(self.accept)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)

    def get_data(self):
        fecha_str = self.dt_edit.date().toString("yyyy-MM-dd")
        return fecha_str, self.spn_t.value(), self.spn_v.value(), self.txt_obs.text().strip() or None


class FastFoodView(QWidget):
    """
    Vista de Consumos Fast Food (CRUD Completo):
    - Creación y edición protegida sin posibilidad de sobreescritura accidental en celdas.
    - NoEditTriggers activo en la tabla.
    - Botones dedicados '✏️' (Editar) y '🗑️' (Eliminar).
    """
    def __init__(self, fast_food_service: Optional[FastFoodService] = None, mes_service: Optional[MesService] = None, parent=None):
        super().__init__(parent)
        self.ff_service = fast_food_service or FastFoodService()
        self.mes_service = mes_service or MesService()
        self.current_year = 2026
        self.current_month = 9
        self._init_ui()

    def set_local(self, local_id: str):
        self.refresh_data()

    def set_periodo(self, anio: int, mes: int):
        self.current_year = anio
        self.current_month = mes
        self.refresh_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("🍔 CONSUMO LOCAL FAST FOOD (Tickets y Vales)")
        title.setStyleSheet("font-size: 18px; font-weight: 900; color: #FFFFFF;")
        header.addWidget(title)

        header.addStretch()

        header.addWidget(QLabel("Período:"))
        self.combo_periodo = QComboBox()
        self.combo_periodo.setStyleSheet("""
            QComboBox {
                background-color: #141414;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 12px;
            }
        """)
        self.combo_periodo.currentIndexChanged.connect(self._on_periodo_changed)
        header.addWidget(self.combo_periodo)

        btn_add = QPushButton("➕ Registrar Consumo Día")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
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
        btn_add.clicked.connect(self._add_consumo)
        header.addWidget(btn_add)

        btn_edit_sel = QPushButton("✏️ Editar Consumo")
        btn_edit_sel.setCursor(Qt.PointingHandCursor)
        btn_edit_sel.setStyleSheet("""
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
        btn_edit_sel.clicked.connect(self._edit_consumo_selected)
        header.addWidget(btn_edit_sel)

        btn_del_sel = QPushButton("🗑️ Eliminar Consumo")
        btn_del_sel.setCursor(Qt.PointingHandCursor)
        btn_del_sel.setStyleSheet("""
            QPushButton {
                background-color: #271214;
                color: #EF4444;
                border: 1px solid #7F1D1D;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #DC2626;
                color: #FFFFFF;
            }
        """)
        btn_del_sel.clicked.connect(self._del_consumo_selected)
        header.addWidget(btn_del_sel)

        btn_refresh = QPushButton("🔄 Actualizar")
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
            }
        """)
        btn_refresh.clicked.connect(self.refresh_data)
        header.addWidget(btn_refresh)

        layout.addLayout(header)

        # KPI Summary
        kpi_layout = QHBoxLayout()
        self.card_tickets = self._create_kpi_card("Tickets Consumidos en Local", "0", "#38BDF8")
        self.card_vales = self._create_kpi_card("Vales Consumidos en Local", "0", "#F59E0B")
        self.card_total = self._create_kpi_card("TOTAL CONSUMOS LOCAL", "0", "#10B981")

        kpi_layout.addWidget(self.card_tickets)
        kpi_layout.addWidget(self.card_vales)
        kpi_layout.addWidget(self.card_total)
        layout.addLayout(kpi_layout)

        # Table
        self.table = QTableWidget()
        headers = ["Fecha", "Tickets en Local", "Vales en Local", "TOTAL CONSUMIDO", "Observación", "Última Actualización", "Acciones"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 95)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self._on_table_double_clicked)
        layout.addWidget(self.table)

        self._load_periodos()

    def _create_kpi_card(self, title: str, value: str, border_color: str) -> QWidget:
        w = QFrame()
        w.setStyleSheet(f"background: #141414; border: 1px solid #262626; border-left: 4px solid {border_color}; border-radius: 8px; padding: 8px;")
        l = QVBoxLayout(w)
        l.setContentsMargins(10, 6, 10, 6)
        l.setSpacing(2)
        lbl_t = QLabel(title.upper())
        lbl_t.setStyleSheet("color: #A1A1AA; font-size: 10px; font-weight: 800; letter-spacing: 0.5px;")
        lbl_v = QLabel(value)
        lbl_v.setObjectName("val")
        lbl_v.setStyleSheet(f"color: {border_color}; font-size: 18px; font-weight: 900;")
        l.addWidget(lbl_t)
        l.addWidget(lbl_v)
        return w

    def _update_kpi(self, card: QWidget, text: str):
        lbl = card.findChild(QLabel, "val")
        if lbl:
            lbl.setText(text)

    def _load_periodos(self):
        self.combo_periodo.blockSignals(True)
        self.combo_periodo.clear()
        meses = self.mes_service.get_all()
        for m in meses:
            self.combo_periodo.addItem(m.display_name, (m.anio, m.mes))
        if not meses:
            self.combo_periodo.addItem("SEPTIEMBRE 2026", (2026, 9))
        self.combo_periodo.blockSignals(False)
        self.refresh_data()

    def _on_periodo_changed(self, idx):
        data = self.combo_periodo.currentData()
        if data:
            self.current_year, self.current_month = data
            self.refresh_data()

    def refresh_data(self):
        anio, mes = self.current_year, self.current_month
        res = self.ff_service.get_resumen_mes(anio, mes)
        self._update_kpi(self.card_tickets, str(res["total_tickets_local"]))
        self._update_kpi(self.card_vales, str(res["total_vales_local"]))
        self._update_kpi(self.card_total, str(res["total_consumido"]))

        consumos = self.ff_service.get_by_mes(anio, mes)
        self.table.setRowCount(len(consumos))
        for r, c in enumerate(consumos):
            self.table.setItem(r, 0, QTableWidgetItem(c.fecha))
            self.table.setItem(r, 1, QTableWidgetItem(str(c.tickets_local)))
            self.table.setItem(r, 2, QTableWidgetItem(str(c.vales_local)))
            self.table.setItem(r, 3, QTableWidgetItem(str(c.total_consumido)))
            self.table.setItem(r, 4, QTableWidgetItem(c.observacion or ""))
            self.table.setItem(r, 5, QTableWidgetItem(c.fecha_actualizacion or ""))

            # Acciones dedicadas
            action_box = QWidget()
            action_layout = QHBoxLayout(action_box)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(4)

            btn_edit = QPushButton("✏️")
            btn_edit.setToolTip("Editar consumo de este día")
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
            f_val = c.fecha
            btn_edit.clicked.connect(lambda ch, f=f_val: self._edit_consumo(f))
            action_layout.addWidget(btn_edit)

            btn_del = QPushButton("🗑️")
            btn_del.setToolTip("Eliminar consumo de este día")
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
            btn_del.clicked.connect(lambda ch, f=f_val: self._del_consumo(f))
            action_layout.addWidget(btn_del)

            self.table.setCellWidget(r, 6, action_box)

    def _on_table_double_clicked(self, row: int, col: int):
        item = self.table.item(row, 0)
        if item and item.text():
            self._edit_consumo(item.text())

    def _add_consumo(self):
        default_f = f"{self.current_year:04d}-{self.current_month:02d}-01"
        dlg = EditarFastFoodDialog(consumo=None, fecha_default=default_f, parent=self)
        if dlg.exec() == QDialog.Accepted:
            fecha, tickets, vales, obs = dlg.get_data()
            ok, msg, _ = self.ff_service.guardar_consumo(fecha, tickets, vales, obs)
            if ok:
                ToastManager.show_success(f"Consumo de {fecha} guardado", self)
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Error", msg)

    def _edit_consumo(self, fecha: str):
        c = self.ff_service.get_by_fecha(fecha)
        if not c:
            return
        dlg = EditarFastFoodDialog(consumo=c, parent=self)
        if dlg.exec() == QDialog.Accepted:
            f, tickets, vales, obs = dlg.get_data()
            ok, msg, _ = self.ff_service.guardar_consumo(f, tickets, vales, obs)
            if ok:
                ToastManager.show_success(f"Consumo de {f} actualizado", self)
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Error", msg)

    def _edit_consumo_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atención", "Seleccione un consumo de la lista para editar.")
            return
        item = self.table.item(row, 0)
        if item and item.text():
            self._edit_consumo(item.text())

    def _del_consumo(self, fecha: str):
        if QMessageBox.question(self, "Confirmar", f"¿Desea eliminar el registro de consumo del {fecha}?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            ok, msg = self.ff_service.eliminar_consumo(fecha)
            if ok:
                ToastManager.show_info(f"Consumo del {fecha} eliminado", self)
                self.refresh_data()
            else:
                QMessageBox.warning(self, "Error", msg)

    def _del_consumo_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atención", "Seleccione un consumo de la lista para eliminar.")
            return
        item = self.table.item(row, 0)
        if item and item.text():
            self._del_consumo(item.text())
