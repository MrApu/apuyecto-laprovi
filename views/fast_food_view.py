from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QMessageBox, QSpinBox,
    QDialog, QFormLayout, QDialogButtonBox, QDateEdit, QLineEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor
from typing import Optional

from services.fast_food_service import FastFoodService
from services.mes_service import MesService
from models.fast_food_consumo import FastFoodConsumo

class FastFoodView(QWidget):
    def __init__(self, fast_food_service: Optional[FastFoodService] = None, mes_service: Optional[MesService] = None, parent=None):
        super().__init__(parent)
        self.ff_service = fast_food_service or FastFoodService()
        self.mes_service = mes_service or MesService()
        self.current_year = 2026
        self.current_month = 9
        self._init_ui()

    def set_local(self, local_id: str):
        # Specific to Fast Food
        self.refresh_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("🍔 CONSUMO LOCAL FAST FOOD (Tickets y Vales en Local)")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header.addWidget(title)

        header.addStretch()

        header.addWidget(QLabel("Período:"))
        self.combo_periodo = QComboBox()
        self.combo_periodo.currentIndexChanged.connect(self._on_periodo_changed)
        header.addWidget(self.combo_periodo)

        btn_add = QPushButton("➕ Registrar Consumo Día")
        btn_add.setStyleSheet("background: #d97706; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
        btn_add.clicked.connect(self._add_consumo)
        header.addWidget(btn_add)

        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.clicked.connect(self.refresh_data)
        header.addWidget(btn_refresh)

        layout.addLayout(header)

        # KPI Summary
        kpi_layout = QHBoxLayout()
        self.card_tickets = self._create_kpi_card("Tickets Consumidos en Local", "0", "#38bdf8")
        self.card_vales = self._create_kpi_card("Vales Consumidos en Local", "0", "#f59e0b")
        self.card_total = self._create_kpi_card("TOTAL CONSUMOS LOCAL", "0", "#10b981")

        kpi_layout.addWidget(self.card_tickets)
        kpi_layout.addWidget(self.card_vales)
        kpi_layout.addWidget(self.card_total)
        layout.addLayout(kpi_layout)

        # Table
        self.table = QTableWidget()
        headers = ["Fecha", "Tickets en Local", "Vales en Local", "TOTAL CONSUMIDO", "Observación", "Última Actualización"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self._load_periodos()

    def _create_kpi_card(self, title: str, value: str, border_color: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: #0f172a; border-left: 4px solid {border_color}; border-radius: 6px; padding: 8px;")
        l = QVBoxLayout(w)
        l.setContentsMargins(8, 6, 8, 6)
        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")
        lbl_v = QLabel(value)
        lbl_v.setObjectName("val")
        lbl_v.setStyleSheet(f"color: {border_color}; font-size: 18px; font-weight: bold;")
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

    def _add_consumo(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Registrar Consumo Local Fast Food")
        layout = QFormLayout(dlg)

        dt_edit = QDateEdit(QDate(self.current_year, self.current_month, 1))
        dt_edit.setCalendarPopup(True)
        layout.addRow("Fecha:", dt_edit)

        spn_t = QSpinBox()
        spn_t.setRange(0, 9999)
        layout.addRow("Tickets en Local:", spn_t)

        spn_v = QSpinBox()
        spn_v.setRange(0, 9999)
        layout.addRow("Vales en Local:", spn_v)

        txt_obs = QLineEdit()
        layout.addRow("Observación:", txt_obs)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addRow(btns)

        if dlg.exec() == QDialog.Accepted:
            self.ff_service.guardar_consumo(
                fecha=dt_edit.date().toString("yyyy-MM-dd"),
                tickets_local=spn_t.value(),
                vales_local=spn_v.value(),
                observacion=txt_obs.text().strip() or None
            )
            self.refresh_data()
