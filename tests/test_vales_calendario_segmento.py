import pytest
import os
from PySide6.QtWidgets import QApplication, QTableWidget
from services.ticket_service import TicketService
from models.ticket import TicketDiario
from models.vale import Vale

def test_ticket_service_calendario_con_vales():
    service = TicketService()
    anio, mes = 2026, 9
    
    # Save a test day with unit tickets, local tickets, vales delivered and vales redeemed
    fecha = "2026-09-15"
    ok, msg = service.guardar_ticket_y_vales(
        fecha=fecha,
        para_unidad=40,
        local=25,
        vales_entregados=15,
        vales_canjeados=10,
        observacion="Control especial"
    )
    assert ok is True

    # Retrieve matrix con vales
    dias = service.get_calendario_con_vales(anio, mes)
    assert len(dias) >= 28

    dia_15 = next((d for d in dias if d["fecha"] == fecha), None)
    assert dia_15 is not None
    assert dia_15["para_unidad"] == 40
    assert dia_15["local"] == 25
    assert dia_15["total_policias"] == 65
    assert dia_15["vales_entregados"] == 15
    assert dia_15["vales_canjeados"] == 10
    # Descuento exacto: Saldo restante = Entregados - Canjeados
    assert dia_15["saldo_dia"] == 5

def test_calendario_view_segmento_vales():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication([])

    from views.calendario_view import CalendarioView
    v_cal = CalendarioView()
    v_cal.set_periodo(2026, 9)

    # Check that segment button and stacked widget exist
    assert hasattr(v_cal, "btn_view_vales")
    assert hasattr(v_cal, "table_vales")
    assert v_cal.table_vales.editTriggers() == QTableWidget.NoEditTriggers

    # Switch to segment 2
    v_cal._set_view_mode(2)
    assert v_cal.stack.currentIndex() == 2
    assert v_cal.btn_view_vales.isChecked() is True
    assert v_cal.table_vales.rowCount() >= 28

    # Test copying WhatsApp text
    v_cal._copiar_whatsapp_vales()
    clipboard_txt = QApplication.clipboard().text()
    assert "CONTROL DIARIO DE VALES Y TICKETS POLICIALES" in clipboard_txt
    assert "CONSUMO DE TICKETS POLICIALES" in clipboard_txt
    assert "BALANCE DE VALES POLICIALES" in clipboard_txt
    assert "VALES RESTANTES POR CANJEAR" in clipboard_txt

def test_dia_ticket_dialog_tickets_y_vales():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication([])

    from views.dialogs.dia_ticket_dialog import DiaTicketDialog

    td = TicketDiario(
        fecha="2026-09-15",
        anio=2026,
        mes=9,
        dia=15,
        dia_semana="Martes",
        para_unidad=30,
        local=20,
        total_policias=50
    )
    vl = Vale(
        fecha="2026-09-15",
        vales_entregados=12,
        vales_consumidos=8,
        saldo=4
    )

    saved_payload = {}
    def dummy_callback(t, ent, canj, motivo):
        saved_payload["td"] = t
        saved_payload["ent"] = ent
        saved_payload["canj"] = canj
        saved_payload["motivo"] = motivo

    dlg = DiaTicketDialog(ticket_diario=td, vale=vl, on_save_callback=dummy_callback)
    assert dlg.spn_unidad.value() == 30
    assert dlg.spn_local.value() == 20
    assert dlg.spn_vales_entregados.value() == 12
    assert dlg.spn_vales_canjeados.value() == 8
    assert "4 vales pendientes de canje" in dlg.lbl_saldo_vales_value.text()

    # Modify values
    dlg.spn_unidad.setValue(35)
    dlg.spn_vales_canjeados.setValue(12)
    assert "0 (Vales al día)" in dlg.lbl_saldo_vales_value.text()

    dlg._ejecutar_guardado()
    assert saved_payload["td"].para_unidad == 35
    assert saved_payload["td"].total_policias == 55
    assert saved_payload["ent"] == 12
    assert saved_payload["canj"] == 12
