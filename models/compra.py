from dataclasses import dataclass
from typing import Optional

@dataclass
class Compra:
    id: Optional[int] = None
    fecha: str = ""
    local_id: str = "restaurante"
    proveedor: str = ""
    categoria: str = "INSUMOS"
    descripcion: str = ""
    cantidad: float = 1.0
    precio_unitario: float = 0.0
    total: float = 0.0
    medio_pago: str = "EFECTIVO"
    nro_documento: Optional[str] = None
    observacion: Optional[str] = None
    fecha_creacion: Optional[str] = None

    def __post_init__(self):
        if self.total == 0.0 and self.cantidad > 0 and self.precio_unitario > 0:
            self.total = round(self.cantidad * self.precio_unitario, 2)
