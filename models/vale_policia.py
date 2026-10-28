from dataclasses import dataclass
from typing import Optional

@dataclass
class ValePolicia:
    id: Optional[int] = None
    policia_id: int = 0
    fecha: str = ""
    local_id: str = "restaurante"
    tipo_operacion: str = "ENTREGA"  # ENTREGA (dimos vales por tickets) o CANJE
    cantidad_vales: int = 1
    tickets_equivalentes: int = 1
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
