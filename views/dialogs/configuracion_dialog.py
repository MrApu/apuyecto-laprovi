from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDoubleSpinBox, QTextEdit, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from repositories.configuracion_repository import ConfiguracionRepository
from views.components.toast import ToastManager

class ConfiguracionPolicialDialog(QDialog):
    """
    Ventana emergente para configurar parámetros del servicio policial:
    - Precio del Menú Policial Estándar (S/).
    - Registro de motivo para trazabilidad y auditoría.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_repo = ConfiguracionRepository()
        self.setWindowTitle("⚙️ Configuración del Servicio Policial")
        self.resize(460, 320)
        self.setModal(True)
        self._init_ui()
        self._cargar_datos()

    def _init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0B0F19;
                color: #F8FAFC;
            }
            QFrame.Card {
                background-color: #111827;
                border: 1px solid #1F2937;
                border-radius: 10px;
                padding: 14px;
            }
            QLabel.Title {
                color: #38BDF8;
                font-size: 16px;
                font-weight: 800;
            }
            QDoubleSpinBox {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 6px;
                color: #38BDF8;
                font-size: 18px;
                font-weight: bold;
                padding: 6px 32px 6px 12px;
                min-height: 38px;
            }
            QDoubleSpinBox:focus {
                border: 1px solid #38BDF8;
                background-color: #0F172A;
            }
            QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 28px;
                height: 18px;
                border-left: 1px solid #374151;
                border-bottom: 1px solid #374151;
                border-top-right-radius: 5px;
                background-color: #1E293B;
            }
            QDoubleSpinBox::up-button:hover {
                background-color: #38BDF8;
            }
            QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 28px;
                height: 18px;
                border-left: 1px solid #374151;
                border-top: 1px solid #374151;
                border-bottom-right-radius: 5px;
                background-color: #1E293B;
            }
            QDoubleSpinBox::down-button:hover {
                background-color: #38BDF8;
            }
            QTextEdit {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 6px;
                color: #F8FAFC;
                font-size: 12px;
                padding: 8px;
            }
            QTextEdit:focus {
                border: 1px solid #38BDF8;
                background-color: #0F172A;
            }
            QPushButton.QuickPrice {
                background-color: #1E293B;
                border: 1px solid #334155;
                color: #E2E8F0;
                font-size: 11px;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton.QuickPrice:hover {
                background-color: #38BDF8;
                color: #0B0F19;
                border-color: #38BDF8;
            }
            QPushButton.PrimaryBtn {
                background-color: #0284C7;
                color: white;
                font-weight: 800;
                font-size: 13px;
                border-radius: 6px;
                padding: 10px 18px;
                border: none;
            }
            QPushButton.PrimaryBtn:hover {
                background-color: #0369A1;
            }
            QPushButton.CancelBtn {
                background-color: #1F2937;
                color: #94A3B8;
                font-weight: bold;
                font-size: 13px;
                border-radius: 6px;
                padding: 10px 14px;
                border: 1px solid #374151;
            }
            QPushButton.CancelBtn:hover {
                background-color: #374151;
                color: #F8FAFC;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header
        top_h = QHBoxLayout()
        lbl_icon = QLabel("⚙️")
        lbl_icon.setFont(QFont("Segoe UI Emoji", 20))
        top_h.addWidget(lbl_icon)

        v_titles = QVBoxLayout()
        lbl_title = QLabel("Configuración de Tarifa Policial")
        lbl_title.setProperty("class", "Title")
        lbl_sub = QLabel("Actualice el precio por menú para el cálculo de facturación.")
        lbl_sub.setStyleSheet("color: #94A3B8; font-size: 11px;")
        v_titles.addWidget(lbl_title)
        v_titles.addWidget(lbl_sub)
        top_h.addLayout(v_titles)
        top_h.addStretch()
        layout.addLayout(top_h)

        # Card
        card = QFrame()
        card.setProperty("class", "Card")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(10)

        # Price row with Quick buttons
        lbl_p = QLabel("💵 Precio Menú Policial Unitario (S/):")
        lbl_p.setStyleSheet("color: #E2E8F0; font-size: 13px; font-weight: bold;")
        c_layout.addWidget(lbl_p)

        h_spin = QHBoxLayout()
        self.spin_precio = QDoubleSpinBox()
        self.spin_precio.setRange(1.0, 500.0)
        self.spin_precio.setDecimals(2)
        self.spin_precio.setPrefix("S/ ")
        h_spin.addWidget(self.spin_precio, 2)

        for p_val in [12.0, 13.0, 14.0, 15.0]:
            btn = QPushButton(f"S/ {p_val:.0f}")
            btn.setProperty("class", "QuickPrice")
            btn.clicked.connect(lambda _, v=p_val: self.spin_precio.setValue(v))
            h_spin.addWidget(btn)

        c_layout.addLayout(h_spin)

        # Motivo audit
        lbl_m = QLabel("📝 Motivo del cambio (para trazabilidad / auditoría):")
        lbl_m.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: bold;")
        c_layout.addWidget(lbl_m)

        self.txt_motivo = QTextEdit()
        self.txt_motivo.setPlaceholderText("Ej: Actualización de tarifa acordada para el nuevo periodo...")
        self.txt_motivo.setMaximumHeight(65)
        c_layout.addWidget(self.txt_motivo)

        info_lbl = QLabel("ℹ️ <b>Nota:</b> El cambio aplicará a las liquidaciones policiales del periodo activo.")
        info_lbl.setStyleSheet("color: #64748B; font-size: 11px;")
        c_layout.addWidget(info_lbl)

        layout.addWidget(card)

        # Buttons
        b_layout = QHBoxLayout()
        btn_canc = QPushButton("Cancelar")
        btn_canc.setProperty("class", "CancelBtn")
        btn_canc.clicked.connect(self.reject)
        b_layout.addWidget(btn_canc)

        b_layout.addStretch()

        btn_save = QPushButton("💾 Guardar Configuración")
        btn_save.setProperty("class", "PrimaryBtn")
        btn_save.clicked.connect(self._on_guardar)
        b_layout.addWidget(btn_save)

        layout.addLayout(b_layout)

    def _cargar_datos(self):
        precio = self.config_repo.get_float("precio_menu_policial", 15.0)
        self.spin_precio.setValue(precio)

    def _on_guardar(self):
        nuevo_precio = self.spin_precio.value()
        motivo = self.txt_motivo.toPlainText().strip() or "Actualización desde Calendario Policial"
        self.config_repo.set_valor("precio_menu_policial", str(nuevo_precio), usuario="USUARIO", motivo=motivo)
        if self.parent():
            ToastManager.show_success(f"Tarifa policial actualizada a S/ {nuevo_precio:.2f}", self.parent())
        self.accept()
