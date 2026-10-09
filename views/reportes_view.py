from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog,
    QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt
from typing import Optional
from exports.exporter import Exporter
from services.dashboard_service import DashboardService
from services.consistency_checker import ConsistencyChecker
from services.mes_service import MesService

class ReportesView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.exporter = Exporter()
        self.dashboard_service = DashboardService()
        self.consistency_checker = ConsistencyChecker()
        self.mes_service = MesService()
        self.current_anio = 2026
        self.current_mes = 9
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_box = QHBoxLayout()
        self.lbl_title = QLabel("Generador de Reportes y Exportación")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1F4E78;")
        header_box.addWidget(self.lbl_title)
        header_box.addStretch()

        self.btn_excel = QPushButton("📊 Exportar a Excel (.xlsx)")
        self.btn_excel.setProperty("class", "SuccessBtn")
        self.btn_excel.clicked.connect(self._on_export_excel)
        header_box.addWidget(self.btn_excel)

        self.btn_pdf = QPushButton("📄 Exportar a PDF (.pdf)")
        self.btn_pdf.setProperty("class", "PrimaryBtn")
        self.btn_pdf.clicked.connect(self._on_export_pdf)
        header_box.addWidget(self.btn_pdf)

        layout.addLayout(header_box)

        # Consistency Checker Box
        self.grp_consistencia = QGroupBox("Estado de Consistencia del Período")
        self.l_cons = QVBoxLayout(self.grp_consistencia)
        self.lbl_cons = QLabel("Comprobando consistencia...")
        self.l_cons.addWidget(self.lbl_cons)
        layout.addWidget(self.grp_consistencia)

        # Monthly Preview Table
        layout.addWidget(QLabel("<b>Vista Previa del Reporte Mensual:</b>"))
        self.table_preview = QTableWidget()
        self.table_preview.setColumnCount(3)
        self.table_preview.setHorizontalHeaderLabels(["Concepto", "Valor", "Detalle"])
        self.table_preview.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_preview.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_preview.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.table_preview)

    def set_local(self, local_id: str):
        self.current_local = local_id
        self.cargar_datos()

    def set_periodo(self, anio: int, mes: int):
        self.current_anio = anio
        self.current_mes = mes
        self.lbl_title.setText(f"Reportes y Exportación - {mes:02d}/{anio}")
        self.cargar_datos()

    def cargar_datos(self):
        local = getattr(self, "current_local", "restaurante")
        data = self.dashboard_service.get_dashboard_data(self.current_anio, self.current_mes, local)
        kpis = data.get("kpis", {})
        m = self.mes_service.get_by_anio_mes(self.current_anio, self.current_mes)
        precio_menu = m.precio_menu_policial if m else 15.0

        filas = [
            ("VENTA TOTAL", f"S/ {kpis.get('venta_total', 0.0):,.2f}", "Total ventas generales ingresadas"),
            ("MENÚS VENDIDOS", str(kpis.get("menus_vendidos", 0)), "Total menús vendidos del restaurante"),
            ("PARA UNIDAD", str(kpis.get("tickets_para_unidad", 0)), "Tickets enviados a la unidad"),
            ("LOCAL", str(kpis.get("tickets_local", 0)), "Tickets consumidos en local"),
            ("TOTAL POLICÍAS", str(kpis.get("total_tickets_policiales", 0)), "Para unidad + Local"),
            ("MENÚS SIN POLICÍAS", str(kpis.get("menus_sin_policias", 0)), "Menús vendidos - Policías"),
            ("VENTA POLICIAL CALCULADA", f"S/ {kpis.get('venta_policial_calculada', 0.0):,.2f}", f"Policías x S/ {precio_menu:.2f}"),
            ("VENTA SIN POLICÍAS CALCULADA", f"S/ {kpis.get('venta_sin_policias', 0.0):,.2f}", "Venta total - Venta policial"),
            ("VALES ENTREGADOS", str(kpis.get("vales_entregados", 0)), "Vales emitidos a efectivos"),
            ("VALES CANJEADOS", str(kpis.get("vales_canjeados", 0)), "Vales liquidados / canjeados"),
            ("SALDO VALES", str(kpis.get("saldo_vales", 0)), "Entregados - Canjeados"),
            ("TICKETS PAGADOS", str(kpis.get("tickets_pagados", 0)), "Tickets cancelados"),
            ("TICKETS DEBIDOS", str(kpis.get("tickets_debidos", 0)), "Tickets pendientes de pago"),
            ("MONTO COBRADO", f"S/ {data.get('kpis', {}).get('monto_pagado', 0.0):,.2f}", "Dinero efectivamente cobrado"),
            ("MONTO PENDIENTE DE COBRO", f"S/ {kpis.get('monto_pendiente', 0.0):,.2f}", "Deuda policial acumulada")
        ]

        self.table_preview.setRowCount(len(filas))
        for r, (c, v, d) in enumerate(filas):
            item_c = QTableWidgetItem(c)
            item_c.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            item_v = QTableWidgetItem(v)
            item_v.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            item_v.setTextAlignment(Qt.AlignCenter)
            item_d = QTableWidgetItem(d)
            item_d.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

            self.table_preview.setItem(r, 0, item_c)
            self.table_preview.setItem(r, 1, item_v)
            self.table_preview.setItem(r, 2, item_d)

        # Check consistency
        incons = self.consistency_checker.verificar_mes(self.current_anio, self.current_mes)
        if not incons:
            self.lbl_cons.setText("✅ <b>Todos los cálculos y balances del período están completamente consistentes.</b>")
            self.lbl_cons.setStyleSheet("color: green;")
        else:
            txt_incons = "<br>".join([f"• <b>{i['fecha']}</b>: {i['mensaje']}" for i in incons[:4]])
            self.lbl_cons.setText(f"⚠️ <b>Se detectaron advertencias de consistencia:</b><br>{txt_incons}")
            self.lbl_cons.setStyleSheet("color: #C62828;")

    def _on_export_excel(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Guardar Reporte Excel",
            f"Reporte_Mensual_{self.current_mes:02d}_{self.current_anio}.xlsx",
            "Excel Files (*.xlsx)"
        )
        if filepath:
            ok = self.exporter.export_excel(self.current_anio, self.current_mes, filepath)
            if ok:
                QMessageBox.information(self, "Exportación Exitosa", f"Reporte guardado en:\n{filepath}")
            else:
                QMessageBox.warning(self, "Error", "No se pudo exportar a Excel.")

    def _on_export_pdf(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Guardar Reporte PDF",
            f"Reporte_Mensual_{self.current_mes:02d}_{self.current_anio}.pdf",
            "PDF Files (*.pdf)"
        )
        if filepath:
            ok = self.exporter.export_pdf(self.current_anio, self.current_mes, filepath)
            if ok:
                QMessageBox.information(self, "Exportación Exitosa", f"Reporte guardado en:\n{filepath}")
            else:
                QMessageBox.warning(self, "Error", "No se pudo exportar a PDF.")
