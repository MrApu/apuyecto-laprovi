import pytest
import os
from datetime import date
from PySide6.QtWidgets import QApplication, QTableWidget
from services.financiero_service import FinancieroService
from database.connection import DatabaseManager

def test_financiero_service_separacion_tickets_y_cobranzas():
    service = FinancieroService()
    # Test for current year and month
    today = date.today()
    datos = service.get_calendario_financiero_mes(today.year, today.month)
    
    assert isinstance(datos, list)
    if len(datos) > 0:
        d = datos[0]
        assert "venta_local" in d
        assert "cantidad_tickets" in d
        assert "precio_ticket" in d
        assert "venta_tickets" in d
        assert "venta_total" in d
        assert "policias_pagaron" in d
        assert "policias_deben" in d
        # Check calculation consistency: venta_total >= venta_local
        assert d["venta_total"] >= d["venta_local"]

def test_calendario_financiero_view_no_edit_and_whatsapp():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication([])

    from views.calendario_financiero_view import CalendarioFinancieroView, FloatingMiniReportPopup
    v_fin = CalendarioFinancieroView()
    assert v_fin.table.editTriggers() == QTableWidget.NoEditTriggers

    # Test sample row for whatsapp generation
    sample_row = {
        "fecha": "2026-10-15",
        "venta_local": 250.0,
        "efectivo": 150.0,
        "yape": 100.0,
        "cantidad_tickets": 10,
        "precio_ticket": 12.0,
        "venta_tickets": 120.0,
        "venta_total": 370.0,
        "egresos": 80.0,
        "saldo": 290.0,
        "policias_pagaron": [{"policia": "Perez Juan", "tickets": 5, "monto": 60.0, "medio": "Efectivo"}],
        "policias_deben": [{"policia": "Gomez Carlos", "tickets": 3, "monto": 36.0}]
    }

    # Verify popup builds correctly
    popup = FloatingMiniReportPopup()
    popup.set_data(sample_row, "Principal")
    assert "250.00" in popup.lbl_venta_local.text()
    assert "120.00" in popup.lbl_tickets.text()
    assert "370.00" in popup.lbl_venta_total.text()

    # Verify whatsapp dia text logic works
    from PySide6.QtGui import QClipboard
    # Call internal helper logic directly or verify clipboard
    v_fin._copiar_whatsapp_dia(sample_row)
    clipboard = QApplication.clipboard().text()
    assert "VENTA DEL LOCAL" in clipboard
    assert "SOLO TICKETS PNP" in clipboard
    assert "COBRANZAS DEL DÍA" in clipboard
    assert "Perez Juan" in clipboard
    assert "Gomez Carlos" in clipboard
