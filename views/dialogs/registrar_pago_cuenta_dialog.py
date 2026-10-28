from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox, QDateEdit, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from models.cuenta_ticket import ResumenCuentaPolicia

class RegistrarPagoCuentaDialog(QDialog):
    def __init__(self, policia: ResumenCuentaPolicia, precio_defecto: float = 12.0, parent=None):
        super().__init__(parent)
        self.policia = policia
        self.precio_defecto = precio_defecto
        self.setWindowTitle(f"🟢 Registrar Pago de Tickets — {policia.apellidos}, {policia.nombres}")
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
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {
                border: 1px solid #10B981;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Card de información del policía
        card = QFrame()
        card.setStyleSheet("background-color: #18181B; border-left: 4px solid #10B981; border-radius: 6px; padding: 10px;")
        l_info = QVBoxLayout(card)
        l_info.setSpacing(4)
        
        lbl_nom = QLabel(f"<b>{self.policia.apellidos}, {self.policia.nombres}</b>")
        lbl_nom.setStyleSheet("font-size: 15px; color: #FFFFFF; font-weight: bold;")
        lbl_det = QLabel(f"Código: {self.policia.codigo} | Área: {self.policia.area}")
        lbl_det.setStyleSheet("font-size: 12px; color: #A1A1AA;")
        lbl_saldo = QLabel(f"Debe actualmente: <b style='color:#EF4444;'>{self.policia.saldo_tickets_debe} tickets (S/ {self.policia.saldo_monto_debe:.2f})</b>")
        
        l_info.addWidget(lbl_nom)
        l_info.addWidget(lbl_det)
        l_info.addWidget(lbl_saldo)
        layout.addWidget(card)

        # Fecha
        lbl_f = QLabel("Fecha de Cobro / Pago:")
        layout.addWidget(lbl_f)
        self.dt_fecha = QDateEdit()
        self.dt_fecha.setCalendarPopup(True)
        self.dt_fecha.setDisplayFormat("yyyy-MM-dd")
        self.dt_fecha.setDate(QDate.currentDate())
        layout.addWidget(self.dt_fecha)

        # Cantidad de tickets pagados
        lbl_cant = QLabel("Tickets que Cancela / Paga:")
        layout.addWidget(lbl_cant)
        
        row_tk = QHBoxLayout()
        self.spn_tickets = QSpinBox()
        self.spn_tickets.setRange(1, 9999)
        val_ini = self.policia.saldo_tickets_debe if self.policia.saldo_tickets_debe > 0 else 1
        self.spn_tickets.setValue(val_ini)
        self.spn_tickets.valueChanged.connect(self._recalc_monto)
        row_tk.addWidget(self.spn_tickets, 2)

        btn_todo = QPushButton("Pagar Deuda Total")
        btn_todo.setCursor(Qt.PointingHandCursor)
        btn_todo.setStyleSheet("background-color: #27272A; color: #E4E4E7; border-radius: 6px; padding: 6px 12px; font-weight: bold;")
        btn_todo.clicked.connect(self._pagar_todo)
        row_tk.addWidget(btn_todo, 1)
        layout.addLayout(row_tk)

        # Monto pagado
        lbl_tot = QLabel("Monto Cobrado (S/):")
        layout.addWidget(lbl_tot)
        self.spn_total = QDoubleSpinBox()
        self.spn_total.setRange(0.0, 999999.0)
        self.spn_total.setPrefix("S/ ")
        self.spn_total.setValue(round(self.spn_tickets.value() * self.precio_defecto, 2))
        layout.addWidget(self.spn_total)

        # Medio de pago
        lbl_medio = QLabel("Medio de Pago:")
        layout.addWidget(lbl_medio)
        self.cmb_medio = QComboBox()
        self.cmb_medio.addItems(["EFECTIVO", "YAPE", "PLIN", "TRANSFERENCIA"])
        layout.addWidget(self.cmb_medio)

        # Observación
        lbl_obs = QLabel("Observación (opcional):")
        layout.addWidget(lbl_obs)
        self.txt_obs = QLineEdit()
        self.txt_obs.setPlaceholderText("Ej: Canceló tickets adeudados en efectivo")
        layout.addWidget(self.txt_obs)

        # Botones
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet("background-color: #27272A; color: #FFFFFF; border-radius: 6px; padding: 8px 16px;")
        btn_cancelar.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancelar)

        btn_guardar = QPushButton("🟢 Registrar Pago")
        btn_guardar.setCursor(Qt.PointingHandCursor)
        btn_guardar.setStyleSheet("background-color: #10B981; color: #FFFFFF; font-weight: bold; border-radius: 6px; padding: 8px 16px;")
        btn_guardar.clicked.connect(self._guardar)
        btn_box.addWidget(btn_guardar)

        layout.addLayout(btn_box)

    def _recalc_monto(self, val: int):
        self.spn_total.setValue(round(val * self.precio_defecto, 2))

    def _pagar_todo(self):
        deb = self.policia.saldo_tickets_debe
        if deb > 0:
            self.spn_tickets.setValue(deb)
            self.spn_total.setValue(self.policia.saldo_monto_debe)
        else:
            self.spn_tickets.setValue(1)

    def _guardar(self):
        if self.spn_tickets.value() <= 0 and self.spn_total.value() <= 0:
            QMessageBox.warning(self, "Validación", "Debe ingresar tickets o monto pagado.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "fecha": self.dt_fecha.date().toString("yyyy-MM-dd"),
            "cantidad_tickets": self.spn_tickets.value(),
            "monto_total": self.spn_total.value(),
            "medio_pago": self.cmb_medio.currentText(),
            "observacion": self.txt_obs.text().strip() or None
        }
