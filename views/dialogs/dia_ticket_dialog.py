from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QLineEdit, QFrame, QMessageBox, QWidget, QGridLayout,
    QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from typing import Optional, Callable, Tuple
from models.ticket import TicketDiario, DIAS_SEMANA_ES
from models.vale import Vale
from datetime import datetime
import inspect

class DiaTicketDialog(QDialog):
    """
    Diálogo emergente moderno e interactivo para registrar y editar
    los tickets diarios de la policía (Para Unidad, Local) y el control
    integral de Vales Policiales (Vales entregados, Vales canjeados y Saldo restante).
    """
    guardado = Signal(TicketDiario)
    siguiente_dia_solicitado = Signal(str)  # Emite la fecha siguiente

    def __init__(
        self,
        ticket_diario: TicketDiario,
        vale: Optional[Vale] = None,
        parent=None,
        on_save_callback: Optional[Callable] = None,
        tiene_siguiente: bool = False
    ):
        super().__init__(parent)
        self.ticket_diario = ticket_diario
        self.vale = vale
        self.on_save_callback = on_save_callback
        self.tiene_siguiente = tiene_siguiente
        self.setWindowTitle(f"Control Diario de Tickets y Vales — {ticket_diario.fecha}")
        self.resize(540, 680)
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
                padding: 12px;
            }
            QLabel.SectionTitle {
                color: #94A3B8;
                font-size: 11px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            QSpinBox {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 6px;
                color: #F8FAFC;
                font-size: 18px;
                font-weight: bold;
                padding: 6px 32px 6px 10px;
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
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 4px;
                color: #E2E8F0;
                font-size: 11px;
                font-weight: bold;
                padding: 4px 8px;
                min-width: 32px;
            }
            QPushButton.QuickBtn:hover {
                background-color: #38BDF8;
                color: #0F172A;
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

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header with Date and Badge
        header_layout = QHBoxLayout()
        icon_lbl = QLabel("📅")
        icon_lbl.setFont(QFont("Segoe UI Emoji", 24))
        header_layout.addWidget(icon_lbl)

        title_vbox = QVBoxLayout()
        self.lbl_header_date = QLabel()
        self.lbl_header_date.setStyleSheet("font-size: 16px; font-weight: 900; color: #38BDF8;")
        self.lbl_header_sub = QLabel()
        self.lbl_header_sub.setStyleSheet("font-size: 12px; color: #94A3B8;")
        title_vbox.addWidget(self.lbl_header_date)
        title_vbox.addWidget(self.lbl_header_sub)
        header_layout.addLayout(title_vbox)
        header_layout.addStretch()

        self.lbl_sede_badge = QLabel("RESTAURANTE")
        self.lbl_sede_badge.setStyleSheet("background-color: #1E293B; color: #38BDF8; padding: 6px 12px; border-radius: 6px; font-weight: bold; font-size: 11px;")
        header_layout.addWidget(self.lbl_sede_badge)
        main_layout.addLayout(header_layout)

        # Live Total Banner
        self.total_card = QFrame()
        self.total_card.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E1B4B, stop:1 #0F172A); border: 1px solid #4338CA; border-radius: 8px; padding: 10px;")
        tot_layout = QHBoxLayout(self.total_card)
        tot_layout.setContentsMargins(12, 6, 12, 6)
        
        lbl_tot_text = QLabel("TOTAL TICKETS POLICIALES:")
        lbl_tot_text.setStyleSheet("color: #C7D2FE; font-size: 13px; font-weight: 800; letter-spacing: 0.5px;")
        self.lbl_total_value = QLabel("0")
        self.lbl_total_value.setStyleSheet("color: #38BDF8; font-size: 24px; font-weight: 900;")
        
        tot_layout.addWidget(lbl_tot_text)
        tot_layout.addStretch()
        tot_layout.addWidget(self.lbl_total_value)
        main_layout.addWidget(self.total_card)

        # Content Card
        card = QFrame()
        card.setProperty("class", "CardSection")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        # Row 1: Para Unidad
        sec1_layout = QVBoxLayout()
        h_u = QHBoxLayout()
        lbl_u = QLabel("👮 Tickets Para Unidad (*):")
        lbl_u.setStyleSheet("color: #E2E8F0; font-size: 13px; font-weight: bold;")
        h_u.addWidget(lbl_u)
        h_u.addStretch()
        
        for inc in [1, 5, 10]:
            btn = QPushButton(f"+{inc}")
            btn.setProperty("class", "QuickBtn")
            btn.clicked.connect(lambda _, delta=inc: self._add_unidad(delta))
            h_u.addWidget(btn)
        btn_dec_u = QPushButton("-1")
        btn_dec_u.setProperty("class", "QuickBtn")
        btn_dec_u.clicked.connect(lambda: self._add_unidad(-1))
        h_u.addWidget(btn_dec_u)

        sec1_layout.addLayout(h_u)
        self.spn_unidad = QSpinBox()
        self.spn_unidad.setRange(0, 9999)
        self.spn_unidad.valueChanged.connect(self._on_values_changed)
        sec1_layout.addWidget(self.spn_unidad)
        card_layout.addLayout(sec1_layout)

        # Row 2: En Local
        sec2_layout = QVBoxLayout()
        h_l = QHBoxLayout()
        lbl_l = QLabel("🍽️ Tickets en Local (*):")
        lbl_l.setStyleSheet("color: #E2E8F0; font-size: 13px; font-weight: bold;")
        h_l.addWidget(lbl_l)
        h_l.addStretch()

        for inc in [1, 5, 10]:
            btn = QPushButton(f"+{inc}")
            btn.setProperty("class", "QuickBtn")
            btn.clicked.connect(lambda _, delta=inc: self._add_local(delta))
            h_l.addWidget(btn)
        btn_dec_l = QPushButton("-1")
        btn_dec_l.setProperty("class", "QuickBtn")
        btn_dec_l.clicked.connect(lambda: self._add_local(-1))
        h_l.addWidget(btn_dec_l)

        sec2_layout.addLayout(h_l)
        self.spn_local = QSpinBox()
        self.spn_local.setRange(0, 9999)
        self.spn_local.valueChanged.connect(self._on_values_changed)
        sec2_layout.addWidget(self.spn_local)
        card_layout.addLayout(sec2_layout)

        # Row 3: Vales Policiales: Entregados vs Canjeados
        sec3_layout = QVBoxLayout()
        sec3_layout.setSpacing(6)

        lbl_v_header = QLabel("🎟️ Control de Vales: Entregados vs Canjeados:")
        lbl_v_header.setStyleSheet("color: #F8FAFC; font-size: 13px; font-weight: 800; border-top: 1px dashed #334155; padding-top: 8px;")
        sec3_layout.addWidget(lbl_v_header)

        # 3A: Vales Entregados
        h_vent = QHBoxLayout()
        lbl_vent = QLabel("📤 Vales Entregados a la Unidad:")
        lbl_vent.setStyleSheet("color: #F59E0B; font-size: 12px; font-weight: bold;")
        h_vent.addWidget(lbl_vent)
        h_vent.addStretch()
        for inc in [1, 5, 10]:
            btn = QPushButton(f"+{inc}")
            btn.setProperty("class", "QuickBtn")
            btn.clicked.connect(lambda _, delta=inc: self._add_vales_entregados(delta))
            h_vent.addWidget(btn)
        btn_dec_vent = QPushButton("-1")
        btn_dec_vent.setProperty("class", "QuickBtn")
        btn_dec_vent.clicked.connect(lambda: self._add_vales_entregados(-1))
        h_vent.addWidget(btn_dec_vent)
        sec3_layout.addLayout(h_vent)

        self.spn_vales_entregados = QSpinBox()
        self.spn_vales_entregados.setRange(0, 9999)
        self.spn_vales_entregados.valueChanged.connect(self._on_values_changed)
        sec3_layout.addWidget(self.spn_vales_entregados)

        # 3B: Vales Canjeados / Consumidos
        h_vcanj = QHBoxLayout()
        lbl_vcanj = QLabel("📥 Vales Canjeados / Consumidos en el Día:")
        lbl_vcanj.setStyleSheet("color: #10B981; font-size: 12px; font-weight: bold;")
        h_vcanj.addWidget(lbl_vcanj)
        h_vcanj.addStretch()
        for inc in [1, 5, 10]:
            btn = QPushButton(f"+{inc}")
            btn.setProperty("class", "QuickBtn")
            btn.clicked.connect(lambda _, delta=inc: self._add_vales_canjeados(delta))
            h_vcanj.addWidget(btn)
        btn_dec_vcanj = QPushButton("-1")
        btn_dec_vcanj.setProperty("class", "QuickBtn")
        btn_dec_vcanj.clicked.connect(lambda: self._add_vales_canjeados(-1))
        h_vcanj.addWidget(btn_dec_vcanj)
        sec3_layout.addLayout(h_vcanj)

        self.spn_vales_canjeados = QSpinBox()
        self.spn_vales_canjeados.setRange(0, 9999)
        self.spn_vales_canjeados.valueChanged.connect(self._on_values_changed)
        sec3_layout.addWidget(self.spn_vales_canjeados)

        # Alias for backward compatibility
        self.spn_vales = self.spn_vales_canjeados

        # 3C: Live Banner Saldo de Vales
        self.vales_saldo_card = QFrame()
        self.vales_saldo_card.setStyleSheet("background: #0F172A; border: 1px solid #1E293B; border-radius: 6px; padding: 6px;")
        h_val_saldo = QHBoxLayout(self.vales_saldo_card)
        h_val_saldo.setContentsMargins(8, 4, 8, 4)
        lbl_val_saldo_title = QLabel("⚖️ VALES RESTANTES:")
        lbl_val_saldo_title.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 800;")
        self.lbl_saldo_vales_value = QLabel("0 al día")
        self.lbl_saldo_vales_value.setStyleSheet("color: #10B981; font-size: 13px; font-weight: 900;")
        h_val_saldo.addWidget(lbl_val_saldo_title)
        h_val_saldo.addStretch()
        h_val_saldo.addWidget(self.lbl_saldo_vales_value)
        sec3_layout.addWidget(self.vales_saldo_card)

        card_layout.addLayout(sec3_layout)

        # Row 4: Observación
        sec4_layout = QVBoxLayout()
        lbl_obs = QLabel("📝 Observación / Novedad del día:")
        lbl_obs.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: bold;")
        sec4_layout.addWidget(lbl_obs)
        self.txt_obs = QLineEdit()
        self.txt_obs.setPlaceholderText("Ej. Guardia nocturna, comisión especial, etc.")
        sec4_layout.addWidget(self.txt_obs)
        card_layout.addLayout(sec4_layout)

        # Row 5: Motivo de ajuste (si aplica)
        sec5_layout = QVBoxLayout()
        lbl_motivo = QLabel("💡 Motivo de ajuste (Opcional para auditoría):")
        lbl_motivo.setStyleSheet("color: #64748B; font-size: 11px;")
        sec5_layout.addWidget(lbl_motivo)
        self.txt_motivo = QLineEdit()
        self.txt_motivo.setPlaceholderText("Dejar vacío si es registro regular.")
        sec5_layout.addWidget(self.txt_motivo)
        card_layout.addLayout(sec5_layout)

        main_layout.addWidget(card)

        # Footer Buttons
        btn_layout = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setProperty("class", "CancelBtn")
        self.btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancelar)

        btn_layout.addStretch()

        if self.tiene_siguiente:
            self.btn_siguiente = QPushButton("💾 Guardar y Siguiente ▶")
            self.btn_siguiente.setProperty("class", "NextBtn")
            self.btn_siguiente.clicked.connect(self._on_guardar_y_siguiente)
            btn_layout.addWidget(self.btn_siguiente)

        self.btn_guardar = QPushButton("💾 Guardar Cambios")
        self.btn_guardar.setProperty("class", "PrimaryBtn")
        self.btn_guardar.clicked.connect(self._on_guardar_y_cerrar)
        btn_layout.addWidget(self.btn_guardar)

        main_layout.addLayout(btn_layout)

    def _cargar_datos(self):
        td = self.ticket_diario
        vl = self.vale
        try:
            dt = datetime.strptime(td.fecha, "%Y-%m-%d")
            dia_str = DIAS_SEMANA_ES[dt.weekday()]
            meses_es = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            fecha_bonita = f"{dia_str.upper()} {dt.day:02d} DE {meses_es[dt.month].upper()} {dt.year}"
            self.lbl_header_date.setText(fecha_bonita)
            self.lbl_header_sub.setText(f"Fecha ISO: {td.fecha} | Día {dt.day} de {calendar_month_name(dt.month, dt.year)}")
        except Exception:
            self.lbl_header_date.setText(f"{td.dia_semana.upper()} {td.fecha}")
            self.lbl_header_sub.setText(f"Fecha: {td.fecha}")

        self.lbl_sede_badge.setText((td.local_id or "RESTAURANTE").upper())
        self.spn_unidad.setValue(td.para_unidad or 0)
        self.spn_local.setValue(td.local or 0)

        # Cargar vales entregados y canjeados
        val_ent = vl.vales_entregados if vl else 0
        val_canj = vl.vales_consumidos if vl else (td.vales_policiales or 0)
        self.spn_vales_entregados.setValue(val_ent)
        self.spn_vales_canjeados.setValue(val_canj)

        self.txt_obs.setText(td.observacion or (vl.observacion if vl else "") or "")
        self._on_values_changed()

    def _add_unidad(self, delta: int):
        val = max(0, self.spn_unidad.value() + delta)
        self.spn_unidad.setValue(val)

    def _add_local(self, delta: int):
        val = max(0, self.spn_local.value() + delta)
        self.spn_local.setValue(val)

    def _add_vales_entregados(self, delta: int):
        val = max(0, self.spn_vales_entregados.value() + delta)
        self.spn_vales_entregados.setValue(val)

    def _add_vales_canjeados(self, delta: int):
        val = max(0, self.spn_vales_canjeados.value() + delta)
        self.spn_vales_canjeados.setValue(val)

    def _add_vales(self, delta: int):
        self._add_vales_canjeados(delta)

    def _on_values_changed(self):
        u = self.spn_unidad.value()
        l = self.spn_local.value()
        tot = u + l
        self.lbl_total_value.setText(str(tot))

        # Balance de vales
        v_ent = self.spn_vales_entregados.value()
        v_canj = self.spn_vales_canjeados.value()
        saldo_vales = v_ent - v_canj

        if saldo_vales > 0:
            self.lbl_saldo_vales_value.setText(f"{saldo_vales} vales pendientes de canje")
            self.lbl_saldo_vales_value.setStyleSheet("color: #38BDF8; font-size: 13px; font-weight: 900;")
        elif saldo_vales == 0:
            self.lbl_saldo_vales_value.setText("0 (Vales al día)")
            self.lbl_saldo_vales_value.setStyleSheet("color: #10B981; font-size: 13px; font-weight: 900;")
        else:
            self.lbl_saldo_vales_value.setText(f"⚠️ Sobrecange: {abs(saldo_vales)} canjeados de más")
            self.lbl_saldo_vales_value.setStyleSheet("color: #F43F5E; font-size: 13px; font-weight: 900;")

    def _obtener_ticket_modificado(self) -> TicketDiario:
        td = self.ticket_diario
        u = self.spn_unidad.value()
        l = self.spn_local.value()
        v_canj = self.spn_vales_canjeados.value()
        obs = self.txt_obs.text().strip() or None
        
        td.para_unidad = u
        td.local = l
        td.total_policias = u + l
        td.vales_policiales = v_canj
        td.observacion = obs
        return td

    def get_motivo_ajuste(self) -> Optional[str]:
        return self.txt_motivo.text().strip() or None

    def get_ticket_diario(self) -> TicketDiario:
        return self._obtener_ticket_modificado()

    def get_vales_data(self) -> Tuple[int, int, int]:
        ent = self.spn_vales_entregados.value()
        canj = self.spn_vales_canjeados.value()
        return ent, canj, ent - canj

    def _ejecutar_guardado(self):
        td = self._obtener_ticket_modificado()
        if self.on_save_callback:
            sig = inspect.signature(self.on_save_callback)
            if len(sig.parameters) >= 4:
                self.on_save_callback(
                    td,
                    self.spn_vales_entregados.value(),
                    self.spn_vales_canjeados.value(),
                    self.get_motivo_ajuste()
                )
            else:
                self.on_save_callback(td, self.get_motivo_ajuste())
        self.guardado.emit(td)

    def _on_guardar_y_cerrar(self):
        self._ejecutar_guardado()
        self.accept()

    def _on_guardar_y_siguiente(self):
        td = self._obtener_ticket_modificado()
        self._ejecutar_guardado()
        self.siguiente_dia_solicitado.emit(td.fecha)
        self.accept()

def calendar_month_name(mes: int, anio: int) -> str:
    meses_es = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    return f"{meses_es[mes]} {anio}"
