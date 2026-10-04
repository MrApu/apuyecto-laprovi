from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Policia:
    id: Optional[int] = None
    codigo: str = ""
    apellidos: str = ""
    nombres: str = ""
    sa_pnp: Optional[str] = None
    area: str = ""
    estado: str = "ACTIVO"  # ACTIVO, INACTIVO
    observaciones: Optional[str] = None
    fecha_creacion: Optional[str] = None
    fecha_actualizacion: Optional[str] = None

    @property
    def nombre_completo(self) -> str:
        return f"{self.apellidos} {self.nombres}".strip()

    @property
    def is_activo(self) -> bool:
        return self.estado.upper() == "ACTIVO"
