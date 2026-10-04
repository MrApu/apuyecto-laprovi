from dataclasses import dataclass
from typing import Optional

CONCEPTOS_PAGO = ["Pago diario", "Adelanto", "Sueldo", "Pago semanal", "Pago quincenal", "Bonificación", "Otros"]

@dataclass
class PagoPersonal:
    id: Optional[int] = None
    fecha: str = ""
    local_id: str = "restaurante"
    trabajador: str = ""
    cargo: str = "PERSONAL"
    concepto: str = "SUELDO"
    monto: float = 0.0
    medio_pago: str = "EFECTIVO"
    observacion: Optional[str] = None
    fecha_creacion: Optional[str] = None
