from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QSpinBox,
    QComboBox, QDoubleSpinBox, QPushButton, QLabel, QMessageBox
)
from datetime import datetime
from models.mes import NOMBRES_MESES

class NuevoMesDialog(QDialog):
    def __init__(self, parent=None, precio_actual: float = 15.0):
        super().__init__(parent)
        self.precio_actual = precio_actual
        self.setWindowTitle("Crear Nuevo Período Mensual")
        self.resize(340, 240)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(12)

        now = datetime.now()
        self.spin_anio = QSpinBox()
        self.spin_anio.setRange(2020, 2050)
        self.spin_anio.setValue(now.year)

        self.cmb_mes = QComboBox()
        for idx, m in enumerate(NOMBRES_MESES[1:], start=1):
            self.cmb_mes.addItem(f"{idx:02d} - {m}", idx)
        self.cmb_mes.setCurrentIndex(now.month - 1)

        self.spin_precio = QDoubleSpinBox()
        self.spin_precio.setRange(1.0, 500.0)
        self.spin_precio.setDecimals(2)
        self.spin_precio.setPrefix("S/ ")
        self.spin_precio.setValue(self.precio_actual)

        form.addRow("Año:", self.spin_anio)
        form.addRow("Mes:", self.cmb_mes)
        form.addRow("Precio Menú Policial:", self.spin_precio)

        layout.addLayout(form)

        info_lbl = QLabel("ℹ️ Al crear el mes, se inicializarán los días y se cargarán automáticamente los policías activos.")
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color: #595959; font-size: 11px; padding: 4px;")
        layout.addWidget(info_lbl)

        btn_box = QHBoxLayout()
        self.btn_guardar = QPushButton("Crear Mes")
        self.btn_guardar.setProperty("class", "PrimaryBtn")
        self.btn_guardar.clicked.connect(self.accept)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)

        btn_box.addStretch()
        btn_box.addWidget(self.btn_cancelar)
        btn_box.addWidget(self.btn_guardar)

        layout.addLayout(btn_box)

    def get_datos(self) -> tuple[int, int, float]:
        anio = self.spin_anio.value()
        mes = self.cmb_mes.currentData()
        precio = self.spin_precio.value()
        return anio, mes, precio
