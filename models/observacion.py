from dataclasses import dataclass
from typing import Optional

@dataclass
class Observacion:
    id: Optional[int] = None
    fecha: str = ""  # YYYY-MM-DD
    texto: str = ""
    tipo: str = "GENERAL"
    fecha_creacion: Optional[str] = None
