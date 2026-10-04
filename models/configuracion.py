from dataclasses import dataclass
from typing import Optional

@dataclass
class Configuracion:
    id: Optional[int] = None
    clave: str = ""
    valor: str = ""
    tipo_dato: str = "STRING"  # STRING, FLOAT, INT, BOOL
    descripcion: Optional[str] = None
    fecha_actualizacion: Optional[str] = None

@dataclass
class ConfiguracionHistorial:
    id: Optional[int] = None
    clave: str = ""
    valor_anterior: Optional[str] = None
    valor_nuevo: str = ""
    fecha_cambio: Optional[str] = None
    usuario: str = "SISTEMA"
    motivo: Optional[str] = None
