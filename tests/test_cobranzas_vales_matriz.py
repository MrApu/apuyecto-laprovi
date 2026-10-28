import pytest
from database.connection import DatabaseManager
from repositories.policia_repository import PoliciaRepository
from repositories.mes_repository import MesRepository
from repositories.policia_pago_repository import PoliciaPagoRepository
from repositories.vale_policia_repository import ValePoliciaRepository
from services.mes_service import MesService
from services.pago_service import PagoService
from services.vale_service import ValeService
from services.ticket_service import TicketService
from models.policia import Policia
from models.policia_pago import PoliciaPagoTicket
from models.vale_policia import ValePolicia

@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_cobranzas.db"
    DatabaseManager._instance = None
    db = DatabaseManager(str(db_file))
    yield db
    DatabaseManager._instance = None

def test_cobranzas_debe_y_pago_tickets(temp_db):
    pol_repo = PoliciaRepository(temp_db)
    mes_repo = MesRepository(temp_db)
    mes_service = MesService(mes_repo=mes_repo)
    ticket_service = TicketService(mes_repo=mes_repo)
    pago_service = PagoService(policia_repo=pol_repo, ticket_repo=ticket_service.repo)

    # 1. Crear policías de prueba
    p1_id = pol_repo.create(Policia(codigo="POL-01", apellidos="QUISPE", nombres="JUAN", area="TRANSITO"))
    p2_id = pol_repo.create(Policia(codigo="POL-02", apellidos="RODRIGUEZ", nombres="CARLOS", area="COMISARIA"))

    # 2. Crear mes
    ok, msg, mes_id = mes_service.crear_mes(2026, 10, precio_menu=12.0)
    assert ok

    # 3. Asignar 20 tickets a QUISPE y 10 tickets a RODRIGUEZ
    ticket_service.asignar_cantidad_tickets_policia(mes_id, p1_id, 20)
    ticket_service.asignar_cantidad_tickets_policia(mes_id, p2_id, 10)

    # 4. Consultar resumen de deudas iniciales
    resumen = pago_service.get_resumen_deudas_policias(mes_id, precio_ticket=12.0)
    assert len(resumen) == 2
    
    r_quispe = next(r for r in resumen if r.policia_id == p1_id)
    assert r_quispe.tickets_totales == 20
    assert r_quispe.tickets_pagados == 0
    assert r_quispe.tickets_debidos == 20
    assert r_quispe.monto_pendiente == 240.0
    assert r_quispe.estado == "DEBE"

    # 5. Registrar pago de tickets para QUISPE (paga 15 tickets = S/ 180.00)
    ok_p, msg_p, pago_id = pago_service.registrar_pago_policia(
        policia_id=p1_id,
        mes_id=mes_id,
        fecha="2026-10-15",
        tickets_pagados=15,
        monto_pagado=180.0,
        medio_pago="YAPE",
        observacion="Pago parcial quincena"
    )
    assert ok_p

    # 6. Verificar nuevo estado de QUISPE: Pagó 15, Debe 5 tickets
    resumen_post = pago_service.get_resumen_deudas_policias(mes_id, precio_ticket=12.0)
    r_quispe_post = next(r for r in resumen_post if r.policia_id == p1_id)
    assert r_quispe_post.tickets_pagados == 15
    assert r_quispe_post.tickets_debidos == 5
    assert r_quispe_post.monto_pagado == 180.0
    assert r_quispe_post.monto_pendiente == 60.0
    assert r_quispe_post.estado == "PARCIAL"

    # 7. Buscador con descarte: buscar "RODRIGUEZ" debe descartar a QUISPE
    resumen_filtro = pago_service.get_resumen_deudas_policias(mes_id, busqueda="RODRIGUEZ", precio_ticket=12.0)
    assert len(resumen_filtro) == 1
    assert resumen_filtro[0].codigo == "POL-02"

def test_vales_policias_a_quien_dimos_vales(temp_db):
    pol_repo = PoliciaRepository(temp_db)
    p1_id = pol_repo.create(Policia(codigo="POL-10", apellidos="MAMANI", nombres="PEDRO", area="PATRULLAJE"))
    vale_service = ValeService(policia_repo=pol_repo)

    # 1. Registrar vale por ticket entregado a MAMANI
    ok, msg, vale_id = vale_service.registrar_vale_policia(
        policia_id=p1_id,
        fecha="2026-10-20",
        cantidad_vales=3,
        tickets_equivalentes=3,
        observacion="Vales canjeados por 3 tickets"
    )
    assert ok
    assert vale_id is not None

    # 2. Consultar vales por policía
    vales = vale_service.get_vales_policias(busqueda="MAMANI")
    assert len(vales) == 1
    v = vales[0]
    assert v.policia_apellidos == "MAMANI"
    assert v.cantidad_vales == 3
    assert v.tickets_equivalentes == 3

    # 3. Actualizar vale
    ok_up, msg_up = vale_service.actualizar_vale_policia(
        vale_id=vale_id,
        policia_id=p1_id,
        fecha="2026-10-20",
        cantidad_vales=4,
        tickets_equivalentes=4,
        observacion="Ajuste a 4 vales"
    )
    assert ok_up
    vales_up = vale_service.get_vales_policias()
    assert vales_up[0].cantidad_vales == 4

    # 4. Eliminar vale
    ok_del, msg_del = vale_service.eliminar_vale_policia(vale_id)
    assert ok_del
    assert len(vale_service.get_vales_policias()) == 0

def test_matriz_tickets_asignacion_rapida_y_sincronizacion(temp_db):
    pol_repo = PoliciaRepository(temp_db)
    mes_repo = MesRepository(temp_db)
    mes_service = MesService(mes_repo=mes_repo)
    ticket_service = TicketService(mes_repo=mes_repo)

    p_id = pol_repo.create(Policia(codigo="POL-50", apellidos="FLORES", nombres="ANA", area="INVESTIGACION"))
    ok, msg, mes_id = mes_service.crear_mes(2026, 10)
    assert ok

    # Asignar directamente 18 tickets sin marcar día por día
    ok_asig, msg_asig = ticket_service.asignar_cantidad_tickets_policia(mes_id, p_id, 18)
    assert ok_asig

    # Verificar que en la matriz mensual se reflejan exactamente los 18 tickets
    policias, num_dias, matriz = ticket_service.get_matriz_tickets_mes(mes_id)
    dias_p = matriz.get(p_id, {})
    total_marcados = sum(1 for d in range(1, num_dias + 1) if dias_p.get(d) == 1)
    assert total_marcados == 18

    # Verificar que los primeros 18 días tienen valor 1 y los restantes valor 0
    for d in range(1, 19):
        assert dias_p.get(d) == 1
    for d in range(19, num_dias + 1):
        assert dias_p.get(d, 0) == 0
