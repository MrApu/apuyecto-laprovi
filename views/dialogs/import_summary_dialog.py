from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QGroupBox, QGridLayout
)
from typing import Dict, Any

class ImportSummaryDialog(QDialog):
    def __init__(self, parent=None, resumen: Dict[str, Any] = None):
        super().__init__(parent)
        self.resumen = resumen or {}
        self.setWindowTitle("Resumen de Importación")
        self.resize(550, 450)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        grp = QGroupBox("Resultados de la Importación")
        grid = QGridLayout(grp)
        grid.addWidget(QLabel("<b>Policías nuevos:</b>"), 0, 0)
        grid.addWidget(QLabel(str(self.resumen.get("policias_nuevos", 0))), 0, 1)

        grid.addWidget(QLabel("<b>Policías actualizados:</b>"), 0, 2)
        grid.addWidget(QLabel(str(self.resumen.get("policias_actualizados", 0))), 0, 3)

        grid.addWidget(QLabel("<b>Meses importados:</b>"), 1, 0)
        grid.addWidget(QLabel(str(self.resumen.get("meses_importados", 0))), 1, 1)

        grid.addWidget(QLabel("<b>Registros de tickets:</b>"), 1, 2)
        grid.addWidget(QLabel(str(self.resumen.get("registros_tickets", 0))), 1, 3)

        grid.addWidget(QLabel("<b>Registros de calendario:</b>"), 2, 0)
        grid.addWidget(QLabel(str(self.resumen.get("registros_calendario", 0))), 2, 1)

        grid.addWidget(QLabel("<b>Registros de ventas:</b>"), 2, 2)
        grid.addWidget(QLabel(str(self.resumen.get("registros_ventas", 0))), 2, 3)

        layout.addWidget(grp)

        # Advertencias & Discrepancias
        adverts = self.resumen.get("advertencias", [])
        discreps = self.resumen.get("discrepancias", [])

        if adverts or discreps:
            layout.addWidget(QLabel("<b>Detalles de validación y discrepancias:</b>"))
            txt = QTextEdit()
            txt.setReadOnly(True)
            log_lines = []
            if discreps:
                log_lines.append("--- DISCREPANCIAS ENCONTRADAS (RECALCULADAS AUTOMÁTICAMENTE) ---")
                log_lines.extend(discreps)
            if adverts:
                log_lines.append("\n--- ADVERTENCIAS ---")
                log_lines.extend(adverts)
            txt.setPlainText("\n".join(log_lines))
            layout.addWidget(txt)
        else:
            lbl_ok = QLabel("✅ Todos los registros fueron procesados y validados con total consistencia.")
            lbl_ok.setStyleSheet("color: green; font-weight: bold; padding: 10px;")
            layout.addWidget(lbl_ok)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_ok = QPushButton("Aceptar")
        btn_ok.setProperty("class", "PrimaryBtn")
        btn_ok.clicked.connect(self.accept)
        btn_box.addWidget(btn_ok)
        layout.addLayout(btn_box)
