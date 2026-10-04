# Theme and stylesheet definitions for Control Policial GUI

COLOR_PRIMARY = "#1F4E78"
COLOR_PRIMARY_LIGHT = "#2E75B6"
COLOR_SUCCESS = "#2E7D32"  # Verde = pagado / correcto
COLOR_WARNING = "#F9A825"  # Amarillo = dato a completar / advertencia
COLOR_DANGER = "#C62828"   # Rojo = error / deuda / inconsistencia
COLOR_INFO = "#1565C0"     # Azul = información general

QSS_STYLE = """
QMainWindow {
    background-color: #F4F6F9;
}

QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: #2C3E50;
}

/* Sidebar */
#Sidebar {
    background-color: #1A252F;
    min-width: 220px;
    max-width: 220px;
}

#Sidebar QPushButton {
    background-color: transparent;
    color: #BDC3C7;
    border: none;
    text-align: left;
    padding: 12px 18px;
    font-size: 13px;
    font-weight: 500;
    border-left: 4px solid transparent;
}

#Sidebar QPushButton:hover {
    background-color: #2C3E50;
    color: #FFFFFF;
}

#Sidebar QPushButton:checked {
    background-color: #2C3E50;
    color: #3498DB;
    border-left: 4px solid #3498DB;
    font-weight: bold;
}

/* Top Bar */
#TopBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
    padding: 8px 16px;
}

/* Cards */
QFrame.Card {
    background-color: #FFFFFF;
    border-radius: 8px;
    border: 1px solid #E2E8F0;
    padding: 12px;
}

QLabel.KpiTitle {
    font-size: 11px;
    font-weight: bold;
    color: #7F8C8D;
    text-transform: uppercase;
}

QLabel.KpiValue {
    font-size: 20px;
    font-weight: bold;
    color: #2C3E50;
}

/* Buttons */
QPushButton.PrimaryBtn {
    background-color: #1F4E78;
    color: #FFFFFF;
    border: none;
    border-radius: 5px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton.PrimaryBtn:hover {
    background-color: #2E75B6;
}

QPushButton.SuccessBtn {
    background-color: #2E7D32;
    color: #FFFFFF;
    border: none;
    border-radius: 5px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton.SuccessBtn:hover {
    background-color: #388E3C;
}

QPushButton.DangerBtn {
    background-color: #C62828;
    color: #FFFFFF;
    border: none;
    border-radius: 5px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton.DangerBtn:hover {
    background-color: #D32F2F;
}

/* Tables */
QTableWidget, QTableView {
    background-color: #FFFFFF;
    gridline-color: #E2E8F0;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    selection-background-color: #E0F2FE;
    selection-color: #0369A1;
    alternate-background-color: #F8FAFC;
}

QHeaderView::section {
    background-color: #1F4E78;
    color: #FFFFFF;
    font-weight: bold;
    font-size: 12px;
    padding: 6px;
    border: none;
    border-right: 1px solid #2E75B6;
}

/* Inputs */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 13px;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {
    border: 2px solid #1F4E78;
}

/* Badges / Status Pills */
QLabel.BadgePagado {
    background-color: #E8F5E9;
    color: #2E7D32;
    font-weight: bold;
    padding: 3px 8px;
    border-radius: 4px;
}

QLabel.BadgePendiente {
    background-color: #FFEBEE;
    color: #C62828;
    font-weight: bold;
    padding: 3px 8px;
    border-radius: 4px;
}

QLabel.BadgeParcial {
    background-color: #FFF9C4;
    color: #F57F17;
    font-weight: bold;
    padding: 3px 8px;
    border-radius: 4px;
}
"""
