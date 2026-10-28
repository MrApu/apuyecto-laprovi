from typing import List, Optional, Tuple, Dict, Any
from repositories.vale_repository import ValeRepository
from repositories.auditoria_repository import AuditoriaRepository
from repositories.vale_policia_repository import ValePoliciaRepository
from repositories.policia_repository import PoliciaRepository
from models.vale import Vale
from models.vale_policia import ValePolicia

class ValeService:
    def __init__(
        self,
        vale_repo: Optional[ValeRepository] = None,
        audit_repo: Optional[AuditoriaRepository] = None,
        vale_policia_repo: Optional[ValePoliciaRepository] = None,
        policia_repo: Optional[PoliciaRepository] = None
    ):
        self.repo = vale_repo or ValeRepository()
        self.audit_repo = audit_repo or AuditoriaRepository()
        self.vale_policia_repo = vale_policia_repo or ValePoliciaRepository()
        self.policia_repo = policia_repo or PoliciaRepository()

    # --- Métodos Diarios (Compatibilidad) ---
    def get_by_fecha(self, fecha: str) -> Optional[Vale]:
        return self.repo.get_by_fecha(fecha)

    def get_by_mes(self, anio: int, mes: int) -> List[Vale]:
        return self.repo.get_by_mes(anio, mes)

    def get_resumen_mes(self, anio: int, mes: int) -> dict:
        return self.repo.get_resumen_mes(anio, mes)

    def guardar_vale(
        self,
        fecha: str,
        vales_entregados: int,
        vales_canjeados: int,
        observacion: Optional[str] = None,
        usuario: str = "USUARIO"
    ) -> Tuple[bool, str, Vale]:
        if vales_entregados < 0 or vales_canjeados < 0:
            return False, "Las cantidades de vales no pueden ser negativas.", None

        saldo = vales_entregados - vales_canjeados
        v = Vale(
            fecha=fecha,
            vales_entregados=vales_entregados,
            vales_canjeados=vales_canjeados,
            saldo=saldo,
            observacion=observacion
        )

        self.repo.save(v)

        msg = "Vales guardados exitosamente."
        if saldo < 0:
            msg += " ⚠️ Advertencia: El saldo es negativo (se canjearon más vales de los entregados)."

        self.audit_repo.registrar(
            accion="GUARDAR_VALE",
            entidad="vales",
            entidad_id=fecha,
            detalles=f"Fecha {fecha}: Entregados={vales_entregados}, Canjeados={vales_canjeados}, Saldo={saldo}",
            usuario=usuario
        )

        return True, msg, v

    # --- Vales por Policía (Nuevo Módulo: a quién dimos vales por tickets) ---
    def registrar_vale_policia(
        self,
        policia_id: int,
        fecha: str,
        cantidad_vales: int,
        tickets_equivalentes: int,
        local_id: str = "restaurante",
        tipo_operacion: str = "ENTREGA",
        observacion: Optional[str] = None,
        usuario: str = "USUARIO"
    ) -> Tuple[bool, str, Optional[int]]:
        if cantidad_vales <= 0:
            return False, "La cantidad de vales debe ser mayor a 0.", None

        policia = self.policia_repo.get_by_id(policia_id)
        if not policia:
            return False, "Policía no encontrado.", None

        vale = ValePolicia(
            policia_id=policia_id,
            fecha=fecha,
            local_id=local_id,
            tipo_operacion=tipo_operacion,
            cantidad_vales=cantidad_vales,
            tickets_equivalentes=tickets_equivalentes,
            observacion=observacion
        )
        vale_id = self.vale_policia_repo.registrar(vale)

        self.audit_repo.registrar(
            accion="REGISTRAR_VALE_POLICIA",
            entidad="vales_policias",
            entidad_id=str(vale_id),
            detalles=f"Policía: {policia.apellidos}, {policia.nombres} ({policia.codigo}) | {cantidad_vales} vales dados por {tickets_equivalentes} tickets | Op: {tipo_operacion}",
            usuario=usuario
        )
        return True, f"Registro de {cantidad_vales} vales guardado exitosamente.", vale_id

    def actualizar_vale_policia(
        self,
        vale_id: int,
        policia_id: int,
        fecha: str,
        cantidad_vales: int,
        tickets_equivalentes: int,
        local_id: str = "restaurante",
        tipo_operacion: str = "ENTREGA",
        observacion: Optional[str] = None,
        usuario: str = "USUARIO"
    ) -> Tuple[bool, str]:
        if cantidad_vales <= 0:
            return False, "La cantidad de vales debe ser mayor a 0."

        vale = self.vale_policia_repo.get_by_id(vale_id)
        if not vale:
            return False, "El registro de vale no existe."

        vale.policia_id = policia_id
        vale.fecha = fecha
        vale.local_id = local_id
        vale.tipo_operacion = tipo_operacion
        vale.cantidad_vales = cantidad_vales
        vale.tickets_equivalentes = tickets_equivalentes
        vale.observacion = observacion

        self.vale_policia_repo.actualizar(vale)

        self.audit_repo.registrar(
            accion="ACTUALIZAR_VALE_POLICIA",
            entidad="vales_policias",
            entidad_id=str(vale_id),
            detalles=f"Modificado vale ID {vale_id}: {cantidad_vales} vales por {tickets_equivalentes} tickets, fecha {fecha}.",
            usuario=usuario
        )
        return True, "Registro de vale actualizado correctamente."

    def eliminar_vale_policia(self, vale_id: int, usuario: str = "USUARIO") -> Tuple[bool, str]:
        vale = self.vale_policia_repo.get_by_id(vale_id)
        if not vale:
            return False, "El registro de vale no existe."

        self.vale_policia_repo.eliminar(vale_id)
        self.audit_repo.registrar(
            accion="ELIMINAR_VALE_POLICIA",
            entidad="vales_policias",
            entidad_id=str(vale_id),
            detalles=f"Eliminado vale ID {vale_id} ({vale.cantidad_vales} vales) de policía ID {vale.policia_id}.",
            usuario=usuario
        )
        return True, "Registro de vale eliminado con éxito."

    def get_vales_policias(self, busqueda: Optional[str] = None, mes_prefijo: Optional[str] = None) -> List[ValePolicia]:
        return self.vale_policia_repo.get_all(busqueda=busqueda, mes_prefijo=mes_prefijo)

    def get_vales_by_policia(self, policia_id: int) -> List[ValePolicia]:
        return self.vale_policia_repo.get_by_policia(policia_id)
