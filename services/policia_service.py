from typing import List, Optional, Tuple, Dict, Any
from repositories.policia_repository import PoliciaRepository
from repositories.mes_repository import MesRepository
from repositories.auditoria_repository import AuditoriaRepository
from models.policia import Policia

class PoliciaService:
    def __init__(
        self,
        policia_repo: Optional[PoliciaRepository] = None,
        mes_repo: Optional[MesRepository] = None,
        audit_repo: Optional[AuditoriaRepository] = None
    ):
        self.repo = policia_repo or PoliciaRepository()
        self.mes_repo = mes_repo or MesRepository()
        self.audit_repo = audit_repo or AuditoriaRepository()

    def get_all(self, solo_activos: bool = False, busqueda: Optional[str] = None, area: Optional[str] = None) -> List[Policia]:
        return self.repo.get_all(solo_activos=solo_activos, busqueda=busqueda, area=area)

    def get_by_id(self, policia_id: int) -> Optional[Policia]:
        return self.repo.get_by_id(policia_id)

    def get_by_codigo(self, codigo: str) -> Optional[Policia]:
        return self.repo.get_by_codigo(codigo)

    def crear_policia(self, policia: Policia, usuario: str = "USUARIO") -> Tuple[bool, str, Optional[int]]:
        if not policia.codigo or not policia.codigo.strip():
            return False, "El código del policía es obligatorio.", None

        if not policia.apellidos or not policia.apellidos.strip():
            return False, "Los apellidos son obligatorios.", None

        if not policia.nombres or not policia.nombres.strip():
            return False, "Los nombres son obligatorios.", None

        if not policia.area or not policia.area.strip():
            return False, "El área es obligatoria.", None

        # Check unique code
        existente = self.repo.get_by_codigo(policia.codigo)
        if existente:
            return False, f"Ya existe un policía registrado con el código '{policia.codigo.upper()}'.", None

        nuevo_id = self.repo.create(policia)

        # Automatically propagate to all open or existing months
        meses = self.mes_repo.get_all()
        for m in meses:
            self.mes_repo.sincronizar_policias_mes(m.id)

        self.audit_repo.registrar(
            accion="CREAR_POLICIA",
            entidad="policias",
            entidad_id=str(nuevo_id),
            detalles=f"Creado policía {policia.codigo} - {policia.apellidos}, {policia.nombres} ({policia.area})",
            usuario=usuario
        )

        return True, "Policía registrado exitosamente y sincronizado en los meses.", nuevo_id

    def actualizar_policia(self, policia: Policia, usuario: str = "USUARIO") -> Tuple[bool, str]:
        if not policia.id:
            return False, "ID de policía no válido."

        actual = self.repo.get_by_id(policia.id)
        if not actual:
            return False, "Policía no encontrado."

        # Check code collision if code changed
        if policia.codigo.strip().upper() != actual.codigo.strip().upper():
            existente = self.repo.get_by_codigo(policia.codigo)
            if existente and existente.id != policia.id:
                return False, f"El código '{policia.codigo.upper()}' ya pertenece a otro policía."

        self.repo.update(policia)

        self.audit_repo.registrar(
            accion="EDITAR_POLICIA",
            entidad="policias",
            entidad_id=str(policia.id),
            detalles=f"Modificado policía {policia.codigo}: {policia.apellidos}, {policia.nombres} (Área: {policia.area}, Estado: {policia.estado})",
            usuario=usuario
        )

        return True, "Policía actualizado correctamente."

    def inactivar_policia(self, policia_id: int, usuario: str = "USUARIO") -> Tuple[bool, str]:
        pol = self.repo.get_by_id(policia_id)
        if not pol:
            return False, "Policía no encontrado."

        self.repo.set_estado(policia_id, "INACTIVO")
        self.audit_repo.registrar(
            accion="INACTIVAR_POLICIA",
            entidad="policias",
            entidad_id=str(policia_id),
            detalles=f"Inactivado policía {pol.codigo} - {pol.nombre_completo}",
            usuario=usuario
        )
        return True, f"Policía {pol.codigo} inactivado lógicamente. Su historial se mantiene intacto."

    def reactivar_policia(self, policia_id: int, usuario: str = "USUARIO") -> Tuple[bool, str]:
        pol = self.repo.get_by_id(policia_id)
        if not pol:
            return False, "Policía no encontrado."

        self.repo.set_estado(policia_id, "ACTIVO")

        # Sync with open months
        meses = self.mes_repo.get_all()
        for m in meses:
            self.mes_repo.sincronizar_policias_mes(m.id)

        self.audit_repo.registrar(
            accion="REACTIVAR_POLICIA",
            entidad="policias",
            entidad_id=str(policia_id),
            detalles=f"Reactivado policía {pol.codigo} - {pol.nombre_completo}",
            usuario=usuario
        )
        return True, f"Policía {pol.codigo} reactivado exitosamente."

    def cambiar_estado(self, policia_id: int, nuevo_estado: str, usuario: str = "USUARIO") -> Tuple[bool, str]:
        if nuevo_estado.upper() == "INACTIVO":
            return self.inactivar_policia(policia_id, usuario)
        return self.reactivar_policia(policia_id, usuario)

    def get_areas(self) -> List[str]:
        return self.repo.get_areas()
