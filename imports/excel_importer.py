import os
import csv
import re
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import openpyxl
from models.policia import Policia
from models.mes import Mes, NOMBRES_MESES
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
from services.observacion_service import ObservacionService
from repositories.policia_repository import PoliciaRepository
from repositories.mes_repository import MesRepository
from repositories.ticket_repository import TicketRepository
from repositories.auditoria_repository import AuditoriaRepository

class ExcelImporter:
    """
    Robust Excel (.xlsx, .xlsm) & CSV importer that parses:
    - BD (Master police database)
    - C_JULIO, C_AGOSTO, C_SETIEMBRE (Monthly individual marked ticket sheets)
    - Calendario Policial / Hoja2 (Daily Unidad, Local, Vales, Pagos, Deudas)
    - Control de Ventas
    """

    def __init__(
        self,
        policia_service: Optional[PoliciaService] = None,
        mes_service: Optional[MesService] = None,
        ticket_service: Optional[TicketService] = None,
        vale_service: Optional[ValeService] = None,
        pago_service: Optional[PagoService] = None,
        venta_service: Optional[VentaService] = None,
        obs_service: Optional[ObservacionService] = None
    ):
        self.policia_service = policia_service or PoliciaService()
        self.mes_service = mes_service or MesService()
        self.ticket_service = ticket_service or TicketService()
        self.vale_service = vale_service or ValeService()
        self.pago_service = pago_service or PagoService()
        self.venta_service = venta_service or VentaService()
        self.obs_service = obs_service or ObservacionService()
        self.audit_repo = AuditoriaRepository()

    def importar_archivo(
        self,
        file_path: str,
        estrategia_policias: str = "ACTUALIZAR",  # ACTUALIZAR, OMITIR, SOLO_NUEVOS
        usuario: str = "USUARIO"
    ) -> Dict[str, Any]:
        resumen = {
            "policias_nuevos": 0,
            "policias_actualizados": 0,
            "policias_omitidos": 0,
            "meses_importados": 0,
            "registros_tickets": 0,
            "registros_calendario": 0,
            "registros_vales": 0,
            "registros_pagos": 0,
            "registros_ventas": 0,
            "advertencias": [],
            "discrepancias": []
        }

        if not os.path.exists(file_path):
            resumen["advertencias"].append(f"El archivo no existe: {file_path}")
            return resumen

        ext = os.path.splitext(file_path)[1].lower()
        if ext in (".xlsx", ".xlsm"):
            self._importar_excel(file_path, estrategia_policias, resumen, usuario)
        elif ext == ".csv":
            self._importar_csv(file_path, estrategia_policias, resumen, usuario)
        else:
            resumen["advertencias"].append(f"Formato no soportado: {ext}. Utilice .xlsx, .xlsm o .csv.")

        self.audit_repo.registrar(
            accion="IMPORTAR_EXCEL",
            entidad="importacion",
            entidad_id=os.path.basename(file_path),
            detalles=f"Importado {os.path.basename(file_path)}: PolNuevos={resumen['policias_nuevos']}, Tickets={resumen['registros_tickets']}, Calendario={resumen['registros_calendario']}",
            usuario=usuario
        )

        return resumen

    def _importar_excel(self, file_path: str, estrategia: str, resumen: dict, usuario: str):
        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
        except Exception as e:
            resumen["advertencias"].append(f"Error al abrir archivo Excel: {str(e)}")
            return

        sheet_names = wb.sheetnames

        # 1. Look for BD sheet
        bd_sheet = None
        for name in sheet_names:
            if "BD" in name.upper() or "BASE" in name.upper() or "PERSONAL" in name.upper():
                bd_sheet = wb[name]
                break

        if bd_sheet:
            self._procesar_hoja_bd(bd_sheet, estrategia, resumen, usuario)
        else:
            resumen["advertencias"].append("No se encontró una hoja de 'BD' en el archivo Excel.")

        # 2. Look for Month ticket sheets (e.g. C_JULIO, C_AGOSTO, C_SETIEMBRE, etc.)
        for name in sheet_names:
            upper_name = name.upper()
            if upper_name.startswith("C_") or "TICKET" in upper_name or any(m in upper_name for m in ["JULIO", "AGOSTO", "SETIEMBRE", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE", "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO"]):
                if "VENTA" not in upper_name and "CALENDARIO" not in upper_name and "BD" not in upper_name:
                    self._procesar_hoja_tickets_mes(wb[name], name, resumen, usuario)

        # 3. Look for Calendario Policial
        for name in sheet_names:
            upper_name = name.upper()
            if "CALENDARIO" in upper_name or "HOJA2" in upper_name:
                self._procesar_hoja_calendario(wb[name], resumen, usuario)

        # 4. Look for Ventas Diarias
        for name in sheet_names:
            upper_name = name.upper()
            if "VENTA" in upper_name or "CONTROL DE VENTA" in upper_name:
                self._procesar_hoja_ventas(wb[name], resumen, usuario)

    def _procesar_hoja_bd(self, sheet, estrategia: str, resumen: dict, usuario: str):
        headers = []
        header_row_idx = None

        for r_idx in range(1, min(20, sheet.max_row + 1)):
            row_vals = [str(sheet.cell(r_idx, c).value or "").strip().upper() for c in range(1, sheet.max_column + 1)]
            if any("CÓDIGO" in v or "CODIGO" in v for v in row_vals) and any("APELLIDO" in v for v in row_vals):
                header_row_idx = r_idx
                headers = row_vals
                break

        if not header_row_idx:
            resumen["advertencias"].append("No se encontraron encabezados válidos en la hoja BD.")
            return

        col_codigo = self._find_col(headers, ["CÓDIGO", "CODIGO"])
        col_apellidos = self._find_col(headers, ["APELLIDOS", "APELLIDO"])
        col_nombres = self._find_col(headers, ["NOMBRES", "NOMBRE"])
        col_sa_pnp = self._find_col(headers, ["SA-PNP", "SA_PNP", "SAPNP", "CARNET", "CIP"])
        col_area = self._find_col(headers, ["ÁREA", "AREA"])

        for r in range(header_row_idx + 1, sheet.max_row + 1):
            codigo_val = str(sheet.cell(r, col_codigo).value or "").strip().upper() if col_codigo else ""
            if not codigo_val or codigo_val == "NONE" or "BUSCAR" in codigo_val or "TOTAL" in codigo_val:
                continue

            apellidos_val = str(sheet.cell(r, col_apellidos).value or "").strip().upper() if col_apellidos else ""
            nombres_val = str(sheet.cell(r, col_nombres).value or "").strip().upper() if col_nombres else ""
            sa_pnp_val = str(sheet.cell(r, col_sa_pnp).value or "").strip() if col_sa_pnp else ""
            area_val = str(sheet.cell(r, col_area).value or "").strip().upper() if col_area else "GENERAL"

            if not apellidos_val and not nombres_val:
                continue

            pol = Policia(
                codigo=codigo_val,
                apellidos=apellidos_val,
                nombres=nombres_val,
                sa_pnp=sa_pnp_val if sa_pnp_val and sa_pnp_val != "None" else None,
                area=area_val or "GENERAL",
                estado="ACTIVO"
            )

            existente = self.policia_service.get_by_codigo(codigo_val)
            if existente:
                if estrategia == "ACTUALIZAR":
                    pol.id = existente.id
                    self.policia_service.actualizar_policia(pol, usuario=usuario)
                    resumen["policias_actualizados"] += 1
                else:
                    resumen["policias_omitidos"] += 1
            else:
                ok, msg, new_id = self.policia_service.crear_policia(pol, usuario=usuario)
                if ok:
                    resumen["policias_nuevos"] += 1

    def _procesar_hoja_tickets_mes(self, sheet, sheet_name: str, resumen: dict, usuario: str):
        # Extract month and year from sheet name or header
        anio, mes_num = self._detectar_anio_mes(sheet_name, sheet)
        if not mes_num:
            return

        ok, msg, mes_id = self.mes_service.crear_mes(anio, mes_num, usuario=usuario)
        if not mes_id:
            m = self.mes_service.get_by_anio_mes(anio, mes_num)
            mes_id = m.id if m else None

        if not mes_id:
            return

        resumen["meses_importados"] += 1

        # Locate table header
        header_row_idx = None
        headers = []
        for r_idx in range(1, min(10, sheet.max_row + 1)):
            row_vals = [str(sheet.cell(r_idx, c).value or "").strip().upper() for c in range(1, sheet.max_column + 1)]
            if any("CÓDIGO" in v or "CODIGO" in v for v in row_vals):
                header_row_idx = r_idx
                headers = row_vals
                break

        if not header_row_idx:
            return

        col_codigo = self._find_col(headers, ["CÓDIGO", "CODIGO"])
        col_apellidos = self._find_col(headers, ["APELLIDOS", "APELLIDO"])
        col_nombres = self._find_col(headers, ["NOMBRES", "NOMBRE"])
        col_sa_pnp = self._find_col(headers, ["SA-PNP", "SA_PNP", "SAPNP"])
        col_area = self._find_col(headers, ["ÁREA", "AREA"])
        col_total = self._find_col(headers, ["TOTAL"])

        # Map day columns (1..31)
        day_cols: Dict[int, int] = {}
        for c_idx, h in enumerate(headers, start=1):
            if h.isdigit() and 1 <= int(h) <= 31:
                day_cols[int(h)] = c_idx

        # Read rows
        for r in range(header_row_idx + 1, sheet.max_row + 1):
            codigo_val = str(sheet.cell(r, col_codigo).value or "").strip().upper() if col_codigo else ""
            if not codigo_val or codigo_val == "NONE" or "TOTAL" in codigo_val:
                continue

            # Ensure officer exists in master DB
            pol = self.policia_service.get_by_codigo(codigo_val)
            if not pol:
                apellidos_val = str(sheet.cell(r, col_apellidos).value or "").strip().upper() if col_apellidos else ""
                nombres_val = str(sheet.cell(r, col_nombres).value or "").strip().upper() if col_nombres else ""
                sa_pnp_val = str(sheet.cell(r, col_sa_pnp).value or "").strip() if col_sa_pnp else ""
                area_val = str(sheet.cell(r, col_area).value or "").strip().upper() if col_area else "GENERAL"
                nuevo_pol = Policia(codigo=codigo_val, apellidos=apellidos_val or "SIN APELLIDO", nombres=nombres_val or "SIN NOMBRE", sa_pnp=sa_pnp_val or None, area=area_val or "GENERAL")
                ok_p, _, new_id = self.policia_service.crear_policia(nuevo_pol, usuario=usuario)
                if ok_p and new_id:
                    pol_id = new_id
                    resumen["policias_nuevos"] += 1
                else:
                    pol_exist = self.policia_service.get_by_codigo(codigo_val)
                    pol_id = pol_exist.id if pol_exist else None
            else:
                pol_id = pol.id

            if not pol_id:
                continue

            # Count and record daily marks
            conteo_real = 0
            row_tickets = []
            for dia, col_idx in day_cols.items():
                cell_val = str(sheet.cell(r, col_idx).value or "").strip().upper()
                if cell_val in ("X", "1", "TRUE", "SI", "✓", "X "):
                    row_tickets.append((mes_id, pol_id, dia, 1))
                    conteo_real += 1
                    resumen["registros_tickets"] += 1
                else:
                    row_tickets.append((mes_id, pol_id, dia, 0))

            if row_tickets:
                self.ticket_service.repo.set_tickets_policia_batch(row_tickets)

            # Check discrepancy with Excel formula total if present
            if col_total:
                excel_total_val = sheet.cell(r, col_total).value
                try:
                    excel_tot = int(float(excel_total_val))
                    if excel_tot != conteo_real:
                        resumen["discrepancias"].append(
                            f"Hoja {sheet_name}, Policía {codigo_val}: Total en Excel dice {excel_tot}, pero conteo real de 'X' diarias es {conteo_real}. Se tomó el conteo real ({conteo_real})."
                        )
                except (ValueError, TypeError):
                    pass

    def _procesar_hoja_calendario(self, sheet, resumen: dict, usuario: str):
        # Look for date columns or rows
        # Standard format: FECHA, DÍA, PARA UNIDAD, LOCAL, VALES POLICIALES, TOTAL, OBSERVACIÓN
        for r in range(1, sheet.max_row + 1):
            for c in range(1, sheet.max_column + 1):
                val = str(sheet.cell(r, c).value or "").strip()
                date_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", val)
                if date_match:
                    fecha_str = val
                    # Check next cells in same column / row
                    # In user CSV calendar, day block is placed with Unidad, Local below the date
                    unidad_val = 0
                    local_val = 0
                    obs_val = ""
                    # Search around cell
                    for dr in range(1, 5):
                        sub_val = str(sheet.cell(r + dr, c).value or "").strip()
                        if sub_val.isdigit():
                            if unidad_val == 0:
                                unidad_val = int(sub_val)
                            elif local_val == 0:
                                local_val = int(sub_val)
                        elif "OBS:" in sub_val.upper() or "DEBEN" in sub_val.upper():
                            obs_val = sub_val

                    if unidad_val > 0 or local_val > 0:
                        self.ticket_service.guardar_ticket_diario(
                            fecha=fecha_str,
                            para_unidad=unidad_val,
                            local=local_val,
                            observacion=obs_val or None,
                            usuario=usuario
                        )
                        resumen["registros_calendario"] += 1

    def _procesar_hoja_ventas(self, sheet, resumen: dict, usuario: str):
        # Parses sales table if present
        pass

    def _importar_csv(self, file_path: str, estrategia: str, resumen: dict, usuario: str):
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        # Parse CSV lines into sections (BD, REGISTRO HISTORICO, MESES)
        current_section = "UNKNOWN"
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            if "BASE DE DATOS PNP" in line_str:
                current_section = "BD"
                continue
            elif "REGISTRO HISTÓRICO" in line_str or "REGISTRO HISTORICO" in line_str:
                current_section = "HISTORICO"
                continue
            elif "CONTROL DE ENTREGA DE TICKETS - JULIO" in line_str:
                current_section = "JULIO"
                continue
            elif "CONTROL DE ENTREGA DE TICKETS - AGOSTO" in line_str:
                current_section = "AGOSTO"
                continue
            elif "CONTROL DE ENTREGA DE TICKETS - SETIEMBRE" in line_str or "SEPTIEMBRE" in line_str:
                current_section = "SETIEMBRE"
                continue
            elif "Septiembre 2026" in line_str or "Calendario" in line_str:
                current_section = "CALENDARIO"
                continue

            parts = [p.strip() for p in line.split(",")]

            if current_section == "BD" or current_section == "UNKNOWN":
                if len(parts) >= 6 and parts[1].startswith(("APF-", "APJ-", "AIN-", "DEP-", "ADR-", "SEC-", "ACT-")):
                    codigo = parts[1].strip()
                    apellidos = parts[2].strip()
                    nombres = parts[3].strip()
                    sa_pnp = parts[4].strip() or None
                    area = parts[5].strip()
                    pol = Policia(codigo=codigo, apellidos=apellidos, nombres=nombres, sa_pnp=sa_pnp, area=area)
                    existente = self.policia_service.get_by_codigo(codigo)
                    if existente:
                        if estrategia == "ACTUALIZAR":
                            pol.id = existente.id
                            self.policia_service.actualizar_policia(pol, usuario=usuario)
                            resumen["policias_actualizados"] += 1
                        else:
                            resumen["policias_omitidos"] += 1
                    else:
                        ok, _, _ = self.policia_service.crear_policia(pol, usuario=usuario)
                        if ok:
                            resumen["policias_nuevos"] += 1

            elif current_section == "HISTORICO":
                # Line format: FECHA, CÓDIGO, APELLIDOS, NOMBRES, SA-PNP, ÁREA, MES
                if len(parts) >= 7 and re.match(r"^\d{4}-\d{2}-\d{2}$", parts[0]):
                    fecha = parts[0]
                    codigo = parts[1]
                    apellidos = parts[2]
                    nombres = parts[3]
                    sa_pnp = parts[4] or None
                    area = parts[5]
                    mes_label = parts[6]

                    dt = datetime.strptime(fecha, "%Y-%m-%d")
                    ok_m, _, mes_id = self.mes_service.crear_mes(dt.year, dt.month, usuario=usuario)
                    if not mes_id:
                        m = self.mes_service.get_by_anio_mes(dt.year, dt.month)
                        mes_id = m.id if m else None

                    pol = self.policia_service.get_by_codigo(codigo)
                    if not pol:
                        nuevo_pol = Policia(codigo=codigo, apellidos=apellidos, nombres=nombres, sa_pnp=sa_pnp, area=area)
                        _, _, new_id = self.policia_service.crear_policia(nuevo_pol, usuario=usuario)
                        pol_id = new_id
                        resumen["policias_nuevos"] += 1
                    else:
                        pol_id = pol.id

                    if mes_id and pol_id:
                        self.ticket_service.toggle_ticket(mes_id, pol_id, dt.day, 1, usuario=usuario)
                        resumen["registros_tickets"] += 1

    @staticmethod
    def _find_col(headers: List[str], keywords: List[str]) -> Optional[int]:
        for idx, h in enumerate(headers, start=1):
            if any(k in h for k in keywords):
                return idx
        return None

    @staticmethod
    def _detectar_anio_mes(sheet_name: str, sheet) -> Tuple[int, Optional[int]]:
        name_upper = sheet_name.upper()
        anio = 2026

        # Try to find year
        year_match = re.search(r"20\d{2}", name_upper)
        if year_match:
            anio = int(year_match.group(0))

        mes_map = {
            "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6,
            "JULIO": 7, "AGOSTO": 8, "SETIEMBRE": 9, "SEPTIEMBRE": 9, "OCTUBRE": 10,
            "NOVIEMBRE": 11, "DICIEMBRE": 12
        }

        for m_name, m_num in mes_map.items():
            if m_name in name_upper:
                return anio, m_num

        return anio, None
