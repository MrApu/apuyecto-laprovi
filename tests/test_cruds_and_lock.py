import pytest
import os
from PySide6.QtWidgets import QApplication, QTableWidget

def test_all_views_have_no_edit_triggers():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication([])

    from views.configuracion_view import ConfiguracionView
    from views.egresos_view import EgresosView
    from views.observaciones_view import ObservacionesView
    from views.fast_food_view import FastFoodView
    from views.vales_view import ValesView
    from views.ventas_view import VentasView
    from views.pagos_view import PagosView
    from views.tickets_policia_view import TicketsPoliciaView
    from views.backup_view import BackupView
    from views.reportes_view import ReportesView
    from views.policias_view import PoliciasView
    from views.calendario_view import CalendarioView

    # 1. ConfiguracionView
    v_conf = ConfiguracionView()
    assert v_conf.table_params.editTriggers() == QTableWidget.NoEditTriggers
    assert v_conf.table_hist_precio.editTriggers() == QTableWidget.NoEditTriggers
    assert v_conf.table_audit.editTriggers() == QTableWidget.NoEditTriggers

    # 2. EgresosView
    v_egr = EgresosView()
    assert v_egr.tbl_compras.editTriggers() == QTableWidget.NoEditTriggers
    assert v_egr.tbl_gastos.editTriggers() == QTableWidget.NoEditTriggers
    assert v_egr.tbl_personal.editTriggers() == QTableWidget.NoEditTriggers

    # 3. ObservacionesView
    v_obs = ObservacionesView()
    assert v_obs.table.editTriggers() == QTableWidget.NoEditTriggers

    # 4. FastFoodView
    v_ff = FastFoodView()
    assert v_ff.table.editTriggers() == QTableWidget.NoEditTriggers

    # 5. ValesView
    v_val = ValesView()
    assert v_val.table.editTriggers() == QTableWidget.NoEditTriggers

    # 6. VentasView
    v_vnt = VentasView()
    assert v_vnt.table.editTriggers() == QTableWidget.NoEditTriggers

    # 7. PagosView
    v_pg = PagosView()
    assert v_pg.table.editTriggers() == QTableWidget.NoEditTriggers

    # 8. TicketsPoliciaView
    v_tp = TicketsPoliciaView()
    assert v_tp.table.editTriggers() == QTableWidget.NoEditTriggers

    # 9. BackupView
    v_bk = BackupView()
    assert v_bk.table.editTriggers() == QTableWidget.NoEditTriggers

    # 10. ReportesView
    v_rep = ReportesView()
    assert v_rep.table_preview.editTriggers() == QTableWidget.NoEditTriggers

    # 11. PoliciasView
    v_pol = PoliciasView()
    assert v_pol.table.editTriggers() == QTableWidget.NoEditTriggers

    # 12. CalendarioView (List table)
    v_cal = CalendarioView()
    assert v_cal.table.editTriggers() == QTableWidget.NoEditTriggers
