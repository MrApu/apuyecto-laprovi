from dataclasses import dataclass
from typing import Optional

@dataclass
class MovimientoTicket:
    id: Optional[int] = None
    policia_id: int = 0
    fecha: str = ""
    tipo_movimiento: str = "DEBE"  # 'DEBE' o 'PAGO'
    cantidad_tickets: int = 1
    precio_unitario: float = 12.0
    monto_total: float = 0.0
    medio_pago: Optional[str] = "EFECTIVO"
    observacion: Optional[str] = None
    fecha_registro: Optional[str] = None
    policia_codigo: Optional[str] = None
    policia_apellidos: Optional[str] = None
    policia_nombres: Optional[str] = None
    policia_area: Optional[str] = None

    @property
    def policia_nombre_completo(self) -> str:
        if self.policia_apellidos and self.policia_nombres:
            return f"{self.policia_apellidos}, {self.policia_nombres}"
        return self.policia_apellidos or self.policia_nombres or f"Policía #{self.policia_id}"

@dataclass
class ResumenCuentaPolicia:
    policia_id: int
    codigo: str
    apellidos: str
    nombres: str
    area: str
    sa_pnp: Optional[str] = None
    tickets_debe_total: int = 0
    tickets_pago_total: int = 0
    saldo_tickets_debe: int = 0
    monto_debe_total: float = 0.0
    monto_pago_total: float = 0.0
    saldo_monto_debe: float = 0.0
    estado: str = "AL DÍA"

    @property
    def nombre_completo(self) -> str:
        return f"{self.apellidos}, {self.nombres}"
