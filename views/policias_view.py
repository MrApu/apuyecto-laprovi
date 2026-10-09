from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QButtonGroup, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from typing import Optional, List
from models.policia import Policia
from services.policia_service import PoliciaService
from services.ticket_service import TicketService
from views.dialogs.policia_dialog import PoliciaDialog
from views.dialogs.historial_policia_dialog import HistorialPoliciaDialog
from views.components.toast import ToastManager
from reports.csv_exporter import CSVExporter

class PoliciasView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.policia_service = PoliciaService()
        self.ticket_service = TicketService()
        self.policias: List[Policia] = []
        self.active_chip = "TODOS"
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header bar
        header_box = QHBoxLayout()
        lbl_title = QLabel("👮 BASE DE DATOS MAESTRA DE POLICÍAS")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #F8FAFC;")
        header_box.addWidget(lbl_title)
        header_box.addStretch()

        self.btn_nuevo = QPushButton("➕ Nuevo Policía")
        self.btn_nuevo.setProperty("class", "PrimaryBtn")
        self.btn_nuevo.clicked.connect(self._on_nuevo_policia)
        header_box.addWidget(self.btn_nuevo)

        self.btn_exportar = QPushButton("📥 Exportar CSV")
        self.btn_exportar.clicked.connect(self._on_exportar_csv)
        header_box.addWidget(self.btn_exportar)

        layout.addLayout(header_box)

        # Quick Filter Chips Row (Item 3)
        chip_box = QHBoxLayout()
        chip_box.setSpacing(6)
        lbl_chip_title = QLabel("⚡ Filtros Rápidos:")
        lbl_chip_title.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 800;")
        chip_box.addWidget(lbl_chip_title)

        self.chip_group = QButtonGroup(self)
        self.chip_group.setExclusive(True)

        chips = [
            ("🔘 Todos", "TODOS"),
            ("🟢 Activos", "ACTIVOS"),
            ("🔴 Inactivos", "INACTIVOS"),
            ("🏢 SECINT", "SECINT"),
            ("🚗 Tránsito", "TRANSITO"),
            ("⭐ Con SA-PNP", "CON_SA")
        ]

        for idx, (label, key) in enumerate(chips):
            btn_chip = QPushButton(label)
            btn_chip.setCheckable(True)
            btn_chip.setCursor(Qt.PointingHandCursor)
            if key == "TODOS":
                btn_chip.setChecked(True)
            btn_chip.setStyleSheet("""
                QPushButton {
                    background-color: #111827;
                    color: #94A3B8;
                    border: 1px solid #1F2937;
                    border-radius: 14px;
                    padding: 4px 12px;
                    font-size: 11px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #1E293B;
                    color: #F8FAFC;
                    border-color: #38BDF8;
                }
                QPushButton:checked {
                    background-color: #1E1B4B;
                    color: #A5B4FC;
                    border: 1px solid #6366F1;
                }
            """)
            btn_chip.clicked.connect(lambda _, k=key: self._on_chip_clicked(k))
            self.chip_group.addButton(btn_chip, idx)
            chip_box.addWidget(btn_chip)

        chip_box.addStretch()
        layout.addLayout(chip_box)

        # Filter & Search Bar
        filter_box = QHBoxLayout()
        self.txt_busqueda = QLineEdit()
        self.txt_busqueda.setPlaceholderText("🔍 Buscar por Código, Apellidos, Nombres, SA-PNP o Área...")
        self.txt_busqueda.textChanged.connect(self.cargar_datos)
        filter_box.addWidget(self.txt_busqueda, 3)

        self.cmb_area = QComboBox()
        self.cmb_area.addItem("TODAS LAS ÁREAS", "TODAS")
        self.cmb_area.currentIndexChanged.connect(self.cargar_datos)
        filter_box.addWidget(self.cmb_area, 1)

        self.cmb_estado = QComboBox()
        self.cmb_estado.addItem("TODOS LOS ESTADOS", "")
        self.cmb_estado.addItem("SOLO ACTIVOS", "ACTIVO")
        self.cmb_estado.addItem("SOLO INACTIVOS", "INACTIVO")
        self.cmb_estado.currentIndexChanged.connect(self.cargar_datos)
        filter_box.addWidget(self.cmb_estado, 1)

        layout.addLayout(filter_box)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Código", "Apellidos", "Nombres", "SA-PNP", "Área", "Estado", "Acciones", "ID"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setColumnHidden(7, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_editar_policia)

        layout.addWidget(self.table)

        # Status count footer
        self.lbl_conteo = QLabel("Cargando policías...")
        self.lbl_conteo.setStyleSheet("color: #595959; font-size: 12px;")
        layout.addWidget(self.lbl_conteo)

        self._actualizar_areas_combo()
        self.cargar_datos()

    def _actualizar_areas_combo(self):
        areas = self.policia_service.get_areas()
        current = self.cmb_area.currentData()
        self.cmb_area.blockSignals(True)
        self.cmb_area.clear()
        self.cmb_area.addItem("TODAS LAS ÁREAS", "TODAS")
        for a in areas:
            self.cmb_area.addItem(a, a)
        idx = self.cmb_area.findData(current)
        if idx >= 0:
            self.cmb_area.setCurrentIndex(idx)
        self.cmb_area.blockSignals(False)

    def _on_chip_clicked(self, key: str):
        self.active_chip = key
        self.cargar_datos()

    def cargar_datos(self):
        busqueda = self.txt_busqueda.text().strip()
        area = self.cmb_area.currentData()
        solo_activos = self.cmb_estado.currentData() == "ACTIVO"
        solo_inactivos = self.cmb_estado.currentData() == "INACTIVO"

        all_pol = self.policia_service.get_all(
            solo_activos=solo_activos,
            busqueda=busqueda if busqueda else None,
            area=area if area != "TODAS" else None
        )

        if solo_inactivos:
            all_pol = [p for p in all_pol if p.estado == "INACTIVO"]

        # Apply Quick Chip Filters
        if self.active_chip == "ACTIVOS":
            all_pol = [p for p in all_pol if p.estado == "ACTIVO"]
        elif self.active_chip == "INACTIVOS":
            all_pol = [p for p in all_pol if p.estado == "INACTIVO"]
        elif self.active_chip == "SECINT":
            all_pol = [p for p in all_pol if (p.area or "").upper() == "SECINT"]
        elif self.active_chip == "TRANSITO":
            all_pol = [p for p in all_pol if "TRANS" in (p.area or "").upper()]
        elif self.active_chip == "CON_SA":
            all_pol = [p for p in all_pol if p.sa_pnp and p.sa_pnp != "-"]

        self.policias = all_pol
        self.table.setRowCount(len(all_pol))

        for r, p in enumerate(all_pol):
            self.table.setItem(r, 0, QTableWidgetItem(p.codigo))
            self.table.setItem(r, 1, QTableWidgetItem(p.apellidos))
            self.table.setItem(r, 2, QTableWidgetItem(p.nombres))
            self.table.setItem(r, 3, QTableWidgetItem(p.sa_pnp or "-"))
            self.table.setItem(r, 4, QTableWidgetItem(p.area))

            # Estado
            est_item = QTableWidgetItem(p.estado)
            if p.is_activo:
                est_item.setForeground(QColor("#10B981"))
            else:
                est_item.setForeground(QColor("#F43F5E"))
            est_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 5, est_item)

            # Actions buttons container
            action_widget = QWidget()
            action_l = QHBoxLayout(action_widget)
            action_l.setContentsMargins(2, 2, 2, 2)
            action_l.setSpacing(4)

            btn_edit = QPushButton("✏️")
            btn_edit.setToolTip("Editar Policía")
            btn_edit.setFixedWidth(28)
            btn_edit.clicked.connect(lambda _, pol=p: self._abrir_dialogo_edicion(pol))
            action_l.addWidget(btn_edit)

            btn_hist = QPushButton("📊")
            btn_hist.setToolTip("Ver Historial")
            btn_hist.setFixedWidth(28)
            btn_hist.clicked.connect(lambda _, pol=p: self._abrir_historial(pol))
            action_l.addWidget(btn_hist)

            if p.is_activo:
                btn_inact = QPushButton("⛔")
                btn_inact.setToolTip("Inactivar Policía (Lógica)")
                btn_inact.setFixedWidth(28)
                btn_inact.clicked.connect(lambda _, p_id=p.id: self._inactivar_policia(p_id))
                action_l.addWidget(btn_inact)
            else:
                btn_react = QPushButton("✅")
                btn_react.setToolTip("Reactivar Policía")
                btn_react.setFixedWidth(28)
                btn_react.clicked.connect(lambda _, p_id=p.id: self._reactivar_policia(p_id))
                action_l.addWidget(btn_react)

            self.table.setCellWidget(r, 6, action_widget)
            self.table.setItem(r, 7, QTableWidgetItem(str(p.id)))

        tot_activos = sum(1 for p in all_pol if p.is_activo)
        tot_inactivos = len(all_pol) - tot_activos
        self.lbl_conteo.setText(f"Total mostrados: {len(all_pol)} | Activos: {tot_activos} | Inactivos: {tot_inactivos}")

    def _on_nuevo_policia(self):
        areas = self.policia_service.get_areas()
        dlg = PoliciaDialog(self, areas_disponibles=areas)
        if dlg.exec():
            pol = dlg.get_datos()
            ok, msg, new_id = self.policia_service.crear_policia(pol)
            if ok:
                ToastManager.show_success(f"Policía {pol.apellidos} registrado con éxito", self)
                self._actualizar_areas_combo()
                self.cargar_datos()
            else:
                ToastManager.show_error(msg, self)

    def _on_editar_policia(self):
        row = self.table.currentRow()
        if row >= 0 and row < len(self.policias):
            self._abrir_dialogo_edicion(self.policias[row])

    def _abrir_dialogo_edicion(self, pol: Policia):
        areas = self.policia_service.get_areas()
        dlg = PoliciaDialog(self, policia=pol, areas_disponibles=areas)
        if dlg.exec():
            pol_mod = dlg.get_datos()
            ok, msg = self.policia_service.actualizar_policia(pol_mod)
            if ok:
                QMessageBox.information(self, "Éxito", msg)
                self._actualizar_areas_combo()
                self.cargar_datos()
            else:
                QMessageBox.warning(self, "Error al Actualizar", msg)

    def _abrir_historial(self, pol: Policia):
        historial = self.ticket_service.get_historial_policia(pol.id)
        dlg = HistorialPoliciaDialog(self, policia=pol, historial_meses=historial)
        dlg.exec()

    def _inactivar_policia(self, policia_id: int):
        resp = QMessageBox.question(
            self,
            "Confirmar Inactivación",
            "¿Desea inactivar a este policía?\nNo se eliminará su información ni su historial mensual.",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            ok, msg = self.policia_service.inactivar_policia(policia_id)
            if ok:
                self.cargar_datos()
            else:
                QMessageBox.warning(self, "Error", msg)

    def _reactivar_policia(self, policia_id: int):
        ok, msg = self.policia_service.reactivar_policia(policia_id)
        if ok:
            self.cargar_datos()
        else:
            QMessageBox.warning(self, "Error", msg)

    def _on_exportar_csv(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Exportar Policías", "policias.csv", "CSV Files (*.csv)")
        if filepath:
            headers = ["Código", "Apellidos", "Nombres", "SA-PNP", "Área", "Estado"]
            rows = [[p.codigo, p.apellidos, p.nombres, p.sa_pnp or "", p.area, p.estado] for p in self.policias]
            CSVExporter.exportar_tabla(headers, rows, filepath)
            QMessageBox.information(self, "Exportación Exitosa", f"Archivo exportado a {filepath}")
