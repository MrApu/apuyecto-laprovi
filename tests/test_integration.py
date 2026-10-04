import pytest
import os
import tempfile
import sqlite3
from database.connection import DatabaseManager
from models.policia import Policia
from models.mes import Mes
from models.ticket import TicketDiario
from models.vale import Vale
from models.pago import PagoTicket
from models.venta import VentaDiaria
from services.policia_service import PoliciaService
from services.mes_service import MesService
from services.ticket_service import TicketService
from services.vale_service import ValeService
from services.pago_service import PagoService
from services.venta_service import VentaService
from services.consistency_checker import ConsistencyChecker
from backups.backup_manager import BackupManager
from imports.excel_importer import ExcelImporter
from reports.excel_exporter import ExcelExporter
from reports.pdf_generator import PDFGenerator

@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_control.db")
    db_mgr = DatabaseManager(db_path)
    yield db_mgr
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

def test_prueba_1_crear_policia_aparece_en_modulo_mensual(temp_db):
    """PRUEBA 1: Crear policía en BD -> aparece automáticamente en el módulo mensual."""
    pol_service = PoliciaService(policia_repo=None, mes_repo=None, audit_repo=None)
    pol_service.repo.db = temp_db
    pol_service.mes_repo.db = temp_db
    pol_service.audit_repo.db = temp_db

    mes_service = MesService(mes_repo=None, ticket_repo=None, config_repo=None, audit_repo=None)
    mes_service.repo.db = temp_db
    mes_service.ticket_repo.db = temp_db
    mes_service.config_repo.db = temp_db
    mes_service.audit_repo.db = temp_db

    ticket_service = TicketService()
    ticket_service.repo.db = temp_db
    ticket_service.mes_repo.db = temp_db
    ticket_service.audit_repo.db = temp_db

    # 1. Crear mes de Septiembre 2026
    ok_m, _, mes_id = mes_service.crear_mes(2026, 9, 15.0)
    assert ok_m is True
    assert mes_id is not None

    # 2. Crear policía en BD
    pol = Policia(
        codigo="APF-25",
        apellidos="QUISPE MAMANI",
        nombres="JUAN CARLOS",
        sa_pnp="12345678",
        area="AREPOFIS",
        estado="ACTIVO"
    )
    ok_p, _, pol_id = pol_service.crear_policia(pol)
    assert ok_p is True

    # 3. Comprobar que aparece automáticamente en el módulo mensual de septiembre
    policias_mes, num_dias, matriz = ticket_service.get_matriz_tickets_mes(mes_id)
    encontrado = any(p["codigo"] == "APF-25" for p in policias_mes)
    assert encontrado is True, "El policía recién creado debe aparecer automáticamente en el mes sin duplicar datos."

def test_prueba_2_total_tickets_unidad_local(temp_db):
    """PRUEBA 2: Para unidad = 50, Local = 19 -> Total = 69 (Vales no se suman)."""
    ticket_service = TicketService()
    ticket_service.repo.db = temp_db
    ticket_service.audit_repo.db = temp_db

    ok, msg, td = ticket_service.guardar_ticket_diario(
        fecha="2026-09-24",
        para_unidad=50,
        local=19,
        vales_policiales=10  # 10 vales no deben sumarse al total de tickets
    )
    assert ok is True
    assert td.total_policias == 69, "El total de tickets debe ser exclusivamente Para Unidad (50) + Local (19) = 69."
    assert td.vales_policiales == 10

def test_prueba_3_menus_sin_policias(temp_db):
    """PRUEBA 3: Menús vendidos = 100, Policías = 69 -> Menús sin policías = 31."""
    ticket_service = TicketService()
    ticket_service.repo.db = temp_db
    ticket_service.audit_repo.db = temp_db

    venta_service = VentaService()
    venta_service.repo.db = temp_db
    venta_service.ticket_repo.db = temp_db
    venta_service.vale_repo.db = temp_db
    venta_service.pago_repo.db = temp_db
    venta_service.mes_repo.db = temp_db
    venta_service.config_repo.db = temp_db
    venta_service.audit_repo.db = temp_db

    # Guardar ticket diario: 50 unidad + 19 local = 69 policías
    ticket_service.guardar_ticket_diario("2026-09-24", para_unidad=50, local=19)

    # Registrar venta diaria: Menús vendidos = 100
    ok, msg, v = venta_service.registrar_venta_diaria(
        fecha="2026-09-24",
        venta_total=2500.0,
        menus_vendidos=100
    )
    assert ok is True
    assert v.policias == 69
    assert v.menus_sin_policias == 31, "Menús sin policías = 100 - 69 = 31."

def test_prueba_4_y_5_venta_policial_y_venta_sin_policias(temp_db):
    """
    PRUEBA 4: Precio policial = 15, Policías = 69 -> Venta policial = 1035.
    PRUEBA 5: Venta total = 2500 -> Venta sin policías = 1465.
    """
    mes_service = MesService()
    mes_service.repo.db = temp_db
    mes_service.ticket_repo.db = temp_db
    mes_service.config_repo.db = temp_db
    mes_service.audit_repo.db = temp_db
    mes_service.crear_mes(2026, 9, precio_menu=15.0)

    ticket_service = TicketService()
    ticket_service.repo.db = temp_db
    ticket_service.audit_repo.db = temp_db
    ticket_service.guardar_ticket_diario("2026-09-24", para_unidad=50, local=19)

    venta_service = VentaService()
    venta_service.repo.db = temp_db
    venta_service.ticket_repo.db = temp_db
    venta_service.vale_repo.db = temp_db
    venta_service.pago_repo.db = temp_db
    venta_service.mes_repo.db = temp_db
    venta_service.config_repo.db = temp_db
    venta_service.audit_repo.db = temp_db

    ok, msg, v = venta_service.registrar_venta_diaria("2026-09-24", venta_total=2500.0, menus_vendidos=100)
    assert ok is True
    assert v.venta_policial_calculada == 1035.0, "Venta policial calculada = 69 * 15 = 1035."
    assert v.venta_sin_policias == 1465.0, "Venta sin policías = 2500 - 1035 = 1465."

def test_prueba_6_pagos_y_estado_parcial(temp_db):
    """PRUEBA 6: Tickets = 69, Pagados = 64, Debidos = 5 -> Estado parcial válido."""
    pago_service = PagoService()
    pago_service.repo.db = temp_db
    pago_service.ticket_repo.db = temp_db
    pago_service.audit_repo.db = temp_db

    ok, msg, p = pago_service.guardar_pago(
        fecha="2026-09-24",
        total_tickets=69,
        tickets_pagados=64,
        tickets_debidos=5,
        observacion="Se deben 5 tickets."
    )
    assert ok is True
    assert p.estado == "PARCIAL"
    assert p.is_cuadrado is True

def test_prueba_7_vales_saldo(temp_db):
    """PRUEBA 7: Vales entregados = 300, Vales canjeados = 260 -> Saldo = 40."""
    vale_service = ValeService()
    vale_service.repo.db = temp_db
    vale_service.audit_repo.db = temp_db

    ok, msg, v = vale_service.guardar_vale("2026-09-30", vales_entregados=300, vales_canjeados=260)
    assert ok is True
    assert v.saldo == 40, "Saldo = 300 - 260 = 40."
    assert v.has_alerta_saldo_negativo is False

def test_prueba_8_precio_historico_invariable(temp_db):
    """PRUEBA 8: Modificar precio general no muta cálculos históricos de períodos anteriores."""
    mes_service = MesService()
    mes_service.repo.db = temp_db
    mes_service.ticket_repo.db = temp_db
    mes_service.config_repo.db = temp_db
    mes_service.audit_repo.db = temp_db

    # Septiembre con S/ 15
    mes_service.crear_mes(2026, 9, precio_menu=15.0)

    # Octubre con S/ 16
    mes_service.crear_mes(2026, 10, precio_menu=16.0)

    venta_service = VentaService()
    venta_service.repo.db = temp_db
    venta_service.ticket_repo.db = temp_db
    venta_service.vale_repo.db = temp_db
    venta_service.pago_repo.db = temp_db
    venta_service.mes_repo.db = temp_db
    venta_service.config_repo.db = temp_db
    venta_service.audit_repo.db = temp_db

    precio_sep = venta_service.get_precio_historico_periodo(2026, 9)
    precio_oct = venta_service.get_precio_historico_periodo(2026, 10)

    assert precio_sep == 15.0
    assert precio_oct == 16.0

def test_prueba_9_inactivar_policia_mantiene_historial(temp_db):
    """PRUEBA 9: Inactivar un policía mantiene historial y no lo borra físicamente."""
    pol_service = PoliciaService()
    pol_service.repo.db = temp_db
    pol_service.mes_repo.db = temp_db
    pol_service.audit_repo.db = temp_db

    ok, _, pol_id = pol_service.crear_policia(Policia(codigo="DEP-99", apellidos="TEST", nombres="AGENT", area="DEPINCRI"))
    assert ok is True

    # Inactivar
    ok_inact, _ = pol_service.inactivar_policia(pol_id)
    assert ok_inact is True

    pol = pol_service.get_by_id(pol_id)
    assert pol is not None, "El policía no debe borrarse físicamente."
    assert pol.estado == "INACTIVO"
    assert pol.is_activo is False

def test_prueba_10_crear_nuevo_mes_fechas_automaticas_sin_copiar_datos(temp_db):
    """PRUEBA 10: Crear un nuevo mes genera fechas automáticamente y carga policías sin copiar tickets anteriores."""
    mes_service = MesService()
    mes_service.repo.db = temp_db
    mes_service.ticket_repo.db = temp_db
    mes_service.config_repo.db = temp_db
    mes_service.audit_repo.db = temp_db

    pol_service = PoliciaService()
    pol_service.repo.db = temp_db
    pol_service.mes_repo.db = temp_db
    pol_service.audit_repo.db = temp_db

    pol_service.crear_policia(Policia(codigo="AIN-88", apellidos="PEREZ", nombres="CARLOS", area="AREINCRI"))

    # Crear Octubre 2026 (31 días)
    ok, msg, mes_id = mes_service.crear_mes(2026, 10, 15.0)
    assert ok is True

    ticket_service = TicketService()
    ticket_service.repo.db = temp_db
    ticket_service.mes_repo.db = temp_db
    ticket_service.audit_repo.db = temp_db

    diarios = ticket_service.get_calendario_mes(2026, 10)
    assert len(diarios) == 31, "Octubre debe generar 31 días automáticamente."
    assert all(d.total_policias == 0 for d in diarios), "No debe copiar tickets del mes anterior."

    policias_mes, num_dias, matriz = ticket_service.get_matriz_tickets_mes(mes_id)
    assert num_dias == 31
    assert any(p["codigo"] == "AIN-88" for p in policias_mes)
