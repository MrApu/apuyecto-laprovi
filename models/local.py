from dataclasses import dataclass
from typing import List

LOCAL_RESTAURANTE = "restaurante"
LOCAL_FAST_FOOD = "fast_food"
LOCAL_CONSOLIDADO = "consolidado"

LOCALES_NOMBRES = {
    LOCAL_RESTAURANTE: "LA PROVINCIAL RESTAURANTE",
    LOCAL_FAST_FOOD: "LA PROVINCIAL FAST FOOD",
    LOCAL_CONSOLIDADO: "CONSOLIDADO GENERAL"
}
LOCAL_NAMES = LOCALES_NOMBRES

@dataclass
class Local:
    id: str = "restaurante"
    nombre: str = "LA PROVINCIAL RESTAURANTE"
    activo: bool = True

    @property
    def display_name(self) -> str:
        return self.nombre
