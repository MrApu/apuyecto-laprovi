from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QLineEdit, QComboBox, QDateEdit, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from typing import Optional, List
from models.policia import Policia
from models.vale_policia import ValePolicia

class ValePoliciaDialog(QDialog):
    def __init__(self, policias: List[Policia], vale: Optional[ValePolicia] = None, preselected_policia_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.policias = policias
        self.vale = vale
        self.preselected_id = preselected_policia_id
        is_edit = vale is not None
        self.setWindowTitle("✏️ Modificar Vale a Policía" if is_edit else "🎟️ Registrar Entrega de Vales por Tickets")
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
            QLineEdit, QSpinBox, QComboBox, QDateEdit {
                background-color: #18181B;
                color: #FFFFFF;
                border: 1px solid #27272A;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QDateEdit:focus {
                border: 1px solid #DC2626;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Policía selector
        lbl_p = QLabel("Seleccione el Policía:")
        layout.addWidget(lbl_p)

        self.cmb_policia = QComboBox()
        self.cmb_policia.setEditable(True)
        self.cmb_policia.setInsertPolicy(QComboBox.NoInsert)
        for p in self.policias:
            texto = f"{p.apellidos}, {p.nombres} ({p.codigo} - {p.area})"
            self.cmb_policia.addItem(texto, p.id)

        # Pre-seleccionar
        target_id = self.vale.policia_id if self.vale else self.preselected_id
        if target_id:
            for idx in range(self.cmb_policia.count()):
                if self.cmb_policia.itemData(idx) == target_id:
                    self.cmb_policia.setCurrentIndex(idx)
                    break
        layout.addWidget(self.cmb_policia)

        # Fecha
        lbl_f = QLabel("Fecha:")
        layout.addWidget(lbl_f)
        self.dt_fecha = QDateEdit()
        self.dt_fecha.setCalendarPopup(True)
        self.dt_fecha.setDisplayFormat("yyyy-MM-dd")
        if self.vale and self.vale.fecha:
            self.dt_fecha.setDate(QDate.fromString(self.vale.fecha, "yyyy-MM-dd"))
        else:
            self.dt_fecha.setDate(QDate.currentDate())
        layout.addWidget(self.dt_fecha)

        # Cantidad de vales y tickets equivalentes
        row_nums = QHBoxLayout()
        
        col_vales = QVBoxLayout()
        col_vales.addWidget(QLabel("Vales Dados / Canjeados:"))
        self.spn_vales = QSpinBox()
        self.spn_vales.setRange(1, 999)
        self.spn_vales.setValue(self.vale.cantidad_vales if self.vale else 1)
        self.spn_vales.valueChanged.connect(self._sync_tickets)
        col_vales.addWidget(self.spn_vales)
        row_nums.addLayout(col_vales)

        col_tickets = QVBoxLayout()
        col_tickets.addWidget(QLabel("Tickets Equivalentes:"))
        self.spn_tickets = QSpinBox()
        self.spn_tickets.setRange(1, 999)
        self.spn_tickets.setValue(self.vale.tickets_equivalentes if self.vale else 1)
        col_tickets.addWidget(self.spn_tickets)
        row_nums.addLayout(col_tickets)

        layout.addLayout(row_nums)

        # Observación
        lbl_obs = QLabel("Observación (opcional):")
        layout.addWidget(lbl_obs)
        self.txt_obs = QLineEdit()
        self.txt_obs.setPlaceholderText("Ej: Se entregó vale #105 por canje de ticket")
        if self.vale and self.vale.observacion:
            self.txt_obs.setText(self.vale.observacion)
        layout.addWidget(self.txt_obs)

        # Botones
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet("background-color: #27272A; color: #FFFFFF; border-radius: 6px; padding: 8px 16px;")
        btn_cancelar.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancelar)

        btn_guardar = QPushButton("💾 Guardar" if self.vale else "➕ Registrar Vale")
        btn_guardar.setCursor(Qt.PointingHandCursor)
        btn_guardar.setStyleSheet("background-color: #DC2626; color: #FFFFFF; font-weight: bold; border-radius: 6px; padding: 8px 16px;")
        btn_guardar.clicked.connect(self._guardar)
        btn_box.addWidget(btn_guardar)

        layout.addLayout(btn_box)

    def _sync_tickets(self, val: int):
        # Auto-sugerir misma cantidad de tickets por defecto
        if not self.vale:
            self.spn_tickets.setValue(val)

    def _guardar(self):
        if self.cmb_policia.currentIndex() < 0:
            QMessageBox.warning(self, "Validación", "Debe seleccionar un policía.")
            return
        if self.spn_vales.value() <= 0:
            QMessageBox.warning(self, "Validación", "La cantidad de vales debe ser mayor a 0.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "policia_id": self.cmb_policia.currentData(),
            "fecha": self.dt_fecha.date().toString("yyyy-MM-dd"),
            "cantidad_vales": self.spn_vales.value(),
            "tickets_equivalentes": self.spn_tickets.value(),
            "observacion": self.txt_obs.text().strip() or None
        }
