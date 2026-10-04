from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QScrollArea, QComboBox, QPushButton
)
from PySide6.QtCore import Qt
from typing import Optional
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from services.dashboard_service import DashboardService
from models.local import LOCAL_RESTAURANTE, LOCAL_NAMES

class DashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dashboard_service = DashboardService()
        self.current_local = LOCAL_RESTAURANTE
        self.current_anio = 2026
        self.current_mes = 9
        self._init_ui()

    def set_local(self, local_id: str):
        self.current_local = local_id
        self.lbl_local.setText(f"Local: {LOCAL_NAMES.get(local_id, local_id.upper())}")
        self.cargar_datos()

    def set_periodo(self, anio: int, mes: int):
        self.current_anio = anio
        self.current_mes = mes
        self.cargar_datos()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # Title Bar
        header_box = QHBoxLayout()
        self.lbl_title = QLabel("📊 DASHBOARD Y RESUMEN GENERAL")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1F4E78;")
        header_box.addWidget(self.lbl_title)

        self.lbl_local = QLabel(f"Local: {LOCAL_NAMES.get(self.current_local, 'RESTAURANTE')}")
        self.lbl_local.setStyleSheet("background: #1e293b; color: #38bdf8; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
        header_box.addWidget(self.lbl_local)

        header_box.addStretch()

        self.btn_refresh = QPushButton("🔄 Actualizar")
        self.btn_refresh.setProperty("class", "PrimaryBtn")
        self.btn_refresh.clicked.connect(self.cargar_datos)
        header_box.addWidget(self.btn_refresh)
        main_layout.addLayout(header_box)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(14)

        # KPI Grid
        self.kpi_grid = QGridLayout()
        self.kpi_grid.setSpacing(10)
        self._setup_kpi_cards()
        self.content_layout.addLayout(self.kpi_grid)

        # Charts Area
        self.charts_layout = QGridLayout()
        self.charts_layout.setSpacing(14)
        self._setup_charts_area()
        self.content_layout.addLayout(self.charts_layout)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def _setup_kpi_cards(self):
        self.cards = {}
        kpi_defs = [
            ("venta_total", "VENTA TOTAL", "S/ 0.00", "#10b981"),
            ("total_egresos", "TOTAL EGRESOS", "S/ 0.00", "#ef4444"),
            ("saldo_neto", "SALDO NETO (UTILIDAD)", "S/ 0.00", "#0284c7"),
            ("rentabilidad", "RENTABILIDAD", "0.0%", "#f59e0b"),
            ("total_compras", "COMPRAS / INSUMOS", "S/ 0.00", "#3b82f6"),
            ("total_gastos", "GASTOS OPERATIVOS", "S/ 0.00", "#d97706"),
            ("total_personal", "PAGOS AL PERSONAL", "S/ 0.00", "#8b5cf6"),
            ("venta_sin_tickets", "VENTA SIN TICKETS", "S/ 0.00", "#059669"),
            ("total_policias", "TOTAL TICKETS POLICIALES", "0", "#1565C0"),
            ("venta_policial", "VENTA TICKETS POLICIALES", "S/ 0.00", "#2E7D32"),
            ("tickets_unidad", "PARA UNIDAD", "0", "#475569"),
            ("tickets_local", "LOCAL", "0", "#475569"),
            ("vales_entregados", "VALES ENTREGADOS", "0", "#E65100"),
            ("vales_canjeados", "VALES CANJEADOS", "0", "#EF6C00"),
            ("saldo_vales", "SALDO VALES", "0", "#F57F17"),
            ("monto_pendiente", "MONTO PENDIENTE COBRO", "S/ 0.00", "#dc2626"),
        ]

        row, col = 0, 0
        for key, title, default_val, color in kpi_defs:
            card = QFrame()
            card.setStyleSheet(f"background: #0f172a; border-left: 4px solid {color}; border-radius: 6px; padding: 6px;")
            card_l = QVBoxLayout(card)
            card_l.setContentsMargins(8, 6, 8, 6)
            card_l.setSpacing(2)

            lbl_t = QLabel(title)
            lbl_t.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: bold;")
            lbl_v = QLabel(default_val)
            lbl_v.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")

            card_l.addWidget(lbl_t)
            card_l.addWidget(lbl_v)

            self.cards[key] = lbl_v
            self.kpi_grid.addWidget(card, row, col)

            col += 1
            if col >= 4:
                col = 0
                row += 1

    def _setup_charts_area(self):
        # Chart 1: Ventas vs Egresos vs Saldo
        self.fig_fin, self.ax_fin = plt.subplots(figsize=(5.5, 2.8), dpi=80)
        self.canvas_fin = FigureCanvas(self.fig_fin)
        self.charts_layout.addWidget(self._wrap_chart("Balance Financiero Diario (Ventas vs Egresos vs Saldo)", self.canvas_fin), 0, 0)

        # Chart 2: Tickets Policiales
        self.fig_pol, self.ax_pol = plt.subplots(figsize=(5.5, 2.8), dpi=80)
        self.canvas_pol = FigureCanvas(self.fig_pol)
        self.charts_layout.addWidget(self._wrap_chart("Tickets Policiales Diarios (Unidad vs Local)", self.canvas_pol), 0, 1)

        # Chart 3: Vales Entregados vs Canjeados
        self.fig_val, self.ax_val = plt.subplots(figsize=(5.5, 2.8), dpi=80)
        self.canvas_val = FigureCanvas(self.fig_val)
        self.charts_layout.addWidget(self._wrap_chart("Vales Policiales (Entregados vs Canjeados)", self.canvas_val), 1, 0)

        # Chart 4: Pagos vs Debidos
        self.fig_pag, self.ax_pag = plt.subplots(figsize=(5.5, 2.8), dpi=80)
        self.canvas_pag = FigureCanvas(self.fig_pag)
        self.charts_layout.addWidget(self._wrap_chart("Estado de Tickets (Pagados vs Debidos)", self.canvas_pag), 1, 1)

    def _wrap_chart(self, title_text: str, canvas: FigureCanvas) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("background: #0f172a; border-radius: 6px; padding: 6px;")
        l = QVBoxLayout(frame)
        l.setContentsMargins(6, 6, 6, 6)
        lbl = QLabel(title_text)
        lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #38bdf8;")
        l.addWidget(lbl)
        l.addWidget(canvas)
        return frame

    def cargar_datos(self):
        data = self.dashboard_service.get_dashboard_data(self.current_anio, self.current_mes, self.current_local)
        k = data.get("kpis", {})

        self.cards["venta_total"].setText(f"S/ {k.get('venta_total', 0.0):,.2f}")
        self.cards["total_egresos"].setText(f"S/ {k.get('total_egresos', 0.0):,.2f}")

        saldo = k.get('saldo_neto', 0.0)
        color_saldo = "#10b981" if saldo >= 0 else "#ef4444"
        self.cards["saldo_neto"].setText(f"S/ {saldo:,.2f}")
        self.cards["saldo_neto"].setStyleSheet(f"color: {color_saldo}; font-size: 14px; font-weight: bold;")
        self.cards["rentabilidad"].setText(f"{k.get('rentabilidad_pct', 0.0):.1f}%")

        self.cards["total_compras"].setText(f"S/ {k.get('total_compras', 0.0):,.2f}")
        self.cards["total_gastos"].setText(f"S/ {k.get('total_gastos', 0.0):,.2f}")
        self.cards["total_personal"].setText(f"S/ {k.get('total_personal', 0.0):,.2f}")

        self.cards["venta_sin_tickets"].setText(f"S/ {k.get('venta_sin_tickets', 0.0):,.2f}")
        self.cards["total_policias"].setText(str(k.get("total_tickets_policiales", 0)))
        self.cards["venta_policial"].setText(f"S/ {k.get('venta_policial_calculada', 0.0):,.2f}")
        self.cards["tickets_unidad"].setText(str(k.get("tickets_para_unidad", 0)))
        self.cards["tickets_local"].setText(str(k.get("tickets_local", 0)))

        self.cards["vales_entregados"].setText(str(k.get("vales_entregados", 0)))
        self.cards["vales_canjeados"].setText(str(k.get("vales_canjeados", 0)))
        self.cards["saldo_vales"].setText(str(k.get("saldo_vales", 0)))
        self.cards["monto_pendiente"].setText(f"S/ {k.get('monto_pendiente', 0.0):,.2f}")

        self._draw_charts(data.get("series", {}))

    def _draw_charts(self, s: dict):
        dias = s.get("dias", [])
        if not dias:
            return

        # 1. Ventas vs Egresos vs Saldo
        self.ax_fin.clear()
        self.ax_fin.plot(dias, s.get("ventas_total", []), label="Ventas", color="#10b981", marker='o', linewidth=2)
        self.ax_fin.plot(dias, s.get("egresos_total", []), label="Egresos", color="#ef4444", marker='s', linewidth=2)
        self.ax_fin.plot(dias, s.get("saldos_netos", []), label="Saldo Diario", color="#38bdf8", linestyle='--', linewidth=1.5)
        self.ax_fin.set_facecolor('#0f172a')
        self.ax_fin.tick_params(colors='#94a3b8', labelsize=7)
        self.ax_fin.legend(fontsize=7, facecolor='#1e293b', edgecolor='none', labelcolor='white')
        self.ax_fin.grid(True, linestyle=':', alpha=0.3, color='#334155')
        self.fig_fin.patch.set_facecolor('#0f172a')
        self.canvas_fin.draw()

        # 2. Tickets Unidad vs Local
        self.ax_pol.clear()
        self.ax_pol.bar(dias, s.get("para_unidad", []), label="Unidad", color="#3b82f6", alpha=0.8)
        self.ax_pol.bar(dias, s.get("local", []), bottom=s.get("para_unidad", []), label="Local", color="#06b6d4", alpha=0.8)
        self.ax_pol.set_facecolor('#0f172a')
        self.ax_pol.tick_params(colors='#94a3b8', labelsize=7)
        self.ax_pol.legend(fontsize=7, facecolor='#1e293b', edgecolor='none', labelcolor='white')
        self.ax_pol.grid(True, linestyle=':', alpha=0.3, color='#334155')
        self.fig_pol.patch.set_facecolor('#0f172a')
        self.canvas_pol.draw()

        # 3. Vales Entregados vs Canjeados
        self.ax_val.clear()
        self.ax_val.plot(dias, s.get("vales_entregados", []), label="Entregados", color="#f97316", marker='o')
        self.ax_val.plot(dias, s.get("vales_canjeados", []), label="Canjeados", color="#eab308", marker='x')
        self.ax_val.set_facecolor('#0f172a')
        self.ax_val.tick_params(colors='#94a3b8', labelsize=7)
        self.ax_val.legend(fontsize=7, facecolor='#1e293b', edgecolor='none', labelcolor='white')
        self.ax_val.grid(True, linestyle=':', alpha=0.3, color='#334155')
        self.fig_val.patch.set_facecolor('#0f172a')
        self.canvas_val.draw()

        # 4. Tickets Pagados vs Debidos
        self.ax_pag.clear()
        self.ax_pag.bar(dias, s.get("tickets_pagados", []), label="Pagados", color="#10b981", alpha=0.8)
        self.ax_pag.bar(dias, s.get("tickets_debidos", []), bottom=s.get("tickets_pagados", []), label="Debidos", color="#ef4444", alpha=0.8)
        self.ax_pag.set_facecolor('#0f172a')
        self.ax_pag.tick_params(colors='#94a3b8', labelsize=7)
        self.ax_pag.legend(fontsize=7, facecolor='#1e293b', edgecolor='none', labelcolor='white')
        self.ax_pag.grid(True, linestyle=':', alpha=0.3, color='#334155')
        self.fig_pag.patch.set_facecolor('#0f172a')
        self.canvas_pag.draw()
