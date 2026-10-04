import pytest
import os
import tempfile
import time
from database.connection import DatabaseManager
from models.policia import Policia
from models.mes import Mes
from models.ticket import TicketDiario
from models.vale import Vale
from models.pago import PagoTicket
from models.venta import VentaDiaria
from models.compra import Compra
from models.gasto import Gasto
from models.pago_personal import PagoPersonal
from models.fast_food_consumo import FastFoodConsumo
from models.local import LOCAL_RESTAURANTE, LOCAL_FAST_FOOD, LOCAL_CONSOLIDADO

from services.policia_service import PoliciaService
from services.mes_service import MesService
from services.ticket_service import TicketService
from services.vale_service import ValeService
from services.pago_service import PagoService
from services.venta_service import VentaService
from services.egreso_service import EgresoService
from services.fast_food_service import FastFoodService
from services.financiero_service import FinancieroService
from services.consistency_checker import ConsistencyChecker
from backups.backup_manager import BackupManager
from reports.excel_exporter import ExcelExporter
from reports.pdf_generator import PDFGenerator

@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_reqs.db")
    db_mgr = DatabaseManager(db_path)
    yield db_mgr
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

# 1. Crear policía en BD -> aparece automáticamente en meses futuros sin volver a escribir datos.
def test_1_crear_policia_aparece_en_meses_futuros(temp_db):
    pol_service = PoliciaService()
    pol_service.repo.db = temp_db
    pol_service.mes_repo.db = temp_db
    pol_service.audit_repo.db = temp_db

    mes_service = MesService()
    mes_service.repo.db = temp_db
    mes_service.ticket_repo.db = temp_db
    mes_service.config_repo.db = temp_db
    mes_service.audit_repo.db = temp_db

    # Create month
    ok_m, _, mes_id = mes_service.crear_mes(2026, 9, 12.0)
    assert ok_m is True

    # Register officer in BD
    p = Policia(codigo="APF-25", apellidos="QUISPE MAMANI", nombres="JUAN CARLOS", sa_pnp="12345678", area="AREPOFIS")
    ok_p, _, pol_id = pol_service.crear_policia(p)
    assert ok_p is True

    # Verify officer is in month 9/2026
    policias_mes = mes_service.repo.get_policias_en_mes(mes_id)
    codigos = [item["codigo"] for item in policias_mes]
    assert "APF-25" in codigos

# 2. No duplicar policía con el mismo código.
def test_2_no_duplicar_codigo_policia(temp_db):
    pol_service = PoliciaService()
    pol_service.repo.db = temp_db
    pol_service.mes_repo.db = temp_db
    pol_service.audit_repo.db = temp_db

    p1 = Policia(codigo="APF-25", apellidos="QUISPE", nombres="JUAN", area="SEC")
    ok1, _, _ = pol_service.crear_policia(p1)
    assert ok1 is True

    p2 = Policia(codigo="APF-25", apellidos="MAMANI", nombres="CARLOS", area="SEC")
    ok2, msg, _ = pol_service.crear_policia(p2)
    assert ok2 is False
    assert "ya existe" in msg.lower()

# 3. Historial del policía no cambia si se modifica en BD después.
def test_3_historial_policia_invariable_al_modificar_datos(temp_db):
    pol_service = PoliciaService()
    pol_service.repo.db = temp_db
    pol_service.mes_repo.db = temp_db
    pol_service.audit_repo.db = temp_db

    mes_service = MesService()
    mes_service.repo.db = temp_db
    mes_service.ticket_repo.db = temp_db
    mes_service.config_repo.db = temp_db
    mes_service.audit_repo.db = temp_db

    mes_service.crear_mes(2026, 9, 12.0)
    ok, _, pol_id = pol_service.crear_policia(Policia(codigo="ARE-01", apellidos="LOPEZ", nombres="PEDRO", area="AREPOFIS"))
    
    # Check historical snapshot in mes
    m = mes_service.get_by_anio_mes(2026, 9)
    p_mes = mes_service.repo.get_policias_en_mes(m.id)
    assert p_mes[0]["area_historica"] == "AREPOFIS"

    # Now edit officer's current area in master BD to DEPINCRI
    pol_service.actualizar_policia(Policia(id=pol_id, codigo="ARE-01", apellidos="LOPEZ", nombres="PEDRO", area="DEPINCRI"))

    # Month September still keeps AREPOFIS
    p_mes_after = mes_service.repo.get_policias_en_mes(m.id)
    assert p_mes_after[0]["area_historica"] == "AREPOFIS"

# 4. Inactivar policía -> no aparece en nuevos meses pero conserva historial.
def test_4_inactivar_policia_desaparece_de_nuevos_meses_pero_conserva_historial(temp_db):
    pol_service = PoliciaService()
    pol_service.repo.db = temp_db
    pol_service.mes_repo.db = temp_db
    pol_service.audit_repo.db = temp_db

    mes_service = MesService()
    mes_service.repo.db = temp_db
    mes_service.ticket_repo.db = temp_db
    mes_service.config_repo.db = temp_db
    mes_service.audit_repo.db = temp_db

    mes_service.crear_mes(2026, 9, 12.0)
    ok, _, pol_id = pol_service.crear_policia(Policia(codigo="DEP-50", apellidos="GARCIA", nombres="ANA", area="ADMIN"))
    
    # Inactivate officer
    pol_service.cambiar_estado(pol_id, "INACTIVO")

    # Create new month October 2026
    ok_o, _, mes_oct_id = mes_service.crear_mes(2026, 10, 12.0)
    p_oct = mes_service.repo.get_policias_en_mes(mes_oct_id)
    codigos_oct = [p["codigo"] for p in p_oct]
    assert "DEP-50" not in codigos_oct

    # September still retains the officer
    m_sep = mes_service.get_by_anio_mes(2026, 9)
    p_sep = mes_service.repo.get_policias_en_mes(m_sep.id)
    assert "DEP-50" in [p["codigo"] for p in p_sep]

# 5. Reactivar policía -> vuelve a estar disponible.
def test_5_reactivar_policia(temp_db):
    pol_service = PoliciaService()
    pol_service.repo.db = temp_db
    pol_service.mes_repo.db = temp_db
    pol_service.audit_repo.db = temp_db

    mes_service = MesService()
    mes_service.repo.db = temp_db
    mes_service.ticket_repo.db = temp_db
    mes_service.config_repo.db = temp_db
    mes_service.audit_repo.db = temp_db

    ok, _, pol_id = pol_service.crear_policia(Policia(codigo="DEP-77", apellidos="DIAZ", nombres="LUCAS", area="INTEL"))
    pol_service.cambiar_estado(pol_id, "INACTIVO")
    pol_service.cambiar_estado(pol_id, "ACTIVO")

    ok_n, _, mes_id = mes_service.crear_mes(2026, 11, 12.0)
    p_nov = mes_service.repo.get_policias_en_mes(mes_id)
    assert "DEP-77" in [p["codigo"] for p in p_nov]

# 6. Para unidad = 50, Local = 19 -> Total Tickets = 69.
def test_6_total_tickets_unidad_mas_local(temp_db):
    ticket_service = TicketService()
    ticket_service.repo.db = temp_db
    ticket_service.audit_repo.db = temp_db

    ok, msg, td = ticket_service.guardar_ticket_diario("2026-09-24", para_unidad=50, local=19)
    assert ok is True
    assert td.total_policias == 69
    assert td.para_unidad == 50
    assert td.local == 19

# 7. Vales no se suman a Total Tickets: Para unidad = 50, Local = 19, Vales = 15 -> Total = 69, Vales = 15.
def test_7_vales_no_se_suman_a_tickets(temp_db):
    ticket_service = TicketService()
    ticket_service.repo.db = temp_db
    ticket_service.audit_repo.db = temp_db

    ok, msg, td = ticket_service.guardar_ticket_diario("2026-09-24", para_unidad=50, local=19, vales_policiales=15)
    assert td.total_policias == 69
    assert td.vales_policiales == 15
    assert td.total_policias != 84

# 8. Cálculo de Venta Sin Tickets = Efectivo + Yape: Efectivo = 800, Yape = 350 -> Venta Sin Tickets = 1150.
def test_8_calculo_venta_sin_tickets_efectivo_mas_yape(temp_db):
    venta = VentaDiaria(fecha="2026-09-24", efectivo=800.0, yape=350.0, para_unidad=0, local=0, venta_incluye_tickets=0)
    venta.recalcular()
    assert venta.venta_sin_tickets == 1150.0

# 9. Cálculo de Venta Tickets Policiales = Cantidad Tickets × S/ 12.00 (o precio histórico): 69 tickets × 12 = 828.00.
def test_9_calculo_venta_tickets_policiales_por_precio_historico(temp_db):
    venta = VentaDiaria(fecha="2026-09-24", efectivo=1000.0, yape=500.0, para_unidad=50, local=19, precio_ticket_aplicado=12.00)
    venta.recalcular()
    assert venta.cantidad_tickets == 69
    assert venta.venta_tickets == 828.00

# 10. Cálculo de Venta Total: Efectivo = 800, Yape = 350, Tickets = 69 (S/ 828) -> Total = 1978.00.
def test_10_calculo_venta_total_segun_configuracion(temp_db):
    venta = VentaDiaria(fecha="2026-09-24", efectivo=800.0, yape=350.0, para_unidad=50, local=19, precio_ticket_aplicado=12.00, venta_incluye_tickets=0)
    venta.recalcular()
    assert venta.venta_total == 1978.00

# 11. Consumo Local Fast Food: Tickets = 12, Vales = 8 -> Total consumido = 20.
def test_11_consumo_local_fast_food(temp_db):
    ff_service = FastFoodService()
    ff_service.repo.db = temp_db
    ok, msg, c = ff_service.guardar_consumo("2026-09-24", tickets_local=12, vales_local=8)
    assert ok is True
    assert c.total_consumido == 20

# 12. Separación total de movimientos entre Restaurante y Fast Food.
def test_12_separacion_total_dos_locales(temp_db):
    egreso_service = EgresoService()
    egreso_service.compra_repo.db = temp_db
    egreso_service.gasto_repo.db = temp_db
    egreso_service.pago_personal_repo.db = temp_db

    # Compra restaurante
    c_rest = Compra(fecha="2026-09-24", local_id=LOCAL_RESTAURANTE, proveedor="CARNES SAC", descripcion="Carne", total=500.0)
    egreso_service.registrar_compra(c_rest)

    # Compra fast food
    c_ff = Compra(fecha="2026-09-24", local_id=LOCAL_FAST_FOOD, proveedor="PAPAS SAC", descripcion="Papas", total=200.0)
    egreso_service.registrar_compra(c_ff)

    tot_rest = egreso_service.compra_repo.get_total_mes(2026, 9, LOCAL_RESTAURANTE)
    tot_ff = egreso_service.compra_repo.get_total_mes(2026, 9, LOCAL_FAST_FOOD)

    assert tot_rest == 500.0
    assert tot_ff == 200.0

# 13. Consolidado de ambos locales: Restaurante = 500, Fast Food = 200 -> Consolidado = 700.
def test_13_consolidado_ambos_locales(temp_db):
    egreso_service = EgresoService()
    egreso_service.compra_repo.db = temp_db
    egreso_service.gasto_repo.db = temp_db
    egreso_service.pago_personal_repo.db = temp_db

    c_rest = Compra(fecha="2026-09-24", local_id=LOCAL_RESTAURANTE, proveedor="P1", descripcion="Desc1", total=500.0)
    c_ff = Compra(fecha="2026-09-24", local_id=LOCAL_FAST_FOOD, proveedor="P2", descripcion="Desc2", total=200.0)
    egreso_service.registrar_compra(c_rest)
    egreso_service.registrar_compra(c_ff)

    tot_cons = egreso_service.compra_repo.get_total_mes(2026, 9, LOCAL_CONSOLIDADO)
    assert tot_cons == 700.0

# 14. Compras por local y consolidado.
def test_14_compras_por_local_y_consolidado(temp_db):
    egreso_service = EgresoService()
    egreso_service.compra_repo.db = temp_db
    egreso_service.gasto_repo.db = temp_db
    egreso_service.pago_personal_repo.db = temp_db

    egreso_service.registrar_compra(Compra(fecha="2026-09-01", local_id=LOCAL_RESTAURANTE, proveedor="P1", descripcion="D1", total=100.0))
    egreso_service.registrar_compra(Compra(fecha="2026-09-02", local_id=LOCAL_FAST_FOOD, proveedor="P2", descripcion="D2", total=150.0))

    assert egreso_service.compra_repo.get_total_mes(2026, 9, LOCAL_RESTAURANTE) == 100.0
    assert egreso_service.compra_repo.get_total_mes(2026, 9, LOCAL_FAST_FOOD) == 150.0
    assert egreso_service.compra_repo.get_total_mes(2026, 9, LOCAL_CONSOLIDADO) == 250.0

# 15. Gastos por local y consolidado.
def test_15_gastos_por_local_y_consolidado(temp_db):
    egreso_service = EgresoService()
    egreso_service.compra_repo.db = temp_db
    egreso_service.gasto_repo.db = temp_db
    egreso_service.pago_personal_repo.db = temp_db

    egreso_service.registrar_gasto(Gasto(fecha="2026-09-05", local_id=LOCAL_RESTAURANTE, categoria="LUZ", descripcion="Luz", monto=80.0))
    egreso_service.registrar_gasto(Gasto(fecha="2026-09-05", local_id=LOCAL_FAST_FOOD, categoria="AGUA", descripcion="Agua", monto=40.0))

    assert egreso_service.gasto_repo.get_total_mes(2026, 9, LOCAL_RESTAURANTE) == 80.0
    assert egreso_service.gasto_repo.get_total_mes(2026, 9, LOCAL_FAST_FOOD) == 40.0
    assert egreso_service.gasto_repo.get_total_mes(2026, 9, LOCAL_CONSOLIDADO) == 120.0

# 16. Pagos al personal por local y consolidado.
def test_16_pagos_personal_por_local_y_consolidado(temp_db):
    egreso_service = EgresoService()
    egreso_service.compra_repo.db = temp_db
    egreso_service.gasto_repo.db = temp_db
    egreso_service.pago_personal_repo.db = temp_db

    egreso_service.registrar_pago_personal(PagoPersonal(fecha="2026-09-15", local_id=LOCAL_RESTAURANTE, trabajador="Juan", cargo="Mozo", monto=300.0))
    egreso_service.registrar_pago_personal(PagoPersonal(fecha="2026-09-15", local_id=LOCAL_FAST_FOOD, trabajador="Pedro", cargo="Cocinero", monto=350.0))

    assert egreso_service.pago_personal_repo.get_total_mes(2026, 9, LOCAL_RESTAURANTE) == 300.0
    assert egreso_service.pago_personal_repo.get_total_mes(2026, 9, LOCAL_FAST_FOOD) == 350.0
    assert egreso_service.pago_personal_repo.get_total_mes(2026, 9, LOCAL_CONSOLIDADO) == 650.0

# 17. Total Egresos = Compras + Gastos + Pagos al Personal: Compras = 100, Gastos = 50, Personal = 200 -> Egresos = 350.
def test_17_total_egresos(temp_db):
    egreso_service = EgresoService()
    egreso_service.compra_repo.db = temp_db
    egreso_service.gasto_repo.db = temp_db
    egreso_service.pago_personal_repo.db = temp_db

    egreso_service.registrar_compra(Compra(fecha="2026-09-10", local_id=LOCAL_RESTAURANTE, proveedor="P", descripcion="D", total=100.0))
    egreso_service.registrar_gasto(Gasto(fecha="2026-09-10", local_id=LOCAL_RESTAURANTE, categoria="C", descripcion="D", monto=50.0))
    egreso_service.registrar_pago_personal(PagoPersonal(fecha="2026-09-10", local_id=LOCAL_RESTAURANTE, trabajador="T", cargo="C", monto=200.0))

    res = egreso_service.get_resumen_egresos_mes(2026, 9, LOCAL_RESTAURANTE)
    assert res["total_compras"] == 100.0
    assert res["total_gastos"] == 50.0
    assert res["total_personal"] == 200.0
    assert res["total_egresos"] == 350.0

# 18. Saldo del Día = Venta Total - Total Egresos: Venta Total = 1000, Total Egresos = 350 -> Saldo = 650.
def test_18_saldo_del_dia(temp_db):
    fin_service = FinancieroService()
    fin_service.venta_repo.db = temp_db
    fin_service.compra_repo.db = temp_db
    fin_service.gasto_repo.db = temp_db
    fin_service.pago_pers_repo.db = temp_db

    # Venta total 1000
    v = VentaDiaria(fecha="2026-09-10", local_id=LOCAL_RESTAURANTE, efectivo=1000.0, yape=0.0)
    fin_service.venta_repo.save(v)

    # Egresos 350 (100 + 50 + 200)
    fin_service.compra_repo.save(Compra(fecha="2026-09-10", local_id=LOCAL_RESTAURANTE, proveedor="P", descripcion="D", total=100.0))
    fin_service.gasto_repo.save(Gasto(fecha="2026-09-10", local_id=LOCAL_RESTAURANTE, categoria="C", descripcion="D", monto=50.0))
    fin_service.pago_pers_repo.save(PagoPersonal(fecha="2026-09-10", local_id=LOCAL_RESTAURANTE, trabajador="T", cargo="C", monto=200.0))

    cal = fin_service.get_calendario_financiero_mes(2026, 9, LOCAL_RESTAURANTE)
    dia_10 = [d for d in cal if d["fecha"] == "2026-09-10"][0]
    assert dia_10["venta_total"] == 1000.0
    assert dia_10["total_egresos"] == 350.0
    assert dia_10["saldo"] == 650.0

# 19. Control de Vales: Vales entregados = 300, Vales canjeados = 260 -> Saldo = 40.
def test_19_control_vales_saldo_y_alertas(temp_db):
    vale_service = ValeService()
    vale_service.repo.db = temp_db
    vale_service.audit_repo.db = temp_db

    ok, msg, v = vale_service.guardar_vale("2026-09-30", vales_entregados=300, vales_canjeados=260)
    assert ok is True
    assert v.saldo == 40
    assert not v.has_alerta_saldo_negativo

# 20. Control de Pagos de Tickets: Total = 69, Pagados = 40, Debidos = 29 -> Estado = PARCIAL.
def test_20_control_pagos_tickets_estados(temp_db):
    pago_service = PagoService()
    pago_service.repo.db = temp_db
    pago_service.ticket_repo.db = temp_db
    pago_service.audit_repo.db = temp_db

    ok, msg, p = pago_service.registrar_pago("2026-09-24", total_tickets=69, tickets_pagados=40, tickets_debidos=29)
    assert ok is True
    assert p.estado == "PARCIAL"
    assert p.tickets_pagados == 40
    assert p.tickets_debidos == 29

# 21. Reporte mensual Excel exportado exitosamente.
def test_21_reporte_mensual_excel(temp_db):
    mes_service = MesService()
    mes_service.repo.db = temp_db
    mes_service.ticket_repo.db = temp_db
    mes_service.config_repo.db = temp_db
    mes_service.audit_repo.db = temp_db
    mes_service.crear_mes(2026, 9, 12.0)

    exporter = ExcelExporter()
    exporter.policia_repo.db = temp_db
    exporter.mes_repo.db = temp_db
    exporter.ticket_repo.db = temp_db
    exporter.vale_repo.db = temp_db
    exporter.pago_repo.db = temp_db
    exporter.venta_repo.db = temp_db

    tmp_out = os.path.join(tempfile.gettempdir(), "test_reporte_mensual.xlsx")
    res = exporter.exportar_reporte_mensual(2026, 9, tmp_out, LOCAL_RESTAURANTE)
    assert res is True
    assert os.path.exists(tmp_out)
    assert os.path.getsize(tmp_out) > 1000
    os.remove(tmp_out)

# 22. Reporte mensual PDF exportado exitosamente.
def test_22_reporte_mensual_pdf(temp_db):
    mes_service = MesService()
    mes_service.repo.db = temp_db
    mes_service.ticket_repo.db = temp_db
    mes_service.config_repo.db = temp_db
    mes_service.audit_repo.db = temp_db
    mes_service.crear_mes(2026, 9, 12.0)

    pdf_gen = PDFGenerator()
    pdf_gen.mes_repo.db = temp_db
    pdf_gen.ticket_repo.db = temp_db
    pdf_gen.vale_repo.db = temp_db
    pdf_gen.pago_repo.db = temp_db
    pdf_gen.venta_repo.db = temp_db

    tmp_out = os.path.join(tempfile.gettempdir(), "test_reporte_mensual.pdf")
    res = pdf_gen.generar_reporte_mensual_pdf(2026, 9, tmp_out)
    assert res is True
    assert os.path.exists(tmp_out)
    assert os.path.getsize(tmp_out) > 500
    os.remove(tmp_out)

# 23. Reporte anual de 12 meses.
def test_23_reporte_anual_12_meses(temp_db):
    fin_service = FinancieroService()
    fin_service.venta_repo.db = temp_db
    fin_service.compra_repo.db = temp_db
    fin_service.gasto_repo.db = temp_db
    fin_service.pago_pers_repo.db = temp_db

    anual = fin_service.get_resumen_anual(2026, LOCAL_CONSOLIDADO)
    assert len(anual) == 12
    assert anual[0]["mes_nombre"] == "ENERO"
    assert anual[11]["mes_nombre"] == "DICIEMBRE"

# 24. Copia de seguridad y restauración.
def test_24_copias_seguridad(temp_db):
    bm = BackupManager(db_path=temp_db.db_path)
    ok_b, msg_b, backup_path = bm.crear_backup(usuario="TEST_USER")
    assert ok_b is True
    assert os.path.exists(backup_path)

    ok_v, _ = bm.verificar_integridad(backup_path)
    assert ok_v is True

# 25. Rendimiento de carga masiva de matriz con 100 policías en menos de 1 segundo.
def test_25_rendimiento_carga_100_policias_sub_segundo(temp_db):
    pol_service = PoliciaService()
    pol_service.repo.db = temp_db
    pol_service.mes_repo.db = temp_db
    pol_service.audit_repo.db = temp_db

    mes_service = MesService()
    mes_service.repo.db = temp_db
    mes_service.ticket_repo.db = temp_db
    mes_service.config_repo.db = temp_db
    mes_service.audit_repo.db = temp_db

    ticket_service = TicketService()
    ticket_service.repo.db = temp_db
    ticket_service.mes_repo.db = temp_db
    ticket_service.audit_repo.db = temp_db

    ok_m, _, mes_id = mes_service.crear_mes(2026, 9, 12.0)

    # Insert 100 officers in bulk
    with temp_db.get_connection() as conn:
        for i in range(1, 101):
            conn.execute(
                "INSERT INTO policias (codigo, apellidos, nombres, area, estado) VALUES (?, ?, ?, ?, 'ACTIVO')",
                (f"POL-{i:03d}", f"APELLIDO_{i}", f"NOMBRE_{i}", "AREPOFIS")
            )
        conn.commit()

    # Sync into month
    mes_service.repo.sincronizar_policias_mes(mes_id)

    # Measure time to get matrix with 100 officers
    t0 = time.time()
    policias, num_dias, matriz = ticket_service.get_matriz_tickets_mes(mes_id)
    t1 = time.time()
    elapsed = t1 - t0

    assert len(policias) == 100
    assert elapsed < 1.0  # Must be sub-second
