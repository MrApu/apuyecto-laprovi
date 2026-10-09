from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QLabel, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QIcon, QKeyEvent

from database.connection import DatabaseManager
from models.policia import Policia
from services.policia_service import PoliciaService

class SpotlightSearchDialog(QDialog):
    """
    Buscador global rápido (Spotlight / Ctrl+K) para navegación y búsqueda instantánea:
    - Policías por código, apellidos, nombres o área
    - Módulos y vistas del sistema
    - Días específicos del calendario
    """
    action_triggered = Signal(str, object)  # (tipo_accion, payload)

    def __init__(self, parent=None, policia_service: Optional[PoliciaService] = None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(650, 420)
        self.policia_service = policia_service or PoliciaService()
        self._init_modules()
        self._init_ui()

    def _init_modules(self):
        self.modules = [
            ("📊 Dashboard Modular BI", 0, "Métricas ejecutivas, gráficos de ingresos, egresos y cobranzas"),
            ("👮 Base de Datos PNP", 1, "Directorio maestro de efectivos policiales"),
            ("📅 Calendario de Tickets", 2, "Consumo diario de tickets de policías"),
            ("🎫 Matriz Mensual Tickets", 3, "Control por efectivo y días del mes"),
            ("🎟️ Vales Policiales", 4, "Registro y canje de vales de consumo"),
            ("💰 Cobranzas y Deudas", 5, "Pagos de tickets y control de saldos debidos"),
            ("📈 Ventas Diarias (EF/YP)", 6, "Registro de ventas en efectivo, yape y tickets"),
            ("💸 Egresos (Compras/Gastos)", 7, "Compras de insumos, gastos varios y planilla"),
            ("📆 Calendario Financiero", 8, "Cuadrícula visual de saldo diario y evolución"),
            ("🍔 Consumo Fast Food", 9, "Control de ventas y consumos Fast Food"),
            ("📝 Bitácora Observaciones", 10, "Novedades y notas del mes"),
            ("📄 Reportes y Exportación", 11, "Generación de PDF y Excel ejecutivos"),
            ("⚙️ Configuración Precios", 12, "Precios de menú policial y ajustes"),
            ("💾 Copias de Seguridad", 13, "Respaldos y restauración de SQLite")
        ]

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Container Frame with glassmorphism style
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: #0F172A;
                border: 1px solid #6366F1;
                border-radius: 12px;
            }
        """)
        c_layout = QVBoxLayout(self.container)
        c_layout.setContentsMargins(16, 16, 16, 16)
        c_layout.setSpacing(12)

        # Search Input
        search_box = QHBoxLayout()
        lbl_icon = QLabel("🔍")
        lbl_icon.setStyleSheet("font-size: 18px; background: transparent;")
        search_box.addWidget(lbl_icon)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Escribe para buscar policías, módulos o acciones... (Esc para salir)")
        self.txt_search.setStyleSheet("""
            QLineEdit {
                background-color: #1E293B;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 600;
                padding: 10px 14px;
                border: 1px solid #334155;
                border-radius: 8px;
            }
            QLineEdit:focus {
                border: 1px solid #818CF8;
                background-color: #1E1B4B;
            }
        """)
        self.txt_search.textChanged.connect(self._on_search_changed)
        search_box.addWidget(self.txt_search)
        c_layout.addLayout(search_box)

        # Results List
        self.list_results = QListWidget()
        self.list_results.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                color: #F8FAFC;
                outline: none;
            }
            QListWidget::item {
                background-color: #111827;
                border: 1px solid #1F2937;
                border-radius: 8px;
                padding: 10px 12px;
                margin-bottom: 6px;
            }
            QListWidget::item:hover {
                background-color: #1E293B;
                border: 1px solid #38BDF8;
            }
            QListWidget::item:selected {
                background-color: #1E1B4B;
                border: 1px solid #6366F1;
                color: #FFFFFF;
            }
        """)
        self.list_results.itemActivated.connect(self._on_item_selected)
        c_layout.addWidget(self.list_results)

        # Footer Hint
        lbl_hint = QLabel("💡 <b>Enter</b> para seleccionar  •  <b>↑/↓</b> para navegar  •  <b>Esc</b> para cerrar")
        lbl_hint.setStyleSheet("color: #64748B; font-size: 11px; background: transparent; padding-top: 4px;")
        lbl_hint.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(lbl_hint)

        main_layout.addWidget(self.container)
        self._populate_initial()

    def _populate_initial(self):
        self.list_results.clear()
        for title, idx, desc in self.modules[:6]:
            item = QListWidgetItem(f"{title}\n   ↳ {desc}")
            item.setData(Qt.UserRole, ("module", idx))
            self.list_results.addItem(item)
        if self.list_results.count() > 0:
            self.list_results.setCurrentRow(0)

    def _on_search_changed(self, text: str):
        query = text.strip().lower()
        self.list_results.clear()
        if not query:
            self._populate_initial()
            return

        # 1. Search modules
        for title, idx, desc in self.modules:
            if query in title.lower() or query in desc.lower():
                item = QListWidgetItem(f"{title}\n   ↳ {desc}")
                item.setData(Qt.UserRole, ("module", idx))
                self.list_results.addItem(item)

        # 2. Search police officers
        try:
            pols = self.policia_service.get_all(solo_activos=False)
            matched_pols = [
                p for p in pols
                if query in (p.apellidos or "").lower()
                or query in (p.nombres or "").lower()
                or query in (p.codigo or "").lower()
                or query in (p.area or "").lower()
                or query in (p.sa_pnp or "").lower()
            ]

            for p in matched_pols[:15]:
                status_icon = "🟢" if p.estado == "ACTIVO" else "🔴"
                item = QListWidgetItem(f"👮 {p.apellidos} {p.nombres} ({p.codigo})  {status_icon}\n   ↳ Área: {p.area or '-'} | SA-PNP: {p.sa_pnp or '-'}")
                item.setData(Qt.UserRole, ("policia", p))
                self.list_results.addItem(item)
        except Exception:
            pass

        if self.list_results.count() > 0:
            self.list_results.setCurrentRow(0)

    def _on_item_selected(self, item: QListWidgetItem):
        data = item.data(Qt.UserRole)
        if data:
            tipo, payload = data
            self.action_triggered.emit(tipo, payload)
            self.accept()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key_Down, Qt.Key_Up):
            self.list_results.keyPressEvent(event)
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            curr = self.list_results.currentItem()
            if curr:
                self._on_item_selected(curr)
        else:
            super().keyPressEvent(event)
