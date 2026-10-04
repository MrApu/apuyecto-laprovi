from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QDoubleSpinBox, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from typing import Optional, List, Dict, Any

from models.venta import VentaDiaria
from models.local import LOCAL_RESTAURANTE, LOCAL_FAST_FOOD, LOCAL_CONSOLIDADO, LOCAL_NAMES
from services.venta_service import VentaService
from services.ticket_service import TicketService
from services.mes_service import MesService
from repositories.compra_repository import CompraRepository
from repositories.gasto_repository import GastoRepository
from repositories.pago_personal_repository import PagoPersonalRepository

class VentasView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.venta_service = VentaService()
        self.ticket_service = TicketService()
        self.mes_service = MesService()
        self.compra_repo = CompraRepository()
        self.gasto_repo = GastoRepository()
        self.personal_repo = PagoPersonalRepository()

        self.current_local = LOCAL_RESTAURANTE
        self.current_anio = 2026
        self.current_mes = 9
        self.precio_ticket = 12.0
        self.widgets: Dict[int, dict] = {}
        self._init_ui()

    def set_local(self, local_id: str):
        self.current_local = local_id
        self.lbl_local.setText(f"Local: {LOCAL_NAMES.get(local_id, local_id.upper())}")
        self.cargar_datos()

    def set_periodo(self, anio: int, mes: int):
        self.current_anio = anio
        self.current_mes = mes
        m = self.mes_service.get_by_anio_mes(anio, mes)
        self.precio_ticket = m.precio_ticket_policial if m else 12.0
        self.lbl_title.setText(f"📈 CONTROL DE VENTAS, EGRESOS Y SALDO DIARIO - {mes:02d}/{anio} (Ticket: S/ {self.precio_ticket:.2f})")
        self.cargar_datos()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header_box = QHBoxLayout()
        self.lbl_title = QLabel("📈 CONTROL DE VENTAS, EGRESOS Y SALDO DIARIO")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1F4E78;")
        header_box.addWidget(self.lbl_title)

        self.lbl_local = QLabel(f"Local: {LOCAL_NAMES.get(self.current_local, 'RESTAURANTE')}")
        self.lbl_local.setStyleSheet("background: #1e293b; color: #38bdf8; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
        header_box.addWidget(self.lbl_local)

        header_box.addStretch()

        self.btn_guardar_todo = QPushButton("💾 Guardar Ventas del Mes")
        self.btn_guardar_todo.setProperty("class", "PrimaryBtn")
        self.btn_guardar_todo.clicked.connect(self._on_guardar_todo)
        header_box.addWidget(self.btn_guardar_todo)

        layout.addLayout(header_box)

        # Info Banner
        info_banner = QLabel("ℹ️ <b>Regla Financiera:</b> Ingrese <b>Efectivo</b> y <b>Yape</b>. El sistema calcula automáticamente: <i>Venta Sin Tickets = Efectivo + Yape</i>, <i>Venta Tickets = Cantidad × S/ 12.00</i>, <i>Venta Total = Efectivo + Yape + Venta Tickets</i>, deduce los <b>Egresos (Compras + Gastos + Personal)</b> y calcula el <b>Saldo Neto del Día</b>.")
        info_banner.setStyleSheet("background-color: #EBF5FB; color: #1B4F72; padding: 8px 12px; border-radius: 4px; border: 1px solid #AED6F1;")
        info_banner.setWordWrap(True)
        layout.addWidget(info_banner)

        # Table
        self.table = QTableWidget()
        headers = [
            "Fecha", "Efectivo (*)", "Yape (*)", "Venta Sin Tickets",
            "Cant. Tickets", "Venta Tickets", "VENTA TOTAL",
            "Compras", "Gastos", "Personal", "TOTAL EGRESOS", "SALDO NETO", "Observaciones"
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        for c in range(len(headers) - 1):
            self.table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(len(headers) - 1, QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Resumen Bar
        self.lbl_resumen = QLabel("Totales del mes: Calculando...")
        self.lbl_resumen.setStyleSheet("background: #0f172a; color: #38bdf8; font-size: 13px; font-weight: bold; padding: 10px; border-radius: 4px;")
        layout.addWidget(self.lbl_resumen)

    def cargar_datos(self):
        diarios = self.ticket_service.get_calendario_mes(self.current_anio, self.current_mes, self.current_local)
        ventas_map = {v.fecha: v for v in self.venta_service.get_by_mes(self.current_anio, self.current_mes, self.current_local)}
        vales_map = {v.fecha: v for v in self.venta_service.vale_repo.get_by_mes(self.current_anio, self.current_mes, self.current_local)}
        pagos_map = {p.fecha: p for p in self.venta_service.pago_repo.get_by_mes(self.current_anio, self.current_mes, self.current_local)}

        # Aggregate daily egresos
        compras_list = self.compra_repo.get_by_mes(self.current_anio, self.current_mes, self.current_local)
        gastos_list = self.gasto_repo.get_by_mes(self.current_anio, self.current_mes, self.current_local)
        personal_list = self.personal_repo.get_by_mes(self.current_anio, self.current_mes, self.current_local)

        compras_map: Dict[str, float] = {}
        for c in compras_list:
            compras_map[c.fecha] = round(compras_map.get(c.fecha, 0.0) + (c.total or 0.0), 2)

        gastos_map: Dict[str, float] = {}
        for g in gastos_list:
            gastos_map[g.fecha] = round(gastos_map.get(g.fecha, 0.0) + (g.monto or 0.0), 2)

        personal_map: Dict[str, float] = {}
        for p in personal_list:
            personal_map[p.fecha] = round(personal_map.get(p.fecha, 0.0) + (p.monto or 0.0), 2)

        self.table.setRowCount(len(diarios))
        self.widgets = {}

        for r, td in enumerate(diarios):
            fecha = td.fecha
            v = ventas_map.get(fecha)
            vl = vales_map.get(fecha)
            pg = pagos_map.get(fecha)

            efectivo_val = v.efectivo if v else 0.0
            yape_val = v.yape if v else 0.0
            obs = v.observaciones if v else (td.observacion or "")

            cant_tickets = td.total_policias
            v_tickets = round(cant_tickets * self.precio_ticket, 2)
            v_sin_tickets = round(efectivo_val + yape_val, 2)
            v_total = round(v_sin_tickets + v_tickets, 2)

            compra_dia = compras_map.get(fecha, 0.0)
            gasto_dia = gastos_map.get(fecha, 0.0)
            personal_dia = personal_map.get(fecha, 0.0)
            total_egresos = round(compra_dia + gasto_dia + personal_dia, 2)
            saldo_neto = round(v_total - total_egresos, 2)

            # 0. Fecha
            self.table.setItem(r, 0, self._locked_item(fecha))

            # 1. Efectivo (Editable)
            dsp_ef = QDoubleSpinBox()
            dsp_ef.setRange(0.0, 999999.0)
            dsp_ef.setDecimals(2)
            dsp_ef.setPrefix("S/ ")
            dsp_ef.setValue(efectivo_val)
            dsp_ef.valueChanged.connect(lambda _, row=r: self._on_input_changed(row))
            self.table.setCellWidget(r, 1, dsp_ef)

            # 2. Yape (Editable)
            dsp_yp = QDoubleSpinBox()
            dsp_yp.setRange(0.0, 999999.0)
            dsp_yp.setDecimals(2)
            dsp_yp.setPrefix("S/ ")
            dsp_yp.setValue(yape_val)
            dsp_yp.valueChanged.connect(lambda _, row=r: self._on_input_changed(row))
            self.table.setCellWidget(r, 2, dsp_yp)

            # 3. Venta Sin Tickets (Calculated)
            self.table.setItem(r, 3, self._locked_item(f"S/ {v_sin_tickets:,.2f}"))

            # 4. Cant. Tickets (Auto from tickets_diarios)
            self.table.setItem(r, 4, self._locked_item(str(cant_tickets)))

            # 5. Venta Tickets (Calculated)
            self.table.setItem(r, 5, self._locked_item(f"S/ {v_tickets:,.2f}"))

            # 6. VENTA TOTAL (Calculated)
            item_vt = self._locked_item(f"S/ {v_total:,.2f}")
            item_vt.setFont(QFont("Segoe UI", 9, QFont.Bold))
            item_vt.setForeground(QColor("#10b981"))
            self.table.setItem(r, 6, item_vt)

            # 7. Compras
            self.table.setItem(r, 7, self._locked_item(f"S/ {compra_dia:,.2f}"))

            # 8. Gastos
            self.table.setItem(r, 8, self._locked_item(f"S/ {gasto_dia:,.2f}"))

            # 9. Personal
            self.table.setItem(r, 9, self._locked_item(f"S/ {personal_dia:,.2f}"))

            # 10. Total Egresos
            item_egr = self._locked_item(f"S/ {total_egresos:,.2f}")
            item_egr.setFont(QFont("Segoe UI", 9, QFont.Bold))
            item_egr.setForeground(QColor("#ef4444"))
            self.table.setItem(r, 10, item_egr)

            # 11. Saldo Neto
            item_saldo = self._locked_item(f"S/ {saldo_neto:,.2f}")
            item_saldo.setFont(QFont("Segoe UI", 9, QFont.Bold))
            if saldo_neto > 0:
                item_saldo.setForeground(QColor("#10b981"))
            elif saldo_neto < 0:
                item_saldo.setForeground(QColor("#ef4444"))
            else:
                item_saldo.setForeground(QColor("#94a3b8"))
            self.table.setItem(r, 11, item_saldo)

            # 12. Observaciones
            self.table.setItem(r, 12, QTableWidgetItem(obs))

            self.widgets[r] = {
                "fecha": fecha,
                "efectivo_spn": dsp_ef,
                "yape_spn": dsp_yp,
                "cant_tickets": cant_tickets,
                "v_tickets": v_tickets,
                "compra_dia": compra_dia,
                "gasto_dia": gasto_dia,
                "personal_dia": personal_dia,
                "total_egresos": total_egresos,
                "observaciones": obs,
                "para_unidad": td.para_unidad,
                "local": td.local,
                "vales_consumidos": vl.vales_consumidos if vl else 0,
                "tickets_pagados": pg.tickets_pagados if pg else 0,
                "tickets_debidos": pg.tickets_debidos if pg else 0
            }

        self._recalcular_resumen()

    def _locked_item(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        return item

    def _on_input_changed(self, row: int):
        w = self.widgets.get(row)
        if not w:
            return

        ef = w["efectivo_spn"].value()
        yp = w["yape_spn"].value()
        cant_t = w["cant_tickets"]
        v_tick = w["v_tickets"]

        v_sin_t = round(ef + yp, 2)
        v_tot = round(v_sin_t + v_tick, 2)
        egr = w["total_egresos"]
        saldo = round(v_tot - egr, 2)

        # Update cell 3 (Venta sin tickets)
        item_vst = self.table.item(row, 3)
        if item_vst:
            item_vst.setText(f"S/ {v_sin_t:,.2f}")

        # Update cell 6 (Venta total)
        item_vt = self.table.item(row, 6)
        if item_vt:
            item_vt.setText(f"S/ {v_tot:,.2f}")

        # Update cell 11 (Saldo neto)
        item_s = self.table.item(row, 11)
        if item_s:
            item_s.setText(f"S/ {saldo:,.2f}")
            if saldo > 0:
                item_s.setForeground(QColor("#10b981"))
            elif saldo < 0:
                item_s.setForeground(QColor("#ef4444"))
            else:
                item_s.setForeground(QColor("#94a3b8"))

        self._recalcular_resumen()

    def _recalcular_resumen(self):
        tot_ef = 0.0
        tot_yp = 0.0
        tot_sin_t = 0.0
        tot_tickets_cant = 0
        tot_tickets_monto = 0.0
        tot_ventas = 0.0
        tot_egresos = 0.0

        for r in range(self.table.rowCount()):
            w = self.widgets.get(r)
            if w:
                ef = w["efectivo_spn"].value()
                yp = w["yape_spn"].value()
                v_tick = w["v_tickets"]
                v_tot = ef + yp + v_tick
                egr = w["total_egresos"]

                tot_ef += ef
                tot_yp += yp
                tot_sin_t += (ef + yp)
                tot_tickets_cant += w["cant_tickets"]
                tot_tickets_monto += v_tick
                tot_ventas += v_tot
                tot_egresos += egr

        saldo_neto_mes = round(tot_ventas - tot_egresos, 2)
        rentabilidad = round((saldo_neto_mes / tot_ventas * 100.0), 2) if tot_ventas > 0 else 0.0

        color_saldo = "#10b981" if saldo_neto_mes >= 0 else "#ef4444"
        self.lbl_resumen.setText(
            f"📊 TOTALES DEL MES: "
            f"Efectivo: S/ {tot_ef:,.2f} | "
            f"Yape: S/ {tot_yp:,.2f} | "
            f"Venta Sin Tickets: S/ {tot_sin_t:,.2f} | "
            f"Tickets Policiales: {tot_tickets_cant} (S/ {tot_tickets_monto:,.2f}) | "
            f"VENTA TOTAL: S/ {tot_ventas:,.2f} | "
            f"TOTAL EGRESOS: S/ {tot_egresos:,.2f} | "
            f"SALDO NETO: <span style='color:{color_saldo};'>S/ {saldo_neto_mes:,.2f}</span> ({rentabilidad:.1f}% rentabilidad)"
        )

    def _on_guardar_todo(self):
        guardados = 0
        for r in range(self.table.rowCount()):
            w = self.widgets.get(r)
            if not w:
                continue

            fecha = w["fecha"]
            ef = w["efectivo_spn"].value()
            yp = w["yape_spn"].value()
            item_obs = self.table.item(r, 12)
            obs = item_obs.text().strip() if item_obs else ""

            cant_t = w["cant_tickets"]
            v_tickets = w["v_tickets"]
            v_sin_t = round(ef + yp, 2)
            v_total = round(v_sin_t + v_tickets, 2)

            vd = VentaDiaria(
                fecha=fecha,
                local_id=self.current_local if self.current_local != LOCAL_CONSOLIDADO else "restaurante",
                efectivo=ef,
                yape=yp,
                venta_sin_tickets=v_sin_t,
                cantidad_tickets=cant_t,
                precio_ticket_aplicado=self.precio_ticket,
                venta_tickets=v_tickets,
                venta_total=v_total,
                para_unidad=w["para_unidad"],
                local=w["local"],
                vales_consumidos=w["vales_consumidos"],
                tickets_pagados=w["tickets_pagados"],
                tickets_debidos=w["tickets_debidos"],
                observaciones=obs or None
            )
            self.venta_service.repo.save(vd)
            guardados += 1

        QMessageBox.information(self, "Ventas Guardadas", f"Se guardaron correctamente {guardados} registros diarios para {LOCAL_NAMES.get(self.current_local, self.current_local.upper())}.")
        self.cargar_datos()
