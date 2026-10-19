from typing import Optional, Callable
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QLineEdit, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from models.vale import Vale
from models.ticket import DIAS_SEMANA_ES

class ValeRapidoDialog(QDialog):
    """
    Diálogo emergente moderno y ágil para registrar vales policiales:
    - Vales Entregados (con botones rápidos +1, +5, +10, -1).
    - Vales Canjeados (con botones rápidos +1, +5, +10, -1).
    - Cálculo de Saldo en vivo con alerta de saldo negativo.
    - Navegación secuencial: 'Guardar y Siguiente ▶'.
    """
    guardado = Signal(Vale)
    siguiente_dia_solicitado = Signal(str)

    def __init__(self, vale: Vale, parent=None, on_save_callback: Optional[Callable] = None, tiene_siguiente: bool = False):
        super().__init__(parent)
        self.vale = vale
        self.on_save_callback = on_save_callback
        self.tiene_siguiente = tiene_siguiente
        self.setWindowTitle(f"🎟️ Control de Vales — {vale.fecha}")
        self.resize(480, 500)
        self.setModal(True)
        self._init_ui()
        self._cargar_datos()

    def _init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0B0F19;
                color: #F8FAFC;
            }
            QFrame.CardSection {
                background-color: #111827;
                border: 1px solid #1F2937;
                border-radius: 10px;
                padding: 14px;
            }
            QSpinBox {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 6px;
                color: #F8FAFC;
                font-size: 18px;
                font-weight: bold;
                padding: 6px 32px 6px 12px;
                min-height: 38px;
            }
            QSpinBox:focus {
                border: 1px solid #38BDF8;
                background-color: #0F172A;
            }
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 28px;
                height: 18px;
                border-left: 1px solid #374151;
                border-bottom: 1px solid #374151;
                border-top-right-radius: 5px;
                background-color: #1E293B;
            }
            QSpinBox::up-button:hover {
                background-color: #38BDF8;
            }
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 28px;
                height: 18px;
                border-left: 1px solid #374151;
                border-top: 1px solid #374151;
                border-bottom-right-radius: 5px;
                background-color: #1E293B;
            }
            QSpinBox::down-button:hover {
                background-color: #38BDF8;
            }
            QLineEdit {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 6px;
                color: #F8FAFC;
                font-size: 13px;
                padding: 8px 12px;
            }
            QLineEdit:focus {
                border: 1px solid #38BDF8;
                background-color: #0F172A;
            }
            QPushButton.QuickBtn {
                background-color: #1E293B;
                border: 1px solid #374151;
                border-radius: 4px;
                color: #E2E8F0;
                font-size: 11px;
                font-weight: bold;
                padding: 4px 8px;
                min-width: 34px;
            }
            QPushButton.QuickBtn:hover {
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
            QPushButton.NextBtn {
                background-color: #4F46E5;
                color: white;
                font-weight: 800;
                font-size: 13px;
                border-radius: 6px;
                padding: 10px 16px;
                border: none;
            }
            QPushButton.NextBtn:hover {
                background-color: #4338CA;
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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        h_box = QHBoxLayout()
        icon_lbl = QLabel("🎟️")
        icon_lbl.setFont(QFont("Segoe UI Emoji", 24))
        h_box.addWidget(icon_lbl)

        v_titles = QVBoxLayout()
        self.lbl_fecha = QLabel()
        self.lbl_fecha.setStyleSheet("font-size: 16px; font-weight: 900; color: #38BDF8;")
        self.lbl_sub = QLabel("Registro diario de vales entregados y canjeados")
        self.lbl_sub.setStyleSheet("font-size: 12px; color: #94A3B8;")
        v_titles.addWidget(self.lbl_fecha)
        v_titles.addWidget(self.lbl_sub)
        h_box.addLayout(v_titles)
        h_box.addStretch()
        layout.addLayout(h_box)

        # Saldo Live Card
        self.saldo_card = QFrame()
        self.saldo_card.setStyleSheet("background: #0F172A; border: 1px solid #334155; border-radius: 8px; padding: 10px;")
        s_layout = QHBoxLayout(self.saldo_card)
        s_layout.setContentsMargins(12, 6, 12, 6)

        lbl_s_text = QLabel("SALDO CALCULADO (ENTREGADOS - CANJEADOS):")
        lbl_s_text.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        self.lbl_saldo_val = QLabel("0")
        self.lbl_saldo_val.setStyleSheet("color: #10B981; font-size: 24px; font-weight: 900;")

        s_layout.addWidget(lbl_s_text)
        s_layout.addStretch()
        s_layout.addWidget(self.lbl_saldo_val)
        layout.addWidget(self.saldo_card)

        # Form Card
        card = QFrame()
        card.setProperty("class", "CardSection")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(12)

        # 1. Vales Entregados
        sec1 = QVBoxLayout()
        h_ent = QHBoxLayout()
        lbl_ent = QLabel("📤 Vales Entregados:")
        lbl_ent.setStyleSheet("color: #E2E8F0; font-size: 13px; font-weight: bold;")
        h_ent.addWidget(lbl_ent)
        h_ent.addStretch()

        for delta in [1, 5, 10]:
            b = QPushButton(f"+{delta}")
            b.setProperty("class", "QuickBtn")
            b.clicked.connect(lambda _, d=delta: self._add_entregados(d))
            h_ent.addWidget(b)
        b_dec_ent = QPushButton("-1")
        b_dec_ent.setProperty("class", "QuickBtn")
        b_dec_ent.clicked.connect(lambda: self._add_entregados(-1))
        h_ent.addWidget(b_dec_ent)

        sec1.addLayout(h_ent)
        self.spn_entregados = QSpinBox()
        self.spn_entregados.setRange(0, 9999)
        self.spn_entregados.valueChanged.connect(self._recalcular_saldo)
        sec1.addWidget(self.spn_entregados)
        c_layout.addLayout(sec1)

        # 2. Vales Canjeados
        sec2 = QVBoxLayout()
        h_canj = QHBoxLayout()
        lbl_canj = QLabel("📥 Vales Canjeados:")
        lbl_canj.setStyleSheet("color: #E2E8F0; font-size: 13px; font-weight: bold;")
        h_canj.addWidget(lbl_canj)
        h_canj.addStretch()

        for delta in [1, 5, 10]:
            b = QPushButton(f"+{delta}")
            b.setProperty("class", "QuickBtn")
            b.clicked.connect(lambda _, d=delta: self._add_canjeados(d))
            h_canj.addWidget(b)
        b_dec_canj = QPushButton("-1")
        b_dec_canj.setProperty("class", "QuickBtn")
        b_dec_canj.clicked.connect(lambda: self._add_canjeados(-1))
        h_canj.addWidget(b_dec_canj)

        sec2.addLayout(h_canj)
        self.spn_canjeados = QSpinBox()
        self.spn_canjeados.setRange(0, 9999)
        self.spn_canjeados.valueChanged.connect(self._recalcular_saldo)
        sec2.addWidget(self.spn_canjeados)
        c_layout.addLayout(sec2)

        # 3. Observaciones
        sec3 = QVBoxLayout()
        lbl_obs = QLabel("📝 Observaciones:")
        lbl_obs.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: bold;")
        sec3.addWidget(lbl_obs)
        self.txt_obs = QLineEdit()
        self.txt_obs.setPlaceholderText("Ej: Entrega a comisaría, canje turno mañana...")
        sec3.addWidget(self.txt_obs)
        c_layout.addLayout(sec3)

        layout.addWidget(card)

        # Buttons
        b_box = QHBoxLayout()
        btn_canc = QPushButton("Cancelar")
        btn_canc.setProperty("class", "CancelBtn")
        btn_canc.clicked.connect(self.reject)
        b_box.addWidget(btn_canc)

        b_box.addStretch()

        if self.tiene_siguiente:
            self.btn_next = QPushButton("💾 Guardar y Siguiente ▶")
            self.btn_next.setProperty("class", "NextBtn")
            self.btn_next.clicked.connect(self._on_guardar_siguiente)
            b_box.addWidget(self.btn_next)

        btn_save = QPushButton("💾 Guardar Vales")
        btn_save.setProperty("class", "PrimaryBtn")
        btn_save.clicked.connect(self._on_guardar_cerrar)
        b_box.addWidget(btn_save)

        layout.addLayout(b_box)

    def _cargar_datos(self):
        v = self.vale
        try:
            dt = datetime.strptime(v.fecha, "%Y-%m-%d")
            dia_str = DIAS_SEMANA_ES[dt.weekday()]
            meses_es = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            self.lbl_fecha.setText(f"{dia_str.upper()} {dt.day:02d} DE {meses_es[dt.month].upper()} {dt.year}")
        except Exception:
            self.lbl_fecha.setText(f"FECHA: {v.fecha}")

        self.spn_entregados.setValue(v.vales_entregados or 0)
        self.spn_canjeados.setValue(v.vales_canjeados or 0)
        self.txt_obs.setText(v.observacion or "")
        self._recalcular_saldo()

    def _add_entregados(self, delta: int):
        val = max(0, self.spn_entregados.value() + delta)
        self.spn_entregados.setValue(val)

    def _add_canjeados(self, delta: int):
        val = max(0, self.spn_canjeados.value() + delta)
        self.spn_canjeados.setValue(val)

    def _recalcular_saldo(self):
        ent = self.spn_entregados.value()
        canj = self.spn_canjeados.value()
        saldo = ent - canj
        self.lbl_saldo_val.setText(str(saldo))
        if saldo < 0:
            self.lbl_saldo_val.setStyleSheet("color: #F43F5E; font-size: 24px; font-weight: 900;")
            self.saldo_card.setStyleSheet("background: #2D060F; border: 1px solid #F43F5E; border-radius: 8px; padding: 10px;")
        else:
            self.lbl_saldo_val.setStyleSheet("color: #10B981; font-size: 24px; font-weight: 900;")
            self.saldo_card.setStyleSheet("background: #0F172A; border: 1px solid #334155; border-radius: 8px; padding: 10px;")

    def _obtener_vale_modificado(self) -> Vale:
        v = self.vale
        v.vales_entregados = self.spn_entregados.value()
        v.vales_canjeados = self.spn_canjeados.value()
        v.saldo = v.vales_entregados - v.vales_canjeados
        v.observacion = self.txt_obs.text().strip() or None
        return v

    def _on_guardar_cerrar(self):
        v = self._obtener_vale_modificado()
        if self.on_save_callback:
            self.on_save_callback(v)
        self.guardado.emit(v)
        self.accept()

    def _on_guardar_siguiente(self):
        v = self._obtener_vale_modificado()
        if self.on_save_callback:
            self.on_save_callback(v)
        self.guardado.emit(v)
        self.siguiente_dia_solicitado.emit(v.fecha)
        self.accept()
