from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QDoubleSpinBox, QLineEdit, QDateEdit, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from models.cuenta_ticket import ResumenCuentaPolicia

class RegistrarDeudaTicketDialog(QDialog):
    def __init__(self, policia: ResumenCuentaPolicia, precio_defecto: float = 12.0, parent=None):
        super().__init__(parent)
        self.policia = policia
        self.precio_defecto = precio_defecto
        self.setWindowTitle(f"🔴 Registrar Deuda de Tickets — {policia.apellidos}, {policia.nombres}")
        self.setMinimumWidth(430)
        self.setStyleSheet("""
            QDialog {
                background-color: #0A0A0A;
                color: #FFFFFF;
            }
            QLabel {
                color: #E4E4E7;
                font-size: 13px;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
                border: 1px solid #DC2626;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Card de información del policía
        card = QFrame()
        card.setStyleSheet("background-color: #18181B; border-left: 4px solid #DC2626; border-radius: 6px; padding: 10px;")
        l_info = QVBoxLayout(card)
        l_info.setSpacing(4)
        
        lbl_nom = QLabel(f"<b>{self.policia.apellidos}, {self.policia.nombres}</b>")
        lbl_nom.setStyleSheet("font-size: 15px; color: #FFFFFF; font-weight: bold;")
        lbl_det = QLabel(f"Código: {self.policia.codigo} | Área: {self.policia.area}")
        lbl_det.setStyleSheet("font-size: 12px; color: #A1A1AA;")
        lbl_saldo = QLabel(f"Deuda actual acumulada: <b style='color:#EF4444;'>{self.policia.saldo_tickets_debe} tickets (S/ {self.policia.saldo_monto_debe:.2f})</b>")
        
        l_info.addWidget(lbl_nom)
        l_info.addWidget(lbl_det)
        l_info.addWidget(lbl_saldo)
        layout.addWidget(card)

        # Fecha
        lbl_f = QLabel("Fecha de Registro / Entrega:")
        layout.addWidget(lbl_f)
        self.dt_fecha = QDateEdit()
        self.dt_fecha.setCalendarPopup(True)
        self.dt_fecha.setDisplayFormat("yyyy-MM-dd")
        self.dt_fecha.setDate(QDate.currentDate())
        layout.addWidget(self.dt_fecha)

        # Cantidad de tickets que debe
        lbl_cant = QLabel("Cantidad de Tickets que DEBE:")
        layout.addWidget(lbl_cant)
        self.spn_tickets = QSpinBox()
        self.spn_tickets.setRange(1, 9999)
        self.spn_tickets.setValue(1)
        self.spn_tickets.valueChanged.connect(self._recalc_monto)
        layout.addWidget(self.spn_tickets)

        # Precio unitario y Monto
        row_m = QHBoxLayout()
        col_p = QVBoxLayout()
        col_p.addWidget(QLabel("Precio Unitario (S/):"))
        self.spn_precio = QDoubleSpinBox()
        self.spn_precio.setRange(0.0, 999.0)
        self.spn_precio.setValue(self.precio_defecto)
        self.spn_precio.setPrefix("S/ ")
        self.spn_precio.valueChanged.connect(self._recalc_monto)
        col_p.addWidget(self.spn_precio)
        row_m.addLayout(col_p)

        col_tot = QVBoxLayout()
        col_tot.addWidget(QLabel("Total Deuda (S/):"))
        self.spn_total = QDoubleSpinBox()
        self.spn_total.setRange(0.0, 999999.0)
        self.spn_total.setValue(self.precio_defecto)
        self.spn_total.setPrefix("S/ ")
        col_tot.addWidget(self.spn_total)
        row_m.addLayout(col_tot)

        layout.addLayout(row_m)

        # Observación
        lbl_obs = QLabel("Concepto / Observación (opcional):")
        layout.addWidget(lbl_obs)
        self.txt_obs = QLineEdit()
        self.txt_obs.setPlaceholderText("Ej: Se entregaron 5 tickets fiados para almuerzo")
        layout.addWidget(self.txt_obs)

        # Botones
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet("background-color: #27272A; color: #FFFFFF; border-radius: 6px; padding: 8px 16px;")
        btn_cancelar.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancelar)

        btn_guardar = QPushButton("🔴 Registrar Deuda")
        btn_guardar.setCursor(Qt.PointingHandCursor)
        btn_guardar.setStyleSheet("background-color: #DC2626; color: #FFFFFF; font-weight: bold; border-radius: 6px; padding: 8px 16px;")
        btn_guardar.clicked.connect(self._guardar)
        btn_box.addWidget(btn_guardar)

        layout.addLayout(btn_box)

    def _recalc_monto(self):
        tot = round(self.spn_tickets.value() * self.spn_precio.value(), 2)
        self.spn_total.setValue(tot)

    def _guardar(self):
        if self.spn_tickets.value() <= 0:
            QMessageBox.warning(self, "Validación", "La cantidad de tickets debe ser al menos 1.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "fecha": self.dt_fecha.date().toString("yyyy-MM-dd"),
            "cantidad_tickets": self.spn_tickets.value(),
            "precio_unitario": self.spn_precio.value(),
            "monto_total": self.spn_total.value(),
            "observacion": self.txt_obs.text().strip() or None
        }
