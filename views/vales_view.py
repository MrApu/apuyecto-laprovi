from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QSpinBox, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt
from typing import Optional, List
from models.vale import Vale
from services.vale_service import ValeService
from services.ticket_service import TicketService

class ValesView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vale_service = ValeService()
        self.ticket_service = TicketService()
        self.current_anio = 2026
        self.current_mes = 9
        self.vales: List[Vale] = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header_box = QHBoxLayout()
        self.lbl_title = QLabel("Control de Vales Policiales")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1F4E78;")
        header_box.addWidget(self.lbl_title)
        header_box.addStretch()

        self.btn_guardar_todo = QPushButton("💾 Guardar Vales")
        self.btn_guardar_todo.setProperty("class", "PrimaryBtn")
        self.btn_guardar_todo.clicked.connect(self._on_guardar_todo)
        header_box.addWidget(self.btn_guardar_todo)

        layout.addLayout(header_box)

        # Rules Banner
        info_banner = QLabel("ℹ️ <b>Regla:</b> SALDO = VALES ENTREGADOS - VALES CANJEADOS. (Los vales entregados no son venta hasta que se canjean).")
        info_banner.setStyleSheet("background-color: #FFF3E0; color: #E65100; padding: 8px; border-radius: 4px; border: 1px solid #FFE0B2;")
        layout.addWidget(info_banner)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Fecha", "Vales Entregados", "Vales Canjeados", "Saldo Calculado", "Observaciones"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Resumen Bar
        self.lbl_resumen = QLabel("Resumen del mes: Entregados = 0 | Canjeados = 0 | Saldo = 0")
        self.lbl_resumen.setStyleSheet("font-size: 13px; font-weight: bold; color: #1F4E78; padding: 6px;")
        layout.addWidget(self.lbl_resumen)

    def set_periodo(self, anio: int, mes: int):
        self.current_anio = anio
        self.current_mes = mes
        self.lbl_title.setText(f"Control de Vales Policiales - {mes:02d}/{anio}")
        self.cargar_datos()

    def cargar_datos(self):
        # Ensure days exist
        diarios = self.ticket_service.get_calendario_mes(self.current_anio, self.current_mes)
        vales_existentes = {v.fecha: v for v in self.vale_service.get_by_mes(self.current_anio, self.current_mes)}

        self.table.setRowCount(len(diarios))
        self.widgets = {}

        for r, td in enumerate(diarios):
            fecha = td.fecha
            v = vales_existentes.get(fecha, Vale(fecha=fecha, vales_entregados=td.vales_policiales, vales_canjeados=0))

            self.table.setItem(r, 0, QTableWidgetItem(fecha))

            sb_ent = QSpinBox()
            sb_ent.setRange(0, 9999)
            sb_ent.setValue(v.vales_entregados)
            sb_ent.valueChanged.connect(lambda _, row=r: self._on_value_changed(row))
            self.table.setCellWidget(r, 1, sb_ent)

            sb_canj = QSpinBox()
            sb_canj.setRange(0, 9999)
            sb_canj.setValue(v.vales_canjeados)
            sb_canj.valueChanged.connect(lambda _, row=r: self._on_value_changed(row))
            self.table.setCellWidget(r, 2, sb_canj)

            saldo_item = QTableWidgetItem(str(v.saldo))
            saldo_item.setTextAlignment(Qt.AlignCenter)
            saldo_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            if v.saldo < 0:
                saldo_item.setForeground(Qt.red)
                saldo_item.setBackground(Qt.yellow)
            self.table.setItem(r, 3, saldo_item)

            txt_obs = QLineEdit()
            if v.observacion:
                txt_obs.setText(v.observacion)
            self.table.setCellWidget(r, 4, txt_obs)

            self.widgets[r] = {
                "fecha": fecha,
                "entregados": sb_ent,
                "canjeados": sb_canj,
                "obs": txt_obs
            }

        self._recalcular_resumen()

    def _on_value_changed(self, row: int):
        w = self.widgets.get(row)
        if w:
            ent = w["entregados"].value()
            canj = w["canjeados"].value()
            saldo = ent - canj
            saldo_item = self.table.item(row, 3)
            if saldo_item:
                saldo_item.setText(str(saldo))
                if saldo < 0:
                    saldo_item.setForeground(Qt.red)
                    saldo_item.setBackground(Qt.yellow)
                else:
                    saldo_item.setForeground(Qt.black)
                    saldo_item.setBackground(Qt.white)
        self._recalcular_resumen()

    def _recalcular_resumen(self):
        tot_ent = 0
        tot_canj = 0
        for r, w in self.widgets.items():
            tot_ent += w["entregados"].value()
            tot_canj += w["canjeados"].value()
        saldo_tot = tot_ent - tot_canj

        alerta = " ⚠️ [Alerta: Saldo Negativo]" if saldo_tot < 0 else ""
        self.lbl_resumen.setText(
            f"Resumen del mes: Vales Entregados = {tot_ent} | Vales Canjeados = {tot_canj} | Saldo = {saldo_tot}{alerta}"
        )

    def _on_guardar_todo(self):
        guardados = 0
        negativos = 0
        for r, w in self.widgets.items():
            fecha = w["fecha"]
            ent = w["entregados"].value()
            canj = w["canjeados"].value()
            obs = w["obs"].text().strip() or None

            ok, msg, v = self.vale_service.guardar_vale(fecha, ent, canj, obs)
            if v.saldo < 0:
                negativos += 1
            guardados += 1

        msg = f"Se guardaron correctamente los registros de vales de {guardados} días."
        if negativos > 0:
            msg += f"\n⚠️ Atención: {negativos} fecha(s) presentan saldo negativo."
        QMessageBox.information(self, "Vales Guardados", msg)
