import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from repositories.policia_repository import PoliciaRepository
from repositories.mes_repository import MesRepository
from repositories.ticket_repository import TicketRepository
from repositories.vale_repository import ValeRepository
from repositories.pago_repository import PagoRepository
from repositories.venta_repository import VentaRepository

class PDFGenerator:
    def __init__(self):
        self.mes_repo = MesRepository()
        self.ticket_repo = TicketRepository()
        self.vale_repo = ValeRepository()
        self.pago_repo = PagoRepository()
        self.venta_repo = VentaRepository()

    def generar_reporte_mensual_pdf(self, anio: int, mes: int, output_path: str) -> bool:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1F4E78'),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            'SubTitleStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#595959'),
            spaceAfter=12
        )
        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#1F4E78'),
            spaceBefore=10,
            spaceAfter=6
        )
        normal_style = styles['Normal']

        m = self.mes_repo.get_by_anio_mes(anio, mes)
        nombre_mes = m.nombre_mes if m else f"{mes:02d}/{anio}"

        # Header
        elements.append(Paragraph(f"<b>CONTROL POLICIAL - REPORTE MENSUAL</b>", title_style))
        elements.append(Paragraph(f"Período: <b>{nombre_mes}</b> | Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitle_style))
        elements.append(Spacer(1, 8))

        # KPI Summary Table
        res_ventas = self.venta_repo.get_resumen_mes(anio, mes)
        res_vales = self.vale_repo.get_resumen_mes(anio, mes)
        res_pagos = self.pago_repo.get_resumen_mes(anio, mes)
        diarios = self.ticket_repo.get_tickets_diarios_mes(anio, mes)

        tot_unidad = sum(d.para_unidad for d in diarios)
        tot_local = sum(d.local for d in diarios)
        tot_policias = sum(d.total_policias for d in diarios)

        elements.append(Paragraph("<b>1. Resumen Ejecutivo del Mes</b>", section_style))

        kpi_data = [
            ["Concepto", "Valor", "Concepto", "Valor"],
            ["Venta Total", f"S/ {res_ventas['venta_total']:,.2f}", "Para Unidad", str(tot_unidad)],
            ["Menús Vendidos", str(res_ventas['menus_vendidos']), "Local", str(tot_local)],
            ["Venta Policial", f"S/ {res_ventas['venta_policial']:,.2f}", "Total Policías", str(tot_policias)],
            ["Venta Sin Policías", f"S/ {res_ventas['venta_sin_policias']:,.2f}", "Menús Sin Policías", str(res_ventas['menus_sin_policias'])],
            ["Vales Entregados", str(res_vales['entregados']), "Tickets Pagados", str(res_pagos['pagados'])],
            ["Vales Canjeados", str(res_vales['canjeados']), "Tickets Debidos", str(res_pagos['debidos'])],
            ["Saldo Vales", str(res_vales['saldo']), "Monto Cobrado", f"S/ {res_pagos['monto_pagado']:,.2f}"],
            ["Precio Menú Policial", f"S/ {m.precio_menu_policial if m else 15.0:.2f}", "Monto Pendiente", f"S/ {res_pagos['monto_pendiente']:,.2f}"]
        ]

        t_kpi = Table(kpi_data, colWidths=[130, 130, 130, 130])
        t_kpi.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D9D9D9')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
        ]))
        elements.append(t_kpi)
        elements.append(Spacer(1, 14))

        # Daily Table
        elements.append(Paragraph("<b>2. Detalle Diario de Tickets y Consumos</b>", section_style))
        cal_data = [["Fecha", "Día", "Unidad", "Local", "Policías", "Vales", "Observación"]]
        for td in diarios:
            cal_data.append([
                td.fecha,
                td.dia_semana[:3],
                str(td.para_unidad),
                str(td.local),
                str(td.total_policias),
                str(td.vales_policiales),
                td.observacion or ""
            ])

        t_cal = Table(cal_data, colWidths=[70, 50, 60, 60, 65, 55, 160])
        t_cal.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E75B6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (2, 0), (5, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D9D9D9')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
        ]))
        elements.append(t_cal)

        doc.build(elements)
        return True
