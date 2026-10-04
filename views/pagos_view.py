from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QSpinBox, QDoubleSpinBox, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt
from typing import Optional, List
from models.pago import PagoTicket
from services.pago_service import PagoService
from services.ticket_service import TicketService
from services.mes_service import MesService

class PagosView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pago_service = PagoService()
        self.ticket_service = TicketService()
        self.mes_service = MesService()
        self.current_anio = 2026
        self.current_mes = 9
        self.precio_menu = 15.0
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header_box = QHBoxLayout()
        self.lbl_title = QLabel("Control de Pagos y Deudas de Tickets")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1F4E78;")
        header_box.addWidget(self.lbl_title)
        header_box.addStretch()

        self.btn_guardar_todo = QPushButton("💾 Guardar Pagos")
        self.btn_guardar_todo.setProperty("class", "PrimaryBtn")
        self.btn_guardar_todo.clicked.connect(self._on_guardar_todo)
        header_box.addWidget(self.btn_guardar_todo)

        layout.addLayout(header_box)

        # Banner
        info_banner = QLabel("ℹ️ <b>Regla:</b> TICKETS PAGADOS + TICKETS DEBIDOS = TOTAL TICKETS. Los estados son PAGADO, PENDIENTE o PARCIAL.")
        info_banner.setStyleSheet("background-color: #E8F8F5; color: #117A65; padding: 8px; border-radius: 4px; border: 1px solid #A3E4D7;")
        layout.addWidget(info_banner)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Fecha", "Total Tickets", "Pagados (*)", "Debidos (*)", "Estado", "Monto Pagado (S/)", "Monto Pendiente (S/)", "Observaciones"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Resumen Bar
        self.lbl_resumen = QLabel("Resumen de pagos: Calculando...")
        self.lbl_resumen.setStyleSheet("font-size: 13px; font-weight: bold; color: #1F4E78; padding: 6px;")
        layout.addWidget(self.lbl_resumen)

    def set_periodo(self, anio: int, mes: int):
        self.current_anio = anio
        self.current_mes = mes
        m = self.mes_service.get_by_anio_mes(anio, mes)
        self.precio_menu = m.precio_menu_policial if m else 15.0
        self.lbl_title.setText(f"Control de Pagos y Deudas - {mes:02d}/{anio}")
        self.cargar_datos()

    def cargar_datos(self):
        diarios = self.ticket_service.get_calendario_mes(self.current_anio, self.current_mes)
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

            # Total tickets (auto from calendar)
            tot_item = QTableWidgetItem(str(tot_t))
            tot_item.setTextAlignment(Qt.AlignCenter)
            tot_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(r, 1, tot_item)

            # Pagados SpinBox
            sb_pag = QSpinBox()
            sb_pag.setRange(0, 9999)
            sb_pag.setValue(p.tickets_pagados)
            sb_pag.valueChanged.connect(lambda _, row=r: self._on_value_changed(row))
            self.table.setCellWidget(r, 2, sb_pag)

            # Debidos SpinBox
            sb_deb = QSpinBox()
            sb_deb.setRange(0, 9999)
            sb_deb.setValue(p.tickets_debidos)
            sb_deb.valueChanged.connect(lambda _, row=r: self._on_value_changed(row))
            self.table.setCellWidget(r, 3, sb_deb)

            # Estado Item
            est_item = QTableWidgetItem(p.estado)
            est_item.setTextAlignment(Qt.AlignCenter)
            est_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self._apply_estado_style(est_item, p.estado)
            self.table.setItem(r, 4, est_item)

            # Monto Pagado DoubleSpinBox
            dsp_pag = QDoubleSpinBox()
            dsp_pag.setRange(0.0, 999999.0)
            dsp_pag.setDecimals(2)
            dsp_pag.setPrefix("S/ ")
            dsp_pag.setValue(p.monto_pagado)
            self.table.setCellWidget(r, 5, dsp_pag)

            # Monto Pendiente DoubleSpinBox
            dsp_pend = QDoubleSpinBox()
            dsp_pend.setRange(0.0, 999999.0)
            dsp_pend.setDecimals(2)
            dsp_pend.setPrefix("S/ ")
            dsp_pend.setValue(p.monto_pendiente)
            self.table.setCellWidget(r, 6, dsp_pend)

            txt_obs = QLineEdit()
            if p.observacion:
                txt_obs.setText(p.observacion)
            self.table.setCellWidget(r, 7, txt_obs)

            self.widgets[r] = {
                "fecha": fecha,
                "total_tickets": tot_t,
                "pagados": sb_pag,
                "debidos": sb_deb,
                "monto_pagado": dsp_pag,
                "monto_pendiente": dsp_pend,
                "obs": txt_obs
            }

        self._recalcular_resumen()

    def _on_value_changed(self, row: int):
        w = self.widgets.get(row)
        if w:
            tot = w["total_tickets"]
            pag = w["pagados"].value()
            deb = w["debidos"].value()

            # Auto calculate status
            if tot <= 0:
                estado = "PAGADO"
            elif pag >= tot:
                estado = "PAGADO"
            elif pag == 0:
                estado = "PENDIENTE"
            else:
                estado = "PARCIAL"

            est_item = self.table.item(row, 4)
            if est_item:
                est_item.setText(estado)
                self._apply_estado_style(est_item, estado)

            # Auto compute amounts if unmodified
            w["monto_pagado"].setValue(round(pag * self.precio_menu, 2))
            w["monto_pendiente"].setValue(round(deb * self.precio_menu, 2))

        self._recalcular_resumen()

    def _apply_estado_style(self, item: QTableWidgetItem, estado: str):
        if estado == "PAGADO":
            item.setForeground(Qt.darkGreen)
            item.setBackground(Qt.white)
        elif estado == "PENDIENTE":
            item.setForeground(Qt.red)
            item.setBackground(Qt.white)
        elif estado == "PARCIAL":
            item.setForeground(Qt.darkYellow)
            item.setBackground(Qt.white)

    def _recalcular_resumen(self):
        tot_pag = 0
        tot_deb = 0
        tot_monto_pag = 0.0
        tot_monto_pend = 0.0

        for r, w in self.widgets.items():
            pag = w["pagados"].value()
            deb = w["debidos"].value()
            tot_pag += pag
            tot_deb += deb
            tot_monto_pag += w["monto_pagado"].value()
            tot_monto_pend += w["monto_pendiente"].value()

        self.lbl_resumen.setText(
            f"Resumen del mes: Pagados = {tot_pag} | Debidos = {tot_deb} | Monto Cobrado = S/ {tot_monto_pag:,.2f} | Monto Pendiente = S/ {tot_monto_pend:,.2f}"
        )

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

        msg = f"Se guardaron {guardados} registros de pagos."
        if descuadrados > 0:
            msg += f"\n⚠️ Advertencia: {descuadrados} fecha(s) no cuadran (Pagados + Debidos != Total)."
        QMessageBox.information(self, "Pagos Guardados", msg)
