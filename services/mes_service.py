from typing import List, Optional, Tuple, Dict, Any
from repositories.mes_repository import MesRepository
from repositories.ticket_repository import TicketRepository
from repositories.configuracion_repository import ConfiguracionRepository
from repositories.auditoria_repository import AuditoriaRepository
from models.mes import Mes, NOMBRES_MESES

class MesService:
    def __init__(
        self,
        mes_repo: Optional[MesRepository] = None,
        ticket_repo: Optional[TicketRepository] = None,
        config_repo: Optional[ConfiguracionRepository] = None,
        audit_repo: Optional[AuditoriaRepository] = None
    ):
        self.repo = mes_repo or MesRepository()
        self.ticket_repo = ticket_repo or TicketRepository()
        self.config_repo = config_repo or ConfiguracionRepository()
        self.audit_repo = audit_repo or AuditoriaRepository()

    def get_all(self) -> List[Mes]:
        return self.repo.get_all()

    def get_by_id(self, mes_id: int) -> Optional[Mes]:
        return self.repo.get_by_id(mes_id)

    def get_by_anio_mes(self, anio: int, mes: int) -> Optional[Mes]:
        return self.repo.get_by_anio_mes(anio, mes)

    def crear_mes(self, anio: int, mes: int, precio_menu: Optional[float] = None, usuario: str = "USUARIO") -> Tuple[bool, str, Optional[int]]:
        if not (1 <= mes <= 12):
            return False, "El mes debe estar entre 1 y 12.", None

        existente = self.repo.get_by_anio_mes(anio, mes)
        if existente:
            return False, f"El período {mes:02d}/{anio} ({existente.nombre_mes}) ya existe.", existente.id

        if precio_menu is None:
            precio_menu = self.config_repo.get_float("precio_ticket_policial", 12.0)

        nombre = f"{NOMBRES_MESES[mes]} {anio}"
        nuevo_mes = Mes(
            anio=anio,
            mes=mes,
            nombre_mes=nombre,
            estado="ABIERTO",
            precio_ticket_policial=precio_menu
        )

        mes_id = self.repo.create(nuevo_mes)

        # Initialize days in tickets_diarios
        self.ticket_repo.inicializar_dias_mes(anio, mes)

        # Load active police officers into this month snapshot without copying previous data
        self.repo.sincronizar_policias_mes(mes_id)

        self.audit_repo.registrar(
            accion="CREAR_MES",
            entidad="meses",
            entidad_id=str(mes_id),
            detalles=f"Creado período {nombre} con precio menú S/ {precio_menu:.2f}",
            usuario=usuario
        )

        return True, f"Período {nombre} creado exitosamente con días y policías inicializados.", mes_id

    def cerrar_mes(self, mes_id: int, usuario: str = "USUARIO") -> Tuple[bool, str]:
        m = self.repo.get_by_id(mes_id)
        if not m:
            return False, "Período no encontrado."

        self.repo.update_estado(mes_id, "CERRADO")
        self.audit_repo.registrar(
            accion="CERRAR_MES",
            entidad="meses",
            entidad_id=str(mes_id),
            detalles=f"Cerrado período {m.nombre_mes}",
            usuario=usuario
        )
        return True, f"Período {m.nombre_mes} cerrado."

    def reabrir_mes(self, mes_id: int, usuario: str = "USUARIO") -> Tuple[bool, str]:
        m = self.repo.get_by_id(mes_id)
        if not m:
            return False, "Período no encontrado."

        self.repo.update_estado(mes_id, "ABIERTO")
        self.audit_repo.registrar(
            accion="REABRIR_MES",
            entidad="meses",
            entidad_id=str(mes_id),
            detalles=f"Reabierto período {m.nombre_mes}",
            usuario=usuario
        )
        return True, f"Período {m.nombre_mes} reabierto."

    def actualizar_precio_mes(self, mes_id: int, nuevo_precio: float, motivo: str = "", usuario: str = "USUARIO") -> Tuple[bool, str]:
        if nuevo_precio <= 0:
            return False, "El precio debe ser un número positivo."

        m = self.repo.get_by_id(mes_id)
        if not m:
            return False, "Período no encontrado."

        precio_ant = m.precio_menu_policial
        self.repo.update_precio(mes_id, nuevo_precio)

        self.audit_repo.registrar(
            accion="CAMBIO_PRECIO_MES",
            entidad="meses",
            entidad_id=str(mes_id),
            detalles=f"Modificado precio de {m.nombre_mes} de S/ {precio_ant:.2f} a S/ {nuevo_precio:.2f}. Motivo: {motivo}",
            usuario=usuario
        )

        return True, f"Precio del período {m.nombre_mes} actualizado a S/ {nuevo_precio:.2f}."
