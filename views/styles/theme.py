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
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    color: #F3F4F6;
    background-color: transparent;
}

/* Sidebar */
#Sidebar {
    background-color: #0B0F19;
    min-width: 240px;
    max-width: 240px;
    border-right: 1px solid #1F2937;
}

#Sidebar QPushButton {
    background-color: transparent;
    color: #94A3B8;
    border: 1px solid transparent;
    text-align: left;
    padding: 10px 16px;
    font-size: 12px;
    font-weight: 600;
    border-left: 3px solid transparent;
    border-radius: 6px;
}

#Sidebar QPushButton:hover {
    background-color: #1E293B;
    color: #FFFFFF;
    border: 1px solid #334155;
    border-left: 3px solid #38BDF8;
}

#Sidebar QPushButton:checked {
    background-color: #1E1B4B;
    color: #C7D2FE;
    border: 1px solid #3730A3;
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

QFrame.Card:hover, QFrame[class="Card"]:hover {
    border: 1px solid #334155;
    background-color: #141E33;
}

QLabel.KpiTitle {
    font-size: 11px;
    font-weight: 700;
    color: #94A3B8;
    letter-spacing: 0.5px;
}

QLabel.KpiValue {
    font-size: 22px;
    font-weight: 800;
    color: #F9FAFB;
}

/* Base Buttons */
QPushButton {
    background-color: #1E293B;
    color: #F1F5F9;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 7px 16px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #273549;
    border: 1px solid #6366F1;
    color: #FFFFFF;
}

QPushButton:pressed {
    background-color: #1E1B4B;
    border: 1px solid #4F46E5;
}

/* Specific Style Buttons */
QPushButton.PrimaryBtn, QPushButton[class="PrimaryBtn"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F46E5, stop:1 #6366F1);
    color: #FFFFFF;
    border: 1px solid #818CF8;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 700;
}

QPushButton.PrimaryBtn:hover, QPushButton[class="PrimaryBtn"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338CA, stop:1 #4F46E5);
    border: 1px solid #A5B4FC;
    color: #FFFFFF;
}

QPushButton.PrimaryBtn:pressed, QPushButton[class="PrimaryBtn"]:pressed {
    background-color: #3730A3;
}

QPushButton.SuccessBtn, QPushButton[class="SuccessBtn"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
    color: #FFFFFF;
    border: 1px solid #34D399;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 700;
}

QPushButton.SuccessBtn:hover, QPushButton[class="SuccessBtn"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
    border: 1px solid #6EE7B7;
    color: #FFFFFF;
}

QPushButton.SuccessBtn:pressed, QPushButton[class="SuccessBtn"]:pressed {
    background-color: #065F46;
}

QPushButton.DangerBtn, QPushButton[class="DangerBtn"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E11D48, stop:1 #F43F5E);
    color: #FFFFFF;
    border: 1px solid #FB7185;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 700;
}

QPushButton.DangerBtn:hover, QPushButton[class="DangerBtn"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #BE123C, stop:1 #E11D48);
    border: 1px solid #FDA4AF;
    color: #FFFFFF;
}

QPushButton.DangerBtn:pressed, QPushButton[class="DangerBtn"]:pressed {
    background-color: #9F1239;
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
    padding: 8px;
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

QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover, QDateEdit:hover {
    border: 1px solid #4B5563;
    background-color: #162032;
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
