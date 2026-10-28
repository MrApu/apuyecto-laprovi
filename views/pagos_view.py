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
from models.policia_pago import PoliciaPagoTicket, ResumenDeudaPolicia
from services.pago_service import PagoService
from services.ticket_service import TicketService
from services.mes_service import MesService
from models.local import LOCAL_RESTAURANTE, LOCAL_NAMES
from views.components.toast import ToastManager
from views.dialogs.detalle_dia_dialog import DetalleDiaDialog
from views.dialogs.pago_policia_dialog import RegistrarPagoPoliciaDialog
from views.dialogs.asignar_tickets_policia_dialog import AsignarTicketsPoliciaDialog

class PagosView(QWidget):
    """
    Control de Cobranzas y Deudas con:
    1. Módulo por Policía con buscador en tiempo real interactivo (descarte automático),
       visualización directa de 'Debe Tickets' y 'Pagó Tickets', y registro de pagos.
    2. Resumen Diario General por fecha para control consolidado.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pago_service = PagoService()
        self.ticket_service = TicketService()
        self.mes_service = MesService()
        self.current_anio = 2026
        self.current_mes = 9
        self.current_mes_id: Optional[int] = None
        self.current_local = LOCAL_RESTAURANTE
        self.precio_menu = 12.0
        self.active_chip = "TODOS"
        self.policias_deudas: List[ResumenDeudaPolicia] = []
        self.selected_policia: Optional[ResumenDeudaPolicia] = None
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
        if m:
            self.current_mes_id = m.id
            self.precio_menu = m.precio_ticket_policial or 12.0
        else:
            ok, msg, m_id = self.mes_service.crear_mes(anio, mes)
            self.current_mes_id = m_id
            self.precio_menu = 12.0

        self.lbl_title.setText(f"💰 CONTROL DE COBRANZAS Y DEUDAS — {mes:02d}/{anio}")
        self.cargar_datos()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header principal
        header_box = QHBoxLayout()
        self.lbl_title = QLabel(f"💰 CONTROL DE COBRANZAS Y DEUDAS — {self.current_mes:02d}/{self.current_anio}")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #FFFFFF;")
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

        self.btn_guardar_todo = QPushButton("💾 Guardar Pagos Diarios")
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

        # Tabs: Por Policía y Diario General
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

        # Pestaña 1: Por Policía
        tab_policias = self._build_tab_policias()
        self.tabs.addTab(tab_policias, "👮 Cobranzas y Deudas por Policía")

        # Pestaña 2: Resumen Diario
        tab_diario = self._build_tab_diario()
        self.tabs.addTab(tab_diario, "📅 Control Diario por Fecha")

        layout.addWidget(self.tabs)

    def _build_tab_policias(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(10)

        # Buscador y Chips
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        self.txt_busqueda = QLineEdit()
        self.txt_busqueda.setPlaceholderText("🔍 Buscar policía por apellidos, nombres, código o área... (los demás se van descartando)")
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

        # Chips de filtrado
        self.chip_group = QButtonGroup(self)
        self.chip_group.setExclusive(True)

        chips = [
            ("🔘 Todos", "TODOS"),
            ("🔴 Debe Tickets", "DEUDA"),
            ("🟡 Pago Parcial", "PARCIAL"),
            ("🟢 Pagado / Al Día", "PAGADO")
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

        # KPI Summary Cards
        kpi_row = QHBoxLayout()
        self.lbl_pol_total_tk = QLabel("0")
        self.lbl_pol_pagados = QLabel("0")
        self.lbl_pol_debidos = QLabel("0")
        self.lbl_pol_monto_deuda = QLabel("S/ 0.00")

        kpi_row.addWidget(self._create_kpi_card("TOTAL TICKETS", self.lbl_pol_total_tk, "#38BDF8"))
        kpi_row.addWidget(self._create_kpi_card("TICKETS PAGADOS", self.lbl_pol_pagados, "#10B981"))
        kpi_row.addWidget(self._create_kpi_card("DEBE TICKETS", self.lbl_pol_debidos, "#EF4444"))
        kpi_row.addWidget(self._create_kpi_card("DEUDA TOTAL", self.lbl_pol_monto_deuda, "#F59E0B"))
        l.addLayout(kpi_row)

        # Splitter: Tabla a la izquierda, Ficha a la derecha
        splitter = QSplitter(Qt.Horizontal)

        # Panel Izquierdo: Tabla de Policías
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self.tbl_policias = QTableWidget()
        self.tbl_policias.setColumnCount(9)
        self.tbl_policias.setHorizontalHeaderLabels([
            "Código", "Policía", "Área", "Total Tickets", "Pagó Tickets", "Debe Tickets",
            "Monto Pagado", "Deuda Pendiente", "Acción"
        ])
        self.tbl_policias.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl_policias.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl_policias.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl_policias.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tbl_policias.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tbl_policias.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tbl_policias.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.tbl_policias.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.tbl_policias.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)
        self.tbl_policias.setColumnWidth(8, 120)
        self.tbl_policias.setAlternatingRowColors(True)
        self.tbl_policias.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_policias.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_policias.itemSelectionChanged.connect(self._on_policia_selection_changed)
        left_layout.addWidget(self.tbl_policias)

        splitter.addWidget(left_widget)

        # Panel Derecho: Ficha Interactiva del Policía
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

        lbl_hdr = QLabel("👮 SISTEMA DEBE Y PAGÓ TICKETS")
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

        self.card_debe = self._create_mini_box("DEBE TICKETS", "0", "S/ 0.00", "#EF4444")
        self.card_pago = self._create_mini_box("PAGÓ TICKETS", "0", "S/ 0.00", "#10B981")
        self.card_total = self._create_mini_box("TOTAL TICKETS", "0", "S/ 0.00", "#38BDF8")

        row_cards.addWidget(self.card_debe)
        row_cards.addWidget(self.card_pago)
        row_cards.addWidget(self.card_total)
        l.addLayout(row_cards)

        # Barra de progreso
        lbl_prog = QLabel("Progreso de Pago:")
        lbl_prog.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 700; margin-top: 4px;")
        l.addWidget(lbl_prog)

        self.pbar_policia = QProgressBar()
        self.pbar_policia.setRange(0, 100)
        self.pbar_policia.setValue(100)
        self.pbar_policia.setAlignment(Qt.AlignCenter)
        self.pbar_policia.setFixedHeight(18)
        self.pbar_policia.setStyleSheet("""
            QProgressBar {
                background: #1F2937;
                color: #FFFFFF;
                border: 1px solid #374151;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #10B981;
                border-radius: 3px;
            }
        """)
        l.addWidget(self.pbar_policia)

        # Botones de Acción
        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)

        self.btn_cobrar_policia = QPushButton("💵 Cobrar / Pagó Tickets")
        self.btn_cobrar_policia.setCursor(Qt.PointingHandCursor)
        self.btn_cobrar_policia.setStyleSheet("""
            background-color: #10B981;
            color: #FFFFFF;
            font-weight: 800;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
        """)
        self.btn_cobrar_policia.clicked.connect(self._on_cobrar_seleccionado)
        btn_box.addWidget(self.btn_cobrar_policia)

        self.btn_asignar_policia = QPushButton("⚡ Ajustar Tickets")
        self.btn_asignar_policia.setCursor(Qt.PointingHandCursor)
        self.btn_asignar_policia.setStyleSheet("""
            background-color: #18181B;
            color: #E4E4E7;
            font-weight: 700;
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid #3F3F46;
            font-size: 12px;
        """)
        self.btn_asignar_policia.clicked.connect(self._on_asignar_seleccionado)
        btn_box.addWidget(self.btn_asignar_policia)

        l.addLayout(btn_box)

        # Historial de pagos del policía
        lbl_hist = QLabel("Historial de Pagos de Tickets:")
        lbl_hist.setStyleSheet("color: #E4E4E7; font-size: 12px; font-weight: 700; margin-top: 6px;")
        l.addWidget(lbl_hist)

        self.tbl_historial_policia = QTableWidget()
        self.tbl_historial_policia.setColumnCount(5)
        self.tbl_historial_policia.setHorizontalHeaderLabels(["Fecha", "Tickets", "Monto", "Medio", "Acción"])
        self.tbl_historial_policia.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl_historial_policia.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_historial_policia.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl_historial_policia.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tbl_historial_policia.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.tbl_historial_policia.setColumnWidth(4, 50)
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
        if not self.current_mes_id:
            m = self.mes_service.get_by_anio_mes(self.current_anio, self.current_mes)
            if m:
                self.current_mes_id = m.id
            else:
                return

        # 1. Cargar datos de policías
        self.policias_deudas = self.pago_service.get_resumen_deudas_policias(
            mes_id=self.current_mes_id,
            precio_ticket=self.precio_menu
        )
        self._render_tabla_policias()

        # 2. Cargar datos diarios
        self._cargar_datos_diarios()

    def _render_tabla_policias(self):
        busqueda = self.txt_busqueda.text().strip().upper()
        filtrados: List[ResumenDeudaPolicia] = []

        for p in self.policias_deudas:
            # Filtro texto (descarte automático)
            if busqueda:
                full_text = f"{p.codigo} {p.apellidos} {p.nombres} {p.area} {p.sa_pnp or ''}".upper()
                if busqueda not in full_text:
                    continue

            # Filtro chip
            if self.active_chip == "DEUDA" and p.tickets_debidos <= 0:
                continue
            elif self.active_chip == "PARCIAL" and p.estado != "PARCIAL":
                continue
            elif self.active_chip == "PAGADO" and p.tickets_debidos > 0:
                continue

            filtrados.append(p)

        # Actualizar KPIs de policías
        tot_tk = sum(p.tickets_totales for p in self.policias_deudas)
        tot_pag = sum(p.tickets_pagados for p in self.policias_deudas)
        tot_deb = sum(p.tickets_debidos for p in self.policias_deudas)
        tot_monto_deb = sum(p.monto_pendiente for p in self.policias_deudas)

        self.lbl_pol_total_tk.setText(str(tot_tk))
        self.lbl_pol_pagados.setText(str(tot_pag))
        self.lbl_pol_debidos.setText(str(tot_deb))
        self.lbl_pol_monto_deuda.setText(f"S/ {tot_monto_deb:,.2f}")

        # Renderizar filas
        self.tbl_policias.setRowCount(len(filtrados))
        self.visible_policias = filtrados

        for r, p in enumerate(filtrados):
            self.tbl_policias.setItem(r, 0, QTableWidgetItem(p.codigo))
            
            item_nom = QTableWidgetItem(f"{p.apellidos}, {p.nombres}")
            item_nom.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.tbl_policias.setItem(r, 1, item_nom)

            self.tbl_policias.setItem(r, 2, QTableWidgetItem(p.area))

            # Total Tickets
            it_tot = QTableWidgetItem(str(p.tickets_totales))
            it_tot.setTextAlignment(Qt.AlignCenter)
            self.tbl_policias.setItem(r, 3, it_tot)

            # Pagó Tickets
            it_pag = QTableWidgetItem(str(p.tickets_pagados))
            it_pag.setTextAlignment(Qt.AlignCenter)
            it_pag.setForeground(QColor("#10B981"))
            self.tbl_policias.setItem(r, 4, it_pag)

            # Debe Tickets
            it_deb = QTableWidgetItem(str(p.tickets_debidos))
            it_deb.setTextAlignment(Qt.AlignCenter)
            if p.tickets_debidos > 0:
                it_deb.setForeground(QColor("#EF4444"))
                it_deb.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.tbl_policias.setItem(r, 5, it_deb)

            # Monto Pagado
            it_mpag = QTableWidgetItem(f"S/ {p.monto_pagado:.2f}")
            it_mpag.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_policias.setItem(r, 6, it_mpag)

            # Deuda Pendiente
            it_mdeb = QTableWidgetItem(f"S/ {p.monto_pendiente:.2f}")
            it_mdeb.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if p.monto_pendiente > 0:
                it_mdeb.setForeground(QColor("#EF4444"))
                it_mdeb.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.tbl_policias.setItem(r, 7, it_mdeb)

            # Botón de acción directa en tabla
            btn_act = QPushButton("💵 Cobrar")
            btn_act.setCursor(Qt.PointingHandCursor)
            btn_act.setStyleSheet("""
                QPushButton {
                    background-color: #10B981;
                    color: #FFFFFF;
                    font-weight: bold;
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
            """)
            btn_act.clicked.connect(lambda _, pol=p: self._abrir_modal_pago(pol))
            self.tbl_policias.setCellWidget(r, 8, btn_act)

        # Seleccionar primera fila si hay datos
        if filtrados:
            self.tbl_policias.selectRow(0)
            self._actualizar_panel_ficha(filtrados[0])
        else:
            self._limpiar_panel_ficha()

    def _on_policia_selection_changed(self):
        sel = self.tbl_policias.selectedItems()
        if not sel:
            return
        row = sel[0].row()
        if 0 <= row < len(self.visible_policias):
            pol = self.visible_policias[row]
            self._actualizar_panel_ficha(pol)

    def _actualizar_panel_ficha(self, p: ResumenDeudaPolicia):
        self.selected_policia = p
        self.lbl_ficha_nombre.setText(f"{p.apellidos}, {p.nombres}")
        self.lbl_ficha_codigo_area.setText(f"Código: {p.codigo} | Área: {p.area} | Estado: {p.estado}")

        # Actualizar mini-cards
        self._update_mini_box(self.card_debe, f"{p.tickets_debidos} Tickets", f"S/ {p.monto_pendiente:.2f}")
        self._update_mini_box(self.card_pago, f"{p.tickets_pagados} Tickets", f"S/ {p.monto_pagado:.2f}")
        self._update_mini_box(self.card_total, f"{p.tickets_totales} Tickets", f"S/ {p.tickets_totales * self.precio_menu:.2f}")

        # Progreso
        pct = int((p.tickets_pagados / p.tickets_totales * 100)) if p.tickets_totales > 0 else 100
        self.pbar_policia.setValue(pct)
        self.pbar_policia.setFormat(f"{pct}%")
        color = "#10B981" if pct == 100 else ("#F59E0B" if pct >= 50 else "#EF4444")
        self.pbar_policia.setStyleSheet(f"""
            QProgressBar {{
                background: #1F2937;
                color: #FFFFFF;
                border: 1px solid #374151;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)

        # Cargar historial de pagos
        hist = self.pago_service.get_historial_pagos_policia(p.policia_id, self.current_mes_id)
        self.tbl_historial_policia.setRowCount(len(hist))
        for r, item in enumerate(hist):
            self.tbl_historial_policia.setItem(r, 0, QTableWidgetItem(item.fecha))
            self.tbl_historial_policia.setItem(r, 1, QTableWidgetItem(str(item.tickets_pagados)))
            self.tbl_historial_policia.setItem(r, 2, QTableWidgetItem(f"S/ {item.monto_pagado:.2f}"))
            self.tbl_historial_policia.setItem(r, 3, QTableWidgetItem(item.medio_pago))

            btn_del = QPushButton("🗑️")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setStyleSheet("background: transparent; color: #EF4444; font-size: 12px;")
            btn_del.clicked.connect(lambda _, p_id=item.id: self._eliminar_pago_hist(p_id))
            self.tbl_historial_policia.setCellWidget(r, 4, btn_del)

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
        self._update_mini_box(self.card_total, "0 Tickets", "S/ 0.00")
        self.pbar_policia.setValue(100)
        self.tbl_historial_policia.setRowCount(0)

    def _abrir_modal_pago(self, pol: ResumenDeudaPolicia):
        dlg = RegistrarPagoPoliciaDialog(pol, precio_ticket=self.precio_menu, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            ok, msg, _ = self.pago_service.registrar_pago_policia(
                policia_id=pol.policia_id,
                mes_id=self.current_mes_id,
                fecha=data["fecha"],
                tickets_pagados=data["tickets_pagados"],
                monto_pagado=data["monto_pagado"],
                medio_pago=data["medio_pago"],
                observacion=data["observacion"]
            )
            if ok:
                ToastManager.show_success(msg, self)
                self.cargar_datos()
            else:
                ToastManager.show_warning(msg, self)

    def _on_cobrar_seleccionado(self):
        if self.selected_policia:
            self._abrir_modal_pago(self.selected_policia)
        else:
            QMessageBox.information(self, "Aviso", "Seleccione un policía en la lista primero.")

    def _on_asignar_seleccionado(self):
        if not self.selected_policia:
            QMessageBox.information(self, "Aviso", "Seleccione un policía en la lista primero.")
            return

        pol = self.selected_policia
        num_dias = 30
        mes = self.mes_service.get_by_id(self.current_mes_id) if self.current_mes_id else None
        if mes:
            import calendar
            num_dias = calendar.monthrange(mes.anio, mes.mes)[1]

        dlg = AsignarTicketsPoliciaDialog(
            policia_nombre=f"{pol.apellidos}, {pol.nombres}",
            codigo=pol.codigo,
            tickets_actuales=pol.tickets_totales,
            num_dias_mes=num_dias,
            parent=self
        )
        if dlg.exec():
            nueva_cant = dlg.get_cantidad()
            ok, msg = self.ticket_service.asignar_cantidad_tickets_policia(
                mes_id=self.current_mes_id,
                policia_id=pol.policia_id,
                cantidad=nueva_cant,
                local_id=self.current_local
            )
            if ok:
                ToastManager.show_success(msg, self)
                self.cargar_datos()
            else:
                ToastManager.show_warning(msg, self)

    def _eliminar_pago_hist(self, pago_id: int):
        resp = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            "¿Desea anular este registro de pago de tickets? Se restaurará la deuda correspondiente.",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            ok, msg = self.pago_service.eliminar_pago_policia(pago_id)
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
