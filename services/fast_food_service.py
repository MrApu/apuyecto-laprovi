from typing import List, Optional, Tuple, Dict, Any
from repositories.fast_food_repository import FastFoodRepository
from repositories.auditoria_repository import AuditoriaRepository
from models.fast_food_consumo import FastFoodConsumo

class FastFoodService:
    def __init__(
        self,
        ff_repo: Optional[FastFoodRepository] = None,
        audit_repo: Optional[AuditoriaRepository] = None
    ):
        self.repo = ff_repo or FastFoodRepository()
        self.audit_repo = audit_repo or AuditoriaRepository()

    def get_by_fecha(self, fecha: str) -> Optional[FastFoodConsumo]:
        return self.repo.get_by_fecha(fecha)

    def get_by_mes(self, anio: int, mes: int) -> List[FastFoodConsumo]:
        return self.repo.get_by_mes(anio, mes)

    def get_resumen_mes(self, anio: int, mes: int) -> dict:
        return self.repo.get_resumen_mes(anio, mes)

    def registrar_consumo_fast_food(
        self,
        fecha: str,
        tickets_local: int,
        vales_local: int,
        observacion: Optional[str] = None,
        usuario: str = "USUARIO"
    ) -> Tuple[bool, str, FastFoodConsumo]:
        if tickets_local < 0 or vales_local < 0:
            return False, "Las cantidades de tickets o vales no pueden ser negativas.", None

        ffc = FastFoodConsumo(
            fecha=fecha,
            tickets_local=tickets_local,
            vales_local=vales_local,
            observacion=observacion
        )
        self.repo.save(ffc)

        self.audit_repo.registrar(
            accion="REGISTRAR_CONSUMO_FAST_FOOD",
            entidad="fast_food_consumos",
            entidad_id=fecha,
            local_id="fast_food",
            detalles=f"Fast Food {fecha}: Tickets Local={tickets_local}, Vales Local={vales_local}, Total={ffc.total_consumido}",
            usuario=usuario
        )
        return True, "Consumo de Fast Food registrado exitosamente.", ffc

    def guardar_consumo(
        self,
        fecha: str,
        tickets_local: int,
        vales_local: int,
        observacion: Optional[str] = None,
        usuario: str = "USUARIO"
    ) -> Tuple[bool, str, FastFoodConsumo]:
        return self.registrar_consumo_fast_food(fecha, tickets_local, vales_local, observacion, usuario)
