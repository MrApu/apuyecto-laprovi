from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt
from typing import Optional, Dict, Any, List
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

from services.dashboard_service import DashboardService
from models.local import LOCAL_RESTAURANTE, LOCAL_FAST_FOOD, LOCAL_CONSOLIDADO, LOCAL_NAMES
from views.components.toast import ToastManager


class CollapsibleDashboardSection(QFrame):
    """
    Sección desplegable / colapsable moderna para el Dashboard:
    - Cabecera interactiva con hover suave y acento rojo La Provincial.
    - Indicador de flecha (▾ expandido / ▸ colapsado).
    - Badge de resumen en la cabecera.
    """
    def __init__(self, title: str, icon: str, badge_text: str = "", is_expanded: bool = True, parent=None):
        super().__init__(parent)
        self.is_expanded = is_expanded

        self.setStyleSheet("""
            CollapsibleDashboardSection {
                background-color: #141414;
                border: 1px solid #262626;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header Button
        self.btn_header = QPushButton()
        self.btn_header.setCursor(Qt.PointingHandCursor)
        self.btn_header.setStyleSheet("""
            QPushButton {
                background-color: #18181B;
                color: #FFFFFF;
                text-align: left;
                padding: 12px 18px;
                font-size: 13px;
                font-weight: 900;
                border: none;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom: 1px solid #262626;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #1F1F23;
                color: #FFFFFF;
                border-bottom: 1px solid #DC2626;
            }
        """)

        header_layout = QHBoxLayout(self.btn_header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_title = QLabel(f"{icon}  {title.upper()}")
        self.lbl_title.setStyleSheet("font-weight: 900; font-size: 13px; color: #FFFFFF; background: transparent;")
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()

        self.lbl_badge = QLabel(badge_text)
        self.lbl_badge.setStyleSheet("""
            background: #271214;
            color: #EF4444;
            font-size: 11px;
            font-weight: 800;
            padding: 3px 10px;
            border-radius: 10px;
            border: 1px solid #7F1D1D;
        """)
        if not badge_text:
            self.lbl_badge.setVisible(False)
        header_layout.addWidget(self.lbl_badge)

        self.lbl_arrow = QLabel("▾" if self.is_expanded else "▸")
        self.lbl_arrow.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 900; background: transparent; padding-left: 8px;")
        header_layout.addWidget(self.lbl_arrow)

        self.btn_header.clicked.connect(self.toggle)
        layout.addWidget(self.btn_header)

        # Container for content
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(14, 14, 14, 14)
        self.content_layout.setSpacing(14)
        layout.addWidget(self.content_widget)

        self.content_widget.setVisible(self.is_expanded)

    def set_badge(self, text: str):
        if text:
            self.lbl_badge.setText(text)
            self.lbl_badge.setVisible(True)
        else:
            self.lbl_badge.setVisible(False)

    def toggle(self):
        self.set_expanded(not self.is_expanded)

    def set_expanded(self, expanded: bool):
        self.is_expanded = expanded
        self.content_widget.setVisible(self.is_expanded)
        self.lbl_arrow.setText("▾" if self.is_expanded else "▸")


class DashboardView(QWidget):
    """
    Dashboard Modular BI Desplegable — La Provincial (Rojo, Blanco y Negro):
    - Secciones Desplegables / Colapsables con un clic (Expandir/Colapsar todo)
    - Balance Ejecutivo & Flujo de Caja Integral
    - Análisis de Ingresos y Medios de Pago
    - Desglose de Egresos (Compras e Insumos + Pagos al Personal, sin gastos operativos redundantes)
    - Gráficos HD interactivos integrados al diseño corporativo
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dashboard_service = DashboardService()
        self.current_local = LOCAL_RESTAURANTE
        self.current_anio = 2026
        self.current_mes = 9
        self.cached_data = {}
        self.all_expanded = True
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
        self.setStyleSheet("background-color: #0A0A0A; font-family: 'Segoe UI', Arial, sans-serif;")

        # Header Bar
        header_box = QHBoxLayout()
        self.lbl_title = QLabel("📊 DASHBOARD MODULAR BI — LA PROVINCIAL")
        self.lbl_title.setStyleSheet("font-size: 19px; font-weight: 900; color: #FFFFFF; letter-spacing: 0.5px;")
        header_box.addWidget(self.lbl_title)

        self.lbl_local = QLabel(f"📍 Sede: {LOCAL_NAMES.get(self.current_local, 'RESTAURANTE')}")
        self.lbl_local.setStyleSheet("""
            background: #18181B;
            color: #FFFFFF;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 800;
            font-size: 12px;
            border: 1px solid #DC2626;
        """)
        header_box.addWidget(self.lbl_local)

        header_box.addStretch()

        self.btn_toggle_all = QPushButton("📁 Colapsar Todo")
        self.btn_toggle_all.setStyleSheet("""
            QPushButton {
                background-color: #18181B;
                color: #FFFFFF;
                font-weight: 800;
                font-size: 12px;
                padding: 7px 14px;
                border-radius: 8px;
                border: 1px solid #27272A;
            }
            QPushButton:hover {
                border: 1px solid #DC2626;
                background-color: #27272A;
            }
        """)
        self.btn_toggle_all.clicked.connect(self._toggle_all_sections)
        header_box.addWidget(self.btn_toggle_all)

        self.btn_whatsapp = QPushButton("📲 Copiar WhatsApp")
        self.btn_whatsapp.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #10B981);
                color: #FFFFFF;
                font-weight: 800;
                font-size: 12px;
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
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #991B1B, stop:1 #DC2626);
                color: #FFFFFF;
                font-weight: 900;
                font-size: 12px;
                padding: 7px 18px;
                border-radius: 8px;
                border: 1px solid #EF4444;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7F1D1D, stop:1 #B91C1C);
            }
        """)
        self.btn_refresh.clicked.connect(self._on_refresh_clicked)
        header_box.addWidget(self.btn_refresh)
        main_layout.addLayout(header_box)

        # Scrollable Area for Collapsible Sections
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        scroll_content = QWidget()
        self.content_vbox = QVBoxLayout(scroll_content)
        self.content_vbox.setContentsMargins(4, 4, 4, 4)
        self.content_vbox.setSpacing(16)

        # =========================================================
        # SECCIÓN 1: BALANCE EJECUTIVO & FLUJO DE CAJA (Desplegable)
        # =========================================================
        self.sec_ejecutivo = CollapsibleDashboardSection(
            "Resumen Ejecutivo & Flujo de Caja Integral",
            "📊",
            "Balance General",
            is_expanded=True
        )
        self._build_sec_ejecutivo_content(self.sec_ejecutivo.content_layout)
        self.content_vbox.addWidget(self.sec_ejecutivo)

        # =========================================================
        # SECCIÓN 2: INGRESOS & MEDIOS DE PAGO (Desplegable)
        # =========================================================
        self.sec_finanzas = CollapsibleDashboardSection(
            "Ingresos Diarios & Medios de Pago",
            "💳",
            "Efectivo + Yape + Tickets",
            is_expanded=True
        )
        self._build_sec_finanzas_content(self.sec_finanzas.content_layout)
        self.content_vbox.addWidget(self.sec_finanzas)

        # =========================================================
        # SECCIÓN 3: EGRESOS OPERATIVOS (Desplegable)
        # =========================================================
        self.sec_egresos = CollapsibleDashboardSection(
            "Egresos Operativos: Compras & Pagos al Personal",
            "📉",
            "Compras e Insumos + Personal",
            is_expanded=True
        )
        self._build_sec_egresos_content(self.sec_egresos.content_layout)
        self.content_vbox.addWidget(self.sec_egresos)

        self.sections = [self.sec_ejecutivo, self.sec_finanzas, self.sec_egresos]

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    # -------------------------------------------------------------
    # BUILD CONTENT FOR SECTION 1: BALANCE EJECUTIVO
    # -------------------------------------------------------------
    def _build_sec_ejecutivo_content(self, layout: QVBoxLayout):
        # 4 Hero KPI Cards
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        self.kpi_ejecutivo = {}
        cards_data = [
            ("venta_total", "VENTA TOTAL DEL MES", "S/ 0.00", "Ingresos Totales", "#10B981", "#064E3B"),
            ("total_egresos", "TOTAL EGRESOS ACUMULADOS", "S/ 0.00", "Compras + Personal", "#DC2626", "#271214"),
            ("saldo_neto", "UTILIDAD NETA DISPONIBLE", "S/ 0.00", "Saldo Final Neto", "#FFFFFF", "#1E1E22"),
            ("rentabilidad", "MARGEN DE RENTABILIDAD", "0.0%", "Sobre Venta Total", "#F59E0B", "#381E08"),
        ]

        for key, title, val_def, badge_text, color_accent, color_bg in cards_data:
            card = self._create_card(key, title, val_def, badge_text, color_accent, color_bg)
            kpi_row.addWidget(card)
            self.kpi_ejecutivo[key] = card.findChild(QLabel, f"val_{key}")

        layout.addLayout(kpi_row)

        # Main Wide Chart: Flujo de Caja
        self.fig_ejecutivo, self.ax_ejecutivo = plt.subplots(figsize=(12, 4.0), dpi=100)
        self.fig_ejecutivo.subplots_adjust(left=0.06, right=0.96, top=0.88, bottom=0.15)
        self.canvas_ejecutivo = FigureCanvas(self.fig_ejecutivo)
        self.canvas_ejecutivo.setMinimumHeight(360)
        layout.addWidget(self._wrap_chart_frame("📈 Tendencia Diaria: Ventas Totales vs Egresos y Saldo Neto", self.canvas_ejecutivo))

        # 2 Donut Charts
        donuts_layout = QHBoxLayout()
        donuts_layout.setSpacing(14)

        self.fig_donut_rev, self.ax_donut_rev = plt.subplots(figsize=(5.5, 3.2), dpi=100)
        self.canvas_donut_rev = FigureCanvas(self.fig_donut_rev)
        self.canvas_donut_rev.setMinimumHeight(280)
        donuts_layout.addWidget(self._wrap_chart_frame("💵 Estructura de Ingresos (Efectivo vs Yape vs Tickets)", self.canvas_donut_rev))

        self.fig_donut_egr, self.ax_donut_egr = plt.subplots(figsize=(5.5, 3.2), dpi=100)
        self.canvas_donut_egr = FigureCanvas(self.fig_donut_egr)
        self.canvas_donut_egr.setMinimumHeight(280)
        donuts_layout.addWidget(self._wrap_chart_frame("📉 Distribución de Egresos (Compras e Insumos vs Pagos Personal)", self.canvas_donut_egr))

        layout.addLayout(donuts_layout)

    # -------------------------------------------------------------
    # BUILD CONTENT FOR SECTION 2: FINANZAS & INGRESOS
    # -------------------------------------------------------------
    def _build_sec_finanzas_content(self, layout: QVBoxLayout):
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        self.kpi_finanzas = {}
        cards = [
            ("efectivo", "VENTA EFECTIVO", "S/ 0.00", "Flujo de Caja", "#10B981", "#064E3B"),
            ("yape", "VENTA YAPE / DIGITAL", "S/ 0.00", "Billeteras", "#A855F7", "#3B185F"),
            ("venta_sin_tickets", "VENTA SIN TICKETS", "S/ 0.00", "Efectivo + Yape", "#FFFFFF", "#1E1E22"),
            ("venta_policial", "VENTA TICKETS PNP", "S/ 0.00", "Tickets Efectivos", "#DC2626", "#271214"),
        ]
        for key, title, val_def, badge, color, color_bg in cards:
            c = self._create_card(key, title, val_def, badge, color, color_bg)
            kpi_row.addWidget(c)
            self.kpi_finanzas[key] = c.findChild(QLabel, f"val_{key}")
        layout.addLayout(kpi_row)

        self.fig_fin_stack, self.ax_fin_stack = plt.subplots(figsize=(12, 4.2), dpi=100)
        self.fig_fin_stack.subplots_adjust(left=0.06, right=0.96, top=0.88, bottom=0.15)
        self.canvas_fin_stack = FigureCanvas(self.fig_fin_stack)
        self.canvas_fin_stack.setMinimumHeight(360)
        layout.addWidget(self._wrap_chart_frame("💳 Composición Diaria de Ingresos: Efectivo, Yape y Tickets Policiales", self.canvas_fin_stack))

    # -------------------------------------------------------------
    # BUILD CONTENT FOR SECTION 3: EGRESOS & COMPRAS
    # -------------------------------------------------------------
    def _build_sec_egresos_content(self, layout: QVBoxLayout):
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        self.kpi_egresos = {}
        cards = [
            ("total_compras", "COMPRAS / INSUMOS", "S/ 0.00", "Materia Prima", "#DC2626", "#271214"),
            ("total_personal", "PAGOS AL PERSONAL", "S/ 0.00", "Planilla & Turnos", "#F59E0B", "#381E08"),
            ("total_egresos_tab3", "TOTAL EGRESOS DEL MES", "S/ 0.00", "Salidas Totales", "#FFFFFF", "#1E1E22"),
        ]
        for key, title, val_def, badge, color, color_bg in cards:
            c = self._create_card(key, title, val_def, badge, color, color_bg)
            kpi_row.addWidget(c)
            self.kpi_egresos[key] = c.findChild(QLabel, f"val_{key}")
        layout.addLayout(kpi_row)

        self.fig_egr_daily, self.ax_egr_daily = plt.subplots(figsize=(12, 4.2), dpi=100)
        self.fig_egr_daily.subplots_adjust(left=0.06, right=0.96, top=0.88, bottom=0.15)
        self.canvas_egr_daily = FigureCanvas(self.fig_egr_daily)
        self.canvas_egr_daily.setMinimumHeight(360)
        layout.addWidget(self._wrap_chart_frame("📉 Desglose Diario de Egresos: Compras e Insumos vs Pagos al Personal", self.canvas_egr_daily))

    def _toggle_all_sections(self):
        self.all_expanded = not self.all_expanded
        for sec in self.sections:
            sec.set_expanded(self.all_expanded)
        self.btn_toggle_all.setText("📁 Colapsar Todo" if self.all_expanded else "📂 Expandir Todo")

    def _create_card(self, key: str, title: str, val_def: str, badge: str, color: str, color_bg: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #141414;
                border: 1px solid #262626;
                border-radius: 8px;
            }
            QFrame:hover {
                border: 1px solid #3F3F46;
                background-color: #1A1A1D;
            }
        """)
        l = QVBoxLayout(card)
        l.setContentsMargins(12, 10, 12, 10)
        l.setSpacing(6)

        top_row = QHBoxLayout()
        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("color: #A1A1AA; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        top_row.addWidget(lbl_t)
        top_row.addStretch()

        lbl_badge = QLabel(badge)
        lbl_badge.setStyleSheet(f"""
            background-color: {color_bg};
            color: {color};
            font-size: 10px;
            font-weight: 800;
            padding: 2px 8px;
            border-radius: 10px;
            border: 1px solid {color}44;
        """)
        top_row.addWidget(lbl_badge)
        l.addLayout(top_row)

        lbl_v = QLabel(val_def)
        lbl_v.setObjectName(f"val_{key}")
        lbl_v.setStyleSheet(f"color: #FFFFFF; font-size: 21px; font-weight: 900; padding: 2px 0;")
        l.addWidget(lbl_v)

        bar = QFrame()
        bar.setFixedHeight(3)
        bar.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
        l.addWidget(bar)

        return card

    def _wrap_chart_frame(self, title: str, canvas: FigureCanvas) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #141414;
                border: 1px solid #262626;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        l = QVBoxLayout(frame)
        l.setContentsMargins(6, 6, 6, 6)
        l.setSpacing(8)

        lbl = QLabel(title)
        lbl.setStyleSheet("font-size: 13px; font-weight: 800; color: #FFFFFF; padding-left: 4px;")
        l.addWidget(lbl)
        l.addWidget(canvas)
        return frame

    # -------------------------------------------------------------
    # DATA LOADING & DRAWING
    # -------------------------------------------------------------
    def cargar_datos(self):
        self.cached_data = self.dashboard_service.get_dashboard_data(self.current_anio, self.current_mes, self.current_local)
        k = self.cached_data.get("kpis", {})

        # Total egresos reales sin gastos operativos = compras + personal
        tot_compras = k.get("total_compras", 0.0)
        tot_personal = k.get("total_personal", 0.0)
        tot_egresos_real = round(tot_compras + tot_personal, 2)
        total_ventas = k.get("venta_total", 0.0)
        saldo_real = round(total_ventas - tot_egresos_real, 2)
        rent_real = round((saldo_real / total_ventas * 100.0), 1) if total_ventas > 0 else 0.0

        # Update KPI labels
        self._update_label(self.kpi_ejecutivo, "venta_total", f"S/ {total_ventas:,.2f}")
        self._update_label(self.kpi_ejecutivo, "total_egresos", f"S/ {tot_egresos_real:,.2f}")
        self._update_label(self.kpi_ejecutivo, "saldo_neto", f"S/ {saldo_real:,.2f}", color="#10B981" if saldo_real >= 0 else "#DC2626")
        self._update_label(self.kpi_ejecutivo, "rentabilidad", f"{rent_real:.1f}%")

        self.sec_ejecutivo.set_badge(f"Venta: S/ {total_ventas:,.0f} | Utilidad: S/ {saldo_real:,.0f}")

        self._update_label(self.kpi_finanzas, "efectivo", f"S/ {k.get('efectivo', 0.0):,.2f}")
        self._update_label(self.kpi_finanzas, "yape", f"S/ {k.get('yape', 0.0):,.2f}")
        self._update_label(self.kpi_finanzas, "venta_sin_tickets", f"S/ {k.get('venta_sin_tickets', 0.0):,.2f}")
        self._update_label(self.kpi_finanzas, "venta_policial", f"S/ {k.get('venta_policial_calculada', 0.0):,.2f}")
        self.sec_finanzas.set_badge(f"Efectivo: S/ {k.get('efectivo', 0.0):,.0f} | Yape: S/ {k.get('yape', 0.0):,.0f}")

        self._update_label(self.kpi_egresos, "total_compras", f"S/ {tot_compras:,.2f}")
        self._update_label(self.kpi_egresos, "total_personal", f"S/ {tot_personal:,.2f}")
        self._update_label(self.kpi_egresos, "total_egresos_tab3", f"S/ {tot_egresos_real:,.2f}")
        self.sec_egresos.set_badge(f"Egresos Totales: S/ {tot_egresos_real:,.0f}")

        self._render_all_charts()

    def _update_label(self, card_dict: dict, key: str, text: str, color: Optional[str] = None):
        if not card_dict:
            return
        lbl = card_dict.get(key)
        if lbl:
            lbl.setText(text)
            if color:
                lbl.setStyleSheet(f"color: {color}; font-size: 21px; font-weight: 900; padding: 2px 0;")

    def _render_all_charts(self):
        s = self.cached_data.get("series", {})
        k = self.cached_data.get("kpis", {})
        dias = s.get("dias", [])
        if not dias:
            return

        x = np.arange(len(dias))
        self._render_charts_ejecutivo(x, dias, s, k)
        self._render_charts_finanzas(x, dias, s)
        self._render_charts_egresos(x, dias, s)

    # --- Render Section 1 Charts ---
    def _render_charts_ejecutivo(self, x, dias, s, k):
        self.ax_ejecutivo.clear()
        v_tot = np.array(s.get("ventas_total", []))
        c_dia = np.array(s.get("compras", []))
        p_dia = np.array(s.get("personal", []))
        # Total egresos reales sin gastos operativos
        egr = c_dia + p_dia
        saldos = v_tot - egr

        self.ax_ejecutivo.plot(x, v_tot, label="Venta Total", color="#10B981", marker='o', linewidth=2.5, markersize=4)
        self.ax_ejecutivo.plot(x, egr, label="Egresos (Compras+Personal)", color="#DC2626", marker='s', linewidth=2.5, markersize=4)
        self.ax_ejecutivo.plot(x, saldos, label="Utilidad Neta Diaria", color="#FFFFFF", linestyle="--", linewidth=1.8)
        self.ax_ejecutivo.fill_between(x, saldos, 0, where=(saldos >= 0), color="#10B981", alpha=0.15, interpolate=True)
        self.ax_ejecutivo.fill_between(x, saldos, 0, where=(saldos < 0), color="#DC2626", alpha=0.20, interpolate=True)

        self._style_axes(self.ax_ejecutivo, self.fig_ejecutivo, x, dias, is_currency=True)
        self.ax_ejecutivo.legend(fontsize=9, facecolor='#18181B', edgecolor='#27272A', labelcolor='#FFFFFF', loc='upper left')
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
            colors = ["#10B981", "#A855F7", "#DC2626"]
            wedges, texts, autotexts = self.ax_donut_rev.pie(
                sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                pctdistance=0.75, startangle=140, textprops=dict(color="#FFFFFF", fontsize=8, fontweight='bold'),
                wedgeprops=dict(width=0.45, edgecolor='#141414', linewidth=2)
            )
            for at in autotexts:
                at.set_color("#FFFFFF")
                at.set_fontsize(8)
        else:
            self.ax_donut_rev.text(0, 0, "Sin datos de venta", color="#A1A1AA", ha='center', va='center', fontsize=10)

        self.fig_donut_rev.patch.set_facecolor('#141414')
        self.ax_donut_rev.set_facecolor('#141414')
        self.canvas_donut_rev.draw()

        # Donut Chart Expenses (Compras vs Personal, sin gastos operativos redundantes)
        self.ax_donut_egr.clear()
        comp = k.get("total_compras", 0.0)
        pers = k.get("total_personal", 0.0)
        tot_e = comp + pers
        if tot_e > 0:
            sizes_e = [comp, pers]
            labels_e = [f"Compras / Insumos\nS/ {comp:,.0f}", f"Pagos Personal\nS/ {pers:,.0f}"]
            colors_e = ["#DC2626", "#F59E0B"]
            wedges, texts, autotexts = self.ax_donut_egr.pie(
                sizes_e, labels=labels_e, colors=colors_e, autopct='%1.1f%%',
                pctdistance=0.75, startangle=140, textprops=dict(color="#FFFFFF", fontsize=8, fontweight='bold'),
                wedgeprops=dict(width=0.45, edgecolor='#141414', linewidth=2)
            )
            for at in autotexts:
                at.set_color("#FFFFFF")
                at.set_fontsize(8)
        else:
            self.ax_donut_egr.text(0, 0, "Sin datos de egresos", color="#A1A1AA", ha='center', va='center', fontsize=10)

        self.fig_donut_egr.patch.set_facecolor('#141414')
        self.ax_donut_egr.set_facecolor('#141414')
        self.canvas_donut_egr.draw()

    # --- Render Section 2 Charts ---
    def _render_charts_finanzas(self, x, dias, s):
        self.ax_fin_stack.clear()
        ef = np.array(s.get("efectivo", []))
        yp = np.array(s.get("yape", []))
        vtick = np.array(s.get("venta_tickets", []))

        self.ax_fin_stack.bar(x, ef, label="Efectivo", color="#10B981", width=0.62, alpha=0.95)
        self.ax_fin_stack.bar(x, yp, bottom=ef, label="Yape / Digital", color="#A855F7", width=0.62, alpha=0.95)
        self.ax_fin_stack.bar(x, vtick, bottom=ef + yp, label="Tickets PNP", color="#DC2626", width=0.62, alpha=0.95)

        self._style_axes(self.ax_fin_stack, self.fig_fin_stack, x, dias, is_currency=True)
        self.ax_fin_stack.legend(fontsize=9, facecolor='#18181B', edgecolor='#27272A', labelcolor='#FFFFFF', loc='upper left')
        self.canvas_fin_stack.draw()

    # --- Render Section 3 Charts ---
    def _render_charts_egresos(self, x, dias, s):
        self.ax_egr_daily.clear()
        comp = np.array(s.get("compras", []))
        pers = np.array(s.get("personal", []))

        self.ax_egr_daily.bar(x, comp, label="Compras e Insumos", color="#DC2626", width=0.62, alpha=0.95)
        self.ax_egr_daily.bar(x, pers, bottom=comp, label="Pagos al Personal", color="#F59E0B", width=0.62, alpha=0.95)

        self._style_axes(self.ax_egr_daily, self.fig_egr_daily, x, dias, is_currency=True)
        self.ax_egr_daily.legend(fontsize=9, facecolor='#18181B', edgecolor='#27272A', labelcolor='#FFFFFF', loc='upper left')
        self.canvas_egr_daily.draw()

    def _style_axes(self, ax, fig, x_ticks, labels, is_currency: bool = False):
        ax.set_facecolor('#141414')
        fig.patch.set_facecolor('#141414')
        ax.set_xticks(x_ticks)
        ax.set_xticklabels([f"D{lbl}" if int(lbl) % 2 == 1 or len(labels) <= 15 else lbl for lbl in labels], rotation=0)
        ax.tick_params(colors='#A1A1AA', labelsize=9)

        if is_currency:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, loc: f"S/ {val:,.0f}"))
        else:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, loc: f"{int(val):,d}"))

        ax.grid(True, linestyle='--', alpha=0.20, color='#27272A')
        for spine in ax.spines.values():
            spine.set_color('#262626')
            spine.set_linewidth(1)

    def _on_refresh_clicked(self):
        self.cargar_datos()
        ToastManager.show_success("Métricas del Dashboard actualizadas", self)

    def _copiar_whatsapp(self):
        d = self.cached_data
        if not d:
            return
        k = d.get("kpis", {})
        sede_name = LOCAL_NAMES.get(self.current_local, self.current_local.upper())
        total_ventas = k.get("venta_total", 0.0)
        tot_compras = k.get("total_compras", 0.0)
        tot_personal = k.get("total_personal", 0.0)
        tot_egresos = round(tot_compras + tot_personal, 2)
        saldo_neto = round(total_ventas - tot_egresos, 2)
        signo = "+" if saldo_neto > 0 else ""
        rent = round((saldo_neto / total_ventas * 100.0), 1) if total_ventas > 0 else 0.0

        texto = (
            f"📊 *RESUMEN EJECUTIVO BI — {sede_name.upper()}*\n"
            f"📅 *Período:* {self.current_mes:02d}/{self.current_anio}\n"
            f"───────────────────────────\n"
            f"💰 *Venta Total:* S/ {total_ventas:,.2f}\n"
            f"  • Efectivo: S/ {k.get('efectivo', 0.0):,.2f}\n"
            f"  • Yape / Digital: S/ {k.get('yape', 0.0):,.2f}\n"
            f"  • Tickets PNP: S/ {k.get('venta_policial_calculada', 0.0):,.2f}\n"
            f"───────────────────────────\n"
            f"💸 *Total Egresos:* S/ {tot_egresos:,.2f}\n"
            f"  • Compras / Insumos: S/ {tot_compras:,.2f}\n"
            f"  • Pagos Personal: S/ {tot_personal:,.2f}\n"
            f"───────────────────────────\n"
            f"⚖️ *SALDO NETO:* {signo}S/ {saldo_neto:,.2f}  (Margen: {rent:.1f}%)\n"
            f"👮 *Tickets Policiales:* {k.get('total_tickets_policiales', 0)} emitidos\n"
            f"🌟 *LA PROVINCIAL* — Sistema de Gestión Comercial"
        )
        QApplication.clipboard().setText(texto)
        ToastManager.show_success("¡Resumen ejecutivo copiado al portapapeles para WhatsApp!", self)
