# Theme and stylesheet definitions for LA PROVINCIAL (Rojo, Blanco y Negro Edition)

COLOR_PRIMARY = "#DC2626"        # Rojo Carmesí La Provincial
COLOR_PRIMARY_LIGHT = "#EF4444"  # Rojo Acento Brillante
COLOR_PRIMARY_DARK = "#991B1B"   # Rojo Borgoña Profundo
COLOR_SUCCESS = "#10B981"        # Verde Esmeralda (Utilidad / Ingresos)
COLOR_WARNING = "#F59E0B"        # Ámbar
COLOR_DANGER = "#DC2626"         # Rojo Alerta / Gastos
COLOR_INFO = "#38BDF8"           # Celeste Informativo
COLOR_BG_DARK = "#0A0A0A"        # Negro Carbón Puro
COLOR_SURFACE = "#141414"        # Superficie de Tarjetas
COLOR_SURFACE_HOVER = "#1C1C1F"  # Superficie Tarjetas Hover
COLOR_BORDER = "#27272A"         # Borde Neutral Oscuro
COLOR_BORDER_FOCUS = "#DC2626"   # Borde en Foco Rojo
COLOR_TEXT_PRIMARY = "#FFFFFF"   # Blanco Puro
COLOR_TEXT_MUTED = "#A1A1AA"     # Gris Suave

QSS_STYLE = """
QMainWindow {
    background-color: #0A0A0A;
}

QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    color: #F4F4F5;
    background-color: transparent;
}

/* Sidebar */
#Sidebar {
    background-color: #0D0D0D;
    min-width: 240px;
    max-width: 240px;
    border-right: 1px solid #262626;
}

#Sidebar QPushButton {
    background-color: transparent;
    color: #A1A1AA;
    border: 1px solid transparent;
    text-align: left;
    padding: 10px 16px;
    font-size: 12px;
    font-weight: 600;
    border-left: 3px solid transparent;
    border-radius: 6px;
}

#Sidebar QPushButton:hover {
    background-color: #1A1A1C;
    color: #FFFFFF;
    border: 1px solid #333336;
    border-left: 3px solid #DC2626;
}

#Sidebar QPushButton:checked {
    background-color: #261113;
    color: #FFFFFF;
    border: 1px solid #7F1D1D;
    border-left: 4px solid #DC2626;
    font-weight: 700;
}

/* Top Bar */
#TopBar {
    background-color: #121212;
    border-bottom: 1px solid #262626;
    padding: 8px 16px;
}

/* Cards */
QFrame.Card, QFrame[class="Card"] {
    background-color: #141414;
    border-radius: 10px;
    border: 1px solid #262626;
    padding: 12px;
}

QFrame.Card:hover, QFrame[class="Card"]:hover {
    border: 1px solid #3F3F46;
    background-color: #1A1A1D;
}

QLabel.KpiTitle {
    font-size: 11px;
    font-weight: 800;
    color: #A1A1AA;
    letter-spacing: 0.6px;
}

QLabel.KpiValue {
    font-size: 22px;
    font-weight: 900;
    color: #FFFFFF;
}

/* Base Buttons */
QPushButton {
    background-color: #18181B;
    color: #FFFFFF;
    border: 1px solid #27272A;
    border-radius: 8px;
    padding: 7px 16px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #27272A;
    border: 1px solid #DC2626;
    color: #FFFFFF;
}

QPushButton:pressed {
    background-color: #18181B;
    border: 1px solid #991B1B;
}

/* Specific Style Buttons */
QPushButton.PrimaryBtn, QPushButton[class="PrimaryBtn"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #991B1B, stop:1 #DC2626);
    color: #FFFFFF;
    border: 1px solid #EF4444;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 800;
}

QPushButton.PrimaryBtn:hover, QPushButton[class="PrimaryBtn"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7F1D1D, stop:1 #B91C1C);
    border: 1px solid #F87171;
    color: #FFFFFF;
}

QPushButton.PrimaryBtn:pressed, QPushButton[class="PrimaryBtn"]:pressed {
    background-color: #551214;
}

QPushButton.SuccessBtn, QPushButton[class="SuccessBtn"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #10B981);
    color: #FFFFFF;
    border: 1px solid #34D399;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 800;
}

QPushButton.SuccessBtn:hover, QPushButton[class="SuccessBtn"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #065F46, stop:1 #059669);
    border: 1px solid #6EE7B7;
    color: #FFFFFF;
}

QPushButton.SuccessBtn:pressed, QPushButton[class="SuccessBtn"]:pressed {
    background-color: #064E3B;
}

QPushButton.DangerBtn, QPushButton[class="DangerBtn"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #991B1B, stop:1 #DC2626);
    color: #FFFFFF;
    border: 1px solid #EF4444;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 800;
}

QPushButton.DangerBtn:hover, QPushButton[class="DangerBtn"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7F1D1D, stop:1 #B91C1C);
    border: 1px solid #F87171;
    color: #FFFFFF;
}

QPushButton.DangerBtn:pressed, QPushButton[class="DangerBtn"]:pressed {
    background-color: #551214;
}

/* Tables */
QTableWidget, QTableView {
    background-color: #121212;
    gridline-color: #27272A;
    border: 1px solid #262626;
    border-radius: 8px;
    selection-background-color: #381216;
    selection-color: #FFFFFF;
    alternate-background-color: #0F0F0F;
    color: #F4F4F5;
}

QHeaderView::section {
    background-color: #18181B;
    color: #FFFFFF;
    font-weight: 800;
    font-size: 12px;
    padding: 8px;
    border: none;
    border-right: 1px solid #27272A;
    border-bottom: 2px solid #DC2626;
}

/* Inputs */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {
    background-color: #141414;
    color: #FFFFFF;
    border: 1px solid #27272A;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
}

QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover, QDateEdit:hover {
    border: 1px solid #3F3F46;
    background-color: #1A1A1D;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {
    border: 1px solid #DC2626;
    background-color: #18181B;
}

/* Fix QSpinBox & QDoubleSpinBox up/down buttons */
QSpinBox, QDoubleSpinBox, QDateEdit {
    padding-right: 28px;
}

QSpinBox::up-button, QDoubleSpinBox::up-button, QDateEdit::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 26px;
    height: 16px;
    border-left: 1px solid #27272A;
    border-bottom: 1px solid #27272A;
    border-top-right-radius: 5px;
    background-color: #18181B;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover, QDateEdit::up-button:hover {
    background-color: #DC2626;
    color: #FFFFFF;
}

QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed, QDateEdit::up-button:pressed {
    background-color: #991B1B;
}

QSpinBox::down-button, QDoubleSpinBox::down-button, QDateEdit::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 26px;
    height: 16px;
    border-left: 1px solid #27272A;
    border-top: 1px solid #27272A;
    border-bottom-right-radius: 5px;
    background-color: #18181B;
}

QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover, QDateEdit::down-button:hover {
    background-color: #DC2626;
    color: #FFFFFF;
}

QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed, QDateEdit::down-button:pressed {
    background-color: #991B1B;
}

QComboBox QAbstractItemView {
    background-color: #141414;
    color: #FFFFFF;
    selection-background-color: #DC2626;
    selection-color: #FFFFFF;
    border: 1px solid #27272A;
}

/* Tab Widgets */
QTabWidget::pane {
    border: 1px solid #262626;
    background: #0D0D0D;
    border-radius: 10px;
    padding: 10px;
}

QTabBar::tab {
    background: #141414;
    color: #A1A1AA;
    font-weight: 700;
    font-size: 13px;
    padding: 9px 20px;
    margin-right: 6px;
    border-radius: 8px;
    border: 1px solid #262626;
}

QTabBar::tab:hover {
    background: #1C1C1F;
    color: #FFFFFF;
    border: 1px solid #3F3F46;
}

QTabBar::tab:selected {
    background: #DC2626;
    color: #FFFFFF;
    border: 1px solid #EF4444;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #0A0A0A;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #262626;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #3F3F46;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Badges / Status Pills */
QLabel.BadgePagado {
    background-color: #064E3B;
    color: #34D399;
    font-weight: 800;
    padding: 3px 8px;
    border-radius: 12px;
}

QLabel.BadgePendiente {
    background-color: #4C1113;
    color: #F87171;
    font-weight: 800;
    padding: 3px 8px;
    border-radius: 12px;
}

QLabel.BadgeParcial {
    background-color: #451A03;
    color: #FBBF24;
    font-weight: 800;
    padding: 3px 8px;
    border-radius: 12px;
}
"""
