from dataclasses import dataclass
from typing import Optional

NOMBRES_MESES = [
    "", "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
    "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
]

@dataclass
class Mes:
    id: Optional[int] = None
    anio: int = 2026
    mes: int = 1
    nombre_mes: str = ""
    estado: str = "ABIERTO"  # ABIERTO, CERRADO
    precio_ticket_policial: float = 12.00
    fecha_creacion: Optional[str] = None
    precio_menu_policial: Optional[float] = None

    def __post_init__(self):
        if self.precio_menu_policial is not None:
            self.precio_ticket_policial = float(self.precio_menu_policial)
        else:
            self.precio_menu_policial = self.precio_ticket_policial
        if not self.nombre_mes and 1 <= self.mes <= 12:
            self.nombre_mes = f"{NOMBRES_MESES[self.mes]} {self.anio}"

    @property
    def key(self) -> str:
        return f"{self.mes:02d}/{self.anio}"

    @property
    def display_name(self) -> str:
        return self.nombre_mes or f"{NOMBRES_MESES[self.mes]} {self.anio}"

@dataclass
class PoliciaMes:
    id: Optional[int] = None
    mes_id: int = 0
    policia_id: int = 0
    local_id: str = "restaurante"
    area_historica: str = ""
    estado_en_mes: str = "ACTIVO"
