from typing import List, Optional, Tuple
from repositories.observacion_repository import ObservacionRepository
from repositories.auditoria_repository import AuditoriaRepository
from models.observacion import Observacion

class ObservacionService:
    def __init__(
        self,
        obs_repo: Optional[ObservacionRepository] = None,
        audit_repo: Optional[AuditoriaRepository] = None
    ):
        self.repo = obs_repo or ObservacionRepository()
        self.audit_repo = audit_repo or AuditoriaRepository()

    def get_by_fecha(self, fecha: str) -> List[Observacion]:
        return self.repo.get_by_fecha(fecha)

    def get_by_mes(self, anio: int, mes: int) -> List[Observacion]:
        return self.repo.get_by_mes(anio, mes)

    def agregar_observacion(self, fecha: str, texto: str, tipo: str = "GENERAL", usuario: str = "USUARIO") -> Tuple[bool, str, Optional[int]]:
        if not texto or not texto.strip():
            return False, "El texto de la observación no puede estar vacío.", None

        obs = Observacion(fecha=fecha, texto=texto.strip(), tipo=tipo)
        new_id = self.repo.create(obs)

        self.audit_repo.registrar(
            accion="CREAR_OBSERVACION",
            entidad="observaciones",
            entidad_id=str(new_id),
            detalles=f"Fecha {fecha}: [{tipo}] {texto.strip()}",
            usuario=usuario
        )

        return True, "Observación guardada.", new_id

    def eliminar_observacion(self, obs_id: int, usuario: str = "USUARIO") -> Tuple[bool, str]:
        self.repo.delete(obs_id)
        self.audit_repo.registrar(
            accion="ELIMINAR_OBSERVACION",
            entidad="observaciones",
            entidad_id=str(obs_id),
            detalles=f"Eliminada observación ID {obs_id}",
            usuario=usuario
        )
        return True, "Observación eliminada."
