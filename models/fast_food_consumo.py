from dataclasses import dataclass
from typing import Optional

@dataclass
class FastFoodConsumo:
    id: Optional[int] = None
    fecha: str = ""
    tickets_local: int = 0
    vales_local: int = 0
    total_consumido: int = 0
    observacion: Optional[str] = None
    fecha_actualizacion: Optional[str] = None

    def __post_init__(self):
        self.total_consumido = (self.tickets_local or 0) + (self.vales_local or 0)
