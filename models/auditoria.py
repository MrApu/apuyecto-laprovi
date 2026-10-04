from dataclasses import dataclass
from typing import Optional

@dataclass
class Auditoria:
    id: Optional[int] = None
    fecha: Optional[str] = None
    usuario: str = "USUARIO"
    accion: str = ""
    entidad: str = ""
    entidad_id: Optional[str] = None
    detalles: Optional[str] = None
