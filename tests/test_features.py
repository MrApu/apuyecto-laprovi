import pytest
import os
import tempfile
from database.connection import DatabaseManager
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
    db_path = os.path.join(temp_dir, "test_features.db")
    db_mgr = DatabaseManager(db_path)
    yield db_mgr
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

def test_backup_and_restore(temp_db):
    temp_dir = tempfile.mkdtemp()
    mgr = BackupManager(backup_dir=temp_dir, db=temp_db)

    # Insert a dummy police officer
    pol_service = PoliciaService()
    pol_service.repo.db = temp_db
    pol_service.mes_repo.db = temp_db
    pol_service.audit_repo.db = temp_db
    from models.policia import Policia
    pol_service.crear_policia(Policia(codigo="BK-01", apellidos="GARCIA", nombres="JOSE", area="SECINT"))

    # Create backup
    ok, msg, path = mgr.crear_backup(usuario="TEST_USER")
    assert ok is True
    assert os.path.exists(path)

    # List backups
    backups = mgr.listar_backups()
    assert len(backups) >= 1
    assert backups[0]["nombre"].startswith("backup_")

    # Inactivate police officer
    pol = pol_service.get_by_codigo("BK-01")
    pol_service.inactivar_policia(pol.id)
    assert pol_service.get_by_id(pol.id).estado == "INACTIVO"

    # Restore backup
    ok_res, msg_res = mgr.restaurar_backup(backups[0]["nombre"], usuario="TEST_USER")
    assert ok_res is True
    assert pol_service.get_by_id(pol.id).estado == "ACTIVO", "Al restaurar el backup debe recuperar el estado previo."

def test_import_sample_excel(temp_db):
    xlsx_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "sample_control_policial.xlsx")
    assert os.path.exists(xlsx_path)

    importer = ExcelImporter()
    importer.policia_service.repo.db = temp_db
    importer.policia_service.mes_repo.db = temp_db
    importer.policia_service.audit_repo.db = temp_db
    importer.mes_service.repo.db = temp_db
    importer.mes_service.ticket_repo.db = temp_db
    importer.mes_service.config_repo.db = temp_db
    importer.mes_service.audit_repo.db = temp_db
    importer.ticket_service.repo.db = temp_db
    importer.ticket_service.mes_repo.db = temp_db
    importer.ticket_service.audit_repo.db = temp_db
    importer.audit_repo.db = temp_db

    resumen = importer.importar_archivo(xlsx_path, estrategia_policias="ACTUALIZAR")
    assert resumen["policias_nuevos"] > 0, "Debe importar policías desde la hoja BD."
    assert resumen["meses_importados"] >= 1

def test_export_pdf_and_excel(temp_db):
    temp_dir = tempfile.mkdtemp()
    excel_out = os.path.join(temp_dir, "test_report.xlsx")
    pdf_out = os.path.join(temp_dir, "test_report.pdf")

    mes_service = MesService()
    mes_service.repo.db = temp_db
    mes_service.ticket_repo.db = temp_db
    mes_service.config_repo.db = temp_db
    mes_service.audit_repo.db = temp_db
    mes_service.crear_mes(2026, 9, 15.0)

    exporter = ExcelExporter()
    exporter.policia_repo.db = temp_db
    exporter.mes_repo.db = temp_db
    exporter.ticket_repo.db = temp_db
    exporter.vale_repo.db = temp_db
    exporter.pago_repo.db = temp_db
    exporter.venta_repo.db = temp_db
    exporter.obs_repo.db = temp_db

    ok_e = exporter.exportar_reporte_mensual(2026, 9, excel_out)
    assert ok_e is True
    assert os.path.exists(excel_out)

    pdf_gen = PDFGenerator()
    pdf_gen.mes_repo.db = temp_db
    pdf_gen.ticket_repo.db = temp_db
    pdf_gen.vale_repo.db = temp_db
    pdf_gen.pago_repo.db = temp_db
    pdf_gen.venta_repo.db = temp_db

    ok_p = pdf_gen.generar_reporte_mensual_pdf(2026, 9, pdf_out)
    assert ok_p is True
    assert os.path.exists(pdf_out)
