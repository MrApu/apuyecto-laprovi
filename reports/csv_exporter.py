import csv
import os
from typing import List, Dict, Any

class CSVExporter:
    @staticmethod
    def exportar_tabla(headers: List[str], rows: List[List[Any]], output_path: str) -> bool:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return True
