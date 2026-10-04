from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QTextEdit, QDateEdit, QMessageBox, QComboBox
)
from PySide6.QtCore import QDate, Qt
from typing import Optional, List
from models.observacion import Observacion
from services.observacion_service import ObservacionService

class ObservacionesView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.obs_service = ObservacionService()
        self.current_anio = 2026
        self.current_mes = 9
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_box = QHBoxLayout()
        self.lbl_title = QLabel("Observaciones y Notas Diarias")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1F4E78;")
        header_box.addWidget(self.lbl_title)
        header_box.addStretch()
        layout.addLayout(header_box)

        # New Note Box
        new_box = QHBoxLayout()
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        new_box.addWidget(self.date_picker)

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["GENERAL", "DEUDA", "VALES", "AJUSTE", "PAGO"])
        new_box.addWidget(self.cmb_tipo)

        self.txt_texto = QTextEdit()
        self.txt_texto.setMaximumHeight(60)
        self.txt_texto.setPlaceholderText("Escriba aquí la observación...")
        new_box.addWidget(self.txt_texto, 3)

        self.btn_agregar = QPushButton("➕ Agregar Nota")
        self.btn_agregar.setProperty("class", "PrimaryBtn")
        self.btn_agregar.clicked.connect(self._on_agregar)
        new_box.addWidget(self.btn_agregar)

        layout.addLayout(new_box)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Fecha", "Tipo", "Observación / Nota", "Acción"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

    def set_periodo(self, anio: int, mes: int):
        self.current_anio = anio
        self.current_mes = mes
        self.lbl_title.setText(f"Observaciones y Notas - {mes:02d}/{anio}")
        self.cargar_datos()

    def cargar_datos(self):
        obs_list = self.obs_service.get_by_mes(self.current_anio, self.current_mes)
        self.table.setRowCount(len(obs_list))

        for r, o in enumerate(obs_list):
            self.table.setItem(r, 0, QTableWidgetItem(o.fecha))
            self.table.setItem(r, 1, QTableWidgetItem(o.tipo))
            self.table.setItem(r, 2, QTableWidgetItem(o.texto))

            btn_del = QPushButton("🗑️")
            btn_del.setFixedWidth(30)
            btn_del.clicked.connect(lambda _, o_id=o.id: self._eliminar(o_id))
            self.table.setCellWidget(r, 3, btn_del)

    def _on_agregar(self):
        fecha = self.date_picker.date().toString("yyyy-MM-dd")
        texto = self.txt_texto.toPlainText().strip()
        tipo = self.cmb_tipo.currentText()

        if not texto:
            QMessageBox.warning(self, "Campo Vacío", "Debe ingresar un texto.")
            return

        ok, msg, _ = self.obs_service.agregar_observacion(fecha, texto, tipo)
        if ok:
            self.txt_texto.clear()
            self.cargar_datos()
        else:
            QMessageBox.warning(self, "Error", msg)

    def _eliminar(self, obs_id: int):
        ok, msg = self.obs_service.eliminar_observacion(obs_id)
        if ok:
            self.cargar_datos()
