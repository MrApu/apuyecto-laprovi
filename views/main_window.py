import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QPushButton, QLabel, QComboBox, QSpinBox, QFileDialog, QMessageBox,
    QButtonGroup, QFrame
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LA PROVINCIAL - Sistema de Gestión Comercial y Control Policial PNP")
        self.resize(1366, 850)
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

        # 1. Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(2)

        # App Brand
        brand_frame = QFrame()
        brand_frame.setStyleSheet("background-color: #111A22; padding: 14px 12px;")
        brand_l = QVBoxLayout(brand_frame)
        lbl_app = QLabel("LA PROVINCIAL")
        lbl_app.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: bold; letter-spacing: 1px;")
        lbl_sub = QLabel("Restaurante & Fast Food")
        lbl_sub.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: bold;")
        brand_l.addWidget(lbl_app)
        brand_l.addWidget(lbl_sub)
        sidebar_layout.addWidget(brand_frame)

        # Navigation Buttons
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        nav_items = [
            ("📊 Dashboard", 0),
            ("👮 Base de Policías", 1),
            ("📅 Calendario Policial", 2),
            ("🎫 Tickets por Policía", 3),
            ("🎟️ Vales Policiales", 4),
            ("💰 Pagos y Deudas", 5),
            ("📈 Ventas Diarias", 6),
            ("💸 Egresos (Compras/Gastos)", 7),
            ("📆 Calendario Financiero", 8),
            ("🍔 Consumo Fast Food", 9),
            ("📝 Observaciones", 10),
            ("📄 Reportes y Exportación", 11),
            ("⚙️ Configuración", 12),
            ("💾 Copias de Seguridad", 13),
        ]

        self.nav_buttons = []
        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            if index == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda _, idx=index: self._cambiar_vista(idx))
            self.btn_group.addButton(btn, index)
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Footer badge
        lbl_ver = QLabel("v2.5 Multi-Local\nSQLite Local")
        lbl_ver.setStyleSheet("color: #7F8C8D; font-size: 10px; padding: 12px; text-align: center;")
        sidebar_layout.addWidget(lbl_ver)

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
        top_layout.setContentsMargins(14, 8, 14, 8)
        top_layout.setSpacing(10)

        # Local Selector
        top_layout.addWidget(QLabel("<b>Local Activo:</b>"))
        self.cmb_local = QComboBox()
        self.cmb_local.addItem("🏢 RESTAURANTE", LOCAL_RESTAURANTE)
        self.cmb_local.addItem("🍔 FAST FOOD", LOCAL_FAST_FOOD)
        self.cmb_local.addItem("🌐 CONSOLIDADO GENERAL", LOCAL_CONSOLIDADO)
        self.cmb_local.setStyleSheet("background: #0284c7; color: white; font-weight: bold; padding: 4px 10px; border-radius: 4px;")
        self.cmb_local.currentIndexChanged.connect(self._on_local_changed)
        top_layout.addWidget(self.cmb_local)

        top_layout.addWidget(QLabel("<b>| Período:</b>"))

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

        self.btn_nuevo_mes = QPushButton("➕ Nuevo Mes")
        self.btn_nuevo_mes.setProperty("class", "PrimaryBtn")
        self.btn_nuevo_mes.clicked.connect(self._on_crear_nuevo_mes)
        top_layout.addWidget(self.btn_nuevo_mes)

        self.lbl_estado_mes = QLabel("Estado: ABIERTO")
        self.lbl_estado_mes.setStyleSheet("color: green; font-weight: bold; padding-left: 6px;")
        top_layout.addWidget(self.lbl_estado_mes)

        top_layout.addStretch()

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

    def _cargar_meses(self):
        meses = self.mes_service.get_all()
        if not meses:
            # Create default current month (September 2026)
            self.mes_service.crear_mes(2026, 9, 12.0)
            self.mes_service.crear_mes(2026, 8, 12.0)
            self.mes_service.crear_mes(2026, 7, 12.0)

    def _on_local_changed(self):
        self.current_local = self.cmb_local.currentData() or LOCAL_RESTAURANTE
        self._broadcast_local()

    def _broadcast_local(self):
        views_with_local = [
            self.view_dashboard, self.view_calendario, self.view_tickets,
            self.view_vales, self.view_pagos, self.view_ventas,
            self.view_egresos, self.view_cal_financiero, self.view_fast_food,
            self.view_reportes
        ]
        for v in views_with_local:
            if hasattr(v, "set_local"):
                v.set_local(self.current_local)

    def _on_periodo_changed(self):
        self.current_anio = self.cmb_anio.currentData() or 2026
        self.current_mes = self.cmb_mes.currentData() or 9
        self._sincronizar_periodo()

    def _sincronizar_periodo(self):
        m = self.mes_service.get_by_anio_mes(self.current_anio, self.current_mes)
        if not m:
            self.lbl_estado_mes.setText("Estado: NO INICIALIZADO")
            self.lbl_estado_mes.setStyleSheet("color: gray; font-weight: bold;")
        else:
            self.lbl_estado_mes.setText(f"Estado: {m.estado} | Precio: S/ {m.precio_ticket_policial:.2f}")
            if m.estado == "ABIERTO":
                self.lbl_estado_mes.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.lbl_estado_mes.setStyleSheet("color: red; font-weight: bold;")

        # Notify views
        self.view_dashboard.set_periodo(self.current_anio, self.current_mes)
        self.view_calendario.set_periodo(self.current_anio, self.current_mes)
        self.view_tickets.set_periodo(self.current_anio, self.current_mes)
        self.view_vales.set_periodo(self.current_anio, self.current_mes)
        self.view_pagos.set_periodo(self.current_anio, self.current_mes)
        self.view_ventas.set_periodo(self.current_anio, self.current_mes)
        self.view_observaciones.set_periodo(self.current_anio, self.current_mes)
        self.view_reportes.set_periodo(self.current_anio, self.current_mes)
        self._broadcast_local()

    def _cambiar_vista(self, index: int):
        self.stacked.setCurrentIndex(index)
        # Refresh current view
        widget = self.stacked.currentWidget()
        if hasattr(widget, "cargar_datos"):
            widget.cargar_datos()
        elif hasattr(widget, "refresh_data"):
            widget.refresh_data()

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
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Archivo Excel Actual",
            "",
            "Archivos Excel (*.xlsx *.xlsm *.csv)"
        )
        if filepath:
            resumen = self.excel_importer.importar_archivo(filepath, estrategia_policias="ACTUALIZAR")
            dlg = ImportSummaryDialog(self, resumen=resumen)
            dlg.exec()
            self._sincronizar_periodo()
            self.view_policias.cargar_datos()
            self.view_dashboard.cargar_datos()
