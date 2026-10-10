import calendar
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QMessageBox,
    QFrame, QScrollArea, QDialog, QSizePolicy, QButtonGroup, QSpinBox,
    QLineEdit, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QColor, QFont, QCursor

from models.ticket import TicketDiario, DIAS_SEMANA_ES
from models.local import LOCAL_RESTAURANTE, LOCAL_FAST_FOOD, LOCAL_CONSOLIDADO, LOCAL_NAMES
from services.ticket_service import TicketService
from services.venta_service import VentaService
from services.mes_service import MesService
from views.components.toast import ToastManager
from views.dialogs.dia_ticket_dialog import DiaTicketDialog

class DiaTicketGridCell(QFrame):
    """
    Widget interactivo para cada día del mes en la cuadrícula de tickets.
    Permite ver el resumen rápido y con doble clic abre el diálogo emergente de edición.
    """
    doubleClicked = Signal(str)  # Emite la fecha (YYYY-MM-DD)
    clicked = Signal(str)

    def __init__(self, ticket_diario: Optional[TicketDiario] = None, dia_num: int = 0, es_otro_mes: bool = False, parent=None):
        super().__init__(parent)
        self.ticket_diario = ticket_diario
        self.dia_num = dia_num
        self.es_otro_mes = es_otro_mes
        self.setCursor(QCursor(Qt.PointingHandCursor) if not es_otro_mes else QCursor(Qt.ArrowCursor))
        self._init_ui()

    def _init_ui(self):
        self.setMinimumHeight(110)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        if self.es_otro_mes:
            self.setStyleSheet("""
                QFrame {
                    background-color: #080C14;
                    border: 1px dashed #1E293B;
                    border-radius: 8px;
                    opacity: 0.3;
                }
            """)
            lbl_empty = QLabel(str(self.dia_num) if self.dia_num > 0 else "")
            lbl_empty.setStyleSheet("color: #334155; font-size: 13px; font-weight: bold;")
            layout.addWidget(lbl_empty)
            layout.addStretch()
            return

        td = self.ticket_diario
        tot = td.total_policias if td else 0
        has_vales = (td.vales_policiales > 0) if td else False
        has_obs = bool(td.observacion and td.observacion.strip()) if td else False

        # Base style depending on activity
        if tot > 0:
            border_color = "#38BDF8" if tot >= 20 else "#0284C7"
            bg_color = "#0F172A"
        else:
            border_color = "#1E293B"
            bg_color = "#090D16"

        self.default_style = f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
        """
        self.hover_style = """
            QFrame {
                background-color: #131E35;
                border: 2px solid #38BDF8;
                border-radius: 8px;
            }
        """
        self.setStyleSheet(self.default_style)

        # Header of cell: Day number and weekday
        header_l = QHBoxLayout()
        header_l.setContentsMargins(0, 0, 0, 0)

        lbl_day = QLabel(str(self.dia_num))
        lbl_day.setStyleSheet("font-size: 15px; font-weight: 900; color: #F8FAFC;")
        header_l.addWidget(lbl_day)

        if td:
            lbl_sem = QLabel(td.dia_semana[:3].upper())
            is_weekend = td.dia_semana.lower() in ("sábado", "domingo", "sabado")
            sem_color = "#F59E0B" if is_weekend else "#64748B"
            lbl_sem.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {sem_color};")
            header_l.addWidget(lbl_sem)

        header_l.addStretch()

        if has_obs:
            lbl_note = QLabel("💬")
            lbl_note.setToolTip(f"Observación: {td.observacion}")
            header_l.addWidget(lbl_note)

        layout.addLayout(header_l)

        # Content Chips
        if td and (td.para_unidad > 0 or td.local > 0 or td.vales_policiales > 0):
            # Row 1: Unidad & Local
            h_det = QHBoxLayout()
            h_det.setContentsMargins(0, 0, 0, 0)
            h_det.setSpacing(4)

            lbl_u = QLabel(f"👮 {td.para_unidad}")
            lbl_u.setStyleSheet("background-color: #1E293B; color: #38BDF8; padding: 2px 4px; border-radius: 4px; font-size: 10px; font-weight: bold;")
            lbl_u.setToolTip(f"Para Unidad: {td.para_unidad} tickets")
            h_det.addWidget(lbl_u)

            lbl_l = QLabel(f"🍽️ {td.local}")
            lbl_l.setStyleSheet("background-color: #064E3B; color: #34D399; padding: 2px 4px; border-radius: 4px; font-size: 10px; font-weight: bold;")
            lbl_l.setToolTip(f"En Local: {td.local} tickets")
            h_det.addWidget(lbl_l)
            h_det.addStretch()
            layout.addLayout(h_det)

            # Row 2: Total Badge
            h_tot = QHBoxLayout()
            h_tot.setContentsMargins(0, 0, 0, 0)
            
            lbl_tot_badge = QLabel(f"🎫 TOTAL: {tot}")
            lbl_tot_badge.setStyleSheet("background-color: #1E1B4B; color: #A5B4FC; border: 1px solid #3730A3; padding: 3px 6px; border-radius: 4px; font-size: 11px; font-weight: 900;")
            h_tot.addWidget(lbl_tot_badge)
            
            if has_vales:
                lbl_val = QLabel(f"🎟️ {td.vales_policiales}")
                lbl_val.setStyleSheet("background-color: #581C87; color: #E9D5FF; padding: 2px 4px; border-radius: 4px; font-size: 10px; font-weight: bold;")
                lbl_val.setToolTip(f"Vales: {td.vales_policiales}")
                h_tot.addWidget(lbl_val)
                
            h_tot.addStretch()
            layout.addLayout(h_tot)
        else:
            lbl_vacio = QLabel("Sin tickets")
            lbl_vacio.setStyleSheet("color: #475569; font-size: 10px; font-style: italic;")
            layout.addWidget(lbl_vacio)

        layout.addStretch()

        # Tooltip with full detail
        if td:
            tooltip_txt = (
                f"📅 {td.dia_semana} {td.fecha}\n"
                f"👮 Para Unidad: {td.para_unidad}\n"
                f"🍽️ En Local: {td.local}\n"
                f"🎫 Total Policías: {td.total_policias}\n"
                f"🎟️ Vales Policiales: {td.vales_policiales}\n"
            )
            if td.observacion:
                tooltip_txt += f"📝 Observación: {td.observacion}\n"
            tooltip_txt += "\n💡 Doble clic para abrir ventana emergente de edición"
            self.setToolTip(tooltip_txt)

    def enterEvent(self, event):
        if not self.es_otro_mes:
            self.setStyleSheet(self.hover_style)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.es_otro_mes:
            self.setStyleSheet(self.default_style)
        super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if not self.es_otro_mes and self.ticket_diario:
            self.doubleClicked.emit(self.ticket_diario.fecha)
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if not self.es_otro_mes and self.ticket_diario:
            self.clicked.emit(self.ticket_diario.fecha)
        super().mousePressEvent(event)


class CalendarioView(QWidget):
    """
    Vista principal dinámica de Calendario de Tickets con cuadrícula real mensual,
    edición emergente por doble clic y panel de KPIs.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ticket_service = TicketService()
        self.venta_service = VentaService()
        self.mes_service = MesService()

        self.current_anio = 2026
        self.current_mes = 9
        self.current_local = LOCAL_RESTAURANTE
        self.diarios: List[TicketDiario] = []
        self.diarios_map: Dict[str, TicketDiario] = {}

        self._init_ui()
        self._cargar_combo_periodos()
        self.cargar_datos()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 1. Header Toolbar
        header = QHBoxLayout()
        self.lbl_title = QLabel("📅 CALENDARIO DINÁMICO DE TICKETS")
        self.lbl_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.lbl_title.setStyleSheet("color: #38BDF8;")
        header.addWidget(self.lbl_title)

        self.lbl_local_badge = QLabel(f"Sede: {LOCAL_NAMES.get(self.current_local, 'RESTAURANTE')}")
        self.lbl_local_badge.setStyleSheet("background: #1E293B; color: #38BDF8; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 11px;")
        header.addWidget(self.lbl_local_badge)

        header.addStretch()

        # Month navigation buttons
        btn_prev = QPushButton("◀ Anterior")
        btn_prev.setStyleSheet("background: #1E293B; color: #E2E8F0; padding: 6px 10px; border-radius: 6px; font-weight: bold;")
        btn_prev.clicked.connect(self._on_prev_month)
        header.addWidget(btn_prev)

        self.combo_periodo = QComboBox()
        self.combo_periodo.setStyleSheet("background: #0F172A; color: #F8FAFC; border: 1px solid #334155; padding: 6px 12px; border-radius: 6px; font-weight: bold; min-width: 170px;")
        self.combo_periodo.currentIndexChanged.connect(self._on_periodo_changed)
        header.addWidget(self.combo_periodo)

        btn_next = QPushButton("Siguiente ▶")
        btn_next.setStyleSheet("background: #1E293B; color: #E2E8F0; padding: 6px 10px; border-radius: 6px; font-weight: bold;")
        btn_next.clicked.connect(self._on_next_month)
        header.addWidget(btn_next)

        # View Mode Switcher
        self.btn_view_grid = QPushButton("📅 Calendario")
        self.btn_view_grid.setCheckable(True)
        self.btn_view_grid.setChecked(True)
        self.btn_view_grid.setStyleSheet("""
            QPushButton { background: #1E293B; color: #94A3B8; padding: 6px 12px; border-radius: 6px; font-weight: bold; }
            QPushButton:checked { background: #0284C7; color: white; }
        """)
        self.btn_view_grid.clicked.connect(lambda: self._set_view_mode(0))

        self.btn_view_list = QPushButton("📋 Lista")
        self.btn_view_list.setCheckable(True)
        self.btn_view_list.setStyleSheet("""
            QPushButton { background: #1E293B; color: #94A3B8; padding: 6px 12px; border-radius: 6px; font-weight: bold; }
            QPushButton:checked { background: #0284C7; color: white; }
        """)
        self.btn_view_list.clicked.connect(lambda: self._set_view_mode(1))

        header.addWidget(self.btn_view_grid)
        header.addWidget(self.btn_view_list)

        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.setStyleSheet("background: #334155; color: #F8FAFC; padding: 6px 12px; border-radius: 6px; font-weight: bold;")
        btn_refresh.clicked.connect(self.cargar_datos)
        header.addWidget(btn_refresh)

        layout.addLayout(header)

        # 2. KPI Summary Bar (Tremor BI Style)
        kpi_layout = QHBoxLayout()
        self.card_tot_tickets = self._create_kpi_card("TOTAL TICKETS MES", "0", "#38BDF8", "🎫")
        self.card_unidad = self._create_kpi_card("PARA UNIDAD", "0", "#0284C7", "👮")
        self.card_local = self._create_kpi_card("EN LOCAL", "0", "#10B981", "🍽️")
        self.card_vales = self._create_kpi_card("VALES POLICIALES", "0", "#A855F7", "🎟️")
        self.card_promedio = self._create_kpi_card("PROMEDIO DIARIO", "0.0 / día", "#F59E0B", "📊")

        kpi_layout.addWidget(self.card_tot_tickets)
        kpi_layout.addWidget(self.card_unidad)
        kpi_layout.addWidget(self.card_local)
        kpi_layout.addWidget(self.card_vales)
        kpi_layout.addWidget(self.card_promedio)
        layout.addLayout(kpi_layout)

        # 3. Stacked Area for Views (0: Grid Calendar, 1: List Table)
        self.stack = QStackedWidget()

        # VIEW 0: Grid Calendar
        self.widget_grid = self._build_grid_view()
        self.stack.addWidget(self.widget_grid)

        # VIEW 1: List Table
        self.widget_list = self._build_list_view()
        self.stack.addWidget(self.widget_list)

        layout.addWidget(self.stack, 1)

        # 4. Footer info
        footer_box = QHBoxLayout()
        lbl_hint = QLabel("💡 <b>Tip de uso:</b> Haga <b>doble clic</b> en cualquier día del calendario para abrir la ventana emergente y modificar tickets en segundos.")
        lbl_hint.setStyleSheet("color: #64748B; font-size: 11px;")
        footer_box.addWidget(lbl_hint)
        footer_box.addStretch()
        layout.addLayout(footer_box)

    def _create_kpi_card(self, title: str, value: str, color: str, icon: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"""
            QWidget {{
                background-color: #0F172A;
                border-left: 4px solid {color};
                border-radius: 8px;
            }}
        """)
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 8, 12, 8)
        l.setSpacing(2)

        top_h = QHBoxLayout()
        lbl_t = QLabel(f"{icon} {title}")
        lbl_t.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        top_h.addWidget(lbl_t)
        top_h.addStretch()
        l.addLayout(top_h)

        lbl_v = QLabel(value)
        lbl_v.setObjectName("val")
        lbl_v.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: 900;")
        l.addWidget(lbl_v)
        return w

    def _update_kpi(self, card: QWidget, value: str):
        lbl = card.findChild(QLabel, "val")
        if lbl:
            lbl.setText(value)

    def _build_grid_view(self) -> QWidget:
        container = QWidget()
        l = QVBoxLayout(container)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)

        # Weekdays Header Row (LUN, MAR, MIÉ, JUE, VIE, SÁB, DOM)
        days_header = QHBoxLayout()
        days_header.setSpacing(8)
        dias_labels = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
        for idx, d_name in enumerate(dias_labels):
            is_wend = idx in (5, 6)
            bg_h = "#1E1B4B" if is_wend else "#1E293B"
            txt_h = "#C7D2FE" if is_wend else "#94A3B8"
            lbl = QLabel(d_name)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"background-color: {bg_h}; color: {txt_h}; font-size: 11px; font-weight: 900; padding: 6px; border-radius: 6px;")
            days_header.addWidget(lbl)
        l.addLayout(days_header)

        # Scroll area for calendar cells
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(8)
        scroll.setWidget(self.grid_container)

        l.addWidget(scroll, 1)
        return container

    def _build_list_view(self) -> QWidget:
        container = QWidget()
        l = QVBoxLayout(container)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(8)

        tb = QHBoxLayout()
        btn_save_all = QPushButton("💾 Guardar Todo en Lote")
        btn_save_all.setStyleSheet("background: #0284C7; color: white; font-weight: bold; padding: 6px 14px; border-radius: 6px;")
        btn_save_all.clicked.connect(self._on_guardar_todo_lista)
        tb.addWidget(btn_save_all)

        lbl_info_rule = QLabel("ℹ️ Regla: TOTAL = Para Unidad + Local. Los vales se registran por separado.")
        lbl_info_rule.setStyleSheet("color: #64748B; font-size: 11px; margin-left: 10px;")
        tb.addWidget(lbl_info_rule)
        tb.addStretch()
        l.addLayout(tb)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Fecha", "Día", "Para Unidad (*)", "Local (*)", "Total Policías (Calc)", "Vales Policiales", "Observación"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.cellDoubleClicked.connect(self._on_table_cell_double_clicked)
        l.addWidget(self.table)

        return container

    def _set_view_mode(self, mode: int):
        self.stack.setCurrentIndex(mode)
        self.btn_view_grid.setChecked(mode == 0)
        self.btn_view_list.setChecked(mode == 1)

    def _cargar_combo_periodos(self):
        self.combo_periodo.blockSignals(True)
        self.combo_periodo.clear()
        meses = self.mes_service.get_all()
        for m in meses:
            self.combo_periodo.addItem(m.display_name, (m.anio, m.mes))
        if not meses:
            self.combo_periodo.addItem("SEPTIEMBRE 2026", (2026, 9))
        self.combo_periodo.blockSignals(False)

    def set_local(self, local_id: str):
        self.current_local = local_id
        self.lbl_local_badge.setText(f"Sede: {LOCAL_NAMES.get(local_id, local_id.upper())}")
        self.cargar_datos()

    def set_periodo(self, anio: int, mes: int):
        self.current_anio = anio
        self.current_mes = mes
        self.lbl_title.setText(f"📅 CALENDARIO TICKETS — {mes:02d}/{anio}")
        # Sync combo index
        self.combo_periodo.blockSignals(True)
        for i in range(self.combo_periodo.count()):
            data = self.combo_periodo.itemData(i)
            if data == (anio, mes):
                self.combo_periodo.setCurrentIndex(i)
                break
        self.combo_periodo.blockSignals(False)
        self.cargar_datos()

    def _on_periodo_changed(self, idx):
        data = self.combo_periodo.currentData()
        if data:
            self.current_anio, self.current_mes = data
            self.lbl_title.setText(f"📅 CALENDARIO TICKETS — {self.current_mes:02d}/{self.current_anio}")
            self.cargar_datos()

    def _on_prev_month(self):
        m = self.current_mes - 1
        y = self.current_anio
        if m < 1:
            m = 12
            y -= 1
        self.set_periodo(y, m)

    def _on_next_month(self):
        m = self.current_mes + 1
        y = self.current_anio
        if m > 12:
            m = 1
            y += 1
        self.set_periodo(y, m)

    def cargar_datos(self):
        anio, mes = self.current_anio, self.current_mes
        local = self.current_local

        self.diarios = self.ticket_service.get_calendario_mes(anio, mes, local_id=local)
        self.diarios_map = {d.fecha: d for d in self.diarios}

        # 1. Update KPI Summary
        tot_u = sum(d.para_unidad for d in self.diarios)
        tot_l = sum(d.local for d in self.diarios)
        tot_p = sum(d.total_policias for d in self.diarios)
        tot_v = sum(d.vales_policiales for d in self.diarios)
        dias_activos = sum(1 for d in self.diarios if d.total_policias > 0)
        promedio = (tot_p / dias_activos) if dias_activos > 0 else 0.0

        self._update_kpi(self.card_tot_tickets, f"{tot_p:,} tickets")
        self._update_kpi(self.card_unidad, f"{tot_u:,}")
        self._update_kpi(self.card_local, f"{tot_l:,}")
        self._update_kpi(self.card_vales, f"{tot_v:,}")
        self._update_kpi(self.card_promedio, f"{promedio:.1f} / día")

        # 2. Render Calendar Grid
        self._render_grid_view()

        # 3. Render List View
        self._render_list_view()

    def _render_grid_view(self):
        # Clear existing grid cells
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        anio, mes = self.current_anio, self.current_mes
        cal = calendar.monthcalendar(anio, mes)

        for r, week in enumerate(cal):
            for c, dia_num in enumerate(week):
                if dia_num == 0:
                    cell = DiaTicketGridCell(es_otro_mes=True)
                else:
                    fecha_str = f"{anio:04d}-{mes:02d}-{dia_num:02d}"
                    td = self.diarios_map.get(fecha_str)
                    if not td:
                        td = TicketDiario(
                            fecha=fecha_str,
                            local_id=self.current_local,
                            anio=anio,
                            mes=mes,
                            dia=dia_num,
                            dia_semana=DIAS_SEMANA_ES[calendar.weekday(anio, mes, dia_num)],
                            para_unidad=0,
                            local=0,
                            total_policias=0,
                            vales_policiales=0
                        )
                    cell = DiaTicketGridCell(ticket_diario=td, dia_num=dia_num, es_otro_mes=False)
                    cell.doubleClicked.connect(self._abrir_dialogo_edicion)

                self.grid_layout.addWidget(cell, r, c)

    def _render_list_view(self):
        self.table.setRowCount(len(self.diarios))
        self.spin_widgets = {}

        for r, td in enumerate(self.diarios):
            # 0. Fecha
            self.table.setItem(r, 0, QTableWidgetItem(td.fecha))
            # 1. Dia de la semana
            self.table.setItem(r, 1, QTableWidgetItem(td.dia_semana))

            # 2. Para Unidad (SpinBox)
            sb_unidad = QSpinBox()
            sb_unidad.setRange(0, 9999)
            sb_unidad.setValue(td.para_unidad)
            sb_unidad.valueChanged.connect(lambda val, row=r: self._on_list_value_changed(row))
            self.table.setCellWidget(r, 2, sb_unidad)

            # 3. Local (SpinBox)
            sb_local = QSpinBox()
            sb_local.setRange(0, 9999)
            sb_local.setValue(td.local)
            sb_local.valueChanged.connect(lambda val, row=r: self._on_list_value_changed(row))
            self.table.setCellWidget(r, 3, sb_local)

            # 4. Total
            tot_item = QTableWidgetItem(str(td.total_policias))
            tot_item.setTextAlignment(Qt.AlignCenter)
            tot_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(r, 4, tot_item)

            # 5. Vales policiales
            sb_vales = QSpinBox()
            sb_vales.setRange(0, 9999)
            sb_vales.setValue(td.vales_policiales)
            self.table.setCellWidget(r, 5, sb_vales)

            # 6. Observacion
            txt_obs = QLineEdit()
            if td.observacion:
                txt_obs.setText(td.observacion)
            self.table.setCellWidget(r, 6, txt_obs)

            self.spin_widgets[r] = {
                "unidad": sb_unidad,
                "local": sb_local,
                "vales": sb_vales,
                "obs": txt_obs
            }

    def _on_list_value_changed(self, row: int):
        widgets = self.spin_widgets.get(row)
        if widgets:
            unidad = widgets["unidad"].value()
            local = widgets["local"].value()
            total = unidad + local
            tot_item = self.table.item(row, 4)
            if tot_item:
                tot_item.setText(str(total))

    def _on_table_cell_double_clicked(self, row: int, col: int):
        item = self.table.item(row, 0)
        if item and item.text():
            self._abrir_dialogo_edicion(item.text())

    def _abrir_dialogo_edicion(self, fecha_str: str):
        td = self.diarios_map.get(fecha_str)
        if not td:
            return

        # Check if there is a next day in this month
        dt = datetime.strptime(fecha_str, "%Y-%m-%d")
        num_dias = calendar.monthrange(dt.year, dt.month)[1]
        tiene_siguiente = dt.day < num_dias

        def _guardar_callback(ticket_mod: TicketDiario, motivo_ajuste: Optional[str]):
            ok, msg, _ = self.ticket_service.guardar_ticket_diario(
                fecha=ticket_mod.fecha,
                para_unidad=ticket_mod.para_unidad,
                local=ticket_mod.local,
                vales_policiales=ticket_mod.vales_policiales,
                local_id=self.current_local,
                observacion=ticket_mod.observacion,
                motivo_ajuste=motivo_ajuste
            )
            if ok:
                self.venta_service.sincronizar_desde_calendario(ticket_mod.fecha)
                ToastManager.show_success(
                    f"Guardado {ticket_mod.fecha}: {ticket_mod.total_policias} tickets (U:{ticket_mod.para_unidad} + L:{ticket_mod.local})",
                    self
                )
                self.cargar_datos()
            else:
                QMessageBox.warning(self, "Error", msg)

        dlg = DiaTicketDialog(
            ticket_diario=td,
            parent=self,
            on_save_callback=_guardar_callback,
            tiene_siguiente=tiene_siguiente
        )

        dlg.siguiente_dia_solicitado.connect(self._abrir_siguiente_dia)
        dlg.exec()

    def _abrir_siguiente_dia(self, fecha_actual_str: str):
        try:
            dt = datetime.strptime(fecha_actual_str, "%Y-%m-%d")
            sig_dt = dt + timedelta(days=1)
            if sig_dt.month == self.current_mes and sig_dt.year == self.current_anio:
                sig_fecha_str = sig_dt.strftime("%Y-%m-%d")
                self._abrir_dialogo_edicion(sig_fecha_str)
        except Exception:
            pass

    def _on_guardar_todo_lista(self):
        guardados = 0
        for r, td in enumerate(self.diarios):
            w = self.spin_widgets.get(r)
            if w:
                u = w["unidad"].value()
                l = w["local"].value()
                v = w["vales"].value()
                obs = w["obs"].text().strip() or None

                self.ticket_service.guardar_ticket_diario(
                    fecha=td.fecha,
                    para_unidad=u,
                    local=l,
                    vales_policiales=v,
                    local_id=self.current_local,
                    observacion=obs
                )
                self.venta_service.sincronizar_desde_calendario(td.fecha)
                guardados += 1

        ToastManager.show_success(f"Se guardaron correctamente los {guardados} días del mes.", self)
        self.cargar_datos()
