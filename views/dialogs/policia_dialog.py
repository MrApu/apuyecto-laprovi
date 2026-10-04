from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QTextEdit, QPushButton, QLabel, QMessageBox
)
from typing import Optional
from models.policia import Policia

class PoliciaDialog(QDialog):
    def __init__(self, parent=None, policia: Optional[Policia] = None, areas_disponibles: Optional[list] = None):
        super().__init__(parent)
        self.policia = policia
        self.areas_disponibles = areas_disponibles or ["AREPOFIS", "AREPJR", "DEPINCRI", "AREINCRI", "AREANDRO", "SECINT", "ARECOTER"]
        self.setWindowTitle("Nuevo Policía" if not policia else f"Editar Policía - {policia.codigo}")
        self.resize(420, 380)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_codigo = QLineEdit()
        self.txt_codigo.setPlaceholderText("Ej. APF-25")
        if self.policia:
            self.txt_codigo.setText(self.policia.codigo)

        self.txt_apellidos = QLineEdit()
        self.txt_apellidos.setPlaceholderText("Ej. QUISPE MAMANI")
        if self.policia:
            self.txt_apellidos.setText(self.policia.apellidos)

        self.txt_nombres = QLineEdit()
        self.txt_nombres.setPlaceholderText("Ej. JUAN CARLOS")
        if self.policia:
            self.txt_nombres.setText(self.policia.nombres)

        self.txt_sa_pnp = QLineEdit()
        self.txt_sa_pnp.setPlaceholderText("Ej. 12345678 (Opcional)")
        if self.policia and self.policia.sa_pnp:
            self.txt_sa_pnp.setText(self.policia.sa_pnp)

        self.cmb_area = QComboBox()
        self.cmb_area.setEditable(True)
        for a in self.areas_disponibles:
            self.cmb_area.addItem(a)
        if self.policia:
            idx = self.cmb_area.findText(self.policia.area)
            if idx >= 0:
                self.cmb_area.setCurrentIndex(idx)
            else:
                self.cmb_area.setEditText(self.policia.area)

        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems(["ACTIVO", "INACTIVO"])
        if self.policia:
            self.cmb_estado.setCurrentText(self.policia.estado)

        self.txt_obs = QTextEdit()
        self.txt_obs.setMaximumHeight(70)
        if self.policia and self.policia.observaciones:
            self.txt_obs.setPlainText(self.policia.observaciones)

        form.addRow("Código (*):", self.txt_codigo)
        form.addRow("Apellidos (*):", self.txt_apellidos)
        form.addRow("Nombres (*):", self.txt_nombres)
        form.addRow("SA-PNP:", self.txt_sa_pnp)
        form.addRow("Área (*):", self.cmb_area)
        form.addRow("Estado (*):", self.cmb_estado)
        form.addRow("Observaciones:", self.txt_obs)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setProperty("class", "PrimaryBtn")
        self.btn_guardar.clicked.connect(self._on_guardar)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancelar)
        btn_layout.addWidget(self.btn_guardar)

        layout.addLayout(btn_layout)

    def _on_guardar(self):
        codigo = self.txt_codigo.text().strip().upper()
        apellidos = self.txt_apellidos.text().strip().upper()
        nombres = self.txt_nombres.text().strip().upper()
        area = self.cmb_area.currentText().strip().upper()

        if not codigo:
            QMessageBox.warning(self, "Campo Requerido", "El código es obligatorio.")
            self.txt_codigo.setFocus()
            return
        if not apellidos:
            QMessageBox.warning(self, "Campo Requerido", "Los apellidos son obligatorios.")
            self.txt_apellidos.setFocus()
            return
        if not nombres:
            QMessageBox.warning(self, "Campo Requerido", "Los nombres son obligatorios.")
            self.txt_nombres.setFocus()
            return
        if not area:
            QMessageBox.warning(self, "Campo Requerido", "El área es obligatoria.")
            self.cmb_area.setFocus()
            return

        self.accept()

    def get_datos(self) -> Policia:
        return Policia(
            id=self.policia.id if self.policia else None,
            codigo=self.txt_codigo.text().strip().upper(),
            apellidos=self.txt_apellidos.text().strip().upper(),
            nombres=self.txt_nombres.text().strip().upper(),
            sa_pnp=self.txt_sa_pnp.text().strip() or None,
            area=self.cmb_area.currentText().strip().upper(),
            estado=self.cmb_estado.currentText().strip().upper(),
            observaciones=self.txt_obs.toPlainText().strip() or None
        )
