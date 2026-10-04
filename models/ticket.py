from dataclasses import dataclass
from typing import Optional

DIAS_SEMANA_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

@dataclass
class TicketPolicia:
    id: Optional[int] = None
    mes_id: int = 0
    policia_id: int = 0
    local_id: str = "restaurante"
    dia: int = 1
    valor: int = 1  # 1: marcado, 0: no marcado
    fecha_registro: Optional[str] = None

@dataclass
class TicketDiario:
    id: Optional[int] = None
    fecha: str = ""  # YYYY-MM-DD
    local_id: str = "restaurante"
    anio: int = 2026
    mes: int = 1
    dia: int = 1
    dia_semana: str = ""
    para_unidad: int = 0
    local: int = 0
    total_policias: int = 0  # para_unidad + local (Vales no se suman)
    vales_policiales: int = 0
    observacion: Optional[str] = None
    fecha_actualizacion: Optional[str] = None

    def __post_init__(self):
        self.total_policias = (self.para_unidad or 0) + (self.local or 0)
