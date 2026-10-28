from typing import Optional, List, Dict, Any
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QSpinBox, QDoubleSpinBox, QLineEdit,
    QButtonGroup, QFrame, QProgressBar, QTabWidget, QSplitter, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from models.pago import PagoTicket
from models.cuenta_ticket import MovimientoTicket, ResumenCuentaPolicia
from services.cuenta_ticket_service import CuentaTicketService
from services.pago_service import PagoService
from services.ticket_service import TicketService
from services.mes_service import MesService
from models.local import LOCAL_RESTAURANTE, LOCAL_NAMES
from views.components.toast import ToastManager
from views.dialogs.detalle_dia_dialog import DetalleDiaDialog
from views.dialogs.registrar_deuda_ticket_dialog import RegistrarDeudaTicketDialog
from views.dialogs.registrar_pago_cuenta_dialog import RegistrarPagoCuentaDialog

class PagosView(QWidget):
    """
    Control de Cobranzas y Deudas independiente de la matriz policial:
    - Lista de quiénes deben tickets y quiénes han pagado tickets.
    - Buscador en tiempo real conectado a la base de datos que descarta los demás nombres al escribir.
    - Ficha de cuenta corriente por policía con botones directos:
      ➕ Debe Tickets  y  💵 Pagó Tickets.
    - Resumen Diario consolidado para auditoría.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cuenta_service = CuentaTicketService()
        self.pago_service = PagoService()
        self.ticket_service = TicketService()
        self.mes_service = MesService()
        self.current_anio = 2026
        self.current_mes = 9
        self.current_local = LOCAL_RESTAURANTE
        self.precio_menu = 12.0
        self.active_chip = "TODOS"

        self.resumen_cuentas: List[ResumenCuentaPolicia] = []
        self.selected_policia: Optional[ResumenCuentaPolicia] = None
        self.widgets: Dict[int, Dict[str, Any]] = {}

        self._init_ui()

    def set_local(self, local_id: str):
        self.current_local = local_id
        self.lbl_local_badge.setText(f"📍 Sede: {LOCAL_NAMES.get(local_id, local_id.upper())}")
        self.cargar_datos()

    def set_periodo(self, anio: int, mes: int):
        self.current_anio = anio
        self.current_mes = mes
        m = self.mes_service.get_by_anio_mes(anio, mes)
        self.precio_menu = m.precio_ticket_policial if m else 12.0
        self.lbl_title.setText(f"💰 COBRANZAS: QUIÉN DEBE Y QUIÉN PAGA TICKETS — {mes:02d}/{anio}")
        self.cargar_datos()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header principal
        header_box = QHBoxLayout()
        self.lbl_title = QLabel(f"💰 COBRANZAS: QUIÉN DEBE Y QUIÉN PAGA TICKETS — {self.current_mes:02d}/{self.current_anio}")
        self.lbl_title.setStyleSheet("font-size: 17px; font-weight: 800; color: #FFFFFF;")
        header_box.addWidget(self.lbl_title)

        self.lbl_local_badge = QLabel(f"📍 Sede: {LOCAL_NAMES.get(self.current_local, 'RESTAURANTE')}")
        self.lbl_local_badge.setStyleSheet("""
            background: #18181B;
            color: #DC2626;
            padding: 4px 10px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 11px;
            border: 1px solid #27272A;
        """)
        header_box.addWidget(self.lbl_local_badge)
        header_box.addStretch()

        self.btn_guardar_todo = QPushButton("💾 Guardar Control Diario")
        self.btn_guardar_todo.setCursor(Qt.PointingHandCursor)
        self.btn_guardar_todo.setStyleSheet("""
            background-color: #10B981;
            color: #FFFFFF;
            font-weight: bold;
            padding: 6px 14px;
            border-radius: 6px;
        """)
        self.btn_guardar_todo.clicked.connect(self._on_guardar_todo)
        header_box.addWidget(self.btn_guardar_todo)

        layout.addLayout(header_box)

        # Pestañas principales
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #27272A;
                background: #0A0A0A;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #18181B;
                color: #A1A1AA;
                padding: 8px 18px;
                font-weight: 700;
                font-size: 12px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #DC2626;
                color: #FFFFFF;
            }
        """)

        # Pestaña 1: Quién Debe y Quién Paga (Cuenta Corriente por Policía)
        tab_cuentas = self._build_tab_cuentas()
        self.tabs.addTab(tab_cuentas, "👮 Quién Debe y Quién Paga (Por Policía)")

        # Pestaña 2: Historial de Tickets Pagados
        tab_pagados = self._build_tab_historial_pagados()
        self.tabs.addTab(tab_pagados, "🟢 Lista de Tickets Pagados")

        # Pestaña 3: Historial de Deudas Registradas
        tab_deudas = self._build_tab_historial_deudas()
        self.tabs.addTab(tab_deudas, "🔴 Lista de Deudas (Debe Tickets)")

        # Pestaña 4: Control Diario Consolidado
        tab_diario = self._build_tab_diario()
        self.tabs.addTab(tab_diario, "📅 Control Diario por Fecha")

        layout.addWidget(self.tabs)

    def _build_tab_cuentas(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(10)

        # Buscador y filtros
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        self.txt_busqueda = QLineEdit()
        self.txt_busqueda.setPlaceholderText("🔍 Buscar policía en base de datos por apellidos, nombres, código... (descarte en tiempo real)")
        self.txt_busqueda.setStyleSheet("""
            QLineEdit {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #3F3F46;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 13px;
                font-weight: 600;
            }
            QLineEdit:focus {
                border: 1px solid #DC2626;
            }
        """)
        self.txt_busqueda.textChanged.connect(self._on_busqueda_changed)
        top_bar.addWidget(self.txt_busqueda, 4)

        # Chips de filtro
        self.chip_group = QButtonGroup(self)
        self.chip_group.setExclusive(True)

        chips = [
            ("🔘 Todos los Policías", "TODOS"),
            ("🔴 Con Deuda Pendiente", "DEUDA"),
            ("🟢 Al Día (Sin Deuda)", "AL_DIA")
        ]
        for idx, (lbl, key) in enumerate(chips):
            btn = QPushButton(lbl)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            if key == "TODOS":
                btn.setChecked(True)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #18181B;
                    color: #A1A1AA;
                    border: 1px solid #27272A;
                    border-radius: 14px;
                    padding: 5px 12px;
                    font-size: 11px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    color: #FFFFFF;
                    border-color: #DC2626;
                }
                QPushButton:checked {
                    background-color: #7F1D1D;
                    color: #FFFFFF;
                    border: 1px solid #DC2626;
                }
            """)
            btn.clicked.connect(lambda _, k=key: self._on_chip_clicked(k))
            self.chip_group.addButton(btn, idx)
            top_bar.addWidget(btn)

        l.addLayout(top_bar)

        # KPIs Globales de Cuentas
        kpi_row = QHBoxLayout()
        self.lbl_kpi_total_debe = QLabel("0")
        self.lbl_kpi_total_pago = QLabel("0")
        self.lbl_kpi_saldo_pend = QLabel("0")
        self.lbl_kpi_monto_deuda = QLabel("S/ 0.00")

        kpi_row.addWidget(self._create_kpi_card("TICKETS REGISTRADOS QUE DEBEN", self.lbl_kpi_total_debe, "#EF4444"))
        kpi_row.addWidget(self._create_kpi_card("TICKETS PAGADOS", self.lbl_kpi_total_pago, "#10B981"))
        kpi_row.addWidget(self._create_kpi_card("SALDO PENDIENTE (DEBEN)", self.lbl_kpi_saldo_pend, "#F59E0B"))
        kpi_row.addWidget(self._create_kpi_card("DEUDA TOTAL POR COBRAR", self.lbl_kpi_monto_deuda, "#DC2626"))
        l.addLayout(kpi_row)

        # Splitter: Tabla a la izquierda, Ficha a la derecha
        splitter = QSplitter(Qt.Horizontal)

        # Panel Izquierdo: Tabla de Policías
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self.tbl_policias = QTableWidget()
        self.tbl_policias.setColumnCount(8)
        self.tbl_policias.setHorizontalHeaderLabels([
            "Código", "Policía / Apellidos y Nombres", "Área", "Tickets que Debe",
            "Tickets Pagados", "Saldo Pendiente (Debe)", "Monto Deuda (S/)", "Estado"
        ])
        self.tbl_policias.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl_policias.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl_policias.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl_policias.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tbl_policias.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tbl_policias.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tbl_policias.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.tbl_policias.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.tbl_policias.setAlternatingRowColors(True)
        self.tbl_policias.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_policias.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_policias.itemSelectionChanged.connect(self._on_policia_selection_changed)
        left_layout.addWidget(self.tbl_policias)

        splitter.addWidget(left_widget)

        # Panel Derecho: Ficha Interactiva del Policía Seleccionado
        right_widget = self._build_panel_ficha()
        splitter.addWidget(right_widget)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        l.addWidget(splitter)

        return w

    def _build_panel_ficha(self) -> QWidget:
        w = QFrame()
        w.setStyleSheet("background-color: #111827; border: 1px solid #1F2937; border-radius: 8px;")
        l = QVBoxLayout(w)
        l.setContentsMargins(14, 14, 14, 14)
        l.setSpacing(10)

        lbl_hdr = QLabel("👮 FICHA DE CUENTA CORRIENTE DE TICKETS")
        lbl_hdr.setStyleSheet("font-size: 12px; font-weight: 800; color: #DC2626; letter-spacing: 0.5px;")
        l.addWidget(lbl_hdr)

        self.lbl_ficha_nombre = QLabel("Seleccione un policía en la lista")
        self.lbl_ficha_nombre.setStyleSheet("font-size: 15px; font-weight: 800; color: #FFFFFF;")
        self.lbl_ficha_nombre.setWordWrap(True)
        l.addWidget(self.lbl_ficha_nombre)

        self.lbl_ficha_codigo_area = QLabel("Código: - | Área: -")
        self.lbl_ficha_codigo_area.setStyleSheet("font-size: 11px; color: #94A3B8;")
        l.addWidget(self.lbl_ficha_codigo_area)

        # Mini tarjetas de impacto
        row_cards = QHBoxLayout()
        row_cards.setSpacing(6)

        self.card_debe = self._create_mini_box("TOTAL QUE DEBE", "0", "S/ 0.00", "#EF4444")
        self.card_pago = self._create_mini_box("TOTAL PAGADO", "0", "S/ 0.00", "#10B981")
        self.card_saldo = self._create_mini_box("SALDO ACTUAL (DEBE)", "0", "S/ 0.00", "#F59E0B")

        row_cards.addWidget(self.card_debe)
        row_cards.addWidget(self.card_pago)
        row_cards.addWidget(self.card_saldo)
        l.addLayout(row_cards)

        # Botones de Acción Directa
        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)

        self.btn_debe_tickets = QPushButton("➕ Debe Tickets")
        self.btn_debe_tickets.setCursor(Qt.PointingHandCursor)
        self.btn_debe_tickets.setStyleSheet("""
            background-color: #DC2626;
            color: #FFFFFF;
            font-weight: 800;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
        """)
        self.btn_debe_tickets.clicked.connect(self._on_registrar_debe)
        btn_box.addWidget(self.btn_debe_tickets)

        self.btn_pago_tickets = QPushButton("💵 Pagó Tickets")
        self.btn_pago_tickets.setCursor(Qt.PointingHandCursor)
        self.btn_pago_tickets.setStyleSheet("""
            background-color: #10B981;
            color: #FFFFFF;
            font-weight: 800;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
        """)
        self.btn_pago_tickets.clicked.connect(self._on_registrar_pago)
        btn_box.addWidget(self.btn_pago_tickets)

        l.addLayout(btn_box)

        # Historial de Movimientos del Policía
        lbl_hist = QLabel("Historial de Movimientos (Debe y Pagos):")
        lbl_hist.setStyleSheet("color: #E4E4E7; font-size: 12px; font-weight: 700; margin-top: 6px;")
        l.addWidget(lbl_hist)

        self.tbl_historial_policia = QTableWidget()
        self.tbl_historial_policia.setColumnCount(6)
        self.tbl_historial_policia.setHorizontalHeaderLabels(["Fecha", "Tipo", "Tickets", "Monto", "Detalle", "Acción"])
        self.tbl_historial_policia.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl_historial_policia.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_historial_policia.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl_historial_policia.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tbl_historial_policia.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.tbl_historial_policia.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.tbl_historial_policia.setColumnWidth(5, 50)
        self.tbl_historial_policia.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_historial_policia.setSelectionBehavior(QTableWidget.SelectRows)
        l.addWidget(self.tbl_historial_policia)

        return w

    def _create_mini_box(self, title: str, main_val: str, sub_val: str, color: str) -> QWidget:
        w = QFrame()
        w.setStyleSheet(f"background: #18181B; border: 1px solid #27272A; border-top: 3px solid {color}; border-radius: 6px;")
        l = QVBoxLayout(w)
        l.setContentsMargins(6, 6, 6, 6)
        l.setSpacing(2)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("color: #94A3B8; font-size: 9px; font-weight: 800;")
        l.addWidget(lbl_t)

        lbl_m = QLabel(main_val)
        lbl_m.setObjectName("main_val")
        lbl_m.setStyleSheet(f"color: {color}; font-size: 15px; font-weight: 900;")
        l.addWidget(lbl_m)

        lbl_s = QLabel(sub_val)
        lbl_s.setObjectName("sub_val")
        lbl_s.setStyleSheet("color: #A1A1AA; font-size: 10px; font-weight: 600;")
        l.addWidget(lbl_s)

        return w

    def _build_tab_historial_pagados(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(8)

        lbl_info = QLabel("🟢 <b>Lista General de Tickets Pagados:</b> Registro de todos los pagos realizados por el personal.")
        lbl_info.setStyleSheet("background-color: #18181B; color: #10B981; border-left: 4px solid #10B981; padding: 8px 12px; border-radius: 4px;")
        l.addWidget(lbl_info)

        self.tbl_pagados_general = QTableWidget()
        self.tbl_pagados_general.setColumnCount(7)
        self.tbl_pagados_general.setHorizontalHeaderLabels([
            "Fecha", "Código", "Policía / Nombre", "Tickets Pagados", "Monto Cobrado (S/)", "Medio de Pago", "Acción"
        ])
        self.tbl_pagados_general.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl_pagados_general.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_pagados_general.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl_pagados_general.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tbl_pagados_general.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tbl_pagados_general.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tbl_pagados_general.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.tbl_pagados_general.setColumnWidth(6, 60)
        self.tbl_pagados_general.setAlternatingRowColors(True)
        self.tbl_pagados_general.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_pagados_general.setEditTriggers(QTableWidget.NoEditTriggers)
        l.addWidget(self.tbl_pagados_general)

        return w

    def _build_tab_historial_deudas(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(8)

        lbl_info = QLabel("🔴 <b>Lista General de Deudas (Debe Tickets):</b> Registro de todos los tickets fiados / adeudados.")
        lbl_info.setStyleSheet("background-color: #18181B; color: #EF4444; border-left: 4px solid #EF4444; padding: 8px 12px; border-radius: 4px;")
        l.addWidget(lbl_info)

        self.tbl_deudas_general = QTableWidget()
        self.tbl_deudas_general.setColumnCount(7)
        self.tbl_deudas_general.setHorizontalHeaderLabels([
            "Fecha", "Código", "Policía / Nombre", "Tickets que Debe", "Monto Deuda (S/)", "Observación", "Acción"
        ])
        self.tbl_deudas_general.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl_deudas_general.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_deudas_general.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl_deudas_general.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tbl_deudas_general.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tbl_deudas_general.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.tbl_deudas_general.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.tbl_deudas_general.setColumnWidth(6, 60)
        self.tbl_deudas_general.setAlternatingRowColors(True)
        self.tbl_deudas_general.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_deudas_general.setEditTriggers(QTableWidget.NoEditTriggers)
        l.addWidget(self.tbl_deudas_general)

        return w

    def _build_tab_diario(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(10)

        # KPI Summary Row Diario
        kpi_row = QHBoxLayout()
        self.lbl_kpi_total_tickets = QLabel("0")
        self.lbl_kpi_pagados = QLabel("0")
        self.lbl_kpi_debidos = QLabel("0")
        self.lbl_kpi_monto_pend = QLabel("S/ 0.00")

        kpi_row.addWidget(self._create_kpi_card("Total Tickets", self.lbl_kpi_total_tickets, "#818CF8"))
        kpi_row.addWidget(self._create_kpi_card("Tickets Cobrados", self.lbl_kpi_pagados, "#10B981"))
        kpi_row.addWidget(self._create_kpi_card("Tickets Debidos", self.lbl_kpi_debidos, "#F43F5E"))
        kpi_row.addWidget(self._create_kpi_card("Deuda Pendiente", self.lbl_kpi_monto_pend, "#F59E0B"))
        l.addLayout(kpi_row)

        # Table Diario
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Fecha", "Total Tickets", "Pagados (*)", "Debidos (*)", "Progreso Cobro",
            "Estado", "Monto Cobrado (S/)", "Deuda Pendiente (S/)", "Observaciones"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_table_double_clicked)
        l.addWidget(self.table)

        return w

    def _create_kpi_card(self, title: str, val_lbl: QLabel, color: str) -> QWidget:
        w = QFrame()
        w.setStyleSheet(f"background: #111827; border: 1px solid #1F2937; border-left: 4px solid {color}; border-radius: 8px; padding: 6px;")
        l = QVBoxLayout(w)
        l.setContentsMargins(10, 6, 10, 6)
        l.setSpacing(2)
        lbl_t = QLabel(title.upper())
        lbl_t.setStyleSheet("color: #94A3B8; font-size: 10px; font-weight: 800; letter-spacing: 0.5px;")
        val_lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 800;")
        l.addWidget(lbl_t)
        l.addWidget(val_lbl)
        return w

    def _on_busqueda_changed(self, text: str):
        self._render_tabla_policias()

    def _on_chip_clicked(self, key: str):
        self.active_chip = key
        self._render_tabla_policias()

    def cargar_datos(self):
        # 1. Cargar cuentas independientes de tickets
        self.resumen_cuentas = self.cuenta_service.get_resumen_cuentas()
        self._render_tabla_policias()

        # 2. Cargar listas de pagos y deudas
        self._render_listas_movimientos()

        # 3. Cargar datos diarios
        self._cargar_datos_diarios()

    def _render_tabla_policias(self):
        busqueda = self.txt_busqueda.text().strip().upper()
        filtrados: List[ResumenCuentaPolicia] = []

        for p in self.resumen_cuentas:
            # Filtro texto (descarte automático)
            if busqueda:
                full_text = f"{p.codigo} {p.apellidos} {p.nombres} {p.area} {p.sa_pnp or ''}".upper()
                if busqueda not in full_text:
                    continue

            # Filtro chip
            if self.active_chip == "DEUDA" and p.saldo_tickets_debe <= 0:
                continue
            elif self.active_chip == "AL_DIA" and p.saldo_tickets_debe > 0:
                continue

            filtrados.append(p)

        # Actualizar KPIs globales
        tot_debe = sum(p.tickets_debe_total for p in self.resumen_cuentas)
        tot_pago = sum(p.tickets_pago_total for p in self.resumen_cuentas)
        saldo_pend = sum(p.saldo_tickets_debe for p in self.resumen_cuentas if p.saldo_tickets_debe > 0)
        monto_pend = sum(p.saldo_monto_debe for p in self.resumen_cuentas if p.saldo_monto_debe > 0)

        self.lbl_kpi_total_debe.setText(str(tot_debe))
        self.lbl_kpi_total_pago.setText(str(tot_pago))
        self.lbl_kpi_saldo_pend.setText(str(saldo_pend))
        self.lbl_kpi_monto_deuda.setText(f"S/ {monto_pend:,.2f}")

        # Renderizar filas
        self.tbl_policias.setRowCount(len(filtrados))
        self.visible_policias = filtrados

        for r, p in enumerate(filtrados):
            self.tbl_policias.setItem(r, 0, QTableWidgetItem(p.codigo))

            it_nom = QTableWidgetItem(f"{p.apellidos}, {p.nombres}")
            it_nom.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.tbl_policias.setItem(r, 1, it_nom)

            self.tbl_policias.setItem(r, 2, QTableWidgetItem(p.area))

            it_deb_t = QTableWidgetItem(str(p.tickets_debe_total))
            it_deb_t.setTextAlignment(Qt.AlignCenter)
            self.tbl_policias.setItem(r, 3, it_deb_t)

            it_pag_t = QTableWidgetItem(str(p.tickets_pago_total))
            it_pag_t.setTextAlignment(Qt.AlignCenter)
            it_pag_t.setForeground(QColor("#10B981"))
            self.tbl_policias.setItem(r, 4, it_pag_t)

            it_sal = QTableWidgetItem(str(p.saldo_tickets_debe))
            it_sal.setTextAlignment(Qt.AlignCenter)
            if p.saldo_tickets_debe > 0:
                it_sal.setForeground(QColor("#EF4444"))
                it_sal.setFont(QFont("Segoe UI", 9, QFont.Bold))
            elif p.saldo_tickets_debe == 0:
                it_sal.setForeground(QColor("#10B981"))
            self.tbl_policias.setItem(r, 5, it_sal)

            it_monto = QTableWidgetItem(f"S/ {p.saldo_monto_debe:.2f}")
            it_monto.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if p.saldo_monto_debe > 0:
                it_monto.setForeground(QColor("#EF4444"))
                it_monto.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.tbl_policias.setItem(r, 6, it_monto)

            it_est = QTableWidgetItem(p.estado)
            it_est.setTextAlignment(Qt.AlignCenter)
            if p.estado == "DEBE":
                it_est.setForeground(QColor("#EF4444"))
            else:
                it_est.setForeground(QColor("#10B981"))
            self.tbl_policias.setItem(r, 7, it_est)

        # Seleccionar primero si existe
        if filtrados:
            self.tbl_policias.selectRow(0)
            self._actualizar_panel_ficha(filtrados[0])
        else:
            self._limpiar_panel_ficha()

    def _render_listas_movimientos(self):
        # 1. Lista de pagos
        pagos = self.cuenta_service.get_movimientos_pagos()
        self.tbl_pagados_general.setRowCount(len(pagos))
        for r, m in enumerate(pagos):
            self.tbl_pagados_general.setItem(r, 0, QTableWidgetItem(m.fecha))
            self.tbl_pagados_general.setItem(r, 1, QTableWidgetItem(m.policia_codigo or "-"))
            self.tbl_pagados_general.setItem(r, 2, QTableWidgetItem(m.policia_nombre_completo))

            it_t = QTableWidgetItem(str(m.cantidad_tickets))
            it_t.setTextAlignment(Qt.AlignCenter)
            it_t.setForeground(QColor("#10B981"))
            self.tbl_pagados_general.setItem(r, 3, it_t)

            it_m = QTableWidgetItem(f"S/ {m.monto_total:.2f}")
            it_m.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_pagados_general.setItem(r, 4, it_m)

            self.tbl_pagados_general.setItem(r, 5, QTableWidgetItem(m.medio_pago or "EFECTIVO"))

            btn_d = QPushButton("🗑️")
            btn_d.setCursor(Qt.PointingHandCursor)
            btn_d.setStyleSheet("background: transparent; color: #EF4444; font-size: 12px;")
            btn_d.clicked.connect(lambda _, m_id=m.id: self._eliminar_movimiento(m_id))
            self.tbl_pagados_general.setCellWidget(r, 6, btn_d)

        # 2. Lista de deudas
        deudas = self.cuenta_service.get_movimientos_deudas()
        self.tbl_deudas_general.setRowCount(len(deudas))
        for r, m in enumerate(deudas):
            self.tbl_deudas_general.setItem(r, 0, QTableWidgetItem(m.fecha))
            self.tbl_deudas_general.setItem(r, 1, QTableWidgetItem(m.policia_codigo or "-"))
            self.tbl_deudas_general.setItem(r, 2, QTableWidgetItem(m.policia_nombre_completo))

            it_t = QTableWidgetItem(str(m.cantidad_tickets))
            it_t.setTextAlignment(Qt.AlignCenter)
            it_t.setForeground(QColor("#EF4444"))
            self.tbl_deudas_general.setItem(r, 3, it_t)

            it_m = QTableWidgetItem(f"S/ {m.monto_total:.2f}")
            it_m.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_deudas_general.setItem(r, 4, it_m)

            self.tbl_deudas_general.setItem(r, 5, QTableWidgetItem(m.observacion or "-"))

            btn_d = QPushButton("🗑️")
            btn_d.setCursor(Qt.PointingHandCursor)
            btn_d.setStyleSheet("background: transparent; color: #EF4444; font-size: 12px;")
            btn_d.clicked.connect(lambda _, m_id=m.id: self._eliminar_movimiento(m_id))
            self.tbl_deudas_general.setCellWidget(r, 6, btn_d)

    def _on_policia_selection_changed(self):
        sel = self.tbl_policias.selectedItems()
        if not sel:
            return
        row = sel[0].row()
        if 0 <= row < len(self.visible_policias):
            pol = self.visible_policias[row]
            self._actualizar_panel_ficha(pol)

    def _actualizar_panel_ficha(self, p: ResumenCuentaPolicia):
        self.selected_policia = p
        self.lbl_ficha_nombre.setText(f"{p.apellidos}, {p.nombres}")
        self.lbl_ficha_codigo_area.setText(f"Código: {p.codigo} | Área: {p.area} | Estado: {p.estado}")

        self._update_mini_box(self.card_debe, f"{p.tickets_debe_total} Tickets", f"S/ {p.monto_debe_total:.2f}")
        self._update_mini_box(self.card_pago, f"{p.tickets_pago_total} Tickets", f"S/ {p.monto_pago_total:.2f}")
        self._update_mini_box(self.card_saldo, f"{p.saldo_tickets_debe} Tickets", f"S/ {p.saldo_monto_debe:.2f}")

        # Cargar historial del policía
        movs = self.cuenta_service.get_movimientos_by_policia(p.policia_id)
        self.tbl_historial_policia.setRowCount(len(movs))
        for r, m in enumerate(movs):
            self.tbl_historial_policia.setItem(r, 0, QTableWidgetItem(m.fecha))

            it_tipo = QTableWidgetItem("🔴 DEBE" if m.tipo_movimiento == "DEBE" else "🟢 PAGÓ")
            if m.tipo_movimiento == "DEBE":
                it_tipo.setForeground(QColor("#EF4444"))
            else:
                it_tipo.setForeground(QColor("#10B981"))
            self.tbl_historial_policia.setItem(r, 1, it_tipo)

            it_tk = QTableWidgetItem(str(m.cantidad_tickets))
            it_tk.setTextAlignment(Qt.AlignCenter)
            self.tbl_historial_policia.setItem(r, 2, it_tk)

            it_m = QTableWidgetItem(f"S/ {m.monto_total:.2f}")
            it_m.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_historial_policia.setItem(r, 3, it_m)

            det = m.observacion or (f"Vía {m.medio_pago}" if m.tipo_movimiento == "PAGO" else "-")
            self.tbl_historial_policia.setItem(r, 4, QTableWidgetItem(det))

            btn_del = QPushButton("🗑️")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setStyleSheet("background: transparent; color: #EF4444; font-size: 12px;")
            btn_del.clicked.connect(lambda _, m_id=m.id: self._eliminar_movimiento(m_id))
            self.tbl_historial_policia.setCellWidget(r, 5, btn_del)

    def _update_mini_box(self, card: QWidget, main_val: str, sub_val: str):
        lbl_m = card.findChild(QLabel, "main_val")
        if lbl_m:
            lbl_m.setText(main_val)
        lbl_s = card.findChild(QLabel, "sub_val")
        if lbl_s:
            lbl_s.setText(sub_val)

    def _limpiar_panel_ficha(self):
        self.selected_policia = None
        self.lbl_ficha_nombre.setText("Seleccione un policía en la lista")
        self.lbl_ficha_codigo_area.setText("Código: - | Área: -")
        self._update_mini_box(self.card_debe, "0 Tickets", "S/ 0.00")
        self._update_mini_box(self.card_pago, "0 Tickets", "S/ 0.00")
        self._update_mini_box(self.card_saldo, "0 Tickets", "S/ 0.00")
        self.tbl_historial_policia.setRowCount(0)

    def _on_registrar_debe(self):
        if not self.selected_policia:
            QMessageBox.information(self, "Aviso", "Seleccione un policía en la lista primero.")
            return

        dlg = RegistrarDeudaTicketDialog(self.selected_policia, precio_defecto=self.precio_menu, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            ok, msg, _ = self.cuenta_service.registrar_deuda(
                policia_id=self.selected_policia.policia_id,
                fecha=data["fecha"],
                cantidad_tickets=data["cantidad_tickets"],
                precio_unitario=data["precio_unitario"],
                monto_total=data["monto_total"],
                observacion=data["observacion"]
            )
            if ok:
                ToastManager.show_success(msg, self)
                self.cargar_datos()
            else:
                ToastManager.show_warning(msg, self)

    def _on_registrar_pago(self):
        if not self.selected_policia:
            QMessageBox.information(self, "Aviso", "Seleccione un policía en la lista primero.")
            return

        dlg = RegistrarPagoCuentaDialog(self.selected_policia, precio_defecto=self.precio_menu, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            ok, msg, _ = self.cuenta_service.registrar_pago(
                policia_id=self.selected_policia.policia_id,
                fecha=data["fecha"],
                cantidad_tickets=data["cantidad_tickets"],
                monto_total=data["monto_total"],
                medio_pago=data["medio_pago"],
                observacion=data["observacion"]
            )
            if ok:
                ToastManager.show_success(msg, self)
                self.cargar_datos()
            else:
                ToastManager.show_warning(msg, self)

    def _eliminar_movimiento(self, mov_id: int):
        resp = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            "¿Desea anular este registro de ticket/pago?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            ok, msg = self.cuenta_service.eliminar_movimiento(mov_id)
            if ok:
                ToastManager.show_success(msg, self)
                self.cargar_datos()
            else:
                ToastManager.show_warning(msg, self)

    # --- Módulo Diario Original (Compatibilidad) ---
    def _cargar_datos_diarios(self):
        diarios = self.ticket_service.get_calendario_mes(self.current_anio, self.current_mes, self.current_local)
        pagos_existentes = {p.fecha: p for p in self.pago_service.get_by_mes(self.current_anio, self.current_mes)}

        self.table.setRowCount(len(diarios))
        self.widgets = {}

        for r, td in enumerate(diarios):
            fecha = td.fecha
            tot_t = td.total_policias
            p = pagos_existentes.get(fecha)

            if not p:
                p = PagoTicket(
                    fecha=fecha,
                    total_tickets=tot_t,
                    tickets_pagados=tot_t,
                    tickets_debidos=0,
                    monto_pagado=tot_t * self.precio_menu,
                    monto_pendiente=0.0
                )
                p.calcular_estado()

            self.table.setItem(r, 0, QTableWidgetItem(fecha))

            tot_item = QTableWidgetItem(str(tot_t))
            tot_item.setTextAlignment(Qt.AlignCenter)
            tot_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(r, 1, tot_item)

            sb_pag = QSpinBox()
            sb_pag.setRange(0, 9999)
            sb_pag.setValue(p.tickets_pagados)
            sb_pag.valueChanged.connect(lambda _, row=r: self._on_value_changed(row))
            self.table.setCellWidget(r, 2, sb_pag)

            sb_deb = QSpinBox()
            sb_deb.setRange(0, 9999)
            sb_deb.setValue(p.tickets_debidos)
            sb_deb.valueChanged.connect(lambda _, row=r: self._on_value_changed(row))
            self.table.setCellWidget(r, 3, sb_deb)

            pct = int((p.tickets_pagados / tot_t * 100)) if tot_t > 0 else 100
            pbar = QProgressBar()
            pbar.setRange(0, 100)
            pbar.setValue(pct)
            pbar.setAlignment(Qt.AlignCenter)
            pbar.setFormat(f"{pct}%")
            pbar_color = "#10B981" if pct == 100 else ("#F59E0B" if pct >= 50 else "#F43F5E")
            pbar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: #1E293B;
                    color: #FFFFFF;
                    border: 1px solid #334155;
                    border-radius: 6px;
                    text-align: center;
                    font-size: 10px;
                    font-weight: bold;
                    min-height: 18px;
                    max-height: 20px;
                }}
                QProgressBar::chunk {{
                    background-color: {pbar_color};
                    border-radius: 5px;
                }}
            """)
            self.table.setCellWidget(r, 4, pbar)

            est_item = QTableWidgetItem(p.estado)
            est_item.setTextAlignment(Qt.AlignCenter)
            est_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self._apply_estado_style(est_item, p.estado)
            self.table.setItem(r, 5, est_item)

            dsp_pag = QDoubleSpinBox()
            dsp_pag.setRange(0.0, 999999.0)
            dsp_pag.setDecimals(2)
            dsp_pag.setPrefix("S/ ")
            dsp_pag.setValue(p.monto_pagado)
            self.table.setCellWidget(r, 6, dsp_pag)

            dsp_pend = QDoubleSpinBox()
            dsp_pend.setRange(0.0, 999999.0)
            dsp_pend.setDecimals(2)
            dsp_pend.setPrefix("S/ ")
            dsp_pend.setValue(p.monto_pendiente)
            self.table.setCellWidget(r, 7, dsp_pend)

            txt_obs = QLineEdit()
            if p.observacion:
                txt_obs.setText(p.observacion)
            self.table.setCellWidget(r, 8, txt_obs)

            self.widgets[r] = {
                "fecha": fecha,
                "total_tickets": tot_t,
                "pagados": sb_pag,
                "debidos": sb_deb,
                "pbar": pbar,
                "estado": p.estado,
                "monto_pagado": dsp_pag,
                "monto_pendiente": dsp_pend,
                "obs": txt_obs
            }

        self._recalcular_resumen_diario()

    def _on_value_changed(self, row: int):
        w = self.widgets.get(row)
        if w:
            tot = w["total_tickets"]
            pag = w["pagados"].value()
            deb = w["debidos"].value()

            if tot <= 0 or pag >= tot:
                estado = "PAGADO"
            elif pag == 0:
                estado = "PENDIENTE"
            else:
                estado = "PARCIAL"

            w["estado"] = estado
            est_item = self.table.item(row, 5)
            if est_item:
                est_item.setText(estado)
                self._apply_estado_style(est_item, estado)

            pct = int((pag / tot * 100)) if tot > 0 else 100
            pbar = w["pbar"]
            pbar.setValue(pct)
            pbar.setFormat(f"{pct}%")
            pbar_color = "#10B981" if pct == 100 else ("#F59E0B" if pct >= 50 else "#F43F5E")
            pbar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: #1E293B;
                    color: #FFFFFF;
                    border: 1px solid #334155;
                    border-radius: 6px;
                    text-align: center;
                    font-size: 10px;
                    font-weight: bold;
                    min-height: 18px;
                    max-height: 20px;
                }}
                QProgressBar::chunk {{
                    background-color: {pbar_color};
                    border-radius: 5px;
                }}
            """)

            w["monto_pagado"].setValue(round(pag * self.precio_menu, 2))
            w["monto_pendiente"].setValue(round(deb * self.precio_menu, 2))

        self._recalcular_resumen_diario()

    def _apply_estado_style(self, item: QTableWidgetItem, estado: str):
        if estado == "PAGADO":
            item.setForeground(QColor("#10B981"))
        elif estado == "PENDIENTE":
            item.setForeground(QColor("#F43F5E"))
        elif estado == "PARCIAL":
            item.setForeground(QColor("#F59E0B"))

    def _recalcular_resumen_diario(self):
        tot_tk = 0
        tot_pag = 0
        tot_deb = 0
        tot_monto_pend = 0.0

        for r, w in self.widgets.items():
            tot_tk += w["total_tickets"]
            tot_pag += w["pagados"].value()
            tot_deb += w["debidos"].value()
            tot_monto_pend += w["monto_pendiente"].value()

        self.lbl_kpi_total_tickets.setText(str(tot_tk))
        self.lbl_kpi_pagados.setText(str(tot_pag))
        self.lbl_kpi_debidos.setText(str(tot_deb))
        self.lbl_kpi_monto_pend.setText(f"S/ {tot_monto_pend:,.2f}")

    def _on_table_double_clicked(self, index):
        row = index.row()
        w = self.widgets.get(row)
        if w:
            fecha_str = w["fecha"]
            try:
                dt = datetime.strptime(fecha_str, "%Y-%m-%d")
                dlg = DetalleDiaDialog(dt.year, dt.month, dt.day, self.current_local, parent=self)
                dlg.exec()
            except Exception:
                pass

    def _on_guardar_todo(self):
        guardados = 0
        descuadrados = 0
        for r, w in self.widgets.items():
            fecha = w["fecha"]
            tot = w["total_tickets"]
            pag = w["pagados"].value()
            deb = w["debidos"].value()
            m_pag = w["monto_pagado"].value()
            m_pend = w["monto_pendiente"].value()
            obs = w["obs"].text().strip() or None

            ok, msg, p = self.pago_service.guardar_pago(
                fecha=fecha,
                total_tickets=tot,
                tickets_pagados=pag,
                tickets_debidos=deb,
                monto_pagado=m_pag,
                monto_pendiente=m_pend,
                observacion=obs
            )
            if not p.is_cuadrado:
                descuadrados += 1
            guardados += 1

        if descuadrados > 0:
            ToastManager.show_warning(f"Guardados {guardados} pagos. ⚠️ {descuadrados} fecha(s) no cuadran.", self)
        else:
            ToastManager.show_success(f"¡{guardados} registros de pagos guardados correctamente!", self)
