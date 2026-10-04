import sys
import os

# Add root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import DatabaseManager
from imports.excel_importer import ExcelImporter

def main():
    excel_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "sample_control_policial.xlsx")
    print(f"Importando datos desde: {excel_path}")
    importer = ExcelImporter()
    resumen = importer.importar_archivo(excel_path, estrategia_policias="ACTUALIZAR", usuario="CLI")
    print("\n--- RESUMEN DE IMPORTACIÓN ---")
    for k, v in resumen.items():
        if isinstance(v, list):
            print(f"{k}: {len(v)} elementos")
            for item in v[:5]:
                print(f"  • {item}")
        else:
            print(f"{k}: {v}")

if __name__ == "__main__":
    main()
