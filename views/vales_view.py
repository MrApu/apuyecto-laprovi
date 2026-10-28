from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QSpinBox, QLineEdit, QMessageBox, QFrame,
    QTabWidget
)
from PySide6.QtCore import Qt
from typing import Optional, List, Dict
from models.vale import Vale
from models.vale_policia import ValePolicia
from models.policia import Policia
from services.vale_service import ValeService
from services.ticket_service import TicketService
from services.policia_service import PoliciaService
from views.components.toast import ToastManager
from views.dialogs.vale_dialog import ValeRapidoDialog
from views.dialogs.vale_policia_dialog import ValePoliciaDialog

class ValesView(QWidget):
    """
    Control de Vales Policiales con:
    1. Registro detallado de vales entregados y canjeados por policía (a quién dimos vales por tickets)
       con buscador reactivo instantáneo.
    2. Resumen Diario General de Vales con cálculo automático de saldos y alertas.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vale_service = ValeService()
        self.ticket_service = TicketService()
        self.policia_service = PoliciaService()
        self.current_anio = 2026
        self.current_mes = 9
        self.vales: List[Vale] = []
        self.vales_map: Dict[str, Vale] = {}
        self.vales_policias_data: List[ValePolicia] = []
        self.policias_activos: List[Policia] = []
        self.widgets: Dict[int, Dict[str, Any]] = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header principal
        header_box = QHBoxLayout()
        self.lbl_title = QLabel("🎟️ Control de Vales Policiales")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        header_box.addWidget(self.lbl_title)
        header_box.addStretch()

        self.btn_nuevo_vale_policia = QPushButton("➕ Registrar Vales por Tickets a Policía")
        self.btn_nuevo_vale_policia.setCursor(Qt.PointingHandCursor)
        self.btn_nuevo_vale_policia.setStyleSheet("""
            background-color: #DC2626;
            color: #FFFFFF;
            font-weight: 800;
            padding: 7px 14px;
            border-radius: 6px;
        """)
        self.btn_nuevo_vale_policia.clicked.connect(self._on_nuevo_vale_policia)
        header_box.addWidget(self.btn_nuevo_vale_policia)

        self.btn_editar_sel = QPushButton("✏️ Editar Día Seleccionado")
        self.btn_editar_sel.setCursor(Qt.PointingHandCursor)
        self.btn_editar_sel.setStyleSheet("""
            QPushButton {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #27272A;
                border: 1px solid #DC2626;
            }
        """)
        self.btn_editar_sel.clicked.connect(self._on_editar_seleccionado)
        header_box.addWidget(self.btn_editar_sel)

        self.btn_guardar_todo = QPushButton("💾 Guardar Cambios en Lote")
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

        # Tabs: 1. Por Policía (A quién dimos vales) y 2. Resumen Diario
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

        # Tab 1: Vales por Policía
        tab_policia = self._build_tab_vales_policia()
        self.tabs.addTab(tab_policia, "👮 Vales por Policía (A quién dimos vales por tickets)")

        # Tab 2: Resumen Diario
        tab_diario = self._build_tab_vales_diario()
        self.tabs.addTab(tab_diario, "📅 Resumen Diario General de Vales")

        layout.addWidget(self.tabs)

    def _build_tab_vales_policia(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(10)

        # Buscador instantáneo con descarte
        top_h = QHBoxLayout()
        self.txt_buscar_vale = QLineEdit()
        self.txt_buscar_vale.setPlaceholderText("🔍 Buscar por apellidos, nombres, código del policía o detalle... (descarte en tiempo real)")
        self.txt_buscar_vale.setStyleSheet("""
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
        self.txt_buscar_vale.textChanged.connect(self._filtrar_vales_policias)
        top_h.addWidget(self.txt_buscar_vale, 3)

        btn_add = QPushButton("➕ Entregar Vales a Policía")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            background-color: #DC2626;
            color: #FFFFFF;
            font-weight: 800;
            padding: 8px 16px;
            border-radius: 6px;
        """)
        btn_add.clicked.connect(self._on_nuevo_vale_policia)
        top_h.addWidget(btn_add, 1)

        l.addLayout(top_h)

        # KPIs Vales por Policía
        kpi_row = QHBoxLayout()
        self.lbl_kpi_vales_dados = QLabel("0")
        self.lbl_kpi_tickets_canjeados = QLabel("0")
        self.lbl_kpi_policias_atendidos = QLabel("0")

        kpi_row.addWidget(self._create_kpi_card_simple("VALES ENTREGADOS / CANJEADOS", self.lbl_kpi_vales_dados, "#F59E0B", "🎟️"))
        kpi_row.addWidget(self._create_kpi_card_simple("TICKETS EQUIVALENTES", self.lbl_kpi_tickets_canjeados, "#10B981", "📥"))
        kpi_row.addWidget(self._create_kpi_card_simple("REGISTROS EN EL MES", self.lbl_kpi_policias_atendidos, "#38BDF8", "👥"))
        l.addLayout(kpi_row)

        # Tabla de vales a policías
        self.tbl_vales_policias = QTableWidget()
        self.tbl_vales_policias.setColumnCount(8)
        self.tbl_vales_policias.setHorizontalHeaderLabels([
            "Fecha", "Código", "Policía / Beneficiario", "Área", "Vales Dados / Canjeados",
            "Tickets Equivalentes", "Observación", "Acciones"
        ])
        self.tbl_vales_policias.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl_vales_policias.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_vales_policias.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl_vales_policias.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tbl_vales_policias.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tbl_vales_policias.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tbl_vales_policias.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.tbl_vales_policias.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.tbl_vales_policias.setColumnWidth(7, 130)
        self.tbl_vales_policias.setAlternatingRowColors(True)
        self.tbl_vales_policias.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_vales_policias.setEditTriggers(QTableWidget.NoEditTriggers)
        l.addWidget(self.tbl_vales_policias)

        return w

    def _create_kpi_card_simple(self, title: str, val_lbl: QLabel, color: str, icon: str) -> QWidget:
        w = QFrame()
        w.setStyleSheet(f"background: #111827; border: 1px solid #1F2937; border-left: 4px solid {color}; border-radius: 8px; padding: 6px;")
        l = QVBoxLayout(w)
        l.setContentsMargins(10, 6, 10, 6)
        l.setSpacing(2)
        lbl_t = QLabel(f"{icon} {title}")
        lbl_t.setStyleSheet("color: #94A3B8; font-size: 10px; font-weight: 800; letter-spacing: 0.5px;")
        val_lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 800;")
        l.addWidget(lbl_t)
        l.addWidget(val_lbl)
        return w

    def _build_tab_vales_diario(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(10)

        # KPI Summary Cards Diarios
        kpi_row = QHBoxLayout()
        self.card_entregados = self._create_kpi_card("VALES ENTREGADOS", "0", "#F59E0B", "📤")
        self.card_canjeados = self._create_kpi_card("VALES CANJEADOS", "0", "#10B981", "📥")
        self.card_saldo = self._create_kpi_card("SALDO EN CIRCULACIÓN", "0", "#38BDF8", "⚖️")

        kpi_row.addWidget(self.card_entregados)
        kpi_row.addWidget(self.card_canjeados)
        kpi_row.addWidget(self.card_saldo)
        l.addLayout(kpi_row)

        info_banner = QLabel("💡 <b>Edición protegida:</b> Use el botón <b>'✏️ Editar'</b> de cada fila para abrir la ventana rápida sin riesgo de cambios accidentales.")
        info_banner.setStyleSheet("background-color: #18181B; color: #E4E4E7; padding: 10px 14px; border-radius: 8px; border: 1px solid #27272A;")
        l.addWidget(info_banner)

        # Table Diaria
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Fecha", "Vales Entregados", "Vales Canjeados", "Saldo Calculado", "Observaciones", "Acción"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 95)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        l.addWidget(self.table)

        return w

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

    def _update_kpi(self, card: QWidget, value: str, is_negative: bool = False):
        lbl = card.findChild(QLabel, "val")
        if lbl:
            lbl.setText(value)
            if is_negative:
                lbl.setStyleSheet("color: #F43F5E; font-size: 18px; font-weight: 900;")
            else:
                lbl.setStyleSheet("color: #10B981; font-size: 18px; font-weight: 900;")

    def set_periodo(self, anio: int, mes: int):
        self.current_anio = anio
        self.current_mes = mes
        self.lbl_title.setText(f"🎟️ Control de Vales Policiales — {mes:02d}/{anio}")
        self.cargar_datos()

    def cargar_datos(self):
        # 1. Cargar policías activos
        self.policias_activos = self.policia_service.get_all(solo_activos=True)

        # 2. Cargar vales por policía
        mes_prefijo = f"{self.current_anio:04d}-{self.current_mes:02d}"
        self.vales_policias_data = self.vale_service.get_vales_policias(mes_prefijo=mes_prefijo)
        self._filtrar_vales_policias()

        # 3. Cargar resumen diario
        diarios = self.ticket_service.get_calendario_mes(self.current_anio, self.current_mes)
        vales_existentes = {v.fecha: v for v in self.vale_service.get_by_mes(self.current_anio, self.current_mes)}
        self.vales_map = vales_existentes

        self.table.setRowCount(len(diarios))
        self.widgets = {}

        for r, td in enumerate(diarios):
            fecha = td.fecha
            v = vales_existentes.get(fecha, Vale(fecha=fecha, vales_entregados=td.vales_policiales, vales_canjeados=0))
            self.vales_map[fecha] = v

            self.table.setItem(r, 0, QTableWidgetItem(fecha))

            sb_ent = QSpinBox()
            sb_ent.setRange(0, 9999)
            sb_ent.setValue(v.vales_entregados)
            sb_ent.valueChanged.connect(lambda _, row=r: self._on_value_changed(row))
            self.table.setCellWidget(r, 1, sb_ent)

            sb_can = QSpinBox()
            sb_can.setRange(0, 9999)
            sb_can.setValue(v.vales_canjeados)
            sb_can.valueChanged.connect(lambda _, row=r: self._on_value_changed(row))
            self.table.setCellWidget(r, 2, sb_can)

            sal_item = QTableWidgetItem(str(v.saldo))
            sal_item.setTextAlignment(Qt.AlignCenter)
            sal_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self._apply_saldo_style(sal_item, v.saldo)
            self.table.setItem(r, 3, sal_item)

            txt_obs = QLineEdit()
            if v.observacion:
                txt_obs.setText(v.observacion)
            self.table.setCellWidget(r, 4, txt_obs)

            btn_edit = QPushButton("✏️ Editar")
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setStyleSheet("""
                QPushButton {
                    background-color: #18181B;
                    color: #FFFFFF;
                    border: 1px solid #3F3F46;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #DC2626;
                    border-color: #DC2626;
                }
            """)
            btn_edit.clicked.connect(lambda _, f=fecha: self._abrir_modal_editar(f))
            self.table.setCellWidget(r, 5, btn_edit)

            self.widgets[r] = {
                "fecha": fecha,
                "entregados": sb_ent,
                "canjeados": sb_can,
                "saldo_item": sal_item,
                "obs": txt_obs
            }

        self._recalcular_resumen_diario()

    def _filtrar_vales_policias(self):
        busqueda = self.txt_buscar_vale.text().strip().upper()
        filtrados: List[ValePolicia] = []

        for vp in self.vales_policias_data:
            if busqueda:
                full_text = f"{vp.policia_codigo or ''} {vp.policia_apellidos or ''} {vp.policia_nombres or ''} {vp.policia_area or ''} {vp.observacion or ''}".upper()
                if busqueda not in full_text:
                    continue
            filtrados.append(vp)

        # KPIs
        tot_vales = sum(vp.cantidad_vales for vp in self.vales_policias_data)
        tot_tickets = sum(vp.tickets_equivalentes for vp in self.vales_policias_data)
        self.lbl_kpi_vales_dados.setText(str(tot_vales))
        self.lbl_kpi_tickets_canjeados.setText(str(tot_tickets))
        self.lbl_kpi_policias_atendidos.setText(str(len(self.vales_policias_data)))

        # Renderizar tabla de vales de policías
        self.tbl_vales_policias.setRowCount(len(filtrados))
        for r, vp in enumerate(filtrados):
            self.tbl_vales_policias.setItem(r, 0, QTableWidgetItem(vp.fecha))
            self.tbl_vales_policias.setItem(r, 1, QTableWidgetItem(vp.policia_codigo or "-"))
            
            it_nom = QTableWidgetItem(vp.policia_nombre_completo)
            it_nom.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.tbl_vales_policias.setItem(r, 2, it_nom)

            self.tbl_vales_policias.setItem(r, 3, QTableWidgetItem(vp.policia_area or "-"))

            it_v = QTableWidgetItem(str(vp.cantidad_vales))
            it_v.setTextAlignment(Qt.AlignCenter)
            it_v.setForeground(Qt.yellow)
            self.tbl_vales_policias.setItem(r, 4, it_v)

            it_t = QTableWidgetItem(str(vp.tickets_equivalentes))
            it_t.setTextAlignment(Qt.AlignCenter)
            it_t.setForeground(Qt.green)
            self.tbl_vales_policias.setItem(r, 5, it_t)

            self.tbl_vales_policias.setItem(r, 6, QTableWidgetItem(vp.observacion or "-"))

            # Botones de Acción
            act_box = QWidget()
            h = QHBoxLayout(act_box)
            h.setContentsMargins(4, 2, 4, 2)
            h.setSpacing(6)

            btn_e = QPushButton("✏️")
            btn_e.setCursor(Qt.PointingHandCursor)
            btn_e.setToolTip("Editar vale")
            btn_e.setStyleSheet("background: #27272A; color: #FFFFFF; border-radius: 4px; padding: 2px 6px;")
            btn_e.clicked.connect(lambda _, item=vp: self._editar_vale_policia(item))
            h.addWidget(btn_e)

            btn_d = QPushButton("🗑️")
            btn_d.setCursor(Qt.PointingHandCursor)
            btn_d.setToolTip("Eliminar vale")
            btn_d.setStyleSheet("background: #7F1D1D; color: #FFFFFF; border-radius: 4px; padding: 2px 6px;")
            btn_d.clicked.connect(lambda _, v_id=vp.id: self._eliminar_vale_policia(v_id))
            h.addWidget(btn_d)

            self.tbl_vales_policias.setCellWidget(r, 7, act_box)

    def _on_nuevo_vale_policia(self):
        if not self.policias_activos:
            self.policias_activos = self.policia_service.get_all(solo_activos=True)
        dlg = ValePoliciaDialog(policias=self.policias_activos, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            ok, msg, _ = self.vale_service.registrar_vale_policia(
                policia_id=data["policia_id"],
                fecha=data["fecha"],
                cantidad_vales=data["cantidad_vales"],
                tickets_equivalentes=data["tickets_equivalentes"],
                observacion=data["observacion"]
            )
            if ok:
                ToastManager.show_success(msg, self)
                self.cargar_datos()
            else:
                ToastManager.show_warning(msg, self)

    def _editar_vale_policia(self, vale: ValePolicia):
        if not self.policias_activos:
            self.policias_activos = self.policia_service.get_all(solo_activos=True)
        dlg = ValePoliciaDialog(policias=self.policias_activos, vale=vale, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            ok, msg = self.vale_service.actualizar_vale_policia(
                vale_id=vale.id,
                policia_id=data["policia_id"],
                fecha=data["fecha"],
                cantidad_vales=data["cantidad_vales"],
                tickets_equivalentes=data["tickets_equivalentes"],
                observacion=data["observacion"]
            )
            if ok:
                ToastManager.show_success(msg, self)
                self.cargar_datos()
            else:
                ToastManager.show_warning(msg, self)

    def _eliminar_vale_policia(self, vale_id: int):
        resp = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            "¿Desea eliminar este registro de entrega de vales al policía?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            ok, msg = self.vale_service.eliminar_vale_policia(vale_id)
            if ok:
                ToastManager.show_success(msg, self)
                self.cargar_datos()
            else:
                ToastManager.show_warning(msg, self)

    def _on_value_changed(self, row: int):
        w = self.widgets.get(row)
        if w:
            ent = w["entregados"].value()
            can = w["canjeados"].value()
            sal = ent - can
            sal_item = w["saldo_item"]
            sal_item.setText(str(sal))
            self._apply_saldo_style(sal_item, sal)
        self._recalcular_resumen_diario()

    def _apply_saldo_style(self, item: QTableWidgetItem, saldo: int):
        if saldo < 0:
            item.setForeground(Qt.red)
        elif saldo > 0:
            item.setForeground(Qt.green)
        else:
            item.setForeground(Qt.white)

    def _recalcular_resumen_diario(self):
        tot_ent = 0
        tot_can = 0
        for r, w in self.widgets.items():
            tot_ent += w["entregados"].value()
            tot_can += w["canjeados"].value()
        saldo_mes = tot_ent - tot_can
        self._update_kpi(self.card_entregados, str(tot_ent))
        self._update_kpi(self.card_canjeados, str(tot_can))
        self._update_kpi(self.card_saldo, str(saldo_mes), is_negative=(saldo_mes < 0))

    def _on_cell_double_clicked(self, row: int, col: int):
        w = self.widgets.get(row)
        if w:
            self._abrir_modal_editar(w["fecha"])

    def _on_editar_seleccionado(self):
        sel = self.table.selectedItems()
        if not sel:
            QMessageBox.information(self, "Selección requerida", "Haga clic en una fila de la tabla para editar ese día.")
            return
        row = sel[0].row()
        w = self.widgets.get(row)
        if w:
            self._abrir_modal_editar(w["fecha"])

    def _abrir_modal_editar(self, fecha: str):
        v = self.vales_map.get(fecha, Vale(fecha=fecha))
        dlg = ValeRapidoDialog(v, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            ok, msg, saved_vale = self.vale_service.guardar_vale(
                fecha=fecha,
                vales_entregados=data["vales_entregados"],
                vales_canjeados=data["vales_canjeados"],
                observacion=data["observacion"]
            )
            if ok:
                ToastManager.show_success(msg, self)
                self.cargar_datos()
            else:
                ToastManager.show_warning(msg, self)

    def _on_guardar_todo(self):
        guardados = 0
        negativos = 0
        for r, w in self.widgets.items():
            fecha = w["fecha"]
            ent = w["entregados"].value()
            can = w["canjeados"].value()
            obs = w["obs"].text().strip() or None

            ok, msg, v = self.vale_service.guardar_vale(
                fecha=fecha,
                vales_entregados=ent,
                vales_canjeados=can,
                observacion=obs
            )
            if v.saldo < 0:
                negativos += 1
            guardados += 1

        if negativos > 0:
            ToastManager.show_warning(f"Guardados {guardados} registros. ⚠️ {negativos} día(s) con saldo negativo.", self)
        else:
            ToastManager.show_success(f"¡{guardados} registros de vales guardados correctamente!", self)
