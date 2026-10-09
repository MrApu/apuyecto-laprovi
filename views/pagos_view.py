from typing import Optional, List, Dict, Any
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QSpinBox, QDoubleSpinBox, QLineEdit,
    QButtonGroup, QFrame, QProgressBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from models.pago import PagoTicket
from services.pago_service import PagoService
from services.ticket_service import TicketService
from services.mes_service import MesService
from models.local import LOCAL_RESTAURANTE, LOCAL_NAMES
from views.components.toast import ToastManager
from views.dialogs.detalle_dia_dialog import DetalleDiaDialog

class PagosView(QWidget):
    """
    Vista de Control de Cobranzas y Deudas con:
    - Filtros rápidos por chips (Todos, Con Deuda, Parciales, Pagados).
    - Barra visual de progreso de cobranza (% Cobrado).
    - Drill-down al hacer doble clic para ver la bitácora del día.
    - Notificaciones Toast modernas al guardar.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pago_service = PagoService()
        self.ticket_service = TicketService()
        self.mes_service = MesService()
        self.current_anio = 2026
        self.current_mes = 9
        self.current_local = LOCAL_RESTAURANTE
        self.precio_menu = 15.0
        self.active_chip = "TODOS"
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
        self.precio_menu = m.precio_menu_policial if m else 15.0
        self.lbl_title.setText(f"💰 CONTROL DE COBRANZAS Y DEUDAS — {mes:02d}/{anio}")
        self.cargar_datos()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header_box = QHBoxLayout()
        self.lbl_title = QLabel(f"💰 CONTROL DE COBRANZAS Y DEUDAS — {self.current_mes:02d}/{self.current_anio}")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #F8FAFC;")
        header_box.addWidget(self.lbl_title)

        self.lbl_local_badge = QLabel(f"📍 Sede: {LOCAL_NAMES.get(self.current_local, 'RESTAURANTE')}")
        self.lbl_local_badge.setStyleSheet("""
            background: #1E293B;
            color: #38BDF8;
            padding: 4px 10px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 11px;
            border: 1px solid #334155;
        """)
        header_box.addWidget(self.lbl_local_badge)

        header_box.addStretch()

        self.btn_guardar_todo = QPushButton("💾 Guardar Pagos")
        self.btn_guardar_todo.setProperty("class", "SuccessBtn")
        self.btn_guardar_todo.clicked.connect(self._on_guardar_todo)
        header_box.addWidget(self.btn_guardar_todo)

        layout.addLayout(header_box)

        # Quick Filter Chips Row (Item 3)
        chip_box = QHBoxLayout()
        chip_box.setSpacing(6)
        lbl_chip_title = QLabel("⚡ Filtros Rápidos:")
        lbl_chip_title.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 800;")
        chip_box.addWidget(lbl_chip_title)

        self.chip_group = QButtonGroup(self)
        self.chip_group.setExclusive(True)

        chips = [
            ("🔘 Todos los Días", "TODOS"),
            ("🔴 Con Deuda Pendiente", "DEUDA"),
            ("🟡 Pago Parcial", "PARCIAL"),
            ("🟢 100% Cobrados", "PAGADO")
        ]

        for idx, (label, key) in enumerate(chips):
            btn_chip = QPushButton(label)
            btn_chip.setCheckable(True)
            btn_chip.setCursor(Qt.PointingHandCursor)
            if key == "TODOS":
                btn_chip.setChecked(True)
            btn_chip.setStyleSheet("""
                QPushButton {
                    background-color: #111827;
                    color: #94A3B8;
                    border: 1px solid #1F2937;
                    border-radius: 14px;
                    padding: 4px 12px;
                    font-size: 11px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #1E293B;
                    color: #F8FAFC;
                    border-color: #38BDF8;
                }
                QPushButton:checked {
                    background-color: #1E1B4B;
                    color: #A5B4FC;
                    border: 1px solid #6366F1;
                }
            """)
            btn_chip.clicked.connect(lambda _, k=key: self._on_chip_clicked(k))
            self.chip_group.addButton(btn_chip, idx)
            chip_box.addWidget(btn_chip)

        chip_box.addStretch()
        layout.addLayout(chip_box)

        # KPI Summary Row
        kpi_row = QHBoxLayout()
        self.lbl_kpi_total_tickets = QLabel("0")
        self.lbl_kpi_pagados = QLabel("0")
        self.lbl_kpi_debidos = QLabel("0")
        self.lbl_kpi_monto_pend = QLabel("S/ 0.00")

        kpi_row.addWidget(self._create_kpi_card("Total Tickets", self.lbl_kpi_total_tickets, "#818CF8"))
        kpi_row.addWidget(self._create_kpi_card("Tickets Cobrados", self.lbl_kpi_pagados, "#10B981"))
        kpi_row.addWidget(self._create_kpi_card("Tickets Debidos", self.lbl_kpi_debidos, "#F43F5E"))
        kpi_row.addWidget(self._create_kpi_card("Deuda Pendiente", self.lbl_kpi_monto_pend, "#F59E0B"))
        layout.addLayout(kpi_row)

        # Table
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
        self.table.doubleClicked.connect(self._on_table_double_clicked)
        layout.addWidget(self.table)

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

    def _on_chip_clicked(self, key: str):
        self.active_chip = key
        self._filtrar_filas()

    def _filtrar_filas(self):
        for r in range(self.table.rowCount()):
            w = self.widgets.get(r)
            if not w:
                continue
            estado = w["estado"]
            deb = w["debidos"].value()

            show = True
            if self.active_chip == "DEUDA":
                show = deb > 0 or estado in ("PENDIENTE", "PARCIAL")
            elif self.active_chip == "PARCIAL":
                show = estado == "PARCIAL"
            elif self.active_chip == "PAGADO":
                show = estado == "PAGADO" and deb == 0

            self.table.setRowHidden(r, not show)

    def cargar_datos(self):
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

            # Total tickets
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

            # Barra de Progreso Visual (Item 4)
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

            # Estado Item
            est_item = QTableWidgetItem(p.estado)
            est_item.setTextAlignment(Qt.AlignCenter)
            est_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self._apply_estado_style(est_item, p.estado)
            self.table.setItem(r, 5, est_item)

            # Monto Pagado DoubleSpinBox
            dsp_pag = QDoubleSpinBox()
            dsp_pag.setRange(0.0, 999999.0)
            dsp_pag.setDecimals(2)
            dsp_pag.setPrefix("S/ ")
            dsp_pag.setValue(p.monto_pagado)
            self.table.setCellWidget(r, 6, dsp_pag)

            # Monto Pendiente DoubleSpinBox
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

        self._recalcular_resumen()
        self._filtrar_filas()

    def _on_value_changed(self, row: int):
        w = self.widgets.get(row)
        if w:
            tot = w["total_tickets"]
            pag = w["pagados"].value()
            deb = w["debidos"].value()

            # Auto calculate status
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

            # Update progress bar
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

        self._recalcular_resumen()

    def _apply_estado_style(self, item: QTableWidgetItem, estado: str):
        if estado == "PAGADO":
            item.setForeground(QColor("#10B981"))
        elif estado == "PENDIENTE":
            item.setForeground(QColor("#F43F5E"))
        elif estado == "PARCIAL":
            item.setForeground(QColor("#F59E0B"))

    def _recalcular_resumen(self):
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
