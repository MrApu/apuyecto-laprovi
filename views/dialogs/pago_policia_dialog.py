from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox, QDateEdit, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from datetime import datetime
from typing import Optional
from models.policia_pago import ResumenDeudaPolicia

class RegistrarPagoPoliciaDialog(QDialog):
    def __init__(self, resumen: ResumenDeudaPolicia, precio_ticket: float = 12.0, parent=None):
        super().__init__(parent)
        self.resumen = resumen
        self.precio_ticket = precio_ticket
        self.setWindowTitle(f"Registrar Pago de Tickets — {resumen.apellidos}, {resumen.nombres}")
        self.setMinimumWidth(440)
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
                border: 1px solid #DC2626;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header card
        card_info = QFrame()
        card_info.setStyleSheet("background-color: #18181B; border-left: 4px solid #DC2626; border-radius: 6px; padding: 10px;")
        l_info = QVBoxLayout(card_info)
        l_info.setSpacing(4)
        
        lbl_nombre = QLabel(f"<b>{self.resumen.apellidos}, {self.resumen.nombres}</b>")
        lbl_nombre.setStyleSheet("font-size: 15px; color: #FFFFFF; font-weight: bold;")
        lbl_det = QLabel(f"Código: {self.resumen.codigo} | Área: {self.resumen.area}")
        lbl_det.setStyleSheet("font-size: 12px; color: #A1A1AA;")
        
        lbl_estado = QLabel(f"Debe actualmente: <b>{self.resumen.tickets_debidos} tickets</b> (S/ {self.resumen.monto_pendiente:.2f})")
        lbl_estado.setStyleSheet("font-size: 13px; color: #EF4444; font-weight: bold; margin-top: 4px;")
        
        l_info.addWidget(lbl_nombre)
        l_info.addWidget(lbl_det)
        l_info.addWidget(lbl_estado)
        layout.addWidget(card_info)

        # Fecha de pago
        lbl_f = QLabel("Fecha de Pago:")
        layout.addWidget(lbl_f)
        self.dt_fecha = QDateEdit()
        self.dt_fecha.setCalendarPopup(True)
        self.dt_fecha.setDisplayFormat("yyyy-MM-dd")
        self.dt_fecha.setDate(QDate.currentDate())
        layout.addWidget(self.dt_fecha)

        # Cantidad de tickets a pagar
        lbl_t = QLabel("Tickets a Pagar:")
        layout.addWidget(lbl_t)
        
        box_tk = QHBoxLayout()
        self.spn_tickets = QSpinBox()
        self.spn_tickets.setRange(1, 9999)
        max_sugerido = self.resumen.tickets_debidos if self.resumen.tickets_debidos > 0 else 1
        self.spn_tickets.setValue(max_sugerido)
        self.spn_tickets.valueChanged.connect(self._on_tickets_changed)
        box_tk.addWidget(self.spn_tickets, 2)

        btn_todo = QPushButton("Pagar Todo")
        btn_todo.setCursor(Qt.PointingHandCursor)
        btn_todo.setStyleSheet("background-color: #27272A; color: #E4E4E7; border-radius: 6px; padding: 6px 12px; font-weight: bold;")
        btn_todo.clicked.connect(self._pagar_todo)
        box_tk.addWidget(btn_todo, 1)
        layout.addLayout(box_tk)

        # Monto pagado
        lbl_m = QLabel("Monto a Cobrar / Pagado (S/):")
        layout.addWidget(lbl_m)
        self.spn_monto = QDoubleSpinBox()
        self.spn_monto.setRange(0.0, 999999.0)
        self.spn_monto.setDecimals(2)
        self.spn_monto.setPrefix("S/ ")
        self.spn_monto.setValue(round(self.spn_tickets.value() * self.precio_ticket, 2))
        layout.addWidget(self.spn_monto)

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
        self.txt_obs.setPlaceholderText("Ej: Canceló tickets de la primera quincena")
        layout.addWidget(self.txt_obs)

        # Botones de acción
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet("background-color: #27272A; color: #FFFFFF; border-radius: 6px; padding: 8px 16px;")
        btn_cancelar.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancelar)

        btn_guardar = QPushButton("💾 Confirmar Pago")
        btn_guardar.setCursor(Qt.PointingHandCursor)
        btn_guardar.setStyleSheet("background-color: #DC2626; color: #FFFFFF; font-weight: bold; border-radius: 6px; padding: 8px 16px;")
        btn_guardar.clicked.connect(self._guardar)
        btn_box.addWidget(btn_guardar)

        layout.addLayout(btn_box)

    def _on_tickets_changed(self, val: int):
        self.spn_monto.setValue(round(val * self.precio_ticket, 2))

    def _pagar_todo(self):
        deb = self.resumen.tickets_debidos
        if deb > 0:
            self.spn_tickets.setValue(deb)
        else:
            self.spn_tickets.setValue(1)

    def _guardar(self):
        if self.spn_tickets.value() <= 0 and self.spn_monto.value() <= 0:
            QMessageBox.warning(self, "Validación", "Debe ingresar al menos 1 ticket o un monto válido.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "fecha": self.dt_fecha.date().toString("yyyy-MM-dd"),
            "tickets_pagados": self.spn_tickets.value(),
            "monto_pagado": self.spn_monto.value(),
            "medio_pago": self.cmb_medio.currentText(),
            "observacion": self.txt_obs.text().strip() or None
        }
