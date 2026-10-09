import os
from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QPushButton, QLabel, QComboBox, QSpinBox, QFileDialog, QMessageBox,
    QButtonGroup, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFont

from views.styles.theme import QSS_STYLE
from views.dashboard_view import DashboardView
from views.policias_view import PoliciasView
from views.calendario_view import CalendarioView
from views.tickets_policia_view import TicketsPoliciaView
from views.vales_view import ValesView
from views.pagos_view import PagosView
from views.ventas_view import VentasView
from views.egresos_view import EgresosView
from views.calendario_financiero_view import CalendarioFinancieroView
from views.fast_food_view import FastFoodView
from views.observaciones_view import ObservacionesView
from views.reportes_view import ReportesView
from views.configuracion_view import ConfiguracionView
from views.backup_view import BackupView

from views.dialogs.nuevo_mes_dialog import NuevoMesDialog
from views.dialogs.import_summary_dialog import ImportSummaryDialog
from services.mes_service import MesService
from imports.excel_importer import ExcelImporter
from models.mes import NOMBRES_MESES
from models.local import LOCAL_RESTAURANTE, LOCAL_FAST_FOOD, LOCAL_CONSOLIDADO, LOCAL_NAMES

class CollapsibleCategory(QWidget):
    """Grupo de navegación deslizable / colapsable para el Sidebar."""
    def __init__(self, title: str, icon: str, count_text: str = "", is_expanded: bool = True, parent=None):
        super().__init__(parent)
        self.is_expanded = is_expanded

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 4)
        layout.setSpacing(1)

        # Header button
        self.btn_header = QPushButton()
        self.btn_header.setCheckable(False)
        self.btn_header.setStyleSheet("""
            QPushButton {
                background-color: #111827;
                color: #F9FAFB;
                text-align: left;
                padding: 10px 14px;
                font-size: 12px;
                font-weight: 800;
                border: 1px solid #1F2937;
                border-radius: 8px;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #1E293B;
                border-color: #38BDF8;
                color: #38BDF8;
            }
        """)

        header_layout = QHBoxLayout(self.btn_header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_title = QLabel(f"{icon}  {title.upper()}")
        self.lbl_title.setStyleSheet("font-weight: 800; font-size: 11px; color: #E2E8F0; background: transparent;")
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()

        if count_text:
            lbl_cnt = QLabel(count_text)
            lbl_cnt.setStyleSheet("background: #1E293B; color: #94A3B8; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 8px;")
            header_layout.addWidget(lbl_cnt)

        self.lbl_arrow = QLabel("▾" if self.is_expanded else "▸")
        self.lbl_arrow.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: bold; background: transparent; padding-left: 4px;")
        header_layout.addWidget(self.lbl_arrow)

        self.btn_header.clicked.connect(self.toggle)
        layout.addWidget(self.btn_header)

        # Container for sub-items
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 2, 4, 4)
        self.content_layout.setSpacing(2)
        layout.addWidget(self.content_widget)

        self.content_widget.setVisible(self.is_expanded)

    def add_subitem(self, btn: QPushButton):
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #94A3B8;
                border: none;
                text-align: left;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: 600;
                border-radius: 6px;
                border-left: 3px solid transparent;
            }
            QPushButton:hover {
                background-color: #1E293B;
                color: #F8FAFC;
            }
            QPushButton:checked {
                background-color: #1E1B4B;
                color: #A5B4FC;
                border-left: 3px solid #6366F1;
                font-weight: 700;
            }
        """)
        self.content_layout.addWidget(btn)

    def toggle(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)
        self.lbl_arrow.setText("▾" if self.is_expanded else "▸")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LA PROVINCIAL — Sistema de Gestión Comercial y Control Policial PNP")
        self.resize(1400, 880)
        self.mes_service = MesService()
        self.excel_importer = ExcelImporter()

        self.current_local = LOCAL_RESTAURANTE
        self.current_anio = 2026
        self.current_mes = 9  # Septiembre

        self._init_ui()
        self._cargar_meses()
        self._sincronizar_periodo()

    def _init_ui(self):
        self.setStyleSheet(QSS_STYLE)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar (Accordion Navigation)
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Brand Header
        brand_frame = QFrame()
        brand_frame.setStyleSheet("background-color: #060911; padding: 14px 14px; border-bottom: 1px solid #1F2937;")
        brand_l = QVBoxLayout(brand_frame)
        brand_l.setSpacing(3)
        lbl_app = QLabel("LA PROVINCIAL")
        lbl_app.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 900; letter-spacing: 1.2px;")
        lbl_sub = QLabel("Restaurante & Fast Food")
        lbl_sub.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: 700;")
        brand_l.addWidget(lbl_app)
        brand_l.addWidget(lbl_sub)
        sidebar_layout.addWidget(brand_frame)

        # Scrollable Navigation Container
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QFrame.NoFrame)
        nav_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        nav_content = QWidget()
        nav_layout = QVBoxLayout(nav_content)
        nav_layout.setContentsMargins(10, 10, 10, 10)
        nav_layout.setSpacing(8)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        self.nav_buttons: Dict[int, QPushButton] = {}
        self.breadcrumbs: Dict[int, str] = {}

        # ==========================================
        # GRUPO 1: PANEL & DASHBOARD
        # ==========================================
        sec_dash = CollapsibleCategory("Panel & KPIs", "📊", "2", is_expanded=True)
        self._add_nav_item(sec_dash, "⚡ Dashboard Modular BI", 0, "Panel & KPIs > Dashboard Modular BI")
        self._add_nav_item(sec_dash, "📆 Calendario Financiero", 8, "Panel & KPIs > Calendario Financiero Diario")
        nav_layout.addWidget(sec_dash)

        # ==========================================
        # GRUPO 2: CONTROL POLICIAL PNP
        # ==========================================
        sec_pol = CollapsibleCategory("Control Policial", "👮", "5", is_expanded=True)
        self._add_nav_item(sec_pol, "📋 Base de Datos PNP", 1, "Control Policial > Base de Datos de Efectivos")
        self._add_nav_item(sec_pol, "📅 Calendario de Tickets", 2, "Control Policial > Calendario de Tickets Diarios")
        self._add_nav_item(sec_pol, "🎫 Matriz Mensual Tickets", 3, "Control Policial > Control Mensual por Efectivo")
        self._add_nav_item(sec_pol, "🎟️ Vales Policiales", 4, "Control Policial > Vales y Canjes")
        self._add_nav_item(sec_pol, "💰 Cobranzas y Deudas", 5, "Control Policial > Pagos y Deudas Pendientes")
        nav_layout.addWidget(sec_pol)

        # ==========================================
        # GRUPO 3: VENTAS Y EGRESOS
        # ==========================================
        sec_ventas = CollapsibleCategory("Ventas & Gastos", "💰", "3", is_expanded=True)
        self._add_nav_item(sec_ventas, "📈 Ventas Diarias (EF/YP)", 6, "Ventas & Gastos > Registro Diario de Ventas")
        self._add_nav_item(sec_ventas, "💸 Egresos (Compras/Gastos)", 7, "Ventas & Gastos > Compras, Gastos y Personal")
        self._add_nav_item(sec_ventas, "🍔 Consumo Fast Food", 9, "Ventas & Gastos > Control Consumo Fast Food")
        nav_layout.addWidget(sec_ventas)

        # ==========================================
        # GRUPO 4: REPORTES & SISTEMA
        # ==========================================
        sec_admin = CollapsibleCategory("Reportes & Ajustes", "⚙️", "4", is_expanded=False)
        self._add_nav_item(sec_admin, "📄 Reportes y Exportación", 11, "Reportes & Ajustes > Reportes PDF y Excel")
        self._add_nav_item(sec_admin, "📝 Bitácora Observaciones", 10, "Reportes & Ajustes > Observaciones y Novedades")
        self._add_nav_item(sec_admin, "⚙️ Configuración Precios", 12, "Reportes & Ajustes > Configuración del Sistema")
        self._add_nav_item(sec_admin, "💾 Copias de Seguridad", 13, "Reportes & Ajustes > Respaldo y Backups")
        nav_layout.addWidget(sec_admin)

        nav_layout.addStretch()
        nav_scroll.setWidget(nav_content)
        sidebar_layout.addWidget(nav_scroll)

        # Footer badge
        footer_frame = QFrame()
        footer_frame.setStyleSheet("background-color: #060911; padding: 10px; border-top: 1px solid #1F2937;")
        footer_l = QVBoxLayout(footer_frame)
        lbl_ver = QLabel("⚡ v3.0 Tremor BI Multi-Sede\nBase de datos SQLite activa")
        lbl_ver.setStyleSheet("color: #64748B; font-size: 10px; text-align: center;")
        lbl_ver.setAlignment(Qt.AlignCenter)
        footer_l.addWidget(lbl_ver)
        sidebar_layout.addWidget(footer_frame)

        main_layout.addWidget(sidebar)

        # 2. Right Content Area
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Top Bar
        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 8, 16, 8)
        top_layout.setSpacing(12)

        # Breadcrumb / Location
        self.lbl_breadcrumb = QLabel("📌 Panel & KPIs > Dashboard Modular BI")
        self.lbl_breadcrumb.setStyleSheet("color: #94A3B8; font-weight: 700; font-size: 13px;")
        top_layout.addWidget(self.lbl_breadcrumb)

        top_layout.addStretch()

        # Local Selector
        top_layout.addWidget(QLabel("<b>Sede:</b>"))
        self.cmb_local = QComboBox()
        self.cmb_local.addItem("🏢 RESTAURANTE", LOCAL_RESTAURANTE)
        self.cmb_local.addItem("🍔 FAST FOOD", LOCAL_FAST_FOOD)
        self.cmb_local.addItem("🌐 CONSOLIDADO GENERAL", LOCAL_CONSOLIDADO)
        self.cmb_local.setStyleSheet("""
            QComboBox {
                background: #6366F1;
                color: white;
                font-weight: 800;
                padding: 5px 12px;
                border-radius: 6px;
                border: none;
            }
            QComboBox:hover {
                background: #4F46E5;
            }
        """)
        self.cmb_local.currentIndexChanged.connect(self._on_local_changed)
        top_layout.addWidget(self.cmb_local)

        top_layout.addWidget(QLabel("<b>| Mes:</b>"))

        self.cmb_anio = QComboBox()
        for y in range(2024, 2031):
            self.cmb_anio.addItem(str(y), y)
        self.cmb_anio.setCurrentText(str(self.current_anio))
        self.cmb_anio.currentIndexChanged.connect(self._on_periodo_changed)
        top_layout.addWidget(self.cmb_anio)

        self.cmb_mes = QComboBox()
        for idx, m_name in enumerate(NOMBRES_MESES[1:], start=1):
            self.cmb_mes.addItem(f"{idx:02d} - {m_name}", idx)
        self.cmb_mes.setCurrentIndex(self.current_mes - 1)
        self.cmb_mes.currentIndexChanged.connect(self._on_periodo_changed)
        top_layout.addWidget(self.cmb_mes)

        self.btn_nuevo_mes = QPushButton("➕ Abrir Mes")
        self.btn_nuevo_mes.setProperty("class", "PrimaryBtn")
        self.btn_nuevo_mes.clicked.connect(self._on_crear_nuevo_mes)
        top_layout.addWidget(self.btn_nuevo_mes)

        self.lbl_estado_mes = QLabel("● ABIERTO")
        self.lbl_estado_mes.setStyleSheet("color: #10B981; font-weight: bold; padding-left: 4px; font-size: 11px;")
        top_layout.addWidget(self.lbl_estado_mes)

        top_layout.addSpacing(10)

        self.btn_importar_excel = QPushButton("📥 Importar Excel")
        self.btn_importar_excel.setProperty("class", "SuccessBtn")
        self.btn_importar_excel.clicked.connect(self._on_importar_excel)
        top_layout.addWidget(self.btn_importar_excel)

        right_layout.addWidget(top_bar)

        # Stacked Views
        self.stacked = QStackedWidget()

        self.view_dashboard = DashboardView()
        self.view_policias = PoliciasView()
        self.view_calendario = CalendarioView()
        self.view_tickets = TicketsPoliciaView()
        self.view_vales = ValesView()
        self.view_pagos = PagosView()
        self.view_ventas = VentasView()
        self.view_egresos = EgresosView()
        self.view_cal_financiero = CalendarioFinancieroView()
        self.view_fast_food = FastFoodView()
        self.view_observaciones = ObservacionesView()
        self.view_reportes = ReportesView()
        self.view_configuracion = ConfiguracionView()
        self.view_backup = BackupView()

        self.stacked.addWidget(self.view_dashboard)        # 0
        self.stacked.addWidget(self.view_policias)         # 1
        self.stacked.addWidget(self.view_calendario)       # 2
        self.stacked.addWidget(self.view_tickets)          # 3
        self.stacked.addWidget(self.view_vales)            # 4
        self.stacked.addWidget(self.view_pagos)            # 5
        self.stacked.addWidget(self.view_ventas)           # 6
        self.stacked.addWidget(self.view_egresos)          # 7
        self.stacked.addWidget(self.view_cal_financiero)   # 8
        self.stacked.addWidget(self.view_fast_food)        # 9
        self.stacked.addWidget(self.view_observaciones)    # 10
        self.stacked.addWidget(self.view_reportes)         # 11
        self.stacked.addWidget(self.view_configuracion)    # 12
        self.stacked.addWidget(self.view_backup)           # 13

        right_layout.addWidget(self.stacked)
        main_layout.addWidget(right_panel)

        # Set default active item
        if 0 in self.nav_buttons:
            self.nav_buttons[0].setChecked(True)

    def _add_nav_item(self, category: CollapsibleCategory, title: str, index: int, breadcrumb: str):
        btn = QPushButton(title)
        btn.setCheckable(True)
        btn.clicked.connect(lambda _, idx=index: self._cambiar_vista(idx))
        self.btn_group.addButton(btn, index)
        category.add_subitem(btn)
        self.nav_buttons[index] = btn
        self.breadcrumbs[index] = breadcrumb

    def _cargar_meses(self):
        meses = self.mes_service.get_all()
        if not meses:
            self.mes_service.crear_mes(2026, 9, 12.0)
            self.mes_service.crear_mes(2026, 8, 12.0)
            self.mes_service.crear_mes(2026, 7, 12.0)

    def _on_local_changed(self, index: Optional[int] = None):
        self.current_local = self.cmb_local.currentData() or LOCAL_RESTAURANTE
        self._broadcast_local()

    def _broadcast_local(self):
        self.view_dashboard.set_local(self.current_local)
        self.view_ventas.set_local(self.current_local)
        self.view_egresos.set_local(self.current_local)
        self.view_cal_financiero.set_local(self.current_local)
        self.view_reportes.set_local(self.current_local)
        if hasattr(self.view_calendario, "set_local"):
            self.view_calendario.set_local(self.current_local)
        if hasattr(self.view_tickets, "set_local"):
            self.view_tickets.set_local(self.current_local)
        if hasattr(self.view_vales, "set_local"):
            self.view_vales.set_local(self.current_local)
        if hasattr(self.view_pagos, "set_local"):
            self.view_pagos.set_local(self.current_local)

    def _on_periodo_changed(self):
        self.current_anio = int(self.cmb_anio.currentText())
        self.current_mes = self.cmb_mes.currentIndex() + 1
        self._sincronizar_periodo()

    def _sincronizar_periodo(self):
        mes = self.mes_service.get_by_anio_mes(self.current_anio, self.current_mes)
        if mes:
            st = "● CERRADO" if mes.estado == "CERRADO" else "● ABIERTO"
            color = "#EF4444" if mes.estado == "CERRADO" else "#10B981"
            self.lbl_estado_mes.setText(st)
            self.lbl_estado_mes.setStyleSheet(f"color: {color}; font-weight: bold; padding-left: 4px; font-size: 11px;")
        else:
            self.lbl_estado_mes.setText("● NO CREADO")
            self.lbl_estado_mes.setStyleSheet("color: #F59E0B; font-weight: bold; padding-left: 4px; font-size: 11px;")

        self.view_dashboard.set_periodo(self.current_anio, self.current_mes)
        self.view_calendario.set_periodo(self.current_anio, self.current_mes)
        self.view_tickets.set_periodo(self.current_anio, self.current_mes)
        self.view_vales.set_periodo(self.current_anio, self.current_mes)
        self.view_pagos.set_periodo(self.current_anio, self.current_mes)
        self.view_ventas.set_periodo(self.current_anio, self.current_mes)
        self.view_egresos.set_periodo(self.current_anio, self.current_mes)
        self.view_cal_financiero.set_periodo(self.current_anio, self.current_mes)
        self.view_fast_food.set_periodo(self.current_anio, self.current_mes)
        self.view_reportes.set_periodo(self.current_anio, self.current_mes)

    def _cambiar_vista(self, index: int):
        self.stacked.setCurrentIndex(index)
        b_text = self.breadcrumbs.get(index, "Panel Principal")
        self.lbl_breadcrumb.setText(f"📌 {b_text}")
        if index in self.nav_buttons:
            self.nav_buttons[index].setChecked(True)

    def _on_crear_nuevo_mes(self):
        dlg = NuevoMesDialog(self)
        if dlg.exec():
            anio, mes, precio = dlg.get_datos()
            ok, msg, mes_id = self.mes_service.crear_mes(anio, mes, precio)
            if ok:
                QMessageBox.information(self, "Mes Creado", msg)
                self.cmb_anio.setCurrentText(str(anio))
                self.cmb_mes.setCurrentIndex(mes - 1)
                self._sincronizar_periodo()
            else:
                QMessageBox.warning(self, "Aviso", msg)

    def _on_importar_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Archivo Excel de Control",
            "",
            "Archivos Excel (*.xlsx *.xlsm *.csv)"
        )
        if not file_path:
            return

        resumen = self.excel_importer.importar_archivo(file_path, estrategia_policias="ACTUALIZAR", local_id=self.current_local)
        dlg = ImportSummaryDialog(resumen, self)
        dlg.exec()

        self._sincronizar_periodo()
        self.view_policias.cargar_datos()
        self.view_dashboard.cargar_datos()
