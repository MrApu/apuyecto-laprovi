from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QLineEdit, QTabWidget,
    QMessageBox, QDateEdit, QDoubleSpinBox, QDialog, QFormLayout,
    QDialogButtonBox, QSpinBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFont
from datetime import datetime
from typing import Optional

from services.egreso_service import EgresoService
from services.mes_service import MesService
from models.compra import Compra
from models.gasto import Gasto
from models.pago_personal import PagoPersonal
from models.local import LOCAL_RESTAURANTE, LOCAL_FAST_FOOD, LOCAL_CONSOLIDADO, LOCAL_NAMES
from views.components.toast import ToastManager
from views.dialogs.compra_dialog import CompraSimpleDialog

class EgresosView(QWidget):
    def __init__(self, egreso_service: Optional[EgresoService] = None, mes_service: Optional[MesService] = None, parent=None):
        super().__init__(parent)
        self.egreso_service = egreso_service or EgresoService()
        self.mes_service = mes_service or MesService()
        self.current_local = LOCAL_RESTAURANTE
        self.current_year = 2026
        self.current_month = 9
        self._init_ui()

    def set_local(self, local_id: str):
        self.current_local = local_id
        self.lbl_local_badge.setText(f"Local: {LOCAL_NAMES.get(local_id, local_id.upper())}")
        self.refresh_data()

    def set_periodo(self, anio: int, mes: int):
        self.current_year = anio
        self.current_month = mes
        self.refresh_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Header bar
        header = QHBoxLayout()
        title = QLabel("💰 GESTIÓN DE EGRESOS")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header.addWidget(title)

        self.lbl_local_badge = QLabel(f"Local: {LOCAL_NAMES.get(self.current_local, 'RESTAURANTE')}")
        self.lbl_local_badge.setStyleSheet("background: #1e293b; color: #38bdf8; padding: 4px 10px; border-radius: 4px; font-weight: bold;")
        header.addWidget(self.lbl_local_badge)

        header.addStretch()

        header.addWidget(QLabel("Período:"))
        self.combo_periodo = QComboBox()
        self.combo_periodo.currentIndexChanged.connect(self._on_periodo_changed)
        header.addWidget(self.combo_periodo)

        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.clicked.connect(self.refresh_data)
        header.addWidget(btn_refresh)

        layout.addLayout(header)

        # KPI Cards bar
        kpi_layout = QHBoxLayout()
        self.card_compras = self._create_kpi_card("Total Compras", "S/ 0.00", "#3b82f6")
        self.card_gastos = self._create_kpi_card("Total Gastos", "S/ 0.00", "#f59e0b")
        self.card_personal = self._create_kpi_card("Pagos al Personal", "S/ 0.00", "#8b5cf6")
        self.card_total = self._create_kpi_card("TOTAL EGRESOS", "S/ 0.00", "#ef4444")

        kpi_layout.addWidget(self.card_compras)
        kpi_layout.addWidget(self.card_gastos)
        kpi_layout.addWidget(self.card_personal)
        kpi_layout.addWidget(self.card_total)
        layout.addLayout(kpi_layout)

        # Tab Widget for 3 modules
        self.tabs = QTabWidget()
        self.tab_compras = self._build_compras_tab()
        self.tab_gastos = self._build_gastos_tab()
        self.tab_personal = self._build_personal_tab()

        self.tabs.addTab(self.tab_compras, "🛒 Compras / Insumos")
        self.tabs.addTab(self.tab_gastos, "🧾 Gastos Operativos")
        self.tabs.addTab(self.tab_personal, "👥 Pagos al Personal")
        layout.addWidget(self.tabs)

        self._load_periodos()

    def _create_kpi_card(self, title: str, value: str, border_color: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: #0f172a; border-left: 4px solid {border_color}; border-radius: 6px; padding: 8px;")
        l = QVBoxLayout(w)
        l.setContentsMargins(8, 6, 8, 6)
        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")
        lbl_v = QLabel(value)
        lbl_v.setObjectName("val")
        lbl_v.setStyleSheet(f"color: {border_color}; font-size: 16px; font-weight: bold;")
        l.addWidget(lbl_t)
        l.addWidget(lbl_v)
        return w

    def _update_kpi(self, card: QWidget, value: float):
        lbl = card.findChild(QLabel, "val")
        if lbl:
            lbl.setText(f"S/ {value:,.2f}")

    def _build_compras_tab(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        toolbar = QHBoxLayout()
        btn_add = QPushButton("➕ Registrar Compra / Insumo")
        btn_add.setStyleSheet("background: #0284c7; color: white; font-weight: bold; padding: 6px 14px; border-radius: 6px;")
        btn_add.clicked.connect(self._add_compra)
        toolbar.addWidget(btn_add)

        btn_edit = QPushButton("✏️ Editar Compra")
        btn_edit.setStyleSheet("background: #18181B; color: #FFFFFF; border: 1px solid #27272A; font-weight: bold; padding: 6px 14px; border-radius: 6px;")
        btn_edit.clicked.connect(self._edit_compra)
        toolbar.addWidget(btn_edit)

        btn_del = QPushButton("🗑️ Eliminar Compra")
        btn_del.setStyleSheet("background: #334155; color: #f87171; font-weight: bold; padding: 6px 12px; border-radius: 6px;")
        btn_del.clicked.connect(self._del_compra)
        toolbar.addWidget(btn_del)
        
        lbl_hint = QLabel("💡 Seleccione una compra y use 'Editar Compra' (o doble clic) para modificarla.")
        lbl_hint.setStyleSheet("color: #64748b; font-size: 11px; margin-left: 8px;")
        toolbar.addWidget(lbl_hint)
        
        toolbar.addStretch()
        l.addLayout(toolbar)

        self.tbl_compras = QTableWidget()
        self.tbl_compras.setColumnCount(7)
        self.tbl_compras.setHorizontalHeaderLabels([
            "ID", "Fecha", "Sede", "¿Qué se compró? (Detalle / Observación)", "Categoría", "Monto Gastado (S/)", "Medio Pago"
        ])
        self.tbl_compras.setColumnHidden(0, True)  # Ocultar ID interno
        self.tbl_compras.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tbl_compras.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tbl_compras.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_compras.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_compras.cellDoubleClicked.connect(self._on_compra_double_clicked)
        l.addWidget(self.tbl_compras)
        return w

    def _build_gastos_tab(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        toolbar = QHBoxLayout()
        btn_add = QPushButton("➕ Registrar Gasto")
        btn_add.setStyleSheet("background: #d97706; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
        btn_add.clicked.connect(self._add_gasto)
        toolbar.addWidget(btn_add)

        btn_edit = QPushButton("✏️ Editar Gasto")
        btn_edit.setStyleSheet("background: #18181B; color: #FFFFFF; border: 1px solid #27272A; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
        btn_edit.clicked.connect(self._edit_gasto)
        toolbar.addWidget(btn_edit)

        btn_del = QPushButton("🗑️ Eliminar Gasto")
        btn_del.clicked.connect(self._del_gasto)
        toolbar.addWidget(btn_del)
        toolbar.addStretch()
        l.addLayout(toolbar)

        self.tbl_gastos = QTableWidget()
        self.tbl_gastos.setColumnCount(7)
        self.tbl_gastos.setHorizontalHeaderLabels(["ID", "Fecha", "Local", "Categoría", "Descripción", "Monto", "Medio Pago"])
        self.tbl_gastos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_gastos.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_gastos.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_gastos.cellDoubleClicked.connect(lambda r, c: self._edit_gasto())
        l.addWidget(self.tbl_gastos)
        return w

    def _build_personal_tab(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        toolbar = QHBoxLayout()
        btn_add = QPushButton("➕ Registrar Pago a Personal")
        btn_add.setStyleSheet("background: #7c3aed; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
        btn_add.clicked.connect(self._add_personal)
        toolbar.addWidget(btn_add)

        btn_edit = QPushButton("✏️ Editar Pago")
        btn_edit.setStyleSheet("background: #18181B; color: #FFFFFF; border: 1px solid #27272A; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
        btn_edit.clicked.connect(self._edit_personal)
        toolbar.addWidget(btn_edit)

        btn_del = QPushButton("🗑️ Eliminar Pago")
        btn_del.clicked.connect(self._del_personal)
        toolbar.addWidget(btn_del)
        toolbar.addStretch()
        l.addLayout(toolbar)

        self.tbl_personal = QTableWidget()
        self.tbl_personal.setColumnCount(8)
        self.tbl_personal.setHorizontalHeaderLabels(["ID", "Fecha", "Local", "Trabajador", "Cargo", "Concepto", "Monto", "Medio Pago"])
        self.tbl_personal.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_personal.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_personal.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_personal.cellDoubleClicked.connect(lambda r, c: self._edit_personal())
        l.addWidget(self.tbl_personal)
        return w

    def _load_periodos(self):
        self.combo_periodo.blockSignals(True)
        self.combo_periodo.clear()
        meses = self.mes_service.get_all()
        for m in meses:
            self.combo_periodo.addItem(m.display_name, (m.anio, m.mes))
        if not meses:
            self.combo_periodo.addItem("SEPTIEMBRE 2026", (2026, 9))
        self.combo_periodo.blockSignals(False)
        self.refresh_data()

    def _on_periodo_changed(self, idx):
        data = self.combo_periodo.currentData()
        if data:
            self.current_year, self.current_month = data
            self.refresh_data()

    def refresh_data(self):
        anio, mes = self.current_year, self.current_month
        local = self.current_local

        # 1. Update KPI totals
        res = self.egreso_service.get_resumen_egresos_mes(anio, mes, local)
        self._update_kpi(self.card_compras, res["total_compras"])
        self._update_kpi(self.card_gastos, res["total_gastos"])
        self._update_kpi(self.card_personal, res["total_personal"])
        self._update_kpi(self.card_total, res["total_egresos"])

        # 2. Compras Table (Simplified)
        compras = self.egreso_service.get_compras_mes(anio, mes, local)
        self.tbl_compras.setRowCount(len(compras))
        for r, c in enumerate(compras):
            self.tbl_compras.setItem(r, 0, QTableWidgetItem(str(c.id or "")))
            self.tbl_compras.setItem(r, 1, QTableWidgetItem(c.fecha))
            self.tbl_compras.setItem(r, 2, QTableWidgetItem(LOCAL_NAMES.get(c.local_id, c.local_id)))
            obs_text = c.observacion if c.observacion and c.observacion.strip() else c.descripcion
            self.tbl_compras.setItem(r, 3, QTableWidgetItem(obs_text or ""))
            self.tbl_compras.setItem(r, 4, QTableWidgetItem(c.categoria or "INSUMOS"))
            self.tbl_compras.setItem(r, 5, QTableWidgetItem(f"S/ {c.total:,.2f}"))
            self.tbl_compras.setItem(r, 6, QTableWidgetItem(c.medio_pago or "EFECTIVO"))

        # 3. Gastos Table
        gastos = self.egreso_service.get_gastos_mes(anio, mes, local)
        self.tbl_gastos.setRowCount(len(gastos))
        for r, g in enumerate(gastos):
            self.tbl_gastos.setItem(r, 0, QTableWidgetItem(str(g.id or "")))
            self.tbl_gastos.setItem(r, 1, QTableWidgetItem(g.fecha))
            self.tbl_gastos.setItem(r, 2, QTableWidgetItem(LOCAL_NAMES.get(g.local_id, g.local_id)))
            self.tbl_gastos.setItem(r, 3, QTableWidgetItem(g.categoria))
            self.tbl_gastos.setItem(r, 4, QTableWidgetItem(g.descripcion))
            self.tbl_gastos.setItem(r, 5, QTableWidgetItem(f"S/ {g.monto:,.2f}"))
            self.tbl_gastos.setItem(r, 6, QTableWidgetItem(g.medio_pago))

        # 4. Personal Table
        personal = self.egreso_service.get_pagos_personal_mes(anio, mes, local)
        self.tbl_personal.setRowCount(len(personal))
        for r, p in enumerate(personal):
            self.tbl_personal.setItem(r, 0, QTableWidgetItem(str(p.id or "")))
            self.tbl_personal.setItem(r, 1, QTableWidgetItem(p.fecha))
            self.tbl_personal.setItem(r, 2, QTableWidgetItem(LOCAL_NAMES.get(p.local_id, p.local_id)))
            self.tbl_personal.setItem(r, 3, QTableWidgetItem(p.trabajador))
            self.tbl_personal.setItem(r, 4, QTableWidgetItem(p.cargo))
            self.tbl_personal.setItem(r, 5, QTableWidgetItem(p.concepto))
            self.tbl_personal.setItem(r, 6, QTableWidgetItem(f"S/ {p.monto:,.2f}"))
            self.tbl_personal.setItem(r, 7, QTableWidgetItem(p.medio_pago))

    # --- Add/Del Dialog Handlers ---
    def _add_compra(self):
        dlg = CompraSimpleDialog(self, anio=self.current_year, mes=self.current_month, local_id=self.current_local, mostrar_fecha=True)
        if dlg.exec() == QDialog.Accepted:
            compra = dlg.get_compra()
            ok, msg, _ = self.egreso_service.registrar_compra(compra)
            if ok:
                ToastManager.show_success(f"Compra registrada: S/ {compra.total:,.2f}", self)
            else:
                QMessageBox.warning(self, "Error", msg)
            self.refresh_data()

    def _on_compra_double_clicked(self, row: int, col: int):
        item = self.tbl_compras.item(row, 0)
        if not item or not item.text():
            return
        cid = int(item.text())
        compra = self.egreso_service.get_compra_by_id(cid)
        if not compra:
            return
        dlg = CompraSimpleDialog(self, compra=compra, mostrar_fecha=True)
        if dlg.exec() == QDialog.Accepted:
            compra_mod = dlg.get_compra()
            ok, msg = self.egreso_service.actualizar_compra(compra_mod)
            if ok:
                ToastManager.show_success(f"Compra #{compra_mod.id} actualizada", self)
            else:
                QMessageBox.warning(self, "Error", msg)
            self.refresh_data()

    def _edit_compra(self):
        row = self.tbl_compras.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atención", "Seleccione una compra de la lista para editar.")
            return
        self._on_compra_double_clicked(row, 0)

    def _del_compra(self):
        row = self.tbl_compras.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atención", "Seleccione una compra para eliminar.")
            return
        cid = int(self.tbl_compras.item(row, 0).text())
        if QMessageBox.question(self, "Confirmar", "¿Eliminar compra seleccionada?") == QMessageBox.Yes:
            ok, msg = self.egreso_service.eliminar_compra(cid)
            if ok:
                ToastManager.show_info("Compra eliminada.", self)
            self.refresh_data()

    def _add_gasto(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Registrar Gasto Operativo")
        layout = QFormLayout(dlg)

        dt_edit = QDateEdit(QDate(self.current_year, self.current_month, 1))
        dt_edit.setCalendarPopup(True)
        layout.addRow("Fecha:", dt_edit)

        combo_loc = QComboBox()
        combo_loc.addItem("LA PROVINCIAL RESTAURANTE", LOCAL_RESTAURANTE)
        combo_loc.addItem("LA PROVINCIAL FAST FOOD", LOCAL_FAST_FOOD)
        if self.current_local in (LOCAL_RESTAURANTE, LOCAL_FAST_FOOD):
            combo_loc.setCurrentIndex(0 if self.current_local == LOCAL_RESTAURANTE else 1)
        layout.addRow("Local:", combo_loc)

        txt_cat = QComboBox()
        txt_cat.addItems(["SERVICIOS", "ALQUILER", "LUZ", "AGUA", "GAS", "TRANSPORTE", "MANTENIMIENTO", "OTROS"])
        layout.addRow("Categoría:", txt_cat)

        txt_desc = QLineEdit()
        layout.addRow("Descripción:", txt_desc)

        spn_monto = QDoubleSpinBox()
        spn_monto.setRange(0.01, 9999999.0)
        spn_monto.setValue(10.0)
        layout.addRow("Monto:", spn_monto)

        combo_pago = QComboBox()
        combo_pago.addItems(["EFECTIVO", "YAPE", "TRANSFERENCIA", "TARJETA"])
        layout.addRow("Medio de Pago:", combo_pago)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addRow(btns)

        if dlg.exec() == QDialog.Accepted:
            g = Gasto(
                fecha=dt_edit.date().toString("yyyy-MM-dd"),
                local_id=combo_loc.currentData(),
                categoria=txt_cat.currentText(),
                descripcion=txt_desc.text().strip() or "Gasto",
                monto=spn_monto.value(),
                medio_pago=combo_pago.currentText()
            )
            self.egreso_service.registrar_gasto(g)
            self.refresh_data()

    def _edit_gasto(self):
        row = self.tbl_gastos.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atención", "Seleccione un gasto de la lista para editar.")
            return
        item = self.tbl_gastos.item(row, 0)
        if not item or not item.text():
            return
        gid = int(item.text())
        gasto = self.egreso_service.get_gasto_by_id(gid)
        if not gasto:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"✏️ Editar Gasto #{gasto.id}")
        layout = QFormLayout(dlg)

        try:
            dt = datetime.strptime(gasto.fecha, "%Y-%m-%d")
            dt_edit = QDateEdit(QDate(dt.year, dt.month, dt.day))
        except Exception:
            dt_edit = QDateEdit(QDate(self.current_year, self.current_month, 1))
        dt_edit.setCalendarPopup(True)
        layout.addRow("Fecha:", dt_edit)

        combo_loc = QComboBox()
        combo_loc.addItem("LA PROVINCIAL RESTAURANTE", LOCAL_RESTAURANTE)
        combo_loc.addItem("LA PROVINCIAL FAST FOOD", LOCAL_FAST_FOOD)
        idx_l = 1 if gasto.local_id == LOCAL_FAST_FOOD else 0
        combo_loc.setCurrentIndex(idx_l)
        layout.addRow("Local:", combo_loc)

        txt_cat = QComboBox()
        txt_cat.addItems(["SERVICIOS", "ALQUILER", "LUZ", "AGUA", "GAS", "TRANSPORTE", "MANTENIMIENTO", "OTROS"])
        idx_c = txt_cat.findText(gasto.categoria)
        if idx_c >= 0:
            txt_cat.setCurrentIndex(idx_c)
        layout.addRow("Categoría:", txt_cat)

        txt_desc = QLineEdit(gasto.descripcion)
        layout.addRow("Descripción:", txt_desc)

        spn_monto = QDoubleSpinBox()
        spn_monto.setRange(0.01, 9999999.0)
        spn_monto.setValue(gasto.monto or 0.0)
        layout.addRow("Monto:", spn_monto)

        combo_pago = QComboBox()
        combo_pago.addItems(["EFECTIVO", "YAPE", "TRANSFERENCIA", "TARJETA"])
        idx_p = combo_pago.findText(gasto.medio_pago)
        if idx_p >= 0:
            combo_pago.setCurrentIndex(idx_p)
        layout.addRow("Medio de Pago:", combo_pago)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addRow(btns)

        if dlg.exec() == QDialog.Accepted:
            gasto.fecha = dt_edit.date().toString("yyyy-MM-dd")
            gasto.local_id = combo_loc.currentData()
            gasto.categoria = txt_cat.currentText()
            gasto.descripcion = txt_desc.text().strip() or "Gasto"
            gasto.monto = spn_monto.value()
            gasto.medio_pago = combo_pago.currentText()
            ok, msg = self.egreso_service.actualizar_gasto(gasto)
            if ok:
                ToastManager.show_success(f"Gasto #{gasto.id} actualizado", self)
            else:
                QMessageBox.warning(self, "Error", msg)
            self.refresh_data()

    def _del_gasto(self):
        row = self.tbl_gastos.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atención", "Seleccione un gasto para eliminar.")
            return
        gid = int(self.tbl_gastos.item(row, 0).text())
        if QMessageBox.question(self, "Confirmar", "¿Eliminar gasto seleccionado?") == QMessageBox.Yes:
            self.egreso_service.eliminar_gasto(gid)
            self.refresh_data()

    def _add_personal(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Registrar Pago al Personal")
        layout = QFormLayout(dlg)

        dt_edit = QDateEdit(QDate(self.current_year, self.current_month, 1))
        dt_edit.setCalendarPopup(True)
        layout.addRow("Fecha:", dt_edit)

        combo_loc = QComboBox()
        combo_loc.addItem("LA PROVINCIAL RESTAURANTE", LOCAL_RESTAURANTE)
        combo_loc.addItem("LA PROVINCIAL FAST FOOD", LOCAL_FAST_FOOD)
        if self.current_local in (LOCAL_RESTAURANTE, LOCAL_FAST_FOOD):
            combo_loc.setCurrentIndex(0 if self.current_local == LOCAL_RESTAURANTE else 1)
        layout.addRow("Local:", combo_loc)

        txt_trab = QLineEdit()
        layout.addRow("Trabajador:", txt_trab)

        txt_cargo = QLineEdit()
        layout.addRow("Cargo:", txt_cargo)

        txt_conc = QComboBox()
        txt_conc.addItems(["SUELDO", "ADELANTO", "HORAS EXTRAS", "BONO", "LIQUIDACION", "PROPINAS", "TURNO DÍA", "TURNO NOCHE", "OTROS"])
        layout.addRow("Concepto:", txt_conc)

        spn_monto = QDoubleSpinBox()
        spn_monto.setRange(0.01, 9999999.0)
        spn_monto.setValue(50.0)
        layout.addRow("Monto:", spn_monto)

        combo_pago = QComboBox()
        combo_pago.addItems(["EFECTIVO", "YAPE", "TRANSFERENCIA"])
        layout.addRow("Medio de Pago:", combo_pago)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addRow(btns)

        if dlg.exec() == QDialog.Accepted:
            p = PagoPersonal(
                fecha=dt_edit.date().toString("yyyy-MM-dd"),
                local_id=combo_loc.currentData(),
                trabajador=txt_trab.text().strip() or "Personal",
                cargo=txt_cargo.text().strip() or "Operario",
                concepto=txt_conc.currentText(),
                monto=spn_monto.value(),
                medio_pago=combo_pago.currentText()
            )
            self.egreso_service.registrar_pago_personal(p)
            self.refresh_data()

    def _edit_personal(self):
        row = self.tbl_personal.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atención", "Seleccione un pago de personal de la lista para editar.")
            return
        item = self.tbl_personal.item(row, 0)
        if not item or not item.text():
            return
        pid = int(item.text())
        pago = self.egreso_service.get_pago_personal_by_id(pid)
        if not pago:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"✏️ Editar Pago Personal #{pago.id}")
        layout = QFormLayout(dlg)

        try:
            dt = datetime.strptime(pago.fecha, "%Y-%m-%d")
            dt_edit = QDateEdit(QDate(dt.year, dt.month, dt.day))
        except Exception:
            dt_edit = QDateEdit(QDate(self.current_year, self.current_month, 1))
        dt_edit.setCalendarPopup(True)
        layout.addRow("Fecha:", dt_edit)

        combo_loc = QComboBox()
        combo_loc.addItem("LA PROVINCIAL RESTAURANTE", LOCAL_RESTAURANTE)
        combo_loc.addItem("LA PROVINCIAL FAST FOOD", LOCAL_FAST_FOOD)
        idx_l = 1 if pago.local_id == LOCAL_FAST_FOOD else 0
        combo_loc.setCurrentIndex(idx_l)
        layout.addRow("Local:", combo_loc)

        txt_trab = QLineEdit(pago.trabajador)
        layout.addRow("Trabajador:", txt_trab)

        txt_cargo = QLineEdit(pago.cargo)
        layout.addRow("Cargo:", txt_cargo)

        txt_conc = QComboBox()
        txt_conc.addItems(["SUELDO", "ADELANTO", "HORAS EXTRAS", "BONO", "LIQUIDACION", "PROPINAS", "TURNO DÍA", "TURNO NOCHE", "OTROS"])
        idx_c = txt_conc.findText(pago.concepto)
        if idx_c >= 0:
            txt_conc.setCurrentIndex(idx_c)
        else:
            txt_conc.setEditText(pago.concepto)
        layout.addRow("Concepto:", txt_conc)

        spn_monto = QDoubleSpinBox()
        spn_monto.setRange(0.01, 9999999.0)
        spn_monto.setValue(pago.monto or 0.0)
        layout.addRow("Monto:", spn_monto)

        combo_pago = QComboBox()
        combo_pago.addItems(["EFECTIVO", "YAPE", "TRANSFERENCIA"])
        idx_p = combo_pago.findText(pago.medio_pago)
        if idx_p >= 0:
            combo_pago.setCurrentIndex(idx_p)
        layout.addRow("Medio de Pago:", combo_pago)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addRow(btns)

        if dlg.exec() == QDialog.Accepted:
            pago.fecha = dt_edit.date().toString("yyyy-MM-dd")
            pago.local_id = combo_loc.currentData()
            pago.trabajador = txt_trab.text().strip() or "Personal"
            pago.cargo = txt_cargo.text().strip() or "Operario"
            pago.concepto = txt_conc.currentText()
            pago.monto = spn_monto.value()
            pago.medio_pago = combo_pago.currentText()
            ok, msg = self.egreso_service.actualizar_pago_personal(pago)
            if ok:
                ToastManager.show_success(f"Pago #{pago.id} actualizado", self)
            else:
                QMessageBox.warning(self, "Error", msg)
            self.refresh_data()

    def _del_personal(self):
        row = self.tbl_personal.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atención", "Seleccione un pago para eliminar.")
            return
        pid = int(self.tbl_personal.item(row, 0).text())
        if QMessageBox.question(self, "Confirmar", "¿Eliminar pago de personal seleccionado?") == QMessageBox.Yes:
            self.egreso_service.eliminar_pago_personal(pid)
            self.refresh_data()
