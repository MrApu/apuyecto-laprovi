from dataclasses import dataclass
from typing import Optional

@dataclass
class PoliciaPagoTicket:
    id: Optional[int] = None
    policia_id: int = 0
    mes_id: Optional[int] = None
    fecha: str = ""
    tickets_pagados: int = 0
    monto_pagado: float = 0.0
    medio_pago: str = "EFECTIVO"
    observacion: Optional[str] = None
    fecha_registro: Optional[str] = None
    policia_codigo: Optional[str] = None
    policia_nombre: Optional[str] = None

@dataclass
class ResumenDeudaPolicia:
    policia_id: int
    codigo: str
    apellidos: str
    nombres: str
    sa_pnp: Optional[str]
    area: str
    tickets_totales: int = 0
    tickets_pagados: int = 0
    tickets_debidos: int = 0
    monto_pagado: float = 0.0
    monto_pendiente: float = 0.0
    estado: str = "AL DÍA"

    @property
    def nombre_completo(self) -> str:
        return f"{self.apellidos}, {self.nombres}"
