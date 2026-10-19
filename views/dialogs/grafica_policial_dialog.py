from typing import List, Dict, Any, Optional
import numpy as np
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from models.ticket import TicketDiario
from models.local import LOCAL_NAMES

class GraficaPolicialDialog(QDialog):
    """
    Ventana emergente interactiva de Análisis Gráfico Policial:
    - Tendencia Diaria: Tickets Para Unidad vs Consumo en Local.
    - Comparativa de Vales y Promedios del mes.
    """
    def __init__(self, diarios: List[TicketDiario], anio: int, mes: int, local_id: str = "restaurante", parent=None):
        super().__init__(parent)
        self.diarios = diarios
        self.anio = anio
        self.mes = mes
        self.local_id = local_id
        self.sede_name = LOCAL_NAMES.get(local_id, local_id.upper())

        self.setWindowTitle(f"📊 Análisis Gráfico de Tickets Policiales — {mes:02d}/{anio} ({self.sede_name})")
        self.resize(950, 620)
        self.setModal(True)
        self._init_ui()
        self._render_grafico()

    def _init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #090D16;
                color: #F8FAFC;
            }
            QPushButton.CloseBtn {
                background-color: #1E293B;
                color: #E2E8F0;
                font-weight: bold;
                font-size: 13px;
                border-radius: 6px;
                padding: 8px 18px;
                border: 1px solid #374151;
            }
            QPushButton.CloseBtn:hover {
                background-color: #374151;
                color: #FFFFFF;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header
        top_h = QHBoxLayout()
        v_title = QVBoxLayout()
        lbl_t = QLabel(f"📈 Gráfica de Demanda Policial Diaria — {self.mes:02d}/{self.anio}")
        lbl_t.setStyleSheet("font-size: 17px; font-weight: 800; color: #38BDF8;")
        lbl_sub = QLabel(f"Sede: {self.sede_name} | Comparativa entre Tickets Para Unidad y Consumo en Local")
        lbl_sub.setStyleSheet("font-size: 12px; color: #94A3B8;")
        v_title.addWidget(lbl_t)
        v_title.addWidget(lbl_sub)
        top_h.addLayout(v_title)
        top_h.addStretch()

        btn_close = QPushButton("✕ Cerrar")
        btn_close.setProperty("class", "CloseBtn")
        btn_close.clicked.connect(self.accept)
        top_h.addWidget(btn_close)
        layout.addLayout(top_h)

        # Canvas Frame
        frame_chart = QFrame()
        frame_chart.setStyleSheet("background-color: #111827; border: 1px solid #1F2937; border-radius: 10px; padding: 6px;")
        l_chart = QVBoxLayout(frame_chart)
        l_chart.setContentsMargins(0, 0, 0, 0)

        self.fig, self.ax = plt.subplots(figsize=(11, 5), dpi=100)
        self.fig.subplots_adjust(left=0.06, right=0.96, top=0.90, bottom=0.15)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        l_chart.addWidget(self.canvas)

        layout.addWidget(frame_chart, 1)

    def _render_grafico(self):
        self.ax.clear()

        if not self.diarios:
            self.ax.text(0.5, 0.5, "Sin datos de tickets en este mes", color="#94A3B8", ha='center', va='center', transform=self.ax.transAxes, fontsize=12)
            self.canvas.draw()
            return

        dias = [int(d.dia) for d in self.diarios]
        unidad = np.array([d.para_unidad for d in self.diarios])
        local = np.array([d.local for d in self.diarios])
        totales = unidad + local
        x = np.arange(len(dias))

        # Stacked bar
        self.ax.bar(x, unidad, label="👮 Para Unidad PNP", color="#6366F1", width=0.65, alpha=0.95)
        self.ax.bar(x, local, bottom=unidad, label="🍽️ Consumo en Local", color="#06B6D4", width=0.65, alpha=0.95)

        # Trend line of total
        self.ax.plot(x, totales, label="— Total Diario", color="#38BDF8", linewidth=2.2, marker='o', markersize=4)

        # Style dark theme
        self.ax.set_facecolor('#111827')
        self.fig.patch.set_facecolor('#111827')
        self.ax.set_xticks(x)
        self.ax.set_xticklabels([f"D{d}" if d % 2 == 1 or len(dias) <= 15 else str(d) for d in dias], rotation=0)
        self.ax.tick_params(colors='#9CA3AF', labelsize=9)
        self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, loc: f"{int(val):,d}"))
        self.ax.grid(True, linestyle='--', alpha=0.25, color='#374151')

        for spine in self.ax.spines.values():
            spine.set_color('#1F2937')
            spine.set_linewidth(1)

        self.ax.legend(fontsize=10, facecolor='#1F2937', edgecolor='none', labelcolor='#F9FAFB', loc='upper right')
        self.canvas.draw()
