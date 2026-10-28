from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from typing import Optional

class AsignarTicketsPoliciaDialog(QDialog):
    def __init__(self, policia_nombre: str, codigo: str, tickets_actuales: int, num_dias_mes: int = 30, parent=None):
        super().__init__(parent)
        self.policia_nombre = policia_nombre
        self.codigo = codigo
        self.tickets_actuales = tickets_actuales
        self.num_dias_mes = num_dias_mes
        self.setWindowTitle(f"⚡ Asignación Rápida de Tickets — {policia_nombre}")
        self.setMinimumWidth(380)
        self.setStyleSheet("""
            QDialog {
                background-color: #0A0A0A;
                color: #FFFFFF;
            }
            QLabel {
                color: #E4E4E7;
                font-size: 13px;
            }
            QSpinBox {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 16px;
                font-weight: bold;
            }
            QSpinBox:focus {
                border: 1px solid #DC2626;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header info
        card_info = QFrame()
        card_info.setStyleSheet("background-color: #18181B; border-left: 4px solid #DC2626; border-radius: 6px; padding: 10px;")
        l_info = QVBoxLayout(card_info)
        l_info.setSpacing(4)
        
        lbl_nombre = QLabel(f"<b>{self.policia_nombre}</b>")
        lbl_nombre.setStyleSheet("font-size: 14px; color: #FFFFFF;")
        lbl_det = QLabel(f"Código: {self.codigo} | Tickets Actuales: <b style='color:#38BDF8;'>{self.tickets_actuales}</b>")
        lbl_det.setStyleSheet("font-size: 12px; color: #A1A1AA;")
        
        l_info.addWidget(lbl_nombre)
        l_info.addWidget(lbl_det)
        layout.addWidget(card_info)

        lbl_desc = QLabel("Ingrese la cantidad total de tickets para el mes (sin marcar día por día):")
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #D4D4D8; font-size: 12px;")
        layout.addWidget(lbl_desc)

        # Input
        self.spn_cantidad = QSpinBox()
        self.spn_cantidad.setRange(0, self.num_dias_mes)
        self.spn_cantidad.setValue(self.tickets_actuales)
        self.spn_cantidad.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.spn_cantidad)

        # Botones rápidos
        row_quick = QHBoxLayout()
        for cant, txt in [(0, "0"), (15, "15 (Quincena)"), (20, "20"), (self.num_dias_mes, f"Mes ({self.num_dias_mes})")]:
            if cant <= self.num_dias_mes:
                btn = QPushButton(txt)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setStyleSheet("background-color: #27272A; color: #E4E4E7; border-radius: 4px; padding: 4px 8px; font-size: 11px;")
                btn.clicked.connect(lambda _, c=cant: self.spn_cantidad.setValue(c))
                row_quick.addWidget(btn)
        layout.addLayout(row_quick)

        # Botones de confirmación
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet("background-color: #27272A; color: #FFFFFF; border-radius: 6px; padding: 8px 16px;")
        btn_cancelar.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancelar)

        btn_guardar = QPushButton("💾 Guardar Cantidad")
        btn_guardar.setCursor(Qt.PointingHandCursor)
        btn_guardar.setStyleSheet("background-color: #DC2626; color: #FFFFFF; font-weight: bold; border-radius: 6px; padding: 8px 16px;")
        btn_guardar.clicked.connect(self.accept)
        btn_box.addWidget(btn_guardar)

        layout.addLayout(btn_box)

    def get_cantidad(self) -> int:
        return self.spn_cantidad.value()
