from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from typing import Optional

from services.financiero_service import FinancieroService
from services.mes_service import MesService
from models.local import LOCAL_RESTAURANTE, LOCAL_FAST_FOOD, LOCAL_CONSOLIDADO, LOCAL_NAMES

class CalendarioFinancieroView(QWidget):
    def __init__(self, financiero_service: Optional[FinancieroService] = None, mes_service: Optional[MesService] = None, parent=None):
        super().__init__(parent)
        self.financiero_service = financiero_service or FinancieroService()
        self.mes_service = mes_service or MesService()
        self.current_local = LOCAL_RESTAURANTE
        self.current_year = 2026
        self.current_month = 9
        self._init_ui()

    def set_local(self, local_id: str):
        self.current_local = local_id
        self.lbl_local_badge.setText(f"Local: {LOCAL_NAMES.get(local_id, local_id.upper())}")
        self.refresh_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("📅 CALENDARIO FINANCIERO Y SALDO DIARIO")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header.addWidget(title)

        self.lbl_local_badge = QLabel(f"Local: {LOCAL_NAMES.get(self.current_local, 'RESTAURANTE')}")
        self.lbl_local_badge.setStyleSheet("background: #1e293b; color: #38bdf8; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
        header.addWidget(self.lbl_local_badge)

        header.addStretch()

        header.addWidget(QLabel("Período:"))
        self.combo_periodo = QComboBox()
        self.combo_periodo.currentIndexChanged.connect(self._on_periodo_changed)
        header.addWidget(self.combo_periodo)

        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.clicked.connect(self.refresh_data)
        header.addWidget(btn_refresh)

        layout.addLayout(header)

        # KPI Summary Cards
        kpi_layout = QHBoxLayout()
        self.card_ventas = self._create_kpi_card("Total Ventas", "S/ 0.00", "#10b981")
        self.card_egresos = self._create_kpi_card("Total Egresos", "S/ 0.00", "#ef4444")
        self.card_saldo = self._create_kpi_card("Saldo Neto", "S/ 0.00", "#38bdf8")
        self.card_rentabilidad = self._create_kpi_card("Rentabilidad", "0.0%", "#f59e0b")

        kpi_layout.addWidget(self.card_ventas)
        kpi_layout.addWidget(self.card_egresos)
        kpi_layout.addWidget(self.card_saldo)
        kpi_layout.addWidget(self.card_rentabilidad)
        layout.addLayout(kpi_layout)

        # Table
        self.table = QTableWidget()
        headers = [
            "Fecha", "Día", "Semana", "Efectivo (S/)", "Yape (S/)", "Tickets (Cant)",
            "Venta Tickets (S/)", "Venta Total (S/)", "Compras (S/)", "Gastos (S/)",
            "Personal (S/)", "Total Egresos (S/)", "SALDO DEL DÍA (S/)"
        ]
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
        lbl_v.setStyleSheet(f"color: {border_color}; font-size: 16px; font-weight: bold;")
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
        local = self.current_local

        # 1. Update KPIs
        res = self.financiero_service.get_resumen_financiero_mes(anio, mes, local)
        self._update_kpi(self.card_ventas, f"S/ {res['total_ventas']:,.2f}")
        self._update_kpi(self.card_egresos, f"S/ {res['total_egresos']:,.2f}")
        
        saldo = res["saldo_neto"]
        saldo_card_color = "#10b981" if saldo >= 0 else "#ef4444"
        self._update_kpi(self.card_saldo, f"S/ {saldo:,.2f}")
        self._update_kpi(self.card_rentabilidad, f"{res['rentabilidad_pct']:.1f}%")

        # 2. Populate Table
        dias = self.financiero_service.get_calendario_financiero_mes(anio, mes, local)
        self.table.setRowCount(len(dias))

        for r, d in enumerate(dias):
            self.table.setItem(r, 0, QTableWidgetItem(d["fecha"]))
            self.table.setItem(r, 1, QTableWidgetItem(str(d["dia"])))
            self.table.setItem(r, 2, QTableWidgetItem(d["dia_semana"]))
            self.table.setItem(r, 3, QTableWidgetItem(f"{d['efectivo']:,.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{d['yape']:,.2f}"))
            self.table.setItem(r, 5, QTableWidgetItem(str(d["cantidad_tickets"])))
            self.table.setItem(r, 6, QTableWidgetItem(f"{d['venta_tickets']:,.2f}"))
            self.table.setItem(r, 7, QTableWidgetItem(f"{d['venta_total']:,.2f}"))
            self.table.setItem(r, 8, QTableWidgetItem(f"{d['compras']:,.2f}"))
            self.table.setItem(r, 9, QTableWidgetItem(f"{d['gastos']:,.2f}"))
            self.table.setItem(r, 10, QTableWidgetItem(f"{d['personal']:,.2f}"))
            self.table.setItem(r, 11, QTableWidgetItem(f"{d['total_egresos']:,.2f}"))

            saldo_item = QTableWidgetItem(f"S/ {d['saldo']:,.2f}")
            saldo_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            if d['saldo'] > 0:
                saldo_item.setForeground(QColor("#10b981"))
            elif d['saldo'] < 0:
                saldo_item.setForeground(QColor("#ef4444"))
            else:
                saldo_item.setForeground(QColor("#94a3b8"))

            self.table.setItem(r, 12, saldo_item)
