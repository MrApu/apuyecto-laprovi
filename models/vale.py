from dataclasses import dataclass
from typing import Optional

@dataclass
class Vale:
    id: Optional[int] = None
    fecha: str = ""  # YYYY-MM-DD
    local_id: str = "restaurante"
    vales_entregados: int = 0
    vales_consumidos: int = 0
    saldo: int = 0  # vales_entregados - vales_consumidos
    observacion: Optional[str] = None
    fecha_actualizacion: Optional[str] = None
    vales_canjeados: Optional[int] = None

    def __post_init__(self):
        if self.vales_canjeados is not None:
            self.vales_consumidos = self.vales_canjeados
        else:
            self.vales_canjeados = self.vales_consumidos
        self.saldo = (self.vales_entregados or 0) - (self.vales_consumidos or 0)

    @property
    def has_alerta_saldo_negativo(self) -> bool:
        return self.saldo < 0
