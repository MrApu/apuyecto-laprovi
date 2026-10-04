from typing import List, Any
from reports.excel_exporter import ExcelExporter
from reports.pdf_generator import PDFGenerator
from reports.csv_exporter import CSVExporter

class Exporter:
    def __init__(self):
        self.excel = ExcelExporter()
        self.pdf = PDFGenerator()
        self.csv = CSVExporter()

    def export_excel(self, anio: int, mes: int, filepath: str) -> bool:
        return self.excel.exportar_reporte_mensual(anio, mes, filepath)

    def export_pdf(self, anio: int, mes: int, filepath: str) -> bool:
        return self.pdf.generar_reporte_mensual_pdf(anio, mes, filepath)

    def export_csv(self, headers: List[str], rows: List[List[Any]], filepath: str) -> bool:
        return self.csv.exportar_tabla(headers, rows, filepath)
