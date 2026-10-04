from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QSpinBox, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt
from typing import Optional, List
from models.ticket import TicketDiario
from services.ticket_service import TicketService
from services.venta_service import VentaService

class CalendarioView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ticket_service = TicketService()
        self.venta_service = VentaService()
        self.current_anio = 2026
        self.current_mes = 9
        self.diarios: List[TicketDiario] = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header Bar
        header_box = QHBoxLayout()
        self.lbl_title = QLabel("Calendario Policial - Resumen Diario")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1F4E78;")
        header_box.addWidget(self.lbl_title)
        header_box.addStretch()

        self.btn_guardar_todo = QPushButton("💾 Guardar Todo")
        self.btn_guardar_todo.setProperty("class", "PrimaryBtn")
        self.btn_guardar_todo.clicked.connect(self._on_guardar_todo)
        header_box.addWidget(self.btn_guardar_todo)

        layout.addLayout(header_box)

        # Info Banner
        info_banner = QLabel("ℹ️ <b>Regla:</b> TOTAL = PARA UNIDAD + LOCAL (Los vales se controlan por separado y NO se suman al total).")
        info_banner.setStyleSheet("background-color: #E8F4F8; color: #1F4E78; padding: 8px; border-radius: 4px; border: 1px solid #BEE3F8;")
        layout.addWidget(info_banner)

        # Table
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

        layout.addWidget(self.table)

        # Totals Bar
        self.lbl_totales = QLabel("Totales del mes: Calculando...")
        self.lbl_totales.setStyleSheet("font-size: 13px; font-weight: bold; color: #1F4E78; padding: 6px;")
        layout.addWidget(self.lbl_totales)

    def set_periodo(self, anio: int, mes: int):
        self.current_anio = anio
        self.current_mes = mes
        self.lbl_title.setText(f"Calendario Policial - {mes:02d}/{anio}")
        self.cargar_datos()

    def cargar_datos(self):
        self.diarios = self.ticket_service.get_calendario_mes(self.current_anio, self.current_mes)
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
            sb_unidad.valueChanged.connect(lambda val, row=r: self._on_value_changed(row))
            self.table.setCellWidget(r, 2, sb_unidad)

            # 3. Local (SpinBox)
            sb_local = QSpinBox()
            sb_local.setRange(0, 9999)
            sb_local.setValue(td.local)
            sb_local.valueChanged.connect(lambda val, row=r: self._on_value_changed(row))
            self.table.setCellWidget(r, 3, sb_local)

            # 4. Total (Calculated & locked)
            tot_item = QTableWidgetItem(str(td.total_policias))
            tot_item.setTextAlignment(Qt.AlignCenter)
            tot_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            tot_item.setBackground(Qt.lightGray if td.total_policias == 0 else Qt.white)
            self.table.setItem(r, 4, tot_item)

            # 5. Vales policiales (SpinBox)
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

        self._recalcular_totales_ui()

    def _on_value_changed(self, row: int):
        widgets = self.spin_widgets.get(row)
        if widgets:
            unidad = widgets["unidad"].value()
            local = widgets["local"].value()
            total = unidad + local
            tot_item = self.table.item(row, 4)
            if tot_item:
                tot_item.setText(str(total))
        self._recalcular_totales_ui()

    def _recalcular_totales_ui(self):
        tot_u = 0
        tot_l = 0
        tot_p = 0
        tot_v = 0
        for r, w in self.spin_widgets.items():
            u = w["unidad"].value()
            l = w["local"].value()
            v = w["vales"].value()
            tot_u += u
            tot_l += l
            tot_p += (u + l)
            tot_v += v

        self.lbl_totales.setText(
            f"Totales del mes: Para Unidad = {tot_u} | Local = {tot_l} | Total Policías = {tot_p} | Vales Policiales = {tot_v}"
        )

    def _on_guardar_todo(self):
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
                    observacion=obs
                )
                # Auto-sync with ventas diarias
                self.venta_service.sincronizar_desde_calendario(td.fecha)
                guardados += 1

        QMessageBox.information(self, "Guardado", f"Se guardaron correctamente los {guardados} días del mes.")
