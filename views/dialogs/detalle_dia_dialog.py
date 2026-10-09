from typing import Optional, Dict, Any, List
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QApplication, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from database.connection import DatabaseManager
from services.mes_service import MesService
from models.local import LOCAL_NAMES, LOCAL_CONSOLIDADO
from views.components.toast import ToastManager

class DetalleDiaDialog(QDialog):
    """
    Diálogo de Drill-Down que muestra la bitácora completa del día:
    - Resumen financiero e indicadores clave.
    - Lista de efectivos PNP que consumieron ticket ese día.
    - Compras de insumos registradas en el día.
    - Gastos operativos y servicios del día.
    - Pagos al personal en ese turno.
    - Botón de 1-Clic para copiar reporte formateado a WhatsApp.
    """
    def __init__(self, anio: int, mes: int, dia: int, local_id: str = "restaurante", parent=None):
        super().__init__(parent)
        self.anio = anio
        self.mes = mes
        self.dia = dia
        self.local_id = local_id
        self.fecha_str = f"{anio:04d}-{mes:02d}-{dia:02d}"
        self.db = DatabaseManager.get_instance()
        self.mes_service = MesService()
        self.sede_name = LOCAL_NAMES.get(local_id, local_id.upper())

        self.setWindowTitle(f"🔍 Bitácora del Día — {self.fecha_str} ({self.sede_name})")
        self.resize(850, 620)
        self.setStyleSheet("background-color: #090D16; color: #F3F4F6;")
        self._init_ui()
        self._cargar_datos()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        try:
            dt = datetime.strptime(self.fecha_str, "%Y-%m-%d")
            dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            nombre_dia = dias_semana[dt.weekday()]
            title_text = f"📅 {nombre_dia.upper()}, {dt.day:02d} DE {dt.strftime('%B').upper()} {dt.year}"
        except Exception:
            title_text = f"📅 BITÁCORA DEL DÍA {self.fecha_str}"

        lbl_title = QLabel(title_text)
        lbl_title.setStyleSheet("font-size: 17px; font-weight: 800; color: #F8FAFC;")
        header.addWidget(lbl_title)

        lbl_sede = QLabel(f"📍 {self.sede_name}")
        lbl_sede.setStyleSheet("background: #1E293B; color: #38BDF8; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 11px;")
        header.addWidget(lbl_sede)

        header.addStretch()

        self.btn_whatsapp = QPushButton("📲 Copiar para WhatsApp")
        self.btn_whatsapp.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
                color: #FFFFFF;
                border: 1px solid #34D399;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 800;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
                border: 1px solid #6EE7B7;
            }
        """)
        self.btn_whatsapp.clicked.connect(self._copiar_whatsapp)
        header.addWidget(self.btn_whatsapp)

        btn_close = QPushButton("✕")
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94A3B8;
                font-size: 16px;
                border: none;
                padding: 4px 8px;
            }
            QPushButton:hover {
                color: white;
            }
        """)
        btn_close.clicked.connect(self.accept)
        header.addWidget(btn_close)

        layout.addLayout(header)

        # KPI Summary Cards (Hero Row)
        kpi_row = QHBoxLayout()
        self.lbl_val_venta = QLabel("S/ 0.00")
        self.lbl_val_egreso = QLabel("S/ 0.00")
        self.lbl_val_saldo = QLabel("S/ 0.00")
        self.lbl_val_tickets = QLabel("0 tk")

        kpi_row.addWidget(self._create_card("Venta Total", self.lbl_val_venta, "#10B981"))
        kpi_row.addWidget(self._create_card("Total Egresos", self.lbl_val_egreso, "#F43F5E"))
        kpi_row.addWidget(self._create_card("Saldo Neto", self.lbl_val_saldo, "#38BDF8"))
        kpi_row.addWidget(self._create_card("Tickets PNP", self.lbl_val_tickets, "#818CF8"))
        layout.addLayout(kpi_row)

        # Tabs for details
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #1F2937;
                background: #0B0F19;
                border-radius: 8px;
                padding: 8px;
            }
            QTabBar::tab {
                background: #111827;
                color: #94A3B8;
                font-weight: 700;
                font-size: 12px;
                padding: 8px 16px;
                margin-right: 4px;
                border-radius: 6px;
                border: 1px solid #1F2937;
            }
            QTabBar::tab:selected {
                background: #6366F1;
                color: #FFFFFF;
                border: 1px solid #818CF8;
            }
        """)

        # Tab 1: Policías marcados
        self.table_policias = QTableWidget()
        self.table_policias.setColumnCount(4)
        self.table_policias.setHorizontalHeaderLabels(["Código", "Apellidos y Nombres", "Área / Unidad", "SA-PNP"])
        self.table_policias.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabs.addTab(self.table_policias, "👮 Efectivos PNP")

        # Tab 2: Compras
        self.table_compras = QTableWidget()
        self.table_compras.setColumnCount(4)
        self.table_compras.setHorizontalHeaderLabels(["Proveedor / Descripción", "Categoría", "Comprobante", "Monto (S/)"])
        self.table_compras.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabs.addTab(self.table_compras, "🛒 Compras e Insumos")

        # Tab 3: Gastos
        self.table_gastos = QTableWidget()
        self.table_gastos.setColumnCount(3)
        self.table_gastos.setHorizontalHeaderLabels(["Concepto", "Categoría", "Monto (S/)"])
        self.table_gastos.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabs.addTab(self.table_gastos, "💡 Gastos Operativos")

        # Tab 4: Personal
        self.table_personal = QTableWidget()
        self.table_personal.setColumnCount(3)
        self.table_personal.setHorizontalHeaderLabels(["Personal / Empleado", "Turno / Detalle", "Monto Pagado (S/)"])
        self.table_personal.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabs.addTab(self.table_personal, "👥 Pagos Personal")

        layout.addWidget(self.tabs)

    def _create_card(self, title: str, val_label: QLabel, color: str) -> QWidget:
        w = QFrame()
        w.setStyleSheet(f"background: #111827; border: 1px solid #1F2937; border-left: 4px solid {color}; border-radius: 8px; padding: 8px;")
        l = QVBoxLayout(w)
        l.setContentsMargins(10, 6, 10, 6)
        l.setSpacing(2)
        lbl_t = QLabel(title.upper())
        lbl_t.setStyleSheet("color: #94A3B8; font-size: 10px; font-weight: 800; letter-spacing: 0.5px;")
        val_label.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 800;")
        l.addWidget(lbl_t)
        l.addWidget(val_label)
        return w

    def _cargar_datos(self):
        mes_obj = self.mes_service.get_by_anio_mes(self.anio, self.mes)
        mes_id = mes_obj.id if mes_obj else None

        # 1. Ventas & Finanzas
        v_row = self.db.execute_query(
            "SELECT * FROM ventas_diarias WHERE fecha = ? AND local_id = ?",
            (self.fecha_str, self.local_id)
        )
        if v_row:
            v = v_row[0]
            self.venta_data = {
                "efectivo": v["efectivo"] or 0.0,
                "yape": v["yape"] or 0.0,
                "tickets": v["cantidad_tickets"] or 0,
                "venta_tickets": v["venta_tickets"] or 0.0,
                "venta_total": v["venta_total"] or 0.0
            }
        else:
            self.venta_data = {"efectivo": 0.0, "yape": 0.0, "tickets": 0, "venta_tickets": 0.0, "venta_total": 0.0}

        # 2. Efectivos PNP
        pol_rows = []
        if mes_id:
            if self.local_id == LOCAL_CONSOLIDADO:
                pol_rows = self.db.execute_query("""
                    SELECT p.codigo, p.apellidos, p.nombres, p.area, p.sa_pnp
                    FROM tickets_por_policia t
                    JOIN policias p ON t.policia_id = p.id
                    WHERE t.mes_id = ? AND t.dia = ? AND t.valor = 1
                    GROUP BY p.id
                    ORDER BY p.apellidos, p.nombres
                """, (mes_id, self.dia))
            else:
                pol_rows = self.db.execute_query("""
                    SELECT p.codigo, p.apellidos, p.nombres, p.area, p.sa_pnp
                    FROM tickets_por_policia t
                    JOIN policias p ON t.policia_id = p.id
                    WHERE t.mes_id = ? AND t.dia = ? AND t.valor = 1 AND t.local_id = ?
                    ORDER BY p.apellidos, p.nombres
                """, (mes_id, self.dia, self.local_id))

        self.table_policias.setRowCount(len(pol_rows))
        for r, p in enumerate(pol_rows):
            self.table_policias.setItem(r, 0, QTableWidgetItem(p["codigo"] or ""))
            self.table_policias.setItem(r, 1, QTableWidgetItem(f"{p['apellidos']} {p['nombres']}"))
            self.table_policias.setItem(r, 2, QTableWidgetItem(p["area"] or "-"))
            self.table_policias.setItem(r, 3, QTableWidgetItem(p["sa_pnp"] or "-"))

        # 3. Compras
        comp_rows = self.db.execute_query(
            "SELECT * FROM compras WHERE fecha = ? AND local_id = ?",
            (self.fecha_str, self.local_id)
        )
        self.table_compras.setRowCount(len(comp_rows))
        total_compras = 0.0
        for r, c in enumerate(comp_rows):
            monto = c["total"] or 0.0
            total_compras += monto
            self.table_compras.setItem(r, 0, QTableWidgetItem(c["descripcion"] or c["proveedor"] or "-"))
            self.table_compras.setItem(r, 1, QTableWidgetItem(c["categoria"] or "-"))
            self.table_compras.setItem(r, 2, QTableWidgetItem(c["nro_comprobante"] or "-"))
            self.table_compras.setItem(r, 3, QTableWidgetItem(f"S/ {monto:,.2f}"))

        # 4. Gastos
        gast_rows = self.db.execute_query(
            "SELECT * FROM gastos WHERE fecha = ? AND local_id = ?",
            (self.fecha_str, self.local_id)
        )
        self.table_gastos.setRowCount(len(gast_rows))
        total_gastos = 0.0
        for r, g in enumerate(gast_rows):
            monto = g["monto"] or 0.0
            total_gastos += monto
            self.table_gastos.setItem(r, 0, QTableWidgetItem(g["concepto"] or "-"))
            self.table_gastos.setItem(r, 1, QTableWidgetItem(g["categoria"] or "-"))
            self.table_gastos.setItem(r, 2, QTableWidgetItem(f"S/ {monto:,.2f}"))

        # 5. Personal
        pers_rows = self.db.execute_query(
            "SELECT * FROM pagos_personal WHERE fecha = ? AND local_id = ?",
            (self.fecha_str, self.local_id)
        )
        self.table_personal.setRowCount(len(pers_rows))
        total_personal = 0.0
        for r, pr in enumerate(pers_rows):
            monto = pr["monto"] or 0.0
            total_personal += monto
            self.table_personal.setItem(r, 0, QTableWidgetItem(pr["personal_nombre"] or "-"))
            self.table_personal.setItem(r, 1, QTableWidgetItem(pr["turno"] or pr["concepto"] or "-"))
            self.table_personal.setItem(r, 2, QTableWidgetItem(f"S/ {monto:,.2f}"))

        # Totals
        total_ventas = self.venta_data["venta_total"]
        total_egresos = round(total_compras + total_gastos + total_personal, 2)
        saldo_neto = round(total_ventas - total_egresos, 2)
        cant_tickets = len(pol_rows) if pol_rows else self.venta_data["tickets"]

        self.lbl_val_venta.setText(f"S/ {total_ventas:,.2f}")
        self.lbl_val_egreso.setText(f"S/ {total_egresos:,.2f}")
        signo = "+" if saldo_neto > 0 else ""
        self.lbl_val_saldo.setText(f"{signo}S/ {saldo_neto:,.2f}")
        self.lbl_val_saldo.setStyleSheet(f"color: {'#10B981' if saldo_neto >= 0 else '#F43F5E'}; font-size: 16px; font-weight: 800;")
        self.lbl_val_tickets.setText(f"{cant_tickets} efectivos")

        self.resumen_completo = {
            "fecha": self.fecha_str,
            "sede": self.sede_name,
            "efectivo": self.venta_data["efectivo"],
            "yape": self.venta_data["yape"],
            "tickets_cant": cant_tickets,
            "venta_tickets": self.venta_data["venta_tickets"],
            "venta_total": total_ventas,
            "compras": total_compras,
            "gastos": total_gastos,
            "personal": total_personal,
            "total_egresos": total_egresos,
            "saldo_neto": saldo_neto
        }

    def _copiar_whatsapp(self):
        d = self.resumen_completo
        signo = "+" if d['saldo_neto'] > 0 else ""
        rent = round((d['saldo_neto'] / d['venta_total'] * 100.0), 1) if d['venta_total'] > 0 else 0.0

        texto = (
            f"📊 *REPORTE DIARIO — {d['sede'].upper()}*\n"
            f"📅 *Fecha:* {d['fecha']}\n"
            f"───────────────────────────\n"
            f"💵 *INGRESOS / VENTAS:*\n"
            f"  • Efectivo: S/ {d['efectivo']:,.2f}\n"
            f"  • Yape / Digital: S/ {d['yape']:,.2f}\n"
            f"  • Tickets PNP ({d['tickets_cant']}): S/ {d['venta_tickets']:,.2f}\n"
            f"  ➜ *TOTAL VENTA:* S/ {d['venta_total']:,.2f}\n"
            f"───────────────────────────\n"
            f"💸 *EGRESOS OPERATIVOS:*\n"
            f"  • Compras / Insumos: S/ {d['compras']:,.2f}\n"
            f"  • Gastos Generales: S/ {d['gastos']:,.2f}\n"
            f"  • Pago Personal: S/ {d['personal']:,.2f}\n"
            f"  ➜ *TOTAL EGRESOS:* S/ {d['total_egresos']:,.2f}\n"
            f"───────────────────────────\n"
            f"⚖️ *SALDO NETO:* {signo}S/ {d['saldo_neto']:,.2f}  (Margen: {rent:.1f}%)\n"
            f"🌟 *LA PROVINCIAL* — Sistema de Control"
        )
        QApplication.clipboard().setText(texto)
        ToastManager.show_success("¡Reporte copiado al portapapeles listo para WhatsApp!", self)
