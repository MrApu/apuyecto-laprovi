# Theme and stylesheet definitions for Control Policial GUI (Tremor / Modern Slate Edition)

COLOR_PRIMARY = "#6366F1"        # Indigo
COLOR_PRIMARY_LIGHT = "#818CF8"  # Indigo light
COLOR_SUCCESS = "#10B981"        # Emerald
COLOR_WARNING = "#F59E0B"        # Amber
COLOR_DANGER = "#F43F5E"         # Rose / Red
COLOR_INFO = "#06B6D4"           # Cyan
COLOR_BG_DARK = "#090D16"        # Midnight Slate
COLOR_SURFACE = "#111827"        # Dark Card
COLOR_BORDER = "#1F2937"         # Border Subtlety

QSS_STYLE = """
QMainWindow {
    background-color: #090D16;
}

QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: #F3F4F6;
    background-color: transparent;
}

/* Sidebar */
#Sidebar {
    background-color: #0B0F19;
    min-width: 230px;
    max-width: 230px;
    border-right: 1px solid #1F2937;
}

#Sidebar QPushButton {
    background-color: transparent;
    color: #9CA3AF;
    border: none;
    text-align: left;
    padding: 11px 18px;
    font-size: 13px;
    font-weight: 600;
    border-left: 3px solid transparent;
    border-radius: 0px;
}

#Sidebar QPushButton:hover {
    background-color: #111827;
    color: #F9FAFB;
}

#Sidebar QPushButton:checked {
    background-color: #1F2937;
    color: #818CF8;
    border-left: 3px solid #6366F1;
    font-weight: 700;
}

/* Top Bar */
#TopBar {
    background-color: #0F172A;
    border-bottom: 1px solid #1F2937;
    padding: 8px 16px;
}

/* Cards */
QFrame.Card, QFrame[class="Card"] {
    background-color: #111827;
    border-radius: 10px;
    border: 1px solid #1F2937;
    padding: 12px;
}

QLabel.KpiTitle {
    font-size: 11px;
    font-weight: 700;
    color: #9CA3AF;
    letter-spacing: 0.5px;
}

QLabel.KpiValue {
    font-size: 22px;
    font-weight: 800;
    color: #F9FAFB;
}

/* Buttons */
QPushButton.PrimaryBtn, QPushButton[class="PrimaryBtn"] {
    background-color: #6366F1;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 700;
}

QPushButton.PrimaryBtn:hover, QPushButton[class="PrimaryBtn"]:hover {
    background-color: #4F46E5;
}

QPushButton.SuccessBtn, QPushButton[class="SuccessBtn"] {
    background-color: #10B981;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 700;
}

QPushButton.SuccessBtn:hover, QPushButton[class="SuccessBtn"]:hover {
    background-color: #059669;
}

QPushButton.DangerBtn, QPushButton[class="DangerBtn"] {
    background-color: #F43F5E;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 700;
}

QPushButton.DangerBtn:hover, QPushButton[class="DangerBtn"]:hover {
    background-color: #E11D48;
}

/* Tables */
QTableWidget, QTableView {
    background-color: #0F172A;
    gridline-color: #1E293B;
    border: 1px solid #1F2937;
    border-radius: 8px;
    selection-background-color: #312E81;
    selection-color: #E0E7FF;
    alternate-background-color: #0B0F19;
    color: #F3F4F6;
}

QHeaderView::section {
    background-color: #1E293B;
    color: #F9FAFB;
    font-weight: 700;
    font-size: 12px;
    padding: 7px;
    border: none;
    border-right: 1px solid #334155;
    border-bottom: 1px solid #334155;
}

/* Inputs */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {
    background-color: #111827;
    color: #F9FAFB;
    border: 1px solid #374151;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {
    border: 1px solid #6366F1;
    background-color: #1F2937;
}

QComboBox QAbstractItemView {
    background-color: #111827;
    color: #F9FAFB;
    selection-background-color: #6366F1;
    selection-color: #FFFFFF;
    border: 1px solid #374151;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #090D16;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #1F2937;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #374151;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Badges / Status Pills */
QLabel.BadgePagado {
    background-color: #064E3B;
    color: #34D399;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 12px;
}

QLabel.BadgePendiente {
    background-color: #881337;
    color: #FB7185;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 12px;
}

QLabel.BadgeParcial {
    background-color: #78350F;
    color: #FBBF24;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 12px;
}
"""
