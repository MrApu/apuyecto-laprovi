from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QSpinBox, QLineEdit, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from typing import Optional, List, Dict
from models.vale import Vale
from services.vale_service import ValeService
from services.ticket_service import TicketService
from views.components.toast import ToastManager
from views.dialogs.vale_dialog import ValeRapidoDialog

class ValesView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vale_service = ValeService()
        self.ticket_service = TicketService()
        self.current_anio = 2026
        self.current_mes = 9
        self.vales: List[Vale] = []
        self.vales_map: Dict[str, Vale] = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header_box = QHBoxLayout()
        self.lbl_title = QLabel("🎟️ Control de Vales Policiales")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #38BDF8;")
        header_box.addWidget(self.lbl_title)
        header_box.addStretch()

        self.btn_guardar_todo = QPushButton("💾 Guardar Cambios en Lote")
        self.btn_guardar_todo.setProperty("class", "PrimaryBtn")
        self.btn_guardar_todo.clicked.connect(self._on_guardar_todo)
        header_box.addWidget(self.btn_guardar_todo)

        layout.addLayout(header_box)

        # KPI Summary Cards (Tremor Style)
        kpi_row = QHBoxLayout()
        self.card_entregados = self._create_kpi_card("VALES ENTREGADOS", "0", "#F59E0B", "📤")
        self.card_canjeados = self._create_kpi_card("VALES CANJEADOS", "0", "#10B981", "📥")
        self.card_saldo = self._create_kpi_card("SALDO EN CIRCULACIÓN", "0", "#38BDF8", "⚖️")

        kpi_row.addWidget(self.card_entregados)
        kpi_row.addWidget(self.card_canjeados)
        kpi_row.addWidget(self.card_saldo)
        layout.addLayout(kpi_row)

        # Rules & Hint Banner
        info_banner = QLabel("💡 <b>Tip ágil:</b> Haga <b>doble clic</b> en cualquier fecha para abrir la ventana emergente con botones rápidos (+1, +5, +10) sin usar flechas.")
        info_banner.setStyleSheet("background-color: #0F172A; color: #38BDF8; padding: 10px 14px; border-radius: 8px; border: 1px solid #1E293B;")
        layout.addWidget(info_banner)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Fecha", "Vales Entregados", "Vales Canjeados", "Saldo Calculado", "Observaciones"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        layout.addWidget(self.table)

    def _create_kpi_card(self, title: str, value: str, color: str, icon: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"""
            QWidget {{
                background-color: #0F172A;
                border-left: 4px solid {color};
                border-radius: 8px;
            }}
        """)
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 8, 12, 8)
        l.setSpacing(2)

        top_h = QHBoxLayout()
        lbl_t = QLabel(f"{icon} {title}")
        lbl_t.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        top_h.addWidget(lbl_t)
        top_h.addStretch()
        l.addLayout(top_h)

        lbl_v = QLabel(value)
        lbl_v.setObjectName("val")
        lbl_v.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: 900;")
        l.addWidget(lbl_v)
        return w

    def _update_kpi(self, card: QWidget, value: str, is_negative: bool = False):
        lbl = card.findChild(QLabel, "val")
        if lbl:
            lbl.setText(value)
            if is_negative:
                lbl.setStyleSheet("color: #F43F5E; font-size: 18px; font-weight: 900;")
            else:
                lbl.setStyleSheet("color: #10B981; font-size: 18px; font-weight: 900;")

    def set_periodo(self, anio: int, mes: int):
        self.current_anio = anio
        self.current_mes = mes
        self.lbl_title.setText(f"🎟️ Control de Vales Policiales — {mes:02d}/{anio}")
        self.cargar_datos()

    def cargar_datos(self):
        diarios = self.ticket_service.get_calendario_mes(self.current_anio, self.current_mes)
        vales_existentes = {v.fecha: v for v in self.vale_service.get_by_mes(self.current_anio, self.current_mes)}
        self.vales_map = vales_existentes

        self.table.setRowCount(len(diarios))
        self.widgets = {}

        for r, td in enumerate(diarios):
            fecha = td.fecha
            v = vales_existentes.get(fecha, Vale(fecha=fecha, vales_entregados=td.vales_policiales, vales_canjeados=0))
            self.vales_map[fecha] = v

            self.table.setItem(r, 0, QTableWidgetItem(fecha))

            sb_ent = QSpinBox()
            sb_ent.setRange(0, 9999)
            sb_ent.setValue(v.vales_entregados)
            sb_ent.valueChanged.connect(lambda _, row=r: self._on_value_changed(row))
            self.table.setCellWidget(r, 1, sb_ent)

            sb_canj = QSpinBox()
            sb_canj.setRange(0, 9999)
            sb_canj.setValue(v.vales_canjeados)
            sb_canj.valueChanged.connect(lambda _, row=r: self._on_value_changed(row))
            self.table.setCellWidget(r, 2, sb_canj)

            saldo_item = QTableWidgetItem(str(v.saldo))
            saldo_item.setTextAlignment(Qt.AlignCenter)
            saldo_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            if v.saldo < 0:
                saldo_item.setForeground(Qt.red)
            else:
                saldo_item.setForeground(Qt.green)
            self.table.setItem(r, 3, saldo_item)

            txt_obs = QLineEdit()
            if v.observacion:
                txt_obs.setText(v.observacion)
            self.table.setCellWidget(r, 4, txt_obs)

            self.widgets[r] = {
                "fecha": fecha,
                "entregados": sb_ent,
                "canjeados": sb_canj,
                "obs": txt_obs
            }

        self._recalcular_resumen()

    def _on_value_changed(self, row: int):
        w = self.widgets.get(row)
        if w:
            ent = w["entregados"].value()
            canj = w["canjeados"].value()
            saldo = ent - canj
            saldo_item = self.table.item(row, 3)
            if saldo_item:
                saldo_item.setText(str(saldo))
                if saldo < 0:
                    saldo_item.setForeground(Qt.red)
                else:
                    saldo_item.setForeground(Qt.green)
        self._recalcular_resumen()

    def _recalcular_resumen(self):
        tot_ent = 0
        tot_canj = 0
        for r, w in self.widgets.items():
            tot_ent += w["entregados"].value()
            tot_canj += w["canjeados"].value()
        saldo_tot = tot_ent - tot_canj

        lbl_ent = self.card_entregados.findChild(QLabel, "val")
        if lbl_ent:
            lbl_ent.setText(f"{tot_ent:,}")

        lbl_canj = self.card_canjeados.findChild(QLabel, "val")
        if lbl_canj:
            lbl_canj.setText(f"{tot_canj:,}")

        self._update_kpi(self.card_saldo, f"{saldo_tot:,}", is_negative=(saldo_tot < 0))

    def _on_cell_double_clicked(self, row: int, col: int):
        item_fecha = self.table.item(row, 0)
        if not item_fecha:
            return
        fecha_str = item_fecha.text()
        self._abrir_dialogo_vale(fecha_str)

    def _abrir_dialogo_vale(self, fecha_str: str):
        v = self.vales_map.get(fecha_str)
        if not v:
            v = Vale(fecha=fecha_str, vales_entregados=0, vales_canjeados=0)

        # Check if there is next row
        fechas = sorted(list(self.vales_map.keys()))
        tiene_sig = False
        if fecha_str in fechas:
            idx = fechas.index(fecha_str)
            tiene_sig = idx < len(fechas) - 1

        def _on_save(val_mod: Vale):
            self.vale_service.guardar_vale(
                val_mod.fecha,
                val_mod.vales_entregados,
                val_mod.vales_canjeados,
                val_mod.observacion
            )
            ToastManager.show_success(f"Vales de {val_mod.fecha} guardados (Saldo: {val_mod.saldo})", self)
            self.cargar_datos()

        dlg = ValeRapidoDialog(
            vale=v,
            parent=self,
            on_save_callback=_on_save,
            tiene_siguiente=tiene_sig
        )

        dlg.siguiente_dia_solicitado.connect(self._abrir_siguiente_vale)
        dlg.exec()

    def _abrir_siguiente_vale(self, fecha_actual: str):
        fechas = sorted(list(self.vales_map.keys()))
        if fecha_actual in fechas:
            idx = fechas.index(fecha_actual)
            if idx < len(fechas) - 1:
                self._abrir_dialogo_vale(fechas[idx + 1])

    def _on_guardar_todo(self):
        guardados = 0
        negativos = 0
        for r, w in self.widgets.items():
            fecha = w["fecha"]
            ent = w["entregados"].value()
            canj = w["canjeados"].value()
            obs = w["obs"].text().strip() or None

            ok, msg, v = self.vale_service.guardar_vale(fecha, ent, canj, obs)
            if v.saldo < 0:
                negativos += 1
            guardados += 1

        msg = f"Se guardaron correctamente los registros de vales de {guardados} días."
        if negativos > 0:
            msg += f"\n⚠️ Atención: {negativos} fecha(s) presentan saldo negativo."
        ToastManager.show_success(msg, self)
        self.cargar_datos()
