from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt
from typing import Optional
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

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
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        # Title Bar
        header_box = QHBoxLayout()
        self.lbl_title = QLabel("📊 DASHBOARD Y ANÁLISIS DE GESTIÓN INTEGRAL")
        self.lbl_title.setStyleSheet("font-size: 19px; font-weight: bold; color: #1F4E78;")
        header_box.addWidget(self.lbl_title)

        self.lbl_local = QLabel(f"Local: {LOCAL_NAMES.get(self.current_local, 'RESTAURANTE')}")
        self.lbl_local.setStyleSheet("background: #1e293b; color: #38bdf8; padding: 6px 14px; border-radius: 6px; font-weight: bold; font-size: 13px;")
        header_box.addWidget(self.lbl_local)

        header_box.addStretch()

        self.btn_refresh = QPushButton("🔄 Actualizar Datos")
        self.btn_refresh.setProperty("class", "PrimaryBtn")
        self.btn_refresh.setStyleSheet("font-size: 13px; padding: 6px 16px;")
        self.btn_refresh.clicked.connect(self.cargar_datos)
        header_box.addWidget(self.btn_refresh)
        main_layout.addLayout(header_box)

        # Scroll Area for high-resolution analysis
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(4, 4, 4, 14)
        self.content_layout.setSpacing(18)

        # KPI Grid
        self.kpi_grid = QGridLayout()
        self.kpi_grid.setSpacing(10)
        self._setup_kpi_cards()
        self.content_layout.addLayout(self.kpi_grid)

        # Charts Area (Expanded & High Definition)
        self._setup_charts_area()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def _setup_kpi_cards(self):
        self.cards = {}
        kpi_defs = [
            ("venta_total", "VENTA TOTAL DEL MES", "S/ 0.00", "#10b981", "16px"),
            ("total_egresos", "TOTAL EGRESOS ACUMULADOS", "S/ 0.00", "#ef4444", "16px"),
            ("saldo_neto", "SALDO NETO (UTILIDAD)", "S/ 0.00", "#0284c7", "16px"),
            ("rentabilidad", "RENTABILIDAD SOBRE VENTAS", "0.0%", "#f59e0b", "16px"),
            ("total_compras", "COMPRAS / INSUMOS", "S/ 0.00", "#3b82f6", "14px"),
            ("total_gastos", "GASTOS OPERATIVOS", "S/ 0.00", "#d97706", "14px"),
            ("total_personal", "PAGOS AL PERSONAL", "S/ 0.00", "#8b5cf6", "14px"),
            ("venta_sin_tickets", "VENTA SIN TICKETS (EF+YP)", "S/ 0.00", "#059669", "14px"),
            ("total_policias", "CANTIDAD TICKETS POLICIALES", "0", "#1565C0", "14px"),
            ("venta_policial", "VALOR TICKETS POLICIALES", "S/ 0.00", "#2E7D32", "14px"),
            ("tickets_unidad", "TICKETS PARA UNIDAD", "0", "#475569", "14px"),
            ("tickets_local", "TICKETS DENTRO LOCAL", "0", "#475569", "14px"),
            ("vales_entregados", "VALES ENTREGADOS", "0", "#E65100", "14px"),
            ("vales_canjeados", "VALES CANJEADOS", "0", "#EF6C00", "14px"),
            ("saldo_vales", "SALDO VALES EN CIRCULACIÓN", "0", "#F57F17", "14px"),
            ("monto_pendiente", "DEUDA PENDIENTE COBRO", "S/ 0.00", "#dc2626", "14px"),
        ]

        row, col = 0, 0
        for key, title, default_val, color, font_sz in kpi_defs:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: #0f172a;
                    border: 1px solid #1e293b;
                    border-left: 5px solid {color};
                    border-radius: 8px;
                    padding: 4px;
                }}
            """)
            card_l = QVBoxLayout(card)
            card_l.setContentsMargins(10, 8, 10, 8)
            card_l.setSpacing(3)

            lbl_t = QLabel(title)
            lbl_t.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold; letter-spacing: 0.5px;")
            lbl_v = QLabel(default_val)
            lbl_v.setStyleSheet(f"color: {color}; font-size: {font_sz}; font-weight: bold;")

            card_l.addWidget(lbl_t)
            card_l.addWidget(lbl_v)

            self.cards[key] = lbl_v
            self.kpi_grid.addWidget(card, row, col)

            col += 1
            if col >= 4:
                col = 0
                row += 1

    def _setup_charts_area(self):
        # 1. Main Large Chart: Balance Financiero Completo (Venta Total, Sin Tickets, Egresos y Saldo)
        self.fig_fin, self.ax_fin = plt.subplots(figsize=(12, 4.2), dpi=100)
        self.fig_fin.subplots_adjust(left=0.06, right=0.96, top=0.90, bottom=0.15)
        self.canvas_fin = FigureCanvas(self.fig_fin)
        self.canvas_fin.setMinimumHeight(380)
        self.content_layout.addWidget(
            self._wrap_chart("📈 1. EVOLUCIÓN FINANCIERA DIARIA (Venta Total, Venta Sin Tickets, Egresos y Saldo Neto)", self.canvas_fin)
        )

        # 2-Column Grid for Detailed Breakdown Charts
        grid_charts = QGridLayout()
        grid_charts.setSpacing(16)

        # Chart 2: Composición de Ingresos Diarios (Efectivo vs Yape vs Tickets)
        self.fig_ing, self.ax_ing = plt.subplots(figsize=(6.2, 3.8), dpi=100)
        self.fig_ing.subplots_adjust(left=0.10, right=0.95, top=0.88, bottom=0.15)
        self.canvas_ing = FigureCanvas(self.fig_ing)
        self.canvas_ing.setMinimumHeight(340)
        grid_charts.addWidget(
            self._wrap_chart("💵 2. ESTRUCTURA DE INGRESOS (Efectivo, Yape y Tickets Policiales)", self.canvas_ing), 0, 0
        )

        # Chart 3: Desglose de Egresos por Categoría (Compras, Gastos, Personal)
        self.fig_egr, self.ax_egr = plt.subplots(figsize=(6.2, 3.8), dpi=100)
        self.fig_egr.subplots_adjust(left=0.10, right=0.95, top=0.88, bottom=0.15)
        self.canvas_egr = FigureCanvas(self.fig_egr)
        self.canvas_egr.setMinimumHeight(340)
        grid_charts.addWidget(
            self._wrap_chart("📉 3. DESGLOSE DE EGRESOS (Compras de Insumos, Gastos y Pagos Personal)", self.canvas_egr), 0, 1
        )

        # Chart 4: Demanda y Distribución Policial (Unidad vs Local)
        self.fig_pol, self.ax_pol = plt.subplots(figsize=(6.2, 3.8), dpi=100)
        self.fig_pol.subplots_adjust(left=0.10, right=0.95, top=0.88, bottom=0.15)
        self.canvas_pol = FigureCanvas(self.fig_pol)
        self.canvas_pol.setMinimumHeight(340)
        grid_charts.addWidget(
            self._wrap_chart("👮 4. CONTROL DE TICKETS POLICIALES (Para Unidad vs Dentro del Local)", self.canvas_pol), 1, 0
        )

        # Chart 5: Control de Cobranzas y Vales (Pagados vs Debidos & Vales)
        self.fig_val, self.ax_val = plt.subplots(figsize=(6.2, 3.8), dpi=100)
        self.fig_val.subplots_adjust(left=0.10, right=0.95, top=0.88, bottom=0.15)
        self.canvas_val = FigureCanvas(self.fig_val)
        self.canvas_val.setMinimumHeight(340)
        grid_charts.addWidget(
            self._wrap_chart("🎫 5. ESTADO DE COBRANZAS (Pagados vs Debidos) Y FLUJO DE VALES", self.canvas_val), 1, 1
        )

        self.content_layout.addLayout(grid_charts)

    def _wrap_chart(self, title_text: str, canvas: FigureCanvas) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        l = QVBoxLayout(frame)
        l.setContentsMargins(8, 8, 8, 8)
        l.setSpacing(8)

        lbl = QLabel(title_text)
        lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #38bdf8;")
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
        self.cards["saldo_neto"].setStyleSheet(f"color: {color_saldo}; font-size: 16px; font-weight: bold;")
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

        x = np.arange(len(dias))

        # --- 1. Main Large Chart: Balance Financiero ---
        self.ax_fin.clear()
        v_tot = np.array(s.get("ventas_total", []))
        v_sin_pol = np.array(s.get("venta_sin_policias", []))
        egr = np.array(s.get("egresos_total", []))
        saldos = np.array(s.get("saldos_netos", []))

        self.ax_fin.plot(x, v_tot, label="Venta Total (Inc. Tickets)", color="#10b981", marker='o', linewidth=2.5, markersize=5)
        self.ax_fin.plot(x, v_sin_pol, label="Venta Sin Tickets (EF+YP)", color="#06b6d4", linestyle="--", linewidth=2.0, alpha=0.9)
        self.ax_fin.plot(x, egr, label="Total Egresos", color="#ef4444", marker='s', linewidth=2.2, markersize=5)
        self.ax_fin.plot(x, saldos, label="Saldo Neto Diario", color="#818cf8", marker='^', linewidth=2.0, markersize=5)
        self.ax_fin.fill_between(x, saldos, 0, where=(saldos >= 0), color="#10b981", alpha=0.12, interpolate=True)
        self.ax_fin.fill_between(x, saldos, 0, where=(saldos < 0), color="#ef4444", alpha=0.15, interpolate=True)

        self._style_axis(self.ax_fin, self.fig_fin, x, dias, is_currency=True)
        self.ax_fin.legend(fontsize=9, facecolor='#1e293b', edgecolor='#334155', labelcolor='white', loc='upper left', framealpha=0.9)
        self.canvas_fin.draw()

        # --- 2. Composición de Ingresos (Efectivo vs Yape vs Tickets) ---
        self.ax_ing.clear()
        ef = np.array(s.get("efectivo", []))
        yp = np.array(s.get("yape", []))
        vtick = np.array(s.get("venta_tickets", []))

        self.ax_ing.bar(x, ef, label="Efectivo", color="#10b981", width=0.65, alpha=0.9)
        self.ax_ing.bar(x, yp, bottom=ef, label="Yape", color="#a855f7", width=0.65, alpha=0.9)
        self.ax_ing.bar(x, vtick, bottom=ef + yp, label="Venta Tickets (S/ 12)", color="#3b82f6", width=0.65, alpha=0.9)

        self._style_axis(self.ax_ing, self.fig_ing, x, dias, is_currency=True)
        self.ax_ing.legend(fontsize=8, facecolor='#1e293b', edgecolor='#334155', labelcolor='white', loc='upper left', framealpha=0.9)
        self.canvas_ing.draw()

        # --- 3. Desglose de Egresos (Compras vs Gastos vs Personal) ---
        self.ax_egr.clear()
        comp = np.array(s.get("compras", []))
        gast = np.array(s.get("gastos", []))
        pers = np.array(s.get("personal", []))

        self.ax_egr.bar(x, comp, label="Compras/Insumos", color="#f97316", width=0.65, alpha=0.9)
        self.ax_egr.bar(x, gast, bottom=comp, label="Gastos Operativos", color="#f59e0b", width=0.65, alpha=0.9)
        self.ax_egr.bar(x, pers, bottom=comp + gast, label="Pagos Personal", color="#ec4899", width=0.65, alpha=0.9)

        self._style_axis(self.ax_egr, self.fig_egr, x, dias, is_currency=True)
        self.ax_egr.legend(fontsize=8, facecolor='#1e293b', edgecolor='#334155', labelcolor='white', loc='upper left', framealpha=0.9)
        self.canvas_egr.draw()

        # --- 4. Tickets Policiales (Para Unidad vs Local) ---
        self.ax_pol.clear()
        u = np.array(s.get("para_unidad", []))
        l = np.array(s.get("local", []))

        self.ax_pol.bar(x, u, label="Para Unidad", color="#3b82f6", width=0.65, alpha=0.9)
        self.ax_pol.bar(x, l, bottom=u, label="Dentro del Local", color="#06b6d4", width=0.65, alpha=0.9)

        self._style_axis(self.ax_pol, self.fig_pol, x, dias, is_currency=False)
        self.ax_pol.legend(fontsize=8, facecolor='#1e293b', edgecolor='#334155', labelcolor='white', loc='upper left', framealpha=0.9)
        self.canvas_pol.draw()

        # --- 5. Estado de Cobranzas y Vales ---
        self.ax_val.clear()
        pag = np.array(s.get("tickets_pagados", []))
        deb = np.array(s.get("tickets_debidos", []))
        val_ent = np.array(s.get("vales_entregados", []))
        val_can = np.array(s.get("vales_canjeados", []))

        # Combine bars for pagados/debidos and line for vales
        self.ax_val.bar(x - 0.15, pag, width=0.3, label="Tickets Pagados", color="#10b981", alpha=0.85)
        self.ax_val.bar(x + 0.15, deb, width=0.3, label="Tickets Debidos", color="#ef4444", alpha=0.85)
        self.ax_val.plot(x, val_can, label="Vales Canjeados", color="#eab308", marker='o', linewidth=2, markersize=4)

        self._style_axis(self.ax_val, self.fig_val, x, dias, is_currency=False)
        self.ax_val.legend(fontsize=8, facecolor='#1e293b', edgecolor='#334155', labelcolor='white', loc='upper left', framealpha=0.9)
        self.canvas_val.draw()

    def _style_axis(self, ax, fig, x_ticks, labels, is_currency: bool = False):
        ax.set_facecolor('#0f172a')
        fig.patch.set_facecolor('#0f172a')
        ax.set_xticks(x_ticks)
        ax.set_xticklabels([f"Día {lbl}" if int(lbl) % 2 == 1 or len(labels) <= 15 else lbl for lbl in labels], rotation=0)
        ax.tick_params(colors='#94a3b8', labelsize=8)

        if is_currency:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, loc: f"S/ {val:,.0f}"))
        else:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, loc: f"{int(val):,d}"))

        ax.grid(True, linestyle=':', alpha=0.35, color='#334155')
        for spine in ax.spines.values():
            spine.set_color('#1e293b')
