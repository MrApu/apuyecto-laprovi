from typing import Optional, Dict, Any, List
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QApplication, QMessageBox,
    QLineEdit, QComboBox, QDoubleSpinBox, QFormLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from database.connection import DatabaseManager
from services.mes_service import MesService
from services.ticket_service import TicketService
from services.egreso_service import EgresoService
from services.policia_service import PoliciaService
from models.local import LOCAL_NAMES, LOCAL_CONSOLIDADO, LOCAL_RESTAURANTE, LOCAL_FAST_FOOD
from models.pago_personal import PagoPersonal
from models.compra import Compra
from models.policia import Policia
from views.components.toast import ToastManager
from views.dialogs.compra_dialog import CompraSimpleDialog
from views.dialogs.policia_dialog import PoliciaDialog


class MarcarPoliciaDiaDialog(QDialog):
    """Diálogo modal para buscar y marcar a un efectivo policial en el día seleccionado."""
    def __init__(self, mes_id: int, dia: int, local_id: str, parent=None):
        super().__init__(parent)
        self.mes_id = mes_id
        self.dia = dia
        self.local_id = local_id if local_id != LOCAL_CONSOLIDADO else LOCAL_RESTAURANTE
        self.policia_service = PoliciaService()
        self.ticket_service = TicketService()
        self.policias_list = []

        self.setWindowTitle(f"👮 Marcar Efectivo PNP — Día {self.dia}")
        self.resize(460, 260)
        self.setStyleSheet("""
            QDialog {
                background-color: #0A0A0A;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 12px;
                font-weight: 700;
            }
            QLineEdit, QComboBox {
                background-color: #141414;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #DC2626;
                background-color: #18181B;
            }
        """)
        self._init_ui()
        self._cargar_policias()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header
        lbl_head = QLabel(f"👮 ASIGNAR TICKET PNP — DÍA {self.dia:02d}")
        lbl_head.setStyleSheet("font-size: 15px; font-weight: 900; color: #FFFFFF;")
        layout.addWidget(lbl_head)

        lbl_desc = QLabel("Seleccione o busque al efectivo policial que consumió ticket en esta fecha:")
        lbl_desc.setStyleSheet("color: #A1A1AA; font-size: 11px;")
        layout.addWidget(lbl_desc)

        # Combo con buscador
        form = QFormLayout()
        form.setSpacing(10)

        self.cmb_policia = QComboBox()
        self.cmb_policia.setEditable(True)
        self.cmb_policia.setInsertPolicy(QComboBox.NoInsert)
        form.addRow("👮 Efectivo:", self.cmb_policia)
        layout.addLayout(form)

        # Botón para crear nuevo si no existe en el padrón
        btn_nuevo = QPushButton("➕ ¿No está en la lista? Crear Nuevo Policía")
        btn_nuevo.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #EF4444;
                border: none;
                text-align: left;
                font-size: 11px;
                font-weight: 800;
                text-decoration: underline;
                padding: 2px 0;
            }
            QPushButton:hover {
                color: #F87171;
            }
        """)
        btn_nuevo.clicked.connect(self._crear_nuevo_policia)
        layout.addWidget(btn_nuevo)

        layout.addStretch()

        # Botones de acción
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        btn_cancel = QPushButton("✕ Cancelar")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #18181B;
                color: #A1A1AA;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 7px 16px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #27272A;
                color: #FFFFFF;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        self.btn_marcar = QPushButton("✅ Marcar Ticket Asistencia")
        self.btn_marcar.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #991B1B, stop:1 #DC2626);
                color: #FFFFFF;
                border: 1px solid #EF4444;
                border-radius: 6px;
                padding: 8px 18px;
                font-weight: 900;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7F1D1D, stop:1 #B91C1C);
                border: 1px solid #F87171;
            }
        """)
        self.btn_marcar.clicked.connect(self._marcar_ticket)
        btn_box.addWidget(self.btn_marcar)

        layout.addLayout(btn_box)

    def _cargar_policias(self):
        self.cmb_policia.clear()
        self.policias_list = self.policia_service.get_all(solo_activos=False)
        for p in self.policias_list:
            texto = f"[{p.codigo}] {p.apellidos} {p.nombres} ({p.area})"
            self.cmb_policia.addItem(texto, p.id)

    def _crear_nuevo_policia(self):
        dlg = PoliciaDialog(self)
        if dlg.exec() == QDialog.Accepted:
            p = dlg.get_policia()
            ok, msg, nuevo_id = self.policia_service.crear_policia(p)
            if ok:
                ToastManager.show_success("Policía agregado al padrón", self)
                self._cargar_policias()
                idx = self.cmb_policia.findData(nuevo_id)
                if idx >= 0:
                    self.cmb_policia.setCurrentIndex(idx)
            else:
                QMessageBox.warning(self, "Error", msg)

    def _marcar_ticket(self):
        policia_id = self.cmb_policia.currentData()
        if not policia_id:
            QMessageBox.warning(self, "Atención", "Por favor seleccione un efectivo policial.")
            return

        ok = self.ticket_service.toggle_ticket(self.mes_id, policia_id, self.dia, 1, local_id=self.local_id)
        if ok:
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "No se pudo marcar el ticket para el efectivo.")


class RegistrarPagoPersonalDialog(QDialog):
    """Diálogo modal para registrar pagos al personal en la fecha seleccionada."""
    def __init__(self, fecha_str: str, local_id: str, parent=None):
        super().__init__(parent)
        self.fecha_str = fecha_str
        self.local_id = local_id if local_id != LOCAL_CONSOLIDADO else LOCAL_RESTAURANTE
        self.setWindowTitle("👥 Registrar Pago al Personal")
        self.resize(460, 360)
        self.setStyleSheet("""
            QDialog {
                background-color: #0A0A0A;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 12px;
                font-weight: 700;
            }
            QLineEdit, QComboBox, QDoubleSpinBox {
                background-color: #141414;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #DC2626;
                background-color: #18181B;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        lbl_head = QLabel("👥 NUEVO PAGO AL PERSONAL")
        lbl_head.setStyleSheet("font-size: 15px; font-weight: 900; color: #FFFFFF;")
        layout.addWidget(lbl_head)

        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: #141414; border: 1px solid #262626; border-radius: 8px; padding: 10px;")
        form = QFormLayout(form_frame)
        form.setSpacing(10)

        # 1. Trabajador
        self.txt_trabajador = QLineEdit()
        self.txt_trabajador.setPlaceholderText("Nombre del personal o empleado...")
        form.addRow("👤 Trabajador:", self.txt_trabajador)

        # 2. Cargo
        self.cmb_cargo = QComboBox()
        self.cmb_cargo.addItems(["COCINA", "ATENCIÓN / MOZO", "CAJA", "LIMPIEZA", "SEGURIDAD", "ADMINISTRACIÓN", "OTROS"])
        form.addRow("🏷️ Cargo:", self.cmb_cargo)

        # 3. Concepto / Turno
        self.cmb_concepto = QComboBox()
        self.cmb_concepto.setEditable(True)
        self.cmb_concepto.addItems(["Pago diario", "Turno noche", "Turno día", "Adelanto", "Sueldo", "Horas extras", "Otros"])
        form.addRow("📝 Concepto:", self.cmb_concepto)

        # 4. Monto (S/)
        self.spn_monto = QDoubleSpinBox()
        self.spn_monto.setRange(0.01, 999999.0)
        self.spn_monto.setDecimals(2)
        self.spn_monto.setPrefix("S/ ")
        self.spn_monto.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #18181B;
                color: #FFFFFF;
                font-size: 15px;
                font-weight: 900;
                border: 2px solid #DC2626;
                padding: 6px 10px;
                border-radius: 6px;
            }
        """)
        form.addRow("💰 Monto Pagado:", self.spn_monto)

        # 5. Medio de Pago
        self.cmb_pago = QComboBox()
        self.cmb_pago.addItems(["EFECTIVO", "YAPE", "TRANSFERENCIA", "TARJETA"])
        form.addRow("💳 Medio de Pago:", self.cmb_pago)

        layout.addWidget(form_frame)
        layout.addStretch()

        # Botones
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        btn_cancel = QPushButton("✕ Cancelar")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #18181B;
                color: #A1A1AA;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 7px 16px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #27272A;
                color: #FFFFFF;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        self.btn_guardar = QPushButton("💾 Guardar Pago")
        self.btn_guardar.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #991B1B, stop:1 #DC2626);
                color: #FFFFFF;
                border: 1px solid #EF4444;
                border-radius: 6px;
                padding: 8px 18px;
                font-weight: 900;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7F1D1D, stop:1 #B91C1C);
                border: 1px solid #F87171;
            }
        """)
        self.btn_guardar.clicked.connect(self._guardar)
        btn_box.addWidget(self.btn_guardar)

        layout.addLayout(btn_box)

    def _guardar(self):
        trab = self.txt_trabajador.text().strip()
        if not trab:
            QMessageBox.warning(self, "Atención", "Por favor ingrese el nombre del trabajador.")
            self.txt_trabajador.setFocus()
            return
        monto = self.spn_monto.value()
        if monto <= 0:
            QMessageBox.warning(self, "Atención", "El monto a pagar debe ser mayor a 0.")
            self.spn_monto.setFocus()
            return
        self.accept()

    def get_pago(self) -> PagoPersonal:
        return PagoPersonal(
            fecha=self.fecha_str,
            local_id=self.local_id,
            trabajador=self.txt_trabajador.text().strip().upper(),
            cargo=self.cmb_cargo.currentText(),
            concepto=self.cmb_concepto.currentText(),
            monto=round(self.spn_monto.value(), 2),
            medio_pago=self.cmb_pago.currentText()
        )


class DetalleDiaDialog(QDialog):
    """
    Diálogo de Bitácora del Día (Rojo, Blanco y Negro — La Provincial):
    - Resumen financiero e indicadores clave en vivo.
    - Tab 1: Efectivos PNP con botón para marcar/desmarcar policías directamente.
    - Tab 2: Compras e Insumos con botón para registrar compras directamente.
    - Tab 3: Pagos al Personal con botón para registrar y eliminar pagos directamente.
    - Sin gastos operativos redundantes.
    - Botón de 1-Clic para copiar reporte formateado a WhatsApp.
    """
    def __init__(self, anio: int, mes: int, dia: int, local_id: str = "restaurante", parent=None):
        super().__init__(parent)
        self.anio = anio
        self.mes = mes
        self.dia = dia
        self.local_id = local_id
        self.fecha_str = f"{anio:04d}-{mes:02d}-{dia:02d}"
        self.db = DatabaseManager.get_instance()
        self.mes_service = MesService()
        self.ticket_service = TicketService()
        self.egreso_service = EgresoService()
        self.sede_name = LOCAL_NAMES.get(local_id, local_id.upper())

        self.setWindowTitle(f"🔍 Bitácora del Día — {self.fecha_str} ({self.sede_name})")
        self.resize(900, 640)
        self.setStyleSheet("background-color: #0A0A0A; color: #FFFFFF;")
        self._init_ui()
        self._cargar_datos()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        try:
            dt = datetime.strptime(self.fecha_str, "%Y-%m-%d")
            dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            nombre_dia = dias_semana[dt.weekday()]
            title_text = f"📅 {nombre_dia.upper()}, {dt.day:02d} DE {dt.strftime('%B').upper()} {dt.year}"
        except Exception:
            title_text = f"📅 BITÁCORA DEL DÍA {self.fecha_str}"

        lbl_title = QLabel(title_text)
        lbl_title.setStyleSheet("font-size: 17px; font-weight: 900; color: #FFFFFF;")
        header.addWidget(lbl_title)

        lbl_sede = QLabel(f"📍 {self.sede_name}")
        lbl_sede.setStyleSheet("background: #18181B; color: #FFFFFF; border: 1px solid #DC2626; padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 11px;")
        header.addWidget(lbl_sede)

        header.addStretch()

        self.btn_whatsapp = QPushButton("📲 Copiar para WhatsApp")
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
        self.btn_whatsapp.clicked.connect(self._copiar_whatsapp)
        header.addWidget(self.btn_whatsapp)

        btn_close = QPushButton("✕")
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #A1A1AA;
                font-size: 16px;
                border: none;
                padding: 4px 8px;
            }
            QPushButton:hover {
                color: #DC2626;
            }
        """)
        btn_close.clicked.connect(self.accept)
        header.addWidget(btn_close)

        layout.addLayout(header)

        # KPI Summary Cards (Hero Row)
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(10)
        self.lbl_val_venta = QLabel("S/ 0.00")
        self.lbl_val_egreso = QLabel("S/ 0.00")
        self.lbl_val_saldo = QLabel("S/ 0.00")
        self.lbl_val_tickets = QLabel("0 tk")

        kpi_row.addWidget(self._create_card("Venta Total", self.lbl_val_venta, "#10B981"))
        kpi_row.addWidget(self._create_card("Total Egresos", self.lbl_val_egreso, "#DC2626"))
        kpi_row.addWidget(self._create_card("Saldo Neto", self.lbl_val_saldo, "#FFFFFF"))
        kpi_row.addWidget(self._create_card("Tickets PNP", self.lbl_val_tickets, "#DC2626"))
        layout.addLayout(kpi_row)

        # Tabs for details
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #262626;
                background: #0D0D0D;
                border-radius: 8px;
                padding: 8px;
            }
            QTabBar::tab {
                background: #141414;
                color: #A1A1AA;
                font-weight: 700;
                font-size: 12px;
                padding: 8px 16px;
                margin-right: 4px;
                border-radius: 6px;
                border: 1px solid #262626;
            }
            QTabBar::tab:selected {
                background: #DC2626;
                color: #FFFFFF;
                border: 1px solid #EF4444;
            }
        """)

        # ---------------------------------------------
        # Tab 1: Efectivos PNP
        # ---------------------------------------------
        tab1_widget = QWidget()
        t1_layout = QVBoxLayout(tab1_widget)
        t1_layout.setContentsMargins(6, 6, 6, 6)
        t1_layout.setSpacing(8)

        t1_bar = QHBoxLayout()
        self.lbl_cnt_pol = QLabel("Total Efectivos: 0")
        self.lbl_cnt_pol.setStyleSheet("color: #FFFFFF; font-weight: 800; font-size: 12px;")
        t1_bar.addWidget(self.lbl_cnt_pol)
        t1_bar.addStretch()

        btn_add_pol = QPushButton("➕ Marcar Efectivo PNP")
        btn_add_pol.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #991B1B, stop:1 #DC2626);
                color: #FFFFFF;
                border: 1px solid #EF4444;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 800;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7F1D1D, stop:1 #B91C1C);
            }
        """)
        btn_add_pol.clicked.connect(self._on_agregar_policia)
        t1_bar.addWidget(btn_add_pol)
        t1_layout.addLayout(t1_bar)

        self.table_policias = QTableWidget()
        self.table_policias.setColumnCount(5)
        self.table_policias.setHorizontalHeaderLabels(["Código", "Apellidos y Nombres", "Área / Unidad", "SA-PNP", "Acción"])
        self.table_policias.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_policias.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.table_policias.setColumnWidth(4, 90)
        t1_layout.addWidget(self.table_policias)

        self.tabs.addTab(tab1_widget, "👮 Efectivos PNP")

        # ---------------------------------------------
        # Tab 2: Compras e Insumos
        # ---------------------------------------------
        tab2_widget = QWidget()
        t2_layout = QVBoxLayout(tab2_widget)
        t2_layout.setContentsMargins(6, 6, 6, 6)
        t2_layout.setSpacing(8)

        t2_bar = QHBoxLayout()
        self.lbl_cnt_comp = QLabel("Total Compras: S/ 0.00")
        self.lbl_cnt_comp.setStyleSheet("color: #FFFFFF; font-weight: 800; font-size: 12px;")
        t2_bar.addWidget(self.lbl_cnt_comp)
        t2_bar.addStretch()

        btn_add_comp = QPushButton("➕ Registrar Compra / Insumo")
        btn_add_comp.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #991B1B, stop:1 #DC2626);
                color: #FFFFFF;
                border: 1px solid #EF4444;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 800;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7F1D1D, stop:1 #B91C1C);
            }
        """)
        btn_add_comp.clicked.connect(self._on_agregar_compra)
        t2_bar.addWidget(btn_add_comp)
        t2_layout.addLayout(t2_bar)

        self.table_compras = QTableWidget()
        self.table_compras.setColumnCount(5)
        self.table_compras.setHorizontalHeaderLabels(["Insumo / Descripción", "Categoría", "Medio Pago", "Total (S/)", "Acción"])
        self.table_compras.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_compras.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.table_compras.setColumnWidth(4, 85)
        t2_layout.addWidget(self.table_compras)

        self.tabs.addTab(tab2_widget, "🛒 Compras e Insumos")

        # ---------------------------------------------
        # Tab 3: Pagos al Personal
        # ---------------------------------------------
        tab3_widget = QWidget()
        t3_layout = QVBoxLayout(tab3_widget)
        t3_layout.setContentsMargins(6, 6, 6, 6)
        t3_layout.setSpacing(8)

        t3_bar = QHBoxLayout()
        self.lbl_cnt_pers = QLabel("Total Pagos Personal: S/ 0.00")
        self.lbl_cnt_pers.setStyleSheet("color: #FFFFFF; font-weight: 800; font-size: 12px;")
        t3_bar.addWidget(self.lbl_cnt_pers)
        t3_bar.addStretch()

        btn_add_pers = QPushButton("➕ Registrar Pago Personal")
        btn_add_pers.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #991B1B, stop:1 #DC2626);
                color: #FFFFFF;
                border: 1px solid #EF4444;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 800;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7F1D1D, stop:1 #B91C1C);
            }
        """)
        btn_add_pers.clicked.connect(self._on_agregar_personal)
        t3_bar.addWidget(btn_add_pers)
        t3_layout.addLayout(t3_bar)

        self.table_personal = QTableWidget()
        self.table_personal.setColumnCount(6)
        self.table_personal.setHorizontalHeaderLabels(["Personal / Trabajador", "Cargo", "Concepto / Turno", "Medio Pago", "Monto (S/)", "Acción"])
        self.table_personal.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_personal.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.table_personal.setColumnWidth(5, 85)
        t3_layout.addWidget(self.table_personal)

        self.tabs.addTab(tab3_widget, "👥 Pagos Personal")

        layout.addWidget(self.tabs)

    def _create_card(self, title: str, val_label: QLabel, color: str) -> QWidget:
        w = QFrame()
        w.setStyleSheet(f"background: #141414; border: 1px solid #262626; border-left: 4px solid {color}; border-radius: 8px; padding: 8px;")
        l = QVBoxLayout(w)
        l.setContentsMargins(10, 6, 10, 6)
        l.setSpacing(2)
        lbl_t = QLabel(title.upper())
        lbl_t.setStyleSheet("color: #A1A1AA; font-size: 10px; font-weight: 800; letter-spacing: 0.5px;")
        val_label.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 900;")
        l.addWidget(lbl_t)
        l.addWidget(val_label)
        return w

    def _cargar_datos(self):
        mes_obj = self.mes_service.get_by_anio_mes(self.anio, self.mes)
        self.mes_id = mes_obj.id if mes_obj else None

        # 1. Ventas & Finanzas
        v_row = self.db.execute_query(
            "SELECT * FROM ventas_diarias WHERE fecha = ? AND local_id = ?",
            (self.fecha_str, self.local_id)
        )
        if v_row:
            v = v_row[0]
            self.venta_data = {
                "efectivo": v["efectivo"] or 0.0,
                "yape": v["yape"] or 0.0,
                "tickets": v["cantidad_tickets"] or 0,
                "venta_tickets": v["venta_tickets"] or 0.0,
                "venta_total": v["venta_total"] or 0.0
            }
        else:
            self.venta_data = {"efectivo": 0.0, "yape": 0.0, "tickets": 0, "venta_tickets": 0.0, "venta_total": 0.0}

        # 2. Efectivos PNP
        pol_rows = []
        if self.mes_id:
            if self.local_id == LOCAL_CONSOLIDADO:
                pol_rows = self.db.execute_query("""
                    SELECT p.id, p.codigo, p.apellidos, p.nombres, p.area, p.sa_pnp
                    FROM tickets_por_policia t
                    JOIN policias p ON t.policia_id = p.id
                    WHERE t.mes_id = ? AND t.dia = ? AND t.valor = 1
                    GROUP BY p.id
                    ORDER BY p.apellidos, p.nombres
                """, (self.mes_id, self.dia))
            else:
                pol_rows = self.db.execute_query("""
                    SELECT p.id, p.codigo, p.apellidos, p.nombres, p.area, p.sa_pnp
                    FROM tickets_por_policia t
                    JOIN policias p ON t.policia_id = p.id
                    WHERE t.mes_id = ? AND t.dia = ? AND t.valor = 1 AND t.local_id = ?
                    ORDER BY p.apellidos, p.nombres
                """, (self.mes_id, self.dia, self.local_id))

        self.table_policias.setRowCount(len(pol_rows))
        for r, p in enumerate(pol_rows):
            self.table_policias.setItem(r, 0, QTableWidgetItem(p["codigo"] or ""))
            self.table_policias.setItem(r, 1, QTableWidgetItem(f"{p['apellidos']} {p['nombres']}"))
            self.table_policias.setItem(r, 2, QTableWidgetItem(p["area"] or "-"))
            self.table_policias.setItem(r, 3, QTableWidgetItem(p["sa_pnp"] or "-"))

            # Botón desmarcar
            btn_del = QPushButton("🗑️")
            btn_del.setToolTip("Desmarcar efectivo en este día")
            btn_del.setStyleSheet("""
                QPushButton {
                    background-color: #271214;
                    color: #EF4444;
                    border: 1px solid #7F1D1D;
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #DC2626;
                    color: #FFFFFF;
                }
            """)
            p_id = p["id"]
            btn_del.clicked.connect(lambda ch, pid=p_id: self._on_desmarcar_policia(pid))
            self.table_policias.setCellWidget(r, 4, btn_del)

        self.lbl_cnt_pol.setText(f"Total Efectivos Marcados: {len(pol_rows)}")

        # 3. Compras
        comp_rows = self.db.execute_query(
            "SELECT * FROM compras WHERE fecha = ? AND local_id = ? ORDER BY id DESC",
            (self.fecha_str, self.local_id)
        )
        self.table_compras.setRowCount(len(comp_rows))
        total_compras = 0.0
        for r, c in enumerate(comp_rows):
            monto = c["total"] or 0.0
            total_compras += monto
            self.table_compras.setItem(r, 0, QTableWidgetItem(c["descripcion"] or c["observacion"] or c["proveedor"] or "-"))
            self.table_compras.setItem(r, 1, QTableWidgetItem(c["categoria"] or "-"))
            self.table_compras.setItem(r, 2, QTableWidgetItem(c["medio_pago"] or "EFECTIVO"))
            self.table_compras.setItem(r, 3, QTableWidgetItem(f"S/ {monto:,.2f}"))

            btn_del = QPushButton("🗑️")
            btn_del.setToolTip("Eliminar esta compra")
            btn_del.setStyleSheet("""
                QPushButton {
                    background-color: #271214;
                    color: #EF4444;
                    border: 1px solid #7F1D1D;
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #DC2626;
                    color: #FFFFFF;
                }
            """)
            c_id = c["id"]
            btn_del.clicked.connect(lambda ch, cid=c_id: self._on_eliminar_compra(cid))
            self.table_compras.setCellWidget(r, 4, btn_del)

        self.lbl_cnt_comp.setText(f"Total Compras: S/ {total_compras:,.2f}")

        # 4. Pagos al Personal
        pers_rows = self.db.execute_query(
            "SELECT * FROM pagos_personal WHERE fecha = ? AND local_id = ? ORDER BY id DESC",
            (self.fecha_str, self.local_id)
        )
        self.table_personal.setRowCount(len(pers_rows))
        total_personal = 0.0
        for r, pr in enumerate(pers_rows):
            monto = pr["monto"] or 0.0
            total_personal += monto
            self.table_personal.setItem(r, 0, QTableWidgetItem(pr["trabajador"] or "-"))
            self.table_personal.setItem(r, 1, QTableWidgetItem(pr["cargo"] or "PERSONAL"))
            self.table_personal.setItem(r, 2, QTableWidgetItem(pr["concepto"] or "TURNO"))
            self.table_personal.setItem(r, 3, QTableWidgetItem(pr["medio_pago"] or "EFECTIVO"))
            self.table_personal.setItem(r, 4, QTableWidgetItem(f"S/ {monto:,.2f}"))

            btn_del = QPushButton("🗑️")
            btn_del.setToolTip("Eliminar este pago de personal")
            btn_del.setStyleSheet("""
                QPushButton {
                    background-color: #271214;
                    color: #EF4444;
                    border: 1px solid #7F1D1D;
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #DC2626;
                    color: #FFFFFF;
                }
            """)
            pr_id = pr["id"]
            btn_del.clicked.connect(lambda ch, prid=pr_id: self._on_eliminar_personal(prid))
            self.table_personal.setCellWidget(r, 5, btn_del)

        self.lbl_cnt_pers.setText(f"Total Pagos Personal: S/ {total_personal:,.2f}")

        # Totals (Sin Gastos Operativos)
        total_ventas = self.venta_data["venta_total"]
        total_egresos = round(total_compras + total_personal, 2)
        saldo_neto = round(total_ventas - total_egresos, 2)
        cant_tickets = len(pol_rows) if pol_rows else self.venta_data["tickets"]

        self.lbl_val_venta.setText(f"S/ {total_ventas:,.2f}")
        self.lbl_val_egreso.setText(f"S/ {total_egresos:,.2f}")
        signo = "+" if saldo_neto > 0 else ""
        self.lbl_val_saldo.setText(f"{signo}S/ {saldo_neto:,.2f}")
        self.lbl_val_saldo.setStyleSheet(f"color: {'#10B981' if saldo_neto >= 0 else '#DC2626'}; font-size: 16px; font-weight: 900;")
        self.lbl_val_tickets.setText(f"{cant_tickets} efectivos")

        self.resumen_completo = {
            "fecha": self.fecha_str,
            "sede": self.sede_name,
            "efectivo": self.venta_data["efectivo"],
            "yape": self.venta_data["yape"],
            "tickets_cant": cant_tickets,
            "venta_tickets": self.venta_data["venta_tickets"],
            "venta_total": total_ventas,
            "compras": total_compras,
            "personal": total_personal,
            "total_egresos": total_egresos,
            "saldo_neto": saldo_neto
        }

    # ---------------------------------------------
    # Acciones de Efectivos PNP
    # ---------------------------------------------
    def _on_agregar_policia(self):
        if not self.mes_id:
            QMessageBox.warning(self, "Atención", "No se encontró el registro del mes activo.")
            return

        dlg = MarcarPoliciaDiaDialog(self.mes_id, self.dia, self.local_id, parent=self)
        if dlg.exec() == QDialog.Accepted:
            ToastManager.show_success("Efectivo PNP marcado correctamente", self)
            self._cargar_datos()

    def _on_desmarcar_policia(self, policia_id: int):
        resp = QMessageBox.question(
            self,
            "Confirmar",
            "¿Desea desmarcar el ticket de este efectivo para el día de hoy?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes and self.mes_id:
            target_local = self.local_id if self.local_id != LOCAL_CONSOLIDADO else LOCAL_RESTAURANTE
            self.ticket_service.toggle_ticket(self.mes_id, policia_id, self.dia, 0, local_id=target_local)
            ToastManager.show_info("Efectivo desmarcado", self)
            self._cargar_datos()

    # ---------------------------------------------
    # Acciones de Compras e Insumos
    # ---------------------------------------------
    def _on_agregar_compra(self):
        target_local = self.local_id if self.local_id in (LOCAL_RESTAURANTE, LOCAL_FAST_FOOD) else LOCAL_RESTAURANTE
        dlg = CompraSimpleDialog(parent=self, anio=self.anio, mes=self.mes, local_id=target_local, dia=self.dia)
        if dlg.exec() == QDialog.Accepted:
            compra = dlg.get_compra()
            ok, msg, _ = self.egreso_service.registrar_compra(compra)
            if ok:
                ToastManager.show_success("Compra registrada correctamente", self)
                self._cargar_datos()
            else:
                QMessageBox.warning(self, "Error", msg)

    def _on_eliminar_compra(self, compra_id: int):
        resp = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            "¿Está seguro de eliminar esta compra del registro?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            ok, msg = self.egreso_service.eliminar_compra(compra_id)
            if ok:
                ToastManager.show_info("Compra eliminada", self)
                self._cargar_datos()
            else:
                QMessageBox.warning(self, "Error", msg)

    # ---------------------------------------------
    # Acciones de Pagos al Personal
    # ---------------------------------------------
    def _on_agregar_personal(self):
        dlg = RegistrarPagoPersonalDialog(self.fecha_str, self.local_id, parent=self)
        if dlg.exec() == QDialog.Accepted:
            pago = dlg.get_pago()
            ok, msg, _ = self.egreso_service.registrar_pago_personal(pago)
            if ok:
                ToastManager.show_success("Pago al personal registrado correctamente", self)
                self._cargar_datos()
            else:
                QMessageBox.warning(self, "Error", msg)

    def _on_eliminar_personal(self, pago_id: int):
        resp = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            "¿Está seguro de eliminar este pago al personal?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            ok, msg = self.egreso_service.eliminar_pago_personal(pago_id)
            if ok:
                ToastManager.show_info("Pago eliminado", self)
                self._cargar_datos()
            else:
                QMessageBox.warning(self, "Error", msg)

    # ---------------------------------------------
    # Copiar Reporte WhatsApp
    # ---------------------------------------------
    def _copiar_whatsapp(self):
        d = self.resumen_completo
        signo = "+" if d['saldo_neto'] > 0 else ""
        rent = round((d['saldo_neto'] / d['venta_total'] * 100.0), 1) if d['venta_total'] > 0 else 0.0

        texto = (
            f"📊 *REPORTE DIARIO — {d['sede'].upper()}*\n"
            f"📅 *Fecha:* {d['fecha']}\n"
            f"───────────────────────────\n"
            f"💵 *INGRESOS / VENTAS:*\n"
            f"  • Efectivo: S/ {d['efectivo']:,.2f}\n"
            f"  • Yape / Digital: S/ {d['yape']:,.2f}\n"
            f"  • Tickets PNP ({d['tickets_cant']}): S/ {d['venta_tickets']:,.2f}\n"
            f"  ➜ *TOTAL VENTA:* S/ {d['venta_total']:,.2f}\n"
            f"───────────────────────────\n"
            f"💸 *EGRESOS OPERATIVOS:*\n"
            f"  • Compras / Insumos: S/ {d['compras']:,.2f}\n"
            f"  • Pago Personal: S/ {d['personal']:,.2f}\n"
            f"  ➜ *TOTAL EGRESOS:* S/ {d['total_egresos']:,.2f}\n"
            f"───────────────────────────\n"
            f"⚖️ *SALDO NETO:* {signo}S/ {d['saldo_neto']:,.2f}  (Margen: {rent:.1f}%)\n"
            f"🌟 *LA PROVINCIAL* — Sistema de Control"
        )
        QApplication.clipboard().setText(texto)
        ToastManager.show_success("¡Reporte copiado al portapapeles listo para WhatsApp!", self)
