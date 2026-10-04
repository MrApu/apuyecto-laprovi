from dataclasses import dataclass
from typing import Optional

@dataclass
class PagoTicket:
    id: Optional[int] = None
    fecha: str = ""  # YYYY-MM-DD
    local_id: str = "restaurante"
    total_tickets: int = 0
    tickets_pagados: int = 0
    tickets_debidos: int = 0
    estado: str = "PENDIENTE"  # PAGADO, PENDIENTE, PARCIAL
    monto_pagado: float = 0.0
    monto_pendiente: float = 0.0
    observacion: Optional[str] = None
    fecha_actualizacion: Optional[str] = None

    def calcular_estado(self):
        if self.total_tickets <= 0:
            self.estado = "PAGADO"
        elif self.tickets_pagados >= self.total_tickets:
            self.estado = "PAGADO"
        elif self.tickets_pagados == 0:
            self.estado = "PENDIENTE"
        else:
            self.estado = "PARCIAL"

    @property
    def is_cuadrado(self) -> bool:
        return (self.tickets_pagados + self.tickets_debidos) == self.total_tickets
