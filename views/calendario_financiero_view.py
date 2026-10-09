import calendar
from datetime import datetime
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QMessageBox,
    QFrame, QScrollArea, QDialog, QSizePolicy, QButtonGroup, QApplication
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QFont, QCursor

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

from services.financiero_service import FinancieroService
from services.mes_service import MesService
from models.local import LOCAL_RESTAURANTE, LOCAL_FAST_FOOD, LOCAL_CONSOLIDADO, LOCAL_NAMES
from models.ticket import DIAS_SEMANA_ES
from views.components.toast import ToastManager
from views.dialogs.detalle_dia_dialog import DetalleDiaDialog

class FloatingMiniReportPopup(QFrame):
    """
    Mini-reporte flotante transparente y elegante que aparece al señalar
    un día del calendario con el mouse y desaparece al salir.
    """
    def __init__(self, parent=None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setStyleSheet("""
            QFrame#MiniReport {
                background-color: #0F172A;
                border: 1px solid #6366F1;
                border-radius: 10px;
                padding: 12px;
            }
        """)
        self.setObjectName("MiniReport")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14, 12, 14, 12)
        self.layout.setSpacing(6)

        # Header: Date & Sede
        self.lbl_fecha = QLabel()
        self.lbl_fecha.setStyleSheet("color: #38BDF8; font-size: 13px; font-weight: 800;")
        self.lbl_sede = QLabel()
        self.lbl_sede.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: bold;")
        self.layout.addWidget(self.lbl_fecha)
        self.layout.addWidget(self.lbl_sede)

        # Divider
        self.layout.addWidget(self._create_divider())

        # Ventas section
        lbl_v_title = QLabel("💵 INGRESOS / VENTAS")
        lbl_v_title.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        self.layout.addWidget(lbl_v_title)

        self.lbl_efectivo = QLabel()
        self.lbl_yape = QLabel()
        self.lbl_tickets = QLabel()
        self.lbl_venta_total = QLabel()

        for lbl in [self.lbl_efectivo, self.lbl_yape, self.lbl_tickets]:
            lbl.setStyleSheet("color: #E2E8F0; font-size: 11px;")
            self.layout.addWidget(lbl)

        self.lbl_venta_total.setStyleSheet("color: #10B981; font-size: 12px; font-weight: 800; padding-top: 2px;")
        self.layout.addWidget(self.lbl_venta_total)

        # Divider
        self.layout.addWidget(self._create_divider())

        # Egresos section
        lbl_e_title = QLabel("💸 EGRESOS OPERATIVOS")
        lbl_e_title.setStyleSheet("color: #F43F5E; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        self.layout.addWidget(lbl_e_title)

        self.lbl_compras = QLabel()
        self.lbl_gastos = QLabel()
        self.lbl_personal = QLabel()
        self.lbl_egresos_total = QLabel()

        for lbl in [self.lbl_compras, self.lbl_gastos, self.lbl_personal]:
            lbl.setStyleSheet("color: #E2E8F0; font-size: 11px;")
            self.layout.addWidget(lbl)

        self.lbl_egresos_total.setStyleSheet("color: #F43F5E; font-size: 12px; font-weight: 800; padding-top: 2px;")
        self.layout.addWidget(self.lbl_egresos_total)

        # Divider
        self.layout.addWidget(self._create_divider())

        # Balance Section
        self.lbl_saldo = QLabel()
        self.lbl_saldo.setStyleSheet("font-size: 13px; font-weight: 800;")
        self.layout.addWidget(self.lbl_saldo)

        self.lbl_rentabilidad = QLabel()
        self.lbl_rentabilidad.setStyleSheet("color: #F59E0B; font-size: 11px; font-weight: bold;")
        self.layout.addWidget(self.lbl_rentabilidad)

        lbl_hint = QLabel("💡 Doble clic para abrir bitácora completa")
        lbl_hint.setStyleSheet("color: #64748B; font-size: 10px; font-style: italic; padding-top: 2px;")
        self.layout.addWidget(lbl_hint)

    def _create_divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #1E293B; max-height: 1px; border: none;")
        return line

    def set_data(self, data: Dict[str, Any], sede_name: str):
        fecha_str = data.get("fecha", "")
        dia_sem = data.get("dia_semana", "")
        try:
            dt = datetime.strptime(fecha_str, "%Y-%m-%d")
            fecha_display = f"📅 {dia_sem.upper()} {dt.day:02d}/{dt.month:02d}/{dt.year}"
        except Exception:
            fecha_display = f"📅 {dia_sem} {fecha_str}"

        self.lbl_fecha.setText(fecha_display)
        self.lbl_sede.setText(f"📍 Sede: {sede_name.upper()}")

        efectivo = data.get("efectivo", 0.0)
        yape = data.get("yape", 0.0)
        cant_tk = data.get("cantidad_tickets", 0)
        v_tk = data.get("venta_tickets", 0.0)
        v_tot = data.get("venta_total", 0.0)

        self.lbl_efectivo.setText(f"  • Efectivo:  S/ {efectivo:,.2f}")
        self.lbl_yape.setText(f"  • Yape/Digital:  S/ {yape:,.2f}")
        self.lbl_tickets.setText(f"  • Tickets PNP ({cant_tk}):  S/ {v_tk:,.2f}")
        self.lbl_venta_total.setText(f"  ➜ TOTAL VENTA:  S/ {v_tot:,.2f}")

        compras = data.get("compras", 0.0)
        gastos = data.get("gastos", 0.0)
        personal = data.get("personal", 0.0)
        e_tot = data.get("total_egresos", 0.0)

        self.lbl_compras.setText(f"  • Compras / Insumos:  S/ {compras:,.2f}")
        self.lbl_gastos.setText(f"  • Gastos Generales:  S/ {gastos:,.2f}")
        self.lbl_personal.setText(f"  • Pago Personal:  S/ {personal:,.2f}")
        self.lbl_egresos_total.setText(f"  ➜ TOTAL EGRESOS:  S/ {e_tot:,.2f}")

        saldo = data.get("saldo", 0.0)
        signo = "+" if saldo > 0 else ""
        if saldo > 0:
            self.lbl_saldo.setText(f"⚖️ SALDO NETO:  {signo}S/ {saldo:,.2f}")
            self.lbl_saldo.setStyleSheet("color: #10B981; font-size: 13px; font-weight: 800;")
        elif saldo < 0:
            self.lbl_saldo.setText(f"⚖️ SALDO NETO:  S/ {saldo:,.2f}")
            self.lbl_saldo.setStyleSheet("color: #F43F5E; font-size: 13px; font-weight: 800;")
        else:
            self.lbl_saldo.setText(f"⚖️ SALDO NETO:  S/ 0.00")
            self.lbl_saldo.setStyleSheet("color: #94A3B8; font-size: 13px; font-weight: 800;")

        rent = round((saldo / v_tot * 100.0), 1) if v_tot > 0 else 0.0
        self.lbl_rentabilidad.setText(f"📊 Margen Neto: {rent:.1f}%")

        self.adjustSize()


class DayTileWidget(QFrame):
    """
    Celda de día en la cuadrícula del calendario con interactividad hover y doble clic drill-down.
    """
    def __init__(self, anio: int, mes: int, dia: int, local_id: str, data: Optional[Dict[str, Any]], sede_name: str, popup: FloatingMiniReportPopup, parent=None):
        super().__init__(parent)
        self.anio = anio
        self.mes = mes
        self.dia = dia
        self.local_id = local_id
        self.data = data
        self.sede_name = sede_name
        self.popup = popup
        self._init_ui()

    def _init_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(105)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(3)

        if not self.dia:
            # Empty / Trailing cell outside the month
            self.setStyleSheet("""
                DayTileWidget {
                    background-color: #0B0F19;
                    border: 1px dashed #1E293B;
                    border-radius: 8px;
                }
            """)
            return

        self.setCursor(Qt.PointingHandCursor)

        # Active Day styling
        self.setStyleSheet("""
            DayTileWidget {
                background-color: #111827;
                border: 1px solid #1F2937;
                border-radius: 8px;
            }
            DayTileWidget:hover {
                background-color: #1A2338;
                border: 1px solid #6366F1;
            }
        """)

        # Day header row
        h_box = QHBoxLayout()
        h_box.setContentsMargins(0, 0, 0, 0)

        lbl_num = QLabel(f"{self.dia:02d}")
        lbl_num.setStyleSheet("font-size: 14px; font-weight: 800; color: #F8FAFC;")
        h_box.addWidget(lbl_num)
        h_box.addStretch()

        if self.data:
            saldo = self.data.get("saldo", 0.0)
            lbl_badge = QLabel()
            if saldo > 0:
                lbl_badge.setText(f"+S/ {saldo:,.0f}")
                lbl_badge.setStyleSheet("background-color: #064E3B; color: #34D399; font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 4px;")
            elif saldo < 0:
                lbl_badge.setText(f"S/ {saldo:,.0f}")
                lbl_badge.setStyleSheet("background-color: #881337; color: #FB7185; font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 4px;")
            else:
                lbl_badge.setText("S/ 0")
                lbl_badge.setStyleSheet("background-color: #1E293B; color: #94A3B8; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;")
            h_box.addWidget(lbl_badge)

        layout.addLayout(h_box)

        # Financial values
        if self.data:
            v_tot = self.data.get("venta_total", 0.0)
            e_tot = self.data.get("total_egresos", 0.0)
            cant_tk = self.data.get("cantidad_tickets", 0)

            lbl_v = QLabel(f"📈 S/ {v_tot:,.2f}")
            lbl_v.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 700;")
            layout.addWidget(lbl_v)

            lbl_e = QLabel(f"📉 S/ {e_tot:,.2f}")
            lbl_e.setStyleSheet("color: #F43F5E; font-size: 11px; font-weight: 600;")
            layout.addWidget(lbl_e)

            if cant_tk > 0:
                lbl_tk = QLabel(f"👮 {cant_tk} tk")
                lbl_tk.setStyleSheet("color: #818CF8; font-size: 10px; font-weight: 600;")
                layout.addWidget(lbl_tk)
        else:
            lbl_nodata = QLabel("Sin mov.")
            lbl_nodata.setStyleSheet("color: #475569; font-size: 10px; font-style: italic;")
            layout.addWidget(lbl_nodata)

        layout.addStretch()

    def enterEvent(self, event):
        if self.data and self.popup:
            self.popup.set_data(self.data, self.sede_name)
            global_pos = self.mapToGlobal(QPoint(self.width() + 10, -20))
            screen_geom = self.screen().geometry() if self.screen() else None
            if screen_geom and (global_pos.x() + 280 > screen_geom.right()):
                global_pos = self.mapToGlobal(QPoint(-290, -20))
            self.popup.move(global_pos)
            self.popup.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.popup:
            self.popup.hide()
        super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.dia:
            if self.popup:
                self.popup.hide()
            dlg = DetalleDiaDialog(self.anio, self.mes, self.dia, self.local_id, parent=self)
            dlg.exec()
        super().mouseDoubleClickEvent(event)


class GraficaFinancieraDialog(QDialog):
    """
    Diálogo emergente en Alta Definición con la curva de evolución financiera diaria del mes.
    """
    def __init__(self, dias_data: List[Dict[str, Any]], mes_nombre: str, sede_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"📈 Gráfica Financiera — {mes_nombre.upper()} ({sede_name})")
        self.resize(1100, 680)
        self.setStyleSheet("background-color: #090D16; color: #F3F4F6;")
        self.dias_data = dias_data
        self.mes_nombre = mes_nombre
        self.sede_name = sede_name
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        title = QLabel(f"📈 EVOLUCIÓN FINANCIERA DIARIA — {self.mes_nombre.upper()}")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #F8FAFC;")
        header.addWidget(title)

        lbl_sub = QLabel(f"📍 Sede: {self.sede_name.upper()}")
        lbl_sub.setStyleSheet("background: #1E293B; color: #38BDF8; padding: 4px 12px; border-radius: 6px; font-weight: 700; font-size: 12px;")
        header.addWidget(lbl_sub)

        header.addStretch()

        btn_close = QPushButton("✕ Cerrar")
        btn_close.setProperty("class", "PrimaryBtn")
        btn_close.clicked.connect(self.accept)
        header.addWidget(btn_close)
        layout.addLayout(header)

        # Matplotlib Canvas
        fig = Figure(figsize=(11, 5.5), dpi=100, facecolor='#090D16')
        ax1 = fig.add_subplot(111)
        ax1.set_facecolor('#0F172A')

        canvas = FigureCanvas(fig)
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(canvas)

        if not self.dias_data:
            ax1.text(0.5, 0.5, "No hay datos disponibles para el período", color="#94A3B8", ha='center', va='center')
            canvas.draw()
            return

        dias = [d["dia"] for d in self.dias_data]
        ventas = [d["venta_total"] for d in self.dias_data]
        egresos = [d["total_egresos"] for d in self.dias_data]
        saldos = [d["saldo"] for d in self.dias_data]

        x = np.arange(len(dias))
        width = 0.38

        # Bars for Saldo Diario
        colors_saldo = ['#10B981' if s >= 0 else '#F43F5E' for s in saldos]
        ax1.bar(x, saldos, width=width, label='Saldo Neto Diario (S/)', color=colors_saldo, alpha=0.35, edgecolor=colors_saldo)

        # Lines for Ventas and Egresos
        ax1.plot(x, ventas, color='#10B981', marker='o', linewidth=2.5, markersize=5, label='Venta Total Diaria (S/)')
        ax1.plot(x, egresos, color='#F43F5E', marker='s', linewidth=2.5, markersize=5, linestyle='--', label='Total Egresos Diarios (S/)')

        ax1.set_xticks(x)
        ax1.set_xticklabels([f"D{d}" for d in dias], fontsize=9, color='#94A3B8', rotation=45 if len(dias) > 20 else 0)
        ax1.tick_params(colors='#94A3B8', labelsize=10)
        ax1.grid(True, linestyle=':', alpha=0.3, color='#334155')

        # Legend
        leg = ax1.legend(loc='upper right', facecolor='#111827', edgecolor='#1F2937', labelcolor='#F8FAFC', fontsize=10)

        # Spines
        for spine in ax1.spines.values():
            spine.set_color('#1F2937')

        fig.tight_layout()
        canvas.draw()


class CalendarioFinancieroView(QWidget):
    """
    Vista de Calendario Financiero interactivo con:
    - Cuadrícula visual mensual de 7 columnas (Lunes a Domingo).
    - Mini-Reporte flotante con desglose completo al pasar el mouse por cada día.
    - Drill-Down al hacer doble clic sobre cualquier día para ver la bitácora completa.
    - Botón 1-Clic para copiar el reporte mensual o diario a WhatsApp.
    - Botón de Gráfica Financiera mensual en Alta Definición.
    - Alternancia fluida entre Vista Cuadrícula Calendario y Vista Tabla Detallada.
    """
    def __init__(self, financiero_service: Optional[FinancieroService] = None, mes_service: Optional[MesService] = None, parent=None):
        super().__init__(parent)
        self.financiero_service = financiero_service or FinancieroService()
        self.mes_service = mes_service or MesService()
        self.current_local = LOCAL_RESTAURANTE
        self.current_year = 2026
        self.current_month = 9
        self.cached_dias: List[Dict[str, Any]] = []
        self.cached_resumen: Dict[str, Any] = {}

        # Floating Mini-Report Popup Singleton
        self.popup_report = FloatingMiniReportPopup(self)

        self._init_ui()

    def set_local(self, local_id: str):
        self.current_local = local_id
        self.lbl_local_badge.setText(f"📍 Sede: {LOCAL_NAMES.get(local_id, local_id.upper())}")
        self.refresh_data()

    def set_periodo(self, anio: int, mes: int):
        self.current_year = anio
        self.current_month = mes
        self.refresh_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. Header Bar
        header = QHBoxLayout()
        title = QLabel("📅 CALENDARIO FINANCIERO Y SALDO DIARIO")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #F8FAFC; font-weight: 800; font-size: 18px;")
        header.addWidget(title)

        self.lbl_local_badge = QLabel(f"📍 Sede: {LOCAL_NAMES.get(self.current_local, 'RESTAURANTE')}")
        self.lbl_local_badge.setStyleSheet("""
            background: #1E293B;
            color: #38BDF8;
            padding: 5px 12px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 12px;
            border: 1px solid #334155;
        """)
        header.addWidget(self.lbl_local_badge)

        header.addStretch()

        # Botón Copiar WhatsApp
        self.btn_whatsapp = QPushButton("📲 WhatsApp")
        self.btn_whatsapp.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #10B981);
                color: #FFFFFF;
                border: 1px solid #34D399;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 800;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #065F46, stop:1 #059669);
                border: 1px solid #6EE7B7;
            }
        """)
        self.btn_whatsapp.clicked.connect(self._copiar_whatsapp_mes)
        header.addWidget(self.btn_whatsapp)

        # View Mode Switcher Buttons
        self.btn_grid_mode = QPushButton("📅 Cuadrícula")
        self.btn_grid_mode.setCheckable(True)
        self.btn_grid_mode.setChecked(True)
        self.btn_grid_mode.setStyleSheet("""
            QPushButton {
                background: #1E293B;
                color: #94A3B8;
                border: 1px solid #334155;
                padding: 6px 14px;
                border-radius: 6px;
                font-weight: 700;
            }
            QPushButton:checked {
                background: #6366F1;
                color: white;
                border: 1px solid #818CF8;
            }
        """)

        self.btn_table_mode = QPushButton("📋 Tabla")
        self.btn_table_mode.setCheckable(True)
        self.btn_table_mode.setStyleSheet("""
            QPushButton {
                background: #1E293B;
                color: #94A3B8;
                border: 1px solid #334155;
                padding: 6px 14px;
                border-radius: 6px;
                font-weight: 700;
            }
            QPushButton:checked {
                background: #6366F1;
                color: white;
                border: 1px solid #818CF8;
            }
        """)

        mode_group = QButtonGroup(self)
        mode_group.setExclusive(True)
        mode_group.addButton(self.btn_grid_mode)
        mode_group.addButton(self.btn_table_mode)
        self.btn_grid_mode.clicked.connect(self._toggle_view_mode)
        self.btn_table_mode.clicked.connect(self._toggle_view_mode)

        header.addWidget(self.btn_grid_mode)
        header.addWidget(self.btn_table_mode)

        # Botón de Gráfica 📈
        self.btn_grafica = QPushButton("📈 Ver Gráfica")
        self.btn_grafica.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F46E5, stop:1 #6366F1);
                color: #FFFFFF;
                border: 1px solid #818CF8;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: 800;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338CA, stop:1 #4F46E5);
                border: 1px solid #A5B4FC;
            }
        """)
        self.btn_grafica.clicked.connect(self._mostrar_grafica)
        header.addWidget(self.btn_grafica)

        # Período Selector
        header.addWidget(QLabel("Período:"))
        self.combo_periodo = QComboBox()
        self.combo_periodo.currentIndexChanged.connect(self._on_periodo_changed)
        header.addWidget(self.combo_periodo)

        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.setProperty("class", "PrimaryBtn")
        btn_refresh.clicked.connect(self.refresh_data)
        header.addWidget(btn_refresh)

        main_layout.addLayout(header)

        # 2. KPI Summary Cards
        kpi_layout = QHBoxLayout()
        self.card_ventas = self._create_kpi_card("Total Ventas", "S/ 0.00", "#10B981")
        self.card_egresos = self._create_kpi_card("Total Egresos", "S/ 0.00", "#F43F5E")
        self.card_saldo = self._create_kpi_card("Saldo Neto", "S/ 0.00", "#38BDF8")
        self.card_rentabilidad = self._create_kpi_card("Rentabilidad", "0.0%", "#F59E0B")

        kpi_layout.addWidget(self.card_ventas)
        kpi_layout.addWidget(self.card_egresos)
        kpi_layout.addWidget(self.card_saldo)
        kpi_layout.addWidget(self.card_rentabilidad)
        main_layout.addLayout(kpi_layout)

        # 3. Calendar Grid Container (Visual Mode)
        self.calendar_scroll = QScrollArea()
        self.calendar_scroll.setWidgetResizable(True)
        self.calendar_scroll.setFrameShape(QFrame.NoFrame)
        self.calendar_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.calendar_content = QWidget()
        self.calendar_layout = QVBoxLayout(self.calendar_content)
        self.calendar_layout.setContentsMargins(4, 4, 4, 4)
        self.calendar_layout.setSpacing(6)

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(8)
        self.calendar_layout.addWidget(self.grid_widget)
        self.calendar_scroll.setWidget(self.calendar_content)

        main_layout.addWidget(self.calendar_scroll)

        # 4. Detailed Table Container (Table Mode)
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
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self._on_table_double_clicked)
        self.table.setVisible(False)
        main_layout.addWidget(self.table)

        self._load_periodos()

    def _create_kpi_card(self, title: str, value: str, border_color: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: #111827; border-left: 4px solid {border_color}; border: 1px solid #1F2937; border-left-color: {border_color}; border-radius: 8px; padding: 8px;")
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 8, 12, 8)
        l.setSpacing(2)
        lbl_t = QLabel(title.upper())
        lbl_t.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        lbl_v = QLabel(value)
        lbl_v.setObjectName("val")
        lbl_v.setStyleSheet(f"color: {border_color}; font-size: 18px; font-weight: 800;")
        l.addWidget(lbl_t)
        l.addWidget(lbl_v)
        return w

    def _update_kpi(self, card: QWidget, text: str):
        lbl = card.findChild(QLabel, "val")
        if lbl:
            lbl.setText(text)

    def _toggle_view_mode(self):
        is_grid = self.btn_grid_mode.isChecked()
        self.calendar_scroll.setVisible(is_grid)
        self.table.setVisible(not is_grid)

    def _mostrar_grafica(self):
        sede_name = LOCAL_NAMES.get(self.current_local, self.current_local.upper())
        mes_nombre = self.combo_periodo.currentText()
        dlg = GraficaFinancieraDialog(self.cached_dias, mes_nombre, sede_name, self)
        dlg.exec()

    def _on_table_double_clicked(self, index):
        row = index.row()
        if 0 <= row < len(self.cached_dias):
            dia_info = self.cached_dias[row]
            dia_num = dia_info.get("dia", 1)
            dlg = DetalleDiaDialog(self.current_year, self.current_month, dia_num, self.current_local, parent=self)
            dlg.exec()

    def _copiar_whatsapp_mes(self):
        res = self.cached_resumen
        if not res:
            return
        sede_name = LOCAL_NAMES.get(self.current_local, self.current_local.upper())
        mes_nombre = self.combo_periodo.currentText()
        signo = "+" if res.get('saldo_neto', 0) > 0 else ""

        texto = (
            f"🌟 *REPORTE FINANCIERO MENSUAL — {sede_name.upper()}*\n"
            f"📅 *Período:* {mes_nombre}\n"
            f"───────────────────────────\n"
            f"💵 *INGRESOS / VENTAS:*\n"
            f"  • Efectivo: S/ {res.get('efectivo', 0):,.2f}\n"
            f"  • Yape / Digital: S/ {res.get('yape', 0):,.2f}\n"
            f"  • Tickets PNP ({res.get('cantidad_tickets', 0)}): S/ {res.get('venta_tickets', 0):,.2f}\n"
            f"  ➜ *TOTAL VENTAS:* S/ {res.get('total_ventas', 0):,.2f}\n"
            f"───────────────────────────\n"
            f"💸 *EGRESOS OPERATIVOS:*\n"
            f"  • Compras / Insumos: S/ {res.get('total_compras', 0):,.2f}\n"
            f"  • Gastos Operativos: S/ {res.get('total_gastos', 0):,.2f}\n"
            f"  • Planilla / Personal: S/ {res.get('total_personal', 0):,.2f}\n"
            f"  ➜ *TOTAL EGRESOS:* S/ {res.get('total_egresos', 0):,.2f}\n"
            f"───────────────────────────\n"
            f"⚖️ *SALDO NETO:* {signo}S/ {res.get('saldo_neto', 0):,.2f}\n"
            f"📊 *Rentabilidad Neta:* {res.get('rentabilidad_pct', 0):.1f}%\n"
            f"🌟 *LA PROVINCIAL* — Sistema de Control"
        )
        QApplication.clipboard().setText(texto)
        ToastManager.show_success("¡Reporte mensual copiado al portapapeles para WhatsApp!", self)

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
        sede_name = LOCAL_NAMES.get(local, local.upper())

        # 1. Update KPIs
        res = self.financiero_service.get_resumen_financiero_mes(anio, mes, local)
        self.cached_resumen = res
        self._update_kpi(self.card_ventas, f"S/ {res['total_ventas']:,.2f}")
        self._update_kpi(self.card_egresos, f"S/ {res['total_egresos']:,.2f}")
        
        saldo = res["saldo_neto"]
        signo = "+" if saldo > 0 else ""
        self._update_kpi(self.card_saldo, f"{signo}S/ {saldo:,.2f}")
        self._update_kpi(self.card_rentabilidad, f"{res['rentabilidad_pct']:.1f}%")

        # 2. Get Data Rows
        dias = self.financiero_service.get_calendario_financiero_mes(anio, mes, local)
        self.cached_dias = dias
        dias_by_num = {d["dia"]: d for d in dias}

        # 3. Rebuild Calendar Grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Weekday Headers: LUNES a DOMINGO
        dias_semana_nombres = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
        for col, col_name in enumerate(dias_semana_nombres):
            lbl_header = QLabel(col_name)
            lbl_header.setAlignment(Qt.AlignCenter)
            is_weekend = col in (5, 6)
            bg_col = "#1E1B4B" if is_weekend else "#1E293B"
            txt_col = "#A5B4FC" if is_weekend else "#94A3B8"
            lbl_header.setStyleSheet(f"""
                background-color: {bg_col};
                color: {txt_col};
                font-weight: 800;
                font-size: 11px;
                padding: 6px;
                border-radius: 6px;
            """)
            self.grid_layout.addWidget(lbl_header, 0, col)

        # Build Month Matrix (First day of week = 0: Monday)
        cal = calendar.Calendar(firstweekday=0)
        month_matrix = cal.monthdayscalendar(anio, mes)

        for row_idx, week in enumerate(month_matrix, start=1):
            for col_idx, day_num in enumerate(week):
                day_data = dias_by_num.get(day_num) if day_num > 0 else None
                tile = DayTileWidget(anio, mes, day_num, local, day_data, sede_name, self.popup_report, self)
                self.grid_layout.addWidget(tile, row_idx, col_idx)

        # 4. Populate Table
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

            saldo_val = d['saldo']
            signo_d = "+" if saldo_val > 0 else ""
            saldo_item = QTableWidgetItem(f"{signo_d}S/ {saldo_val:,.2f}")
            saldo_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            if saldo_val > 0:
                saldo_item.setForeground(QColor("#10B981"))
            elif saldo_val < 0:
                saldo_item.setForeground(QColor("#F43F5E"))
            else:
                saldo_item.setForeground(QColor("#94A3B8"))

            self.table.setItem(r, 12, saldo_item)
