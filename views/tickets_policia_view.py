from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QCheckBox
)
from PySide6.QtCore import Qt
from typing import Optional, List, Dict
from services.ticket_service import TicketService
from services.mes_service import MesService
from reports.excel_exporter import ExcelExporter

class TicketsPoliciaView(QWidget):
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
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header
        header_box = QHBoxLayout()
        self.lbl_title = QLabel("Control de Tickets por Policía")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1F4E78;")
        header_box.addWidget(self.lbl_title)
        header_box.addStretch()

        self.btn_exportar = QPushButton("📥 Exportar Matriz a Excel")
        self.btn_exportar.clicked.connect(self._on_exportar_excel)
        header_box.addWidget(self.btn_exportar)

        layout.addLayout(header_box)

        # Filter bar
        filter_box = QHBoxLayout()
        self.txt_busqueda = QLineEdit()
        self.txt_busqueda.setPlaceholderText("🔍 Buscar policía por código, apellidos, nombres...")
        self.txt_busqueda.textChanged.connect(self._on_busqueda_changed)
        filter_box.addWidget(self.txt_busqueda, 3)

        self.cmb_area = QComboBox()
        self.cmb_area.addItem("TODAS LAS ÁREAS", "TODAS")
        self.cmb_area.currentIndexChanged.connect(self._on_area_changed)
        filter_box.addWidget(self.cmb_area, 1)

        layout.addLayout(filter_box)

        # Matrix Table
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.cellClicked.connect(self._on_cell_clicked)
        layout.addWidget(self.table)

        # Status footer
        self.lbl_footer = QLabel("Haga clic en una celda de día para marcar (X) o desmarcar el ticket.")
        self.lbl_footer.setStyleSheet("color: #595959; font-size: 12px; font-style: italic;")
        layout.addWidget(self.lbl_footer)

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

        # Setup columns: Código, Apellidos, Nombres, SA-PNP, Área + 1..num_dias + TOTAL
        num_fixed_cols = 5
        total_cols = num_fixed_cols + self.num_dias + 1
        self.table.setColumnCount(total_cols)

        headers = ["Código", "Apellidos", "Nombres", "SA-PNP", "Área"] + [str(d) for d in range(1, self.num_dias + 1)] + ["TOTAL"]
        self.table.setHorizontalHeaderLabels(headers)

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)

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

            # Locked calculated TOTAL
            tot_item = QTableWidgetItem(str(total_marcado))
            tot_item.setTextAlignment(Qt.AlignCenter)
            tot_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            tot_item.setBackground(Qt.lightGray)
            self.table.setItem(r, total_cols - 1, tot_item)

        self.lbl_footer.setText(f"Policías mostrados: {len(filtered)} de {len(self.policias_data)} | Días del mes: {self.num_dias}")

    def _on_cell_clicked(self, row: int, col: int):
        num_fixed = 5
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

    def _on_exportar_excel(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Exportar Matriz Excel", f"Tickets_{self.current_mes:02d}_{self.current_anio}.xlsx", "Excel Files (*.xlsx)")
        if filepath:
            exporter = ExcelExporter()
            exporter.exportar_reporte_mensual(self.current_anio, self.current_mes, filepath)
            QMessageBox.information(self, "Exportación Exitosa", f"Matriz exportada a {filepath}")
