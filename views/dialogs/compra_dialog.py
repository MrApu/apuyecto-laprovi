from typing import Optional
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QDateEdit,
    QPushButton, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor

from models.compra import Compra
from models.local import LOCAL_RESTAURANTE, LOCAL_FAST_FOOD, LOCAL_NAMES

class CompraSimpleDialog(QDialog):
    """
    Formulario simplificado y cómodo para registrar compras y egresos:
    - Fecha
    - Local / Sede
    - Monto total gastado (S/)
    - Observación / ¿Qué se compró? (sin necesidad de precios unitarios ni cantidades complejas)
    - Medio de pago
    - Categoría rápida
    """
    def __init__(self, parent=None, anio: int = 2026, mes: int = 9, local_id: str = LOCAL_RESTAURANTE, compra: Optional[Compra] = None):
        super().__init__(parent)
        self.anio = anio
        self.mes = mes
        self.default_local = local_id if local_id in (LOCAL_RESTAURANTE, LOCAL_FAST_FOOD) else LOCAL_RESTAURANTE
        self.compra = compra

        title = "✏️ Editar Compra" if compra else "🛒 Registrar Compra / Insumo"
        self.setWindowTitle(title)
        self.resize(480, 420)
        self.setStyleSheet("""
            QDialog {
                background-color: #090D16;
                color: #F8FAFC;
            }
            QLabel {
                color: #E2E8F0;
                font-weight: 600;
                font-size: 12px;
            }
            QLineEdit, QTextEdit, QComboBox, QDateEdit, QDoubleSpinBox {
                background-color: #111827;
                color: #FFFFFF;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {
                border: 1px solid #6366F1;
                background-color: #1E293B;
            }
        """)
        self._init_ui()
        if self.compra:
            self._cargar_datos_edicion()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header Title
        header_box = QHBoxLayout()
        icon = "✏️" if self.compra else "🛒"
        title_text = "EDITAR COMPRA" if self.compra else "NUEVA COMPRA / EGRESO"
        lbl_title = QLabel(f"{icon} {title_text}")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #38BDF8;")
        header_box.addWidget(lbl_title)
        layout.addLayout(header_box)

        # Form Layout
        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: #0F172A; border: 1px solid #1F2937; border-radius: 8px; padding: 12px;")
        form = QFormLayout(form_frame)
        form.setContentsMargins(10, 10, 10, 10)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        # 1. Fecha
        now = datetime.now()
        initial_day = now.day if (now.year == self.anio and now.month == self.mes) else 1
        self.dt_fecha = QDateEdit(QDate(self.anio, self.mes, initial_day))
        self.dt_fecha.setCalendarPopup(True)
        form.addRow("📅 Fecha:", self.dt_fecha)

        # 2. Local
        self.cmb_local = QComboBox()
        self.cmb_local.addItem("🏢 RESTAURANTE", LOCAL_RESTAURANTE)
        self.cmb_local.addItem("🍔 FAST FOOD", LOCAL_FAST_FOOD)
        if self.default_local == LOCAL_FAST_FOOD:
            self.cmb_local.setCurrentIndex(1)
        form.addRow("📍 Sede / Local:", self.cmb_local)

        # 3. Monto Total Gastado (S/) - Destacado
        self.spn_monto = QDoubleSpinBox()
        self.spn_monto.setRange(0.01, 9999999.0)
        self.spn_monto.setDecimals(2)
        self.spn_monto.setPrefix("S/ ")
        self.spn_monto.setValue(0.0)
        self.spn_monto.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #1E293B;
                color: #10B981;
                font-size: 15px;
                font-weight: 800;
                border: 1px solid #10B981;
                padding: 6px 10px;
                border-radius: 6px;
            }
        """)
        form.addRow("💰 Monto Gastado:", self.spn_monto)

        # 4. Observación / ¿Qué se compró?
        self.txt_observacion = QTextEdit()
        self.txt_observacion.setPlaceholderText("Ej: Pollo, carne de res, verduras del mercado, arroz, condimentos, bolsas...")
        self.txt_observacion.setMaximumHeight(85)
        form.addRow("📝 ¿Qué se compró?:", self.txt_observacion)

        # 5. Medio de Pago
        self.cmb_pago = QComboBox()
        self.cmb_pago.addItems(["EFECTIVO", "YAPE", "TRANSFERENCIA", "TARJETA", "CREDITO"])
        form.addRow("💳 Medio de Pago:", self.cmb_pago)

        # 6. Categoría Rápida (Opcional)
        self.cmb_categoria = QComboBox()
        self.cmb_categoria.addItems([
            "INSUMOS GENERALES",
            "VERDURAS Y FRUTAS",
            "CARNES Y POLLOS",
            "ABARROTES",
            "BEBIDAS Y GASEOSAS",
            "LIMPIEZA Y DESCARTABLES",
            "OTROS"
        ])
        form.addRow("🏷️ Categoría:", self.cmb_categoria)

        layout.addWidget(form_frame)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_cancelar = QPushButton("✕ Cancelar")
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #94A3B8;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #FFFFFF;
            }
        """)
        self.btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancelar)

        self.btn_guardar = QPushButton("💾 Guardar Compra")
        self.btn_guardar.setProperty("class", "SuccessBtn")
        self.btn_guardar.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
                color: #FFFFFF;
                border: 1px solid #34D399;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: 800;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
                border: 1px solid #6EE7B7;
            }
        """)
        self.btn_guardar.clicked.connect(self._on_guardar)
        btn_layout.addWidget(self.btn_guardar)

        layout.addLayout(btn_layout)

        # Focus directly on Monto
        self.spn_monto.setFocus()
        self.spn_monto.selectAll()

    def _cargar_datos_edicion(self):
        c = self.compra
        try:
            dt = datetime.strptime(c.fecha, "%Y-%m-%d")
            self.dt_fecha.setDate(QDate(dt.year, dt.month, dt.day))
        except Exception:
            pass

        idx_loc = self.cmb_local.findData(c.local_id)
        if idx_loc >= 0:
            self.cmb_local.setCurrentIndex(idx_loc)

        self.spn_monto.setValue(c.total or 0.0)
        detalle = c.observacion or c.descripcion or ""
        self.txt_observacion.setText(detalle)

        idx_pago = self.cmb_pago.findText(c.medio_pago)
        if idx_pago >= 0:
            self.cmb_pago.setCurrentIndex(idx_pago)

        idx_cat = self.cmb_categoria.findText(c.categoria)
        if idx_cat >= 0:
            self.cmb_categoria.setCurrentIndex(idx_cat)

    def _on_guardar(self):
        monto = self.spn_monto.value()
        if monto <= 0.0:
            QMessageBox.warning(self, "Monto Requerido", "Por favor ingrese el monto gastado en la compra (debe ser mayor a 0).")
            self.spn_monto.setFocus()
            return

        self.accept()

    def get_compra(self) -> Compra:
        fecha_str = self.dt_fecha.date().toString("yyyy-MM-dd")
        local_id = self.cmb_local.currentData()
        monto = round(self.spn_monto.value(), 2)
        detalle = self.txt_observacion.toPlainText().strip() or "Compras e Insumos"
        medio_pago = self.cmb_pago.currentText()
        categoria = self.cmb_categoria.currentText()

        return Compra(
            id=self.compra.id if self.compra else None,
            fecha=fecha_str,
            local_id=local_id,
            proveedor="GENERAL",
            categoria=categoria,
            descripcion=detalle,
            cantidad=1.0,
            precio_unitario=monto,
            total=monto,
            medio_pago=medio_pago,
            observacion=detalle
        )
