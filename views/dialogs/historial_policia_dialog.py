from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt
from typing import List, Dict, Any
from models.policia import Policia

class HistorialPoliciaDialog(QDialog):
    def __init__(self, parent=None, policia: Policia = None, historial_meses: List[dict] = None):
        super().__init__(parent)
        self.policia = policia
        self.historial_meses = historial_meses or []
        self.setWindowTitle(f"Historial de Tickets - {policia.codigo} {policia.nombre_completo}")
        self.resize(650, 480)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Info Box
        grp = QGroupBox("Datos del Efectivo Policial")
        grid = QGridLayout(grp)
        grid.addWidget(QLabel("<b>Código:</b>"), 0, 0)
        grid.addWidget(QLabel(self.policia.codigo), 0, 1)
        grid.addWidget(QLabel("<b>Apellidos y Nombres:</b>"), 0, 2)
        grid.addWidget(QLabel(self.policia.nombre_completo), 0, 3)

        grid.addWidget(QLabel("<b>SA-PNP:</b>"), 1, 0)
        grid.addWidget(QLabel(self.policia.sa_pnp or "N/A"), 1, 1)
        grid.addWidget(QLabel("<b>Área Actual:</b>"), 1, 2)
        grid.addWidget(QLabel(self.policia.area), 1, 3)

        grid.addWidget(QLabel("<b>Estado:</b>"), 2, 0)
        lbl_est = QLabel(self.policia.estado)
        lbl_est.setStyleSheet("color: green; font-weight: bold;" if self.policia.is_activo else "color: red; font-weight: bold;")
        grid.addWidget(lbl_est, 2, 1)

        layout.addWidget(grp)

        # Monthly History Table
        layout.addWidget(QLabel("<b>Historial Mensual de Consumo de Tickets</b>"))
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Año", "Mes", "Total Tickets", "Fechas Específicas Marcadas"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        self.table.setRowCount(len(self.historial_meses))
        tot_acumulado = 0

        for r, h in enumerate(self.historial_meses):
            anio_item = QTableWidgetItem(str(h["anio"]))
            mes_item = QTableWidgetItem(h.get("nombre_mes", str(h["mes"])))
            tot_tickets = h.get("total_tickets", 0)
            tot_acumulado += tot_tickets
            tot_item = QTableWidgetItem(str(tot_tickets))
            tot_item.setTextAlignment(Qt.AlignCenter)
            fechas_item = QTableWidgetItem(h.get("fechas_marcadas") or "-")

            self.table.setItem(r, 0, anio_item)
            self.table.setItem(r, 1, mes_item)
            self.table.setItem(r, 2, tot_item)
            self.table.setItem(r, 3, fechas_item)

        layout.addWidget(self.table)

        # Total footer
        lbl_tot = QLabel(f"<b>Total histórico acumulado:</b> {tot_acumulado} tickets")
        lbl_tot.setStyleSheet("font-size: 14px; color: #1F4E78; padding: 6px;")
        layout.addWidget(lbl_tot)

        # Close button
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        btn_box.addWidget(btn_cerrar)
        layout.addLayout(btn_box)
