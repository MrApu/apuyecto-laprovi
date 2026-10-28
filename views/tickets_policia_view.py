from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QSpinBox, QTabWidget, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from typing import Optional, List, Dict, Any
from services.ticket_service import TicketService
from services.mes_service import MesService
from reports.excel_exporter import ExcelExporter
from views.components.toast import ToastManager
from views.dialogs.asignar_tickets_policia_dialog import AsignarTicketsPoliciaDialog

class TicketsPoliciaView(QWidget):
    """
    Control de Tickets por Policía con dos modos sincronizados:
    1. Modo Matriz: Visualización y edición casilla por casilla (días 1 al 31).
    2. Modo Rápido: Asignación directa de la cantidad de tickets por policía (sin marcar día por día).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ticket_service = TicketService()
        self.mes_service = MesService()
        self.current_anio = 2026
        self.current_mes = 9
        self.current_mes_id: Optional[int] = None
        self.num_dias = 30
        self.policias_data: List[dict] = []
        self.matriz: Dict[int, Dict[int, int]] = {}
        self.filter_text = ""
        self.filter_area = "TODAS"
        self.spinboxes_rapidos: Dict[int, QSpinBox] = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header principal
        header_box = QHBoxLayout()
        self.lbl_title = QLabel("Control de Tickets por Policía")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        header_box.addWidget(self.lbl_title)
        header_box.addStretch()

        self.btn_exportar = QPushButton("📥 Exportar Matriz a Excel")
        self.btn_exportar.setCursor(Qt.PointingHandCursor)
        self.btn_exportar.setStyleSheet("""
            background-color: #18181B;
            color: #FFFFFF;
            border: 1px solid #3F3F46;
            border-radius: 6px;
            padding: 6px 14px;
            font-weight: 700;
        """)
        self.btn_exportar.clicked.connect(self._on_exportar_excel)
        header_box.addWidget(self.btn_exportar)

        layout.addLayout(header_box)

        # Filter bar
        filter_box = QHBoxLayout()
        self.txt_busqueda = QLineEdit()
        self.txt_busqueda.setPlaceholderText("🔍 Buscar policía por código, apellidos, nombres... (descarte en tiempo real)")
        self.txt_busqueda.setStyleSheet("""
            QLineEdit {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #3F3F46;
                border-radius: 6px;
                padding: 7px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #DC2626;
            }
        """)
        self.txt_busqueda.textChanged.connect(self._on_busqueda_changed)
        filter_box.addWidget(self.txt_busqueda, 3)

        self.cmb_area = QComboBox()
        self.cmb_area.addItem("TODAS LAS ÁREAS", "TODAS")
        self.cmb_area.setStyleSheet("""
            background-color: #18181B;
            color: #FFFFFF;
            border: 1px solid #3F3F46;
            border-radius: 6px;
            padding: 6px 10px;
        """)
        self.cmb_area.currentIndexChanged.connect(self._on_area_changed)
        filter_box.addWidget(self.cmb_area, 1)

        layout.addLayout(filter_box)

        # Tabs de los 2 Modos
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

        # Tab 1: Modo Matriz Detallada
        tab_matriz = self._build_tab_matriz()
        self.tabs.addTab(tab_matriz, "📊 Matriz Detallada (Casilla por Casilla)")

        # Tab 2: Modo Asignación Rápida
        tab_rapido = self._build_tab_rapido()
        self.tabs.addTab(tab_rapido, "⚡ Modo Rápido (Cantidad Directa de Tickets)")

        layout.addWidget(self.tabs)

        # Status footer
        self.lbl_footer = QLabel("Haga clic en una celda de día para marcar (X) o use el botón '⚡ Asignar' para ingresar la cantidad directa.")
        self.lbl_footer.setStyleSheet("color: #94A3B8; font-size: 12px; font-style: italic;")
        layout.addWidget(self.lbl_footer)

    def _build_tab_matriz(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(6, 6, 6, 6)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellClicked.connect(self._on_cell_clicked)
        l.addWidget(self.table)
        return w

    def _build_tab_rapido(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(8, 8, 8, 8)
        l.setSpacing(8)

        # Banner informativo
        info = QLabel("⚡ <b>Asignación Rápida:</b> Ingrese directamente la cantidad de tickets de cada policía. La matriz mensual colocará automáticamente las marcas 'X' en los días correspondientes.")
        info.setStyleSheet("background-color: #18181B; color: #E4E4E7; border-left: 4px solid #DC2626; padding: 8px 12px; border-radius: 4px;")
        l.addWidget(info)

        # Botón Guardar en Lote
        top_h = QHBoxLayout()
        top_h.addStretch()
        btn_lote = QPushButton("💾 Guardar Todas las Cantidades Modificadas")
        btn_lote.setCursor(Qt.PointingHandCursor)
        btn_lote.setStyleSheet("""
            background-color: #10B981;
            color: #FFFFFF;
            font-weight: 800;
            padding: 6px 14px;
            border-radius: 6px;
        """)
        btn_lote.clicked.connect(self._guardar_cantidades_lote)
        top_h.addWidget(btn_lote)
        l.addLayout(top_h)

        # Tabla modo rápido
        self.tbl_rapido = QTableWidget()
        self.tbl_rapido.setColumnCount(7)
        self.tbl_rapido.setHorizontalHeaderLabels([
            "Código", "Policía / Apellidos y Nombres", "Área", "Tickets Actuales",
            "Nueva Cantidad de Tickets", "Acción Rápida", "Estado"
        ])
        self.tbl_rapido.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl_rapido.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tbl_rapido.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl_rapido.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tbl_rapido.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tbl_rapido.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tbl_rapido.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.tbl_rapido.setAlternatingRowColors(True)
        self.tbl_rapido.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_rapido.setEditTriggers(QTableWidget.NoEditTriggers)
        l.addWidget(self.tbl_rapido)

        return w

    def set_periodo(self, anio: int, mes: int):
        self.current_anio = anio
        self.current_mes = mes
        m = self.mes_service.get_by_anio_mes(anio, mes)
        if not m:
            ok, msg, mes_id = self.mes_service.crear_mes(anio, mes)
            self.current_mes_id = mes_id
        else:
            self.current_mes_id = m.id

        self.lbl_title.setText(f"Control de Tickets por Policía - {mes:02d}/{anio}")
        self._actualizar_combo_areas()
        self.cargar_datos()

    def _actualizar_combo_areas(self):
        if not self.current_mes_id:
            return
        policias = self.mes_service.repo.get_policias_en_mes(self.current_mes_id)
        areas = sorted(list(set(p["area_historica"] for p in policias if p.get("area_historica"))))
        self.cmb_area.blockSignals(True)
        self.cmb_area.clear()
        self.cmb_area.addItem("TODAS LAS ÁREAS", "TODAS")
        for a in areas:
            self.cmb_area.addItem(a, a)
        self.cmb_area.blockSignals(False)

    def _on_busqueda_changed(self, text: str):
        self.filter_text = text.strip().upper()
        self._filtrar_y_renderizar_tabla()

    def _on_area_changed(self):
        self.filter_area = self.cmb_area.currentData() or "TODAS"
        self._filtrar_y_renderizar_tabla()

    def cargar_datos(self):
        if not self.current_mes_id:
            return

        policias, num_dias, matriz = self.ticket_service.get_matriz_tickets_mes(self.current_mes_id)
        self.policias_data = policias
        self.num_dias = num_dias
        self.matriz = matriz
        self._filtrar_y_renderizar_tabla()

    def _filtrar_y_renderizar_tabla(self):
        filtered = []
        for p in self.policias_data:
            if self.filter_area != "TODAS" and p.get("area_historica", "").upper() != self.filter_area.upper():
                continue
            if self.filter_text:
                full_text = f"{p['codigo']} {p['apellidos']} {p['nombres']} {p.get('sa_pnp') or ''}".upper()
                if self.filter_text not in full_text:
                    continue
            filtered.append(p)

        self.visible_policias = filtered

        # 1. RENDERIZAR TABLA MATRIZ
        # Columnas: Código, Apellidos, Nombres, SA-PNP, Área, [⚡ Asignar] + 1..num_dias + TOTAL
        num_fixed_cols = 6
        total_cols = num_fixed_cols + self.num_dias + 1
        self.table.setColumnCount(total_cols)

        headers = ["Código", "Apellidos", "Nombres", "SA-PNP", "Área", "⚡ Asignar"] + [str(d) for d in range(1, self.num_dias + 1)] + ["TOTAL"]
        self.table.setHorizontalHeaderLabels(headers)

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 75)

        for d in range(1, self.num_dias + 1):
            self.table.setColumnWidth(num_fixed_cols + d - 1, 30)

        self.table.horizontalHeader().setSectionResizeMode(total_cols - 1, QHeaderView.ResizeToContents)

        self.table.setRowCount(len(filtered))

        for r, p in enumerate(filtered):
            p_id = p["policia_id"]
            dias_map = self.matriz.get(p_id, {})

            self.table.setItem(r, 0, QTableWidgetItem(p["codigo"]))
            self.table.setItem(r, 1, QTableWidgetItem(p["apellidos"]))
            self.table.setItem(r, 2, QTableWidgetItem(p["nombres"]))
            self.table.setItem(r, 3, QTableWidgetItem(p.get("sa_pnp") or "-"))
            self.table.setItem(r, 4, QTableWidgetItem(p.get("area_historica") or "-"))

            # Botón ⚡ Asignar Rápido directo en la matriz
            btn_quick = QPushButton("⚡")
            btn_quick.setCursor(Qt.PointingHandCursor)
            btn_quick.setToolTip("Asignar cantidad de tickets directa sin marcar casilla por casilla")
            btn_quick.setStyleSheet("""
                background-color: #18181B;
                color: #38BDF8;
                border: 1px solid #3F3F46;
                border-radius: 4px;
                font-weight: bold;
                padding: 2px;
            """)
            btn_quick.clicked.connect(lambda _, pol=p: self._abrir_modal_asignacion(pol))
            self.table.setCellWidget(r, 5, btn_quick)

            total_marcado = 0
            for d in range(1, self.num_dias + 1):
                col_idx = num_fixed_cols + d - 1
                val = dias_map.get(d, 0)
                item = QTableWidgetItem("X" if val == 1 else "")
                item.setTextAlignment(Qt.AlignCenter)
                if val == 1:
                    item.setBackground(Qt.green)
                    item.setForeground(Qt.black)
                    total_marcado += 1
                self.table.setItem(r, col_idx, item)

            tot_item = QTableWidgetItem(str(total_marcado))
            tot_item.setTextAlignment(Qt.AlignCenter)
            tot_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            tot_item.setBackground(Qt.lightGray)
            self.table.setItem(r, total_cols - 1, tot_item)

        # 2. RENDERIZAR TABLA MODO RÁPIDO
        self.spinboxes_rapidos = {}
        self.tbl_rapido.setRowCount(len(filtered))

        for r, p in enumerate(filtered):
            p_id = p["policia_id"]
            dias_map = self.matriz.get(p_id, {})
            tot_actual = sum(1 for d in range(1, self.num_dias + 1) if dias_map.get(d) == 1)

            self.tbl_rapido.setItem(r, 0, QTableWidgetItem(p["codigo"]))
            
            it_nom = QTableWidgetItem(f"{p['apellidos']}, {p['nombres']}")
            it_nom.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.tbl_rapido.setItem(r, 1, it_nom)

            self.tbl_rapido.setItem(r, 2, QTableWidgetItem(p.get("area_historica") or "-"))

            it_act = QTableWidgetItem(str(tot_actual))
            it_act.setTextAlignment(Qt.AlignCenter)
            self.tbl_rapido.setItem(r, 3, it_act)

            # SpinBox de nueva cantidad directa
            spn = QSpinBox()
            spn.setRange(0, self.num_dias)
            spn.setValue(tot_actual)
            spn.setAlignment(Qt.AlignCenter)
            spn.setStyleSheet("""
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #3F3F46;
                border-radius: 4px;
                padding: 4px;
                font-weight: bold;
            """)
            self.spinboxes_rapidos[p_id] = spn
            self.tbl_rapido.setCellWidget(r, 4, spn)

            # Botón Aplicar individual
            btn_apl = QPushButton("💾 Aplicar")
            btn_apl.setCursor(Qt.PointingHandCursor)
            btn_apl.setStyleSheet("""
                background-color: #DC2626;
                color: #FFFFFF;
                border-radius: 4px;
                padding: 4px 10px;
                font-weight: bold;
                font-size: 11px;
            """)
            btn_apl.clicked.connect(lambda _, pol_id=p_id: self._aplicar_cantidad_policia(pol_id))
            self.tbl_rapido.setCellWidget(r, 5, btn_apl)

            # Estado
            it_est = QTableWidgetItem(f"{tot_actual} / {self.num_dias}")
            it_est.setTextAlignment(Qt.AlignCenter)
            self.tbl_rapido.setItem(r, 6, it_est)

        self.lbl_footer.setText(f"Policías mostrados: {len(filtered)} de {len(self.policias_data)} | Días del mes: {self.num_dias}")

    def _abrir_modal_asignacion(self, p: dict):
        p_id = p["policia_id"]
        dias_map = self.matriz.get(p_id, {})
        tot_actual = sum(1 for d in range(1, self.num_dias + 1) if dias_map.get(d) == 1)

        dlg = AsignarTicketsPoliciaDialog(
            policia_nombre=f"{p['apellidos']}, {p['nombres']}",
            codigo=p["codigo"],
            tickets_actuales=tot_actual,
            num_dias_mes=self.num_dias,
            parent=self
        )
        if dlg.exec():
            nueva_cant = dlg.get_cantidad()
            ok, msg = self.ticket_service.asignar_cantidad_tickets_policia(
                mes_id=self.current_mes_id,
                policia_id=p_id,
                cantidad=nueva_cant
            )
            if ok:
                ToastManager.show_success(msg, self)
                self.cargar_datos()
            else:
                ToastManager.show_warning(msg, self)

    def _aplicar_cantidad_policia(self, policia_id: int):
        spn = self.spinboxes_rapidos.get(policia_id)
        if not spn:
            return
        cant = spn.value()
        ok, msg = self.ticket_service.asignar_cantidad_tickets_policia(
            mes_id=self.current_mes_id,
            policia_id=policia_id,
            cantidad=cant
        )
        if ok:
            ToastManager.show_success(msg, self)
            self.cargar_datos()
        else:
            ToastManager.show_warning(msg, self)

    def _guardar_cantidades_lote(self):
        actualizados = 0
        for p_id, spn in self.spinboxes_rapidos.items():
            cant = spn.value()
            dias_map = self.matriz.get(p_id, {})
            tot_actual = sum(1 for d in range(1, self.num_dias + 1) if dias_map.get(d) == 1)
            if cant != tot_actual:
                self.ticket_service.asignar_cantidad_tickets_policia(
                    mes_id=self.current_mes_id,
                    policia_id=p_id,
                    cantidad=cant
                )
                actualizados += 1

        if actualizados > 0:
            ToastManager.show_success(f"¡Se actualizaron las cantidades de {actualizados} policía(s) en la matriz!", self)
            self.cargar_datos()
        else:
            ToastManager.show_info("No hubo cambios en las cantidades.", self)

    def _on_cell_clicked(self, row: int, col: int):
        num_fixed = 6
        if row < 0 or row >= len(self.visible_policias):
            return
        if col < num_fixed or col >= (num_fixed + self.num_dias):
            return

        dia = col - num_fixed + 1
        p = self.visible_policias[row]
        p_id = p["policia_id"]

        if p_id not in self.matriz:
            self.matriz[p_id] = {}

        current_val = self.matriz[p_id].get(dia, 0)
        new_val = 0 if current_val == 1 else 1
        self.matriz[p_id][dia] = new_val

        # Update DB directly
        self.ticket_service.toggle_ticket(self.current_mes_id, p_id, dia, new_val)

        # Update Table cell
        item = self.table.item(row, col)
        if item:
            item.setText("X" if new_val == 1 else "")
            if new_val == 1:
                item.setBackground(Qt.green)
                item.setForeground(Qt.black)
            else:
                item.setBackground(Qt.white)

        # Update Total Column
        tot_col = num_fixed + self.num_dias
        tot = sum(1 for d in range(1, self.num_dias + 1) if self.matriz[p_id].get(d) == 1)
        tot_item = self.table.item(row, tot_col)
        if tot_item:
            tot_item.setText(str(tot))

        # Sincronizar también con el SpinBox del modo rápido
        if p_id in self.spinboxes_rapidos:
            self.spinboxes_rapidos[p_id].blockSignals(True)
            self.spinboxes_rapidos[p_id].setValue(tot)
            self.spinboxes_rapidos[p_id].blockSignals(False)

    def _on_exportar_excel(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Exportar Matriz Excel", f"Tickets_{self.current_mes:02d}_{self.current_anio}.xlsx", "Excel Files (*.xlsx)")
        if filepath:
            exporter = ExcelExporter()
            exporter.exportar_reporte_mensual(self.current_anio, self.current_mes, filepath)
            QMessageBox.information(self, "Exportación Exitosa", f"Matriz exportada a {filepath}")
