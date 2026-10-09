from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QTabWidget, QTabBar, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt
from typing import Optional, Dict, Any
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

from services.dashboard_service import DashboardService
from models.local import LOCAL_RESTAURANTE, LOCAL_FAST_FOOD, LOCAL_CONSOLIDADO, LOCAL_NAMES
from views.components.toast import ToastManager

class DashboardView(QWidget):
    """
    Dashboard Modular BI inspirado en Tremor.so / Tailwind Admin:
    - Paleta Slate Oscura & Neón Suave (#090D16, #111827, #1F2937)
    - Tarjetas KPI modulares con Badges e Indicadores de Rendimiento
    - Pestañas Segmentadas para Análisis Profundo por Módulo
    - Gráficos Panorámicos en Alta Resolución (HD) con Degradados Suaves
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dashboard_service = DashboardService()
        self.current_local = LOCAL_RESTAURANTE
        self.current_anio = 2026
        self.current_mes = 9
        self.cached_data = {}
        self._init_ui()

    def set_local(self, local_id: str):
        self.current_local = local_id
        self.lbl_local.setText(f"📍 Sede: {LOCAL_NAMES.get(local_id, local_id.upper())}")
        self.cargar_datos()

    def set_periodo(self, anio: int, mes: int):
        self.current_anio = anio
        self.current_mes = mes
        self.cargar_datos()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)
        self.setStyleSheet("background-color: #090D16; font-family: 'Segoe UI', Arial, sans-serif;")

        # Header Bar
        header_box = QHBoxLayout()
        self.lbl_title = QLabel("📊 DASHBOARD MODULAR BI — LA PROVINCIAL")
        self.lbl_title.setStyleSheet("font-size: 20px; font-weight: 800; color: #F9FAFB; letter-spacing: 0.5px;")
        header_box.addWidget(self.lbl_title)

        self.lbl_local = QLabel(f"📍 Sede: {LOCAL_NAMES.get(self.current_local, 'RESTAURANTE')}")
        self.lbl_local.setStyleSheet("""
            background: #1E293B;
            color: #38BDF8;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 13px;
            border: 1px solid #334155;
        """)
        header_box.addWidget(self.lbl_local)

        header_box.addStretch()

        self.btn_whatsapp = QPushButton("📲 Copiar WhatsApp")
        self.btn_whatsapp.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #10B981);
                color: #FFFFFF;
                font-weight: 800;
                font-size: 13px;
                padding: 7px 16px;
                border-radius: 8px;
                border: 1px solid #34D399;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #065F46, stop:1 #059669);
                border: 1px solid #6EE7B7;
            }
        """)
        self.btn_whatsapp.clicked.connect(self._copiar_whatsapp)
        header_box.addWidget(self.btn_whatsapp)

        self.btn_refresh = QPushButton("🔄 Actualizar")
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #6366F1;
                color: #FFFFFF;
                font-weight: 700;
                font-size: 13px;
                padding: 7px 18px;
                border-radius: 8px;
                border: 1px solid #818CF8;
            }
            QPushButton:hover {
                background-color: #4F46E5;
            }
            QPushButton:pressed {
                background-color: #4338CA;
            }
        """)
        self.btn_refresh.clicked.connect(self._on_refresh_clicked)
        header_box.addWidget(self.btn_refresh)
        main_layout.addLayout(header_box)

        # Tab Widget (Segmented Controls Tremor Style)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #1F2937;
                background: #090D16;
                border-radius: 10px;
                padding: 10px;
            }
            QTabBar::tab {
                background: #111827;
                color: #9CA3AF;
                font-weight: 700;
                font-size: 13px;
                padding: 10px 22px;
                margin-right: 6px;
                border-radius: 8px;
                border: 1px solid #1F2937;
            }
            QTabBar::tab:hover {
                background: #1F2937;
                color: #F9FAFB;
            }
            QTabBar::tab:selected {
                background: #6366F1;
                color: #FFFFFF;
                border: 1px solid #818CF8;
            }
        """)

        # Tab 1: Resumen Ejecutivo
        self.tab_ejecutivo = self._build_tab_ejecutivo()
        self.tabs.addTab(self.tab_ejecutivo, "⚡ Resumen Ejecutivo")

        # Tab 2: Finanzas & Medios de Pago
        self.tab_finanzas = self._build_tab_finanzas()
        self.tabs.addTab(self.tab_finanzas, "💰 Finanzas & Ingresos")

        # Tab 3: Egresos & Compras
        self.tab_egresos = self._build_tab_egresos()
        self.tabs.addTab(self.tab_egresos, "📉 Egresos & Compras")

        # Tab 4: Operaciones Policiales & Cobranzas
        self.tab_policial = self._build_tab_policial()
        self.tabs.addTab(self.tab_policial, "👮 Gestión Policial & Cobranzas")

        # Tab 5: Vales Policiales
        self.tab_vales = self._build_tab_vales()
        self.tabs.addTab(self.tab_vales, "🎫 Vales & Canjes")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tabs)

    # -------------------------------------------------------------
    # TAB 1: RESUMEN EJECUTIVO
    # -------------------------------------------------------------
    def _build_tab_ejecutivo(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(16)

        # 4 Hero KPI Cards
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        self.kpi_ejecutivo = {}
        cards_data = [
            ("venta_total", "VENTA TOTAL DEL MES", "S/ 0.00", "Ingresos Totales", "#10B981", "#064E3B"),
            ("total_egresos", "TOTAL EGRESOS ACUMULADOS", "S/ 0.00", "Compras+Gastos+Personal", "#F43F5E", "#881337"),
            ("saldo_neto", "UTILIDAD NETA DISPONIBLE", "S/ 0.00", "Saldo Final Neto", "#38BDF8", "#0C4A6E"),
            ("rentabilidad", "MARGEN DE RENTABILIDAD", "0.0%", "Sobre Venta Total", "#F59E0B", "#78350F"),
        ]

        for key, title, val_def, badge_text, color_accent, color_bg in cards_data:
            card = self._create_tremor_card(key, title, val_def, badge_text, color_accent, color_bg)
            kpi_row.addWidget(card)
            self.kpi_ejecutivo[key] = card.findChild(QLabel, f"val_{key}")

        layout.addLayout(kpi_row)

        # Main Wide Chart: Flujo de Caja Integral
        self.fig_ejecutivo, self.ax_ejecutivo = plt.subplots(figsize=(12, 4.2), dpi=100)
        self.fig_ejecutivo.subplots_adjust(left=0.06, right=0.96, top=0.88, bottom=0.15)
        self.canvas_ejecutivo = FigureCanvas(self.fig_ejecutivo)
        self.canvas_ejecutivo.setMinimumHeight(380)
        layout.addWidget(self._wrap_chart_frame("📈 Tendencia Diaria: Ventas Totales vs Egresos y Saldo Neto", self.canvas_ejecutivo))

        # 2 Donut Charts: Revenue Structure & Expense Breakdown
        donuts_layout = QHBoxLayout()
        donuts_layout.setSpacing(14)

        self.fig_donut_rev, self.ax_donut_rev = plt.subplots(figsize=(5.5, 3.4), dpi=100)
        self.canvas_donut_rev = FigureCanvas(self.fig_donut_rev)
        self.canvas_donut_rev.setMinimumHeight(300)
        donuts_layout.addWidget(self._wrap_chart_frame("💵 Estructura de Ingresos (Efectivo vs Yape vs Tickets)", self.canvas_donut_rev))

        self.fig_donut_egr, self.ax_donut_egr = plt.subplots(figsize=(5.5, 3.4), dpi=100)
        self.canvas_donut_egr = FigureCanvas(self.fig_donut_egr)
        self.canvas_donut_egr.setMinimumHeight(300)
        donuts_layout.addWidget(self._wrap_chart_frame("📉 Distribución de Egresos (Compras vs Gastos vs Personal)", self.canvas_donut_egr))

        layout.addLayout(donuts_layout)

        scroll.setWidget(content)
        return scroll

    # -------------------------------------------------------------
    # TAB 2: FINANZAS & MEDIOS DE PAGO
    # -------------------------------------------------------------
    def _build_tab_finanzas(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(16)

        # Sub-KPIs Finanzas
        kpi_row = QHBoxLayout()
        self.kpi_finanzas = {}
        cards = [
            ("efectivo", "VENTA EFECTIVO", "S/ 0.00", "Flujo de Caja", "#10B981", "#064E3B"),
            ("yape", "VENTA YAPE / DIGITAL", "S/ 0.00", "Billeteras", "#A855F7", "#581C87"),
            ("venta_sin_tickets", "VENTA SIN TICKETS", "S/ 0.00", "Efectivo + Yape", "#06B6D4", "#164E63"),
            ("venta_policial", "VENTA TICKETS POLICIALES", "S/ 0.00", "S/ 12.00 c/u", "#6366F1", "#312E81"),
        ]
        for key, title, val_def, badge, color, color_bg in cards:
            c = self._create_tremor_card(key, title, val_def, badge, color, color_bg)
            kpi_row.addWidget(c)
            self.kpi_finanzas[key] = c.findChild(QLabel, f"val_{key}")
        layout.addLayout(kpi_row)

        # Chart: Daily Breakdown of Payment Methods (Stacked Bars)
        self.fig_fin_stack, self.ax_fin_stack = plt.subplots(figsize=(12, 4.4), dpi=100)
        self.fig_fin_stack.subplots_adjust(left=0.06, right=0.96, top=0.88, bottom=0.15)
        self.canvas_fin_stack = FigureCanvas(self.fig_fin_stack)
        self.canvas_fin_stack.setMinimumHeight(400)
        layout.addWidget(self._wrap_chart_frame("💳 Composición Diaria de Ingresos: Efectivo, Yape y Tickets Policiales", self.canvas_fin_stack))

        scroll.setWidget(content)
        return scroll

    # -------------------------------------------------------------
    # TAB 3: EGRESOS & COMPRAS
    # -------------------------------------------------------------
    def _build_tab_egresos(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(16)

        kpi_row = QHBoxLayout()
        self.kpi_egresos = {}
        cards = [
            ("total_compras", "COMPRAS / INSUMOS", "S/ 0.00", "Materia Prima", "#F97316", "#7C2D12"),
            ("total_gastos", "GASTOS OPERATIVOS", "S/ 0.00", "Servicios & Varios", "#F59E0B", "#78350F"),
            ("total_personal", "PAGOS AL PERSONAL", "S/ 0.00", "Planilla & Turnos", "#EC4899", "#831843"),
            ("total_egresos_tab3", "TOTAL EGRESOS DEL MES", "S/ 0.00", "Salidas Totales", "#F43F5E", "#881337"),
        ]
        for key, title, val_def, badge, color, color_bg in cards:
            c = self._create_tremor_card(key, title, val_def, badge, color, color_bg)
            kpi_row.addWidget(c)
            self.kpi_egresos[key] = c.findChild(QLabel, f"val_{key}")
        layout.addLayout(kpi_row)

        # Chart: Daily Stacked Expenses
        self.fig_egr_daily, self.ax_egr_daily = plt.subplots(figsize=(12, 4.4), dpi=100)
        self.fig_egr_daily.subplots_adjust(left=0.06, right=0.96, top=0.88, bottom=0.15)
        self.canvas_egr_daily = FigureCanvas(self.fig_egr_daily)
        self.canvas_egr_daily.setMinimumHeight(400)
        layout.addWidget(self._wrap_chart_frame("📉 Desglose Diario de Egresos: Compras vs Gastos vs Personal", self.canvas_egr_daily))

        scroll.setWidget(content)
        return scroll

    # -------------------------------------------------------------
    # TAB 4: GESTIÓN POLICIAL & COBRANZAS
    # -------------------------------------------------------------
    def _build_tab_policial(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(16)

        kpi_row = QHBoxLayout()
        self.kpi_policial = {}
        cards = [
            ("total_policias", "TOTAL TICKETS DEL MES", "0", "Consumo Policial", "#38BDF8", "#0C4A6E"),
            ("tickets_unidad", "PARA UNIDAD PNP", "0", "Llevados a base", "#6366F1", "#312E81"),
            ("tickets_local", "CONSUMO EN LOCAL", "0", "En restaurante", "#06B6D4", "#164E63"),
            ("monto_pendiente", "DEUDA POLICIAL PENDIENTE", "S/ 0.00", "Por Cobrar", "#F43F5E", "#881337"),
        ]
        for key, title, val_def, badge, color, color_bg in cards:
            c = self._create_tremor_card(key, title, val_def, badge, color, color_bg)
            kpi_row.addWidget(c)
            self.kpi_policial[key] = c.findChild(QLabel, f"val_{key}")
        layout.addLayout(kpi_row)

        # Chart 1: Unidad vs Local
        self.fig_pol_stack, self.ax_pol_stack = plt.subplots(figsize=(12, 4.0), dpi=100)
        self.fig_pol_stack.subplots_adjust(left=0.06, right=0.96, top=0.88, bottom=0.15)
        self.canvas_pol_stack = FigureCanvas(self.fig_pol_stack)
        self.canvas_pol_stack.setMinimumHeight(360)
        layout.addWidget(self._wrap_chart_frame("👮 Demanda Policial Diaria: Tickets Para Unidad vs Dentro del Local", self.canvas_pol_stack))

        # Chart 2: Pagados vs Debidos
        self.fig_pol_pagos, self.ax_pol_pagos = plt.subplots(figsize=(12, 4.0), dpi=100)
        self.fig_pol_pagos.subplots_adjust(left=0.06, right=0.96, top=0.88, bottom=0.15)
        self.canvas_pol_pagos = FigureCanvas(self.fig_pol_pagos)
        self.canvas_pol_pagos.setMinimumHeight(360)
        layout.addWidget(self._wrap_chart_frame("⚖️ Estado de Cobranza Policial: Tickets Pagados vs Tickets Debidos", self.canvas_pol_pagos))

        scroll.setWidget(content)
        return scroll

    # -------------------------------------------------------------
    # TAB 5: VALES & CANJES
    # -------------------------------------------------------------
    def _build_tab_vales(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(16)

        kpi_row = QHBoxLayout()
        self.kpi_vales = {}
        cards = [
            ("vales_entregados", "VALES ENTREGADOS", "0", "Emitidos", "#F59E0B", "#78350F"),
            ("vales_canjeados", "VALES CANJEADOS", "0", "Consumidos", "#10B981", "#064E3B"),
            ("saldo_vales", "SALDO EN CIRCULACIÓN", "0", "Pendientes", "#EAB308", "#713F12"),
            ("tickets_debidos", "TICKETS DEBIDOS", "0", "Por Cancelar", "#F43F5E", "#881337"),
        ]
        for key, title, val_def, badge, color, color_bg in cards:
            c = self._create_tremor_card(key, title, val_def, badge, color, color_bg)
            kpi_row.addWidget(c)
            self.kpi_vales[key] = c.findChild(QLabel, f"val_{key}")
        layout.addLayout(kpi_row)

        self.fig_val_flow, self.ax_val_flow = plt.subplots(figsize=(12, 4.4), dpi=100)
        self.fig_val_flow.subplots_adjust(left=0.06, right=0.96, top=0.88, bottom=0.15)
        self.canvas_val_flow = FigureCanvas(self.fig_val_flow)
        self.canvas_val_flow.setMinimumHeight(400)
        layout.addWidget(self._wrap_chart_frame("🎫 Flujo Diario de Vales Policiales: Entregados vs Canjeados", self.canvas_val_flow))

        scroll.setWidget(content)
        return scroll

    # -------------------------------------------------------------
    # HELPER COMPONENTS (TREMOR STYLE)
    # -------------------------------------------------------------
    def _create_tremor_card(self, key: str, title: str, val_def: str, badge: str, color: str, color_bg: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #111827;
                border: 1px solid #1F2937;
                border-radius: 10px;
                padding: 12px;
            }}
            QFrame:hover {{
                border: 1px solid {color};
            }}
        """)
        l = QVBoxLayout(card)
        l.setContentsMargins(10, 8, 10, 8)
        l.setSpacing(6)

        # Header row with title & badge
        top_row = QHBoxLayout()
        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("color: #9CA3AF; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        top_row.addWidget(lbl_t)
        top_row.addStretch()

        lbl_badge = QLabel(badge)
        lbl_badge.setStyleSheet(f"""
            background-color: {color_bg};
            color: {color};
            font-size: 10px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 12px;
        """)
        top_row.addWidget(lbl_badge)
        l.addLayout(top_row)

        # Value
        lbl_v = QLabel(val_def)
        lbl_v.setObjectName(f"val_{key}")
        lbl_v.setStyleSheet(f"color: #F9FAFB; font-size: 22px; font-weight: 800; padding: 2px 0;")
        l.addWidget(lbl_v)

        # Accent Bottom Bar
        bar = QFrame()
        bar.setFixedHeight(3)
        bar.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
        l.addWidget(bar)

        return card

    def _wrap_chart_frame(self, title: str, canvas: FigureCanvas) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #1F2937;
                border-radius: 10px;
                padding: 12px;
            }
        """)
        l = QVBoxLayout(frame)
        l.setContentsMargins(8, 8, 8, 8)
        l.setSpacing(10)

        lbl = QLabel(title)
        lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #F9FAFB; padding-left: 4px;")
        l.addWidget(lbl)
        l.addWidget(canvas)
        return frame

    def _on_tab_changed(self, index: int):
        if self.cached_data:
            self._render_current_tab()

    # -------------------------------------------------------------
    # DATA LOADING & DRAWING
    # -------------------------------------------------------------
    def cargar_datos(self):
        self.cached_data = self.dashboard_service.get_dashboard_data(self.current_anio, self.current_mes, self.current_local)
        k = self.cached_data.get("kpis", {})

        # Update KPI labels across all tabs
        self._update_label(self.kpi_ejecutivo, "venta_total", f"S/ {k.get('venta_total', 0.0):,.2f}")
        self._update_label(self.kpi_ejecutivo, "total_egresos", f"S/ {k.get('total_egresos', 0.0):,.2f}")
        saldo = k.get("saldo_neto", 0.0)
        self._update_label(self.kpi_ejecutivo, "saldo_neto", f"S/ {saldo:,.2f}", color="#10B981" if saldo >= 0 else "#F43F5E")
        self._update_label(self.kpi_ejecutivo, "rentabilidad", f"{k.get('rentabilidad_pct', 0.0):.1f}%")

        self._update_label(self.kpi_finanzas, "efectivo", f"S/ {k.get('efectivo', 0.0):,.2f}")
        self._update_label(self.kpi_finanzas, "yape", f"S/ {k.get('yape', 0.0):,.2f}")
        self._update_label(self.kpi_finanzas, "venta_sin_tickets", f"S/ {k.get('venta_sin_tickets', 0.0):,.2f}")
        self._update_label(self.kpi_finanzas, "venta_policial", f"S/ {k.get('venta_policial_calculada', 0.0):,.2f}")

        self._update_label(self.kpi_egresos, "total_compras", f"S/ {k.get('total_compras', 0.0):,.2f}")
        self._update_label(self.kpi_egresos, "total_gastos", f"S/ {k.get('total_gastos', 0.0):,.2f}")
        self._update_label(self.kpi_egresos, "total_personal", f"S/ {k.get('total_personal', 0.0):,.2f}")
        self._update_label(self.kpi_egresos, "total_egresos_tab3", f"S/ {k.get('total_egresos', 0.0):,.2f}")

        self._update_label(self.kpi_policial, "total_policias", f"{k.get('total_tickets_policiales', 0):,d}")
        self._update_label(self.kpi_policial, "tickets_unidad", f"{k.get('tickets_para_unidad', 0):,d}")
        self._update_label(self.kpi_policial, "tickets_local", f"{k.get('tickets_local', 0):,d}")
        self._update_label(self.kpi_policial, "monto_pendiente", f"S/ {k.get('monto_pendiente', 0.0):,.2f}")

        self._update_label(self.kpi_vales, "vales_entregados", f"{k.get('vales_entregados', 0):,d}")
        self._update_label(self.kpi_vales, "vales_canjeados", f"{k.get('vales_canjeados', 0):,d}")
        self._update_label(self.kpi_vales, "saldo_vales", f"{k.get('saldo_vales', 0):,d}")
        self._update_label(self.kpi_vales, "tickets_debidos", f"{k.get('tickets_debidos', 0):,d}")

        self._render_current_tab()

    def _update_label(self, card_dict: dict, key: str, text: str, color: Optional[str] = None):
        lbl = card_dict.get(key)
        if lbl:
            lbl.setText(text)
            if color:
                lbl.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: 800; padding: 2px 0;")

    def _render_current_tab(self):
        s = self.cached_data.get("series", {})
        k = self.cached_data.get("kpis", {})
        dias = s.get("dias", [])
        if not dias:
            return

        x = np.arange(len(dias))
        idx = self.tabs.currentIndex()

        if idx == 0:
            self._render_tab_ejecutivo(x, dias, s, k)
        elif idx == 1:
            self._render_tab_finanzas(x, dias, s)
        elif idx == 2:
            self._render_tab_egresos(x, dias, s)
        elif idx == 3:
            self._render_tab_policial(x, dias, s)
        elif idx == 4:
            self._render_tab_vales(x, dias, s)

    # --- Render Tab 1 ---
    def _render_tab_ejecutivo(self, x, dias, s, k):
        # Line/Area Chart: Flujo de caja
        self.ax_ejecutivo.clear()
        v_tot = np.array(s.get("ventas_total", []))
        egr = np.array(s.get("egresos_total", []))
        saldos = np.array(s.get("saldos_netos", []))

        self.ax_ejecutivo.plot(x, v_tot, label="Venta Total (Inc. Tickets)", color="#10B981", marker='o', linewidth=2.8, markersize=5)
        self.ax_ejecutivo.plot(x, egr, label="Total Egresos", color="#F43F5E", marker='s', linewidth=2.5, markersize=5)
        self.ax_ejecutivo.plot(x, saldos, label="Utilidad Neta Diaria", color="#38BDF8", linestyle="--", linewidth=2.0)
        self.ax_ejecutivo.fill_between(x, saldos, 0, where=(saldos >= 0), color="#10B981", alpha=0.15, interpolate=True)
        self.ax_ejecutivo.fill_between(x, saldos, 0, where=(saldos < 0), color="#F43F5E", alpha=0.18, interpolate=True)

        self._style_axes(self.ax_ejecutivo, self.fig_ejecutivo, x, dias, is_currency=True)
        self.ax_ejecutivo.legend(fontsize=9, facecolor='#1F2937', edgecolor='none', labelcolor='#F9FAFB', loc='upper left')
        self.canvas_ejecutivo.draw()

        # Donut Chart Revenue
        self.ax_donut_rev.clear()
        ef = k.get("efectivo", 0.0)
        yp = k.get("yape", 0.0)
        vt = k.get("venta_policial_calculada", 0.0)
        tot_r = ef + yp + vt
        if tot_r > 0:
            sizes = [ef, yp, vt]
            labels = [f"Efectivo\nS/ {ef:,.0f}", f"Yape\nS/ {yp:,.0f}", f"Tickets\nS/ {vt:,.0f}"]
            colors = ["#10B981", "#A855F7", "#6366F1"]
            wedges, texts, autotexts = self.ax_donut_rev.pie(
                sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                pctdistance=0.75, startangle=140, textprops=dict(color="#F9FAFB", fontsize=8, fontweight='bold'),
                wedgeprops=dict(width=0.45, edgecolor='#111827', linewidth=2)
            )
            for at in autotexts:
                at.set_color("#FFFFFF")
                at.set_fontsize(8)
        else:
            self.ax_donut_rev.text(0, 0, "Sin datos de venta", color="#9CA3AF", ha='center', va='center', fontsize=10)

        self.fig_donut_rev.patch.set_facecolor('#111827')
        self.ax_donut_rev.set_facecolor('#111827')
        self.canvas_donut_rev.draw()

        # Donut Chart Expenses
        self.ax_donut_egr.clear()
        comp = k.get("total_compras", 0.0)
        gast = k.get("total_gastos", 0.0)
        pers = k.get("total_personal", 0.0)
        tot_e = comp + gast + pers
        if tot_e > 0:
            sizes_e = [comp, gast, pers]
            labels_e = [f"Compras\nS/ {comp:,.0f}", f"Gastos\nS/ {gast:,.0f}", f"Personal\nS/ {pers:,.0f}"]
            colors_e = ["#F97316", "#F59E0B", "#EC4899"]
            wedges, texts, autotexts = self.ax_donut_egr.pie(
                sizes_e, labels=labels_e, colors=colors_e, autopct='%1.1f%%',
                pctdistance=0.75, startangle=140, textprops=dict(color="#F9FAFB", fontsize=8, fontweight='bold'),
                wedgeprops=dict(width=0.45, edgecolor='#111827', linewidth=2)
            )
            for at in autotexts:
                at.set_color("#FFFFFF")
                at.set_fontsize(8)
        else:
            self.ax_donut_egr.text(0, 0, "Sin datos de egresos", color="#9CA3AF", ha='center', va='center', fontsize=10)

        self.fig_donut_egr.patch.set_facecolor('#111827')
        self.ax_donut_egr.set_facecolor('#111827')
        self.canvas_donut_egr.draw()

    # --- Render Tab 2 ---
    def _render_tab_finanzas(self, x, dias, s):
        self.ax_fin_stack.clear()
        ef = np.array(s.get("efectivo", []))
        yp = np.array(s.get("yape", []))
        vtick = np.array(s.get("venta_tickets", []))

        self.ax_fin_stack.bar(x, ef, label="Efectivo", color="#10B981", width=0.62, alpha=0.95)
        self.ax_fin_stack.bar(x, yp, bottom=ef, label="Yape / Digital", color="#A855F7", width=0.62, alpha=0.95)
        self.ax_fin_stack.bar(x, vtick, bottom=ef + yp, label="Venta Tickets Policiales", color="#6366F1", width=0.62, alpha=0.95)

        self._style_axes(self.ax_fin_stack, self.fig_fin_stack, x, dias, is_currency=True)
        self.ax_fin_stack.legend(fontsize=9, facecolor='#1F2937', edgecolor='none', labelcolor='#F9FAFB', loc='upper left')
        self.canvas_fin_stack.draw()

    # --- Render Tab 3 ---
    def _render_tab_egresos(self, x, dias, s):
        self.ax_egr_daily.clear()
        comp = np.array(s.get("compras", []))
        gast = np.array(s.get("gastos", []))
        pers = np.array(s.get("personal", []))

        self.ax_egr_daily.bar(x, comp, label="Compras e Insumos", color="#F97316", width=0.62, alpha=0.95)
        self.ax_egr_daily.bar(x, gast, bottom=comp, label="Gastos Operativos", color="#F59E0B", width=0.62, alpha=0.95)
        self.ax_egr_daily.bar(x, pers, bottom=comp + gast, label="Pagos al Personal", color="#EC4899", width=0.62, alpha=0.95)

        self._style_axes(self.ax_egr_daily, self.fig_egr_daily, x, dias, is_currency=True)
        self.ax_egr_daily.legend(fontsize=9, facecolor='#1F2937', edgecolor='none', labelcolor='#F9FAFB', loc='upper left')
        self.canvas_egr_daily.draw()

    # --- Render Tab 4 ---
    def _render_tab_policial(self, x, dias, s):
        # Unidad vs Local
        self.ax_pol_stack.clear()
        u = np.array(s.get("para_unidad", []))
        l = np.array(s.get("local", []))

        self.ax_pol_stack.bar(x, u, label="Para Unidad", color="#6366F1", width=0.62, alpha=0.95)
        self.ax_pol_stack.bar(x, l, bottom=u, label="Dentro del Local", color="#06B6D4", width=0.62, alpha=0.95)
        self._style_axes(self.ax_pol_stack, self.fig_pol_stack, x, dias, is_currency=False)
        self.ax_pol_stack.legend(fontsize=9, facecolor='#1F2937', edgecolor='none', labelcolor='#F9FAFB', loc='upper left')
        self.canvas_pol_stack.draw()

        # Pagados vs Debidos
        self.ax_pol_pagos.clear()
        pag = np.array(s.get("tickets_pagados", []))
        deb = np.array(s.get("tickets_debidos", []))

        self.ax_pol_pagos.bar(x - 0.16, pag, width=0.32, label="Tickets Pagados", color="#10B981", alpha=0.9)
        self.ax_pol_pagos.bar(x + 0.16, deb, width=0.32, label="Tickets Debidos (Por Cobrar)", color="#F43F5E", alpha=0.9)
        self._style_axes(self.ax_pol_pagos, self.fig_pol_pagos, x, dias, is_currency=False)
        self.ax_pol_pagos.legend(fontsize=9, facecolor='#1F2937', edgecolor='none', labelcolor='#F9FAFB', loc='upper left')
        self.canvas_pol_pagos.draw()

    # --- Render Tab 5 ---
    def _render_tab_vales(self, x, dias, s):
        self.ax_val_flow.clear()
        v_ent = np.array(s.get("vales_entregados", []))
        v_canj = np.array(s.get("vales_canjeados", []))

        self.ax_val_flow.plot(x, v_ent, label="Vales Entregados", color="#F59E0B", marker='o', linewidth=2.5, markersize=5)
        self.ax_val_flow.plot(x, v_canj, label="Vales Canjeados", color="#10B981", marker='s', linewidth=2.5, markersize=5)
        self.ax_val_flow.fill_between(x, v_ent, v_canj, where=(v_ent >= v_canj), color="#F59E0B", alpha=0.12, interpolate=True)

        self._style_axes(self.ax_val_flow, self.fig_val_flow, x, dias, is_currency=False)
        self.ax_val_flow.legend(fontsize=9, facecolor='#1F2937', edgecolor='none', labelcolor='#F9FAFB', loc='upper left')
        self.canvas_val_flow.draw()

    def _style_axes(self, ax, fig, x_ticks, labels, is_currency: bool = False):
        ax.set_facecolor('#111827')
        fig.patch.set_facecolor('#111827')
        ax.set_xticks(x_ticks)
        ax.set_xticklabels([f"D{lbl}" if int(lbl) % 2 == 1 or len(labels) <= 15 else lbl for lbl in labels], rotation=0)
        ax.tick_params(colors='#9CA3AF', labelsize=9)

        if is_currency:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, loc: f"S/ {val:,.0f}"))
        else:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, loc: f"{int(val):,d}"))

        ax.grid(True, linestyle='--', alpha=0.25, color='#374151')
        for spine in ax.spines.values():
            spine.set_color('#1F2937')
            spine.set_linewidth(1)

    def _on_refresh_clicked(self):
        self.cargar_datos()
        ToastManager.show_success("Métricas del Dashboard actualizadas", self)

    def _copiar_whatsapp(self):
        d = self.cached_data
        if not d:
            return
        ej = d.get("ejecutivo", {})
        sede_name = LOCAL_NAMES.get(self.current_local, self.current_local.upper())
        signo = "+" if ej.get("saldo_neto", 0) > 0 else ""

        texto = (
            f"📊 *RESUMEN EJECUTIVO BI — {sede_name.upper()}*\n"
            f"📅 *Período:* {self.current_mes:02d}/{self.current_anio}\n"
            f"───────────────────────────\n"
            f"💰 *Venta Total:* S/ {ej.get('total_ventas', 0):,.2f}\n"
            f"💸 *Total Egresos:* S/ {ej.get('total_egresos', 0):,.2f}\n"
            f"⚖️ *SALDO NETO:* {signo}S/ {ej.get('saldo_neto', 0):,.2f}\n"
            f"📈 *Margen Operativo:* {ej.get('rentabilidad_pct', 0):.1f}%\n"
            f"───────────────────────────\n"
            f"👮 *Tickets Policiales:* {ej.get('tickets_policiales', 0)} emitidos\n"
            f"💰 *Cobranzas Realizadas:* S/ {ej.get('recaudacion_policial', 0):,.2f}\n"
            f"💳 *Deuda Pendiente:* S/ {ej.get('deuda_policial_pendiente', 0):,.2f}\n"
            f"🌟 *LA PROVINCIAL* — Sistema de Gestión Modular BI"
        )
        QApplication.clipboard().setText(texto)
        ToastManager.show_success("¡Resumen ejecutivo copiado al portapapeles para WhatsApp!", self)

