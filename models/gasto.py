from dataclasses import dataclass
from typing import Optional

CATEGORIAS_GASTOS = [
    "Servicios", "Transporte", "Mantenimiento", "Limpieza",
    "Gas", "Agua", "Luz", "Internet", "Compras menores", "Movilidad", "Otros"
]

@dataclass
class Gasto:
    id: Optional[int] = None
    fecha: str = ""
    local_id: str = "restaurante"
    categoria: str = "SERVICIOS"
    descripcion: str = ""
    monto: float = 0.0
    medio_pago: str = "EFECTIVO"
    observacion: Optional[str] = None
    fecha_creacion: Optional[str] = None
