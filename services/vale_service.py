from typing import List, Optional, Tuple, Dict, Any
from repositories.vale_repository import ValeRepository
from repositories.auditoria_repository import AuditoriaRepository
from models.vale import Vale

class ValeService:
    def __init__(
        self,
        vale_repo: Optional[ValeRepository] = None,
        audit_repo: Optional[AuditoriaRepository] = None
    ):
        self.repo = vale_repo or ValeRepository()
        self.audit_repo = audit_repo or AuditoriaRepository()

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
