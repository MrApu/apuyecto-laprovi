from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QTextEdit, QPushButton, QLabel, QMessageBox
)

class AjusteDialog(QDialog):
    def __init__(self, parent=None, titulo: str = "Registrar Ajuste / Corrección", detalle_cambio: str = ""):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.resize(400, 220)
        self.detalle_cambio = detalle_cambio
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        if self.detalle_cambio:
            lbl = QLabel(f"<b>Cambio detectado:</b> {self.detalle_cambio}")
            lbl.setWordWrap(True)
            layout.addWidget(lbl)

        form = QFormLayout()
        self.txt_motivo = QTextEdit()
        self.txt_motivo.setPlaceholderText("Explique el motivo del ajuste o corrección para la auditoría...")
        self.txt_motivo.setMaximumHeight(80)

        form.addRow("Motivo del ajuste (*):", self.txt_motivo)
        layout.addLayout(form)

        btn_box = QHBoxLayout()
        self.btn_guardar = QPushButton("Confirmar Ajuste")
        self.btn_guardar.setProperty("class", "PrimaryBtn")
        self.btn_guardar.clicked.connect(self._on_guardar)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)

        btn_box.addStretch()
        btn_box.addWidget(self.btn_cancelar)
        btn_box.addWidget(self.btn_guardar)

        layout.addLayout(btn_box)

    def _on_guardar(self):
        if not self.txt_motivo.toPlainText().strip():
            QMessageBox.warning(self, "Campo Requerido", "Debe ingresar un motivo para registrar la trazabilidad del ajuste.")
            self.txt_motivo.setFocus()
            return
        self.accept()

    def get_motivo(self) -> str:
        return self.txt_motivo.toPlainText().strip()
