from typing import List, Optional, Tuple, Dict, Any
from repositories.compra_repository import CompraRepository
from repositories.gasto_repository import GastoRepository
from repositories.pago_personal_repository import PagoPersonalRepository
from repositories.auditoria_repository import AuditoriaRepository
from models.compra import Compra
from models.gasto import Gasto
from models.pago_personal import PagoPersonal
from models.local import LOCAL_CONSOLIDADO

class EgresoService:
    def __init__(
        self,
        compra_repo: Optional[CompraRepository] = None,
        gasto_repo: Optional[GastoRepository] = None,
        personal_repo: Optional[PagoPersonalRepository] = None,
        audit_repo: Optional[AuditoriaRepository] = None
    ):
        self.compra_repo = compra_repo or CompraRepository()
        self.gasto_repo = gasto_repo or GastoRepository()
        self.personal_repo = personal_repo or PagoPersonalRepository()
        self.pago_personal_repo = self.personal_repo
        self.audit_repo = audit_repo or AuditoriaRepository()

    def get_resumen_egresos_mes(self, anio: int, mes: int, local_id: Optional[str] = None) -> Dict[str, float]:
        res = self.get_totales_egresos_mes(anio, mes, local_id)
        return {
            "total_compras": res["compras"],
            "total_gastos": res["gastos"],
            "total_personal": res["personal"],
            "total_egresos": res["total_egresos"],
            "compras": res["compras"],
            "gastos": res["gastos"],
            "personal": res["personal"]
        }

    def get_compras_mes(self, anio: int, mes: int, local_id: Optional[str] = None) -> List[Compra]:
        return self.compra_repo.get_by_mes(anio, mes, local_id)

    def get_gastos_mes(self, anio: int, mes: int, local_id: Optional[str] = None) -> List[Gasto]:
        return self.gasto_repo.get_by_mes(anio, mes, local_id)

    def get_pagos_personal_mes(self, anio: int, mes: int, local_id: Optional[str] = None) -> List[PagoPersonal]:
        return self.personal_repo.get_by_mes(anio, mes, local_id)

    # --- Compras ---
    def registrar_compra(self, compra: Compra, usuario: str = "USUARIO") -> Tuple[bool, str, Optional[int]]:
        if compra.cantidad <= 0 or compra.precio_unitario < 0:
            return False, "La cantidad debe ser mayor a 0 y el precio no puede ser negativo.", None
        if not compra.proveedor.strip():
            return False, "El proveedor es obligatorio.", None

        if (compra.total or 0.0) > 0 and (compra.precio_unitario or 0.0) == 0.0:
            compra.precio_unitario = round(compra.total / (compra.cantidad or 1.0), 2)
        else:
            compra.total = round((compra.cantidad or 1.0) * (compra.precio_unitario or 0.0), 2)
        new_id = self.compra_repo.create(compra)

        self.audit_repo.registrar(
            accion="REGISTRAR_COMPRA",
            entidad="compras",
            entidad_id=str(new_id),
            local_id=compra.local_id,
            detalles=f"Compra {compra.proveedor}: {compra.descripcion} - Total: S/ {compra.total:.2f}",
            usuario=usuario
        )
        return True, "Compra registrada exitosamente.", new_id

    def eliminar_compra(self, compra_id: int, usuario: str = "USUARIO") -> Tuple[bool, str]:
        c = self.compra_repo.get_by_id(compra_id)
        if not c:
            return False, "Compra no encontrada."
        self.compra_repo.delete(compra_id)
        self.audit_repo.registrar(
            accion="ELIMINAR_COMPRA",
            entidad="compras",
            entidad_id=str(compra_id),
            local_id=c.local_id,
            detalles=f"Eliminada compra ID {compra_id}",
            usuario=usuario
        )
        return True, "Compra eliminada."

    # --- Gastos ---
    def registrar_gasto(self, gasto: Gasto, usuario: str = "USUARIO") -> Tuple[bool, str, Optional[int]]:
        if gasto.monto < 0:
            return False, "El monto del gasto no puede ser negativo.", None
        if not gasto.descripcion.strip():
            return False, "La descripción del gasto es obligatoria.", None

        new_id = self.gasto_repo.create(gasto)
        self.audit_repo.registrar(
            accion="REGISTRAR_GASTO",
            entidad="gastos",
            entidad_id=str(new_id),
            local_id=gasto.local_id,
            detalles=f"Gasto [{gasto.categoria}] {gasto.descripcion}: S/ {gasto.monto:.2f}",
            usuario=usuario
        )
        return True, "Gasto registrado exitosamente.", new_id

    def eliminar_gasto(self, gasto_id: int, usuario: str = "USUARIO") -> Tuple[bool, str]:
        g = self.gasto_repo.get_by_id(gasto_id)
        if not g:
            return False, "Gasto no encontrado."
        self.gasto_repo.delete(gasto_id)
        self.audit_repo.registrar(
            accion="ELIMINAR_GASTO",
            entidad="gastos",
            entidad_id=str(gasto_id),
            local_id=g.local_id,
            detalles=f"Eliminado gasto ID {gasto_id}",
            usuario=usuario
        )
        return True, "Gasto eliminado."

    # --- Pagos Personal ---
    def registrar_pago_personal(self, pago: PagoPersonal, usuario: str = "USUARIO") -> Tuple[bool, str, Optional[int]]:
        if pago.monto < 0:
            return False, "El monto del pago al personal no puede ser negativo.", None
        if not pago.trabajador.strip():
            return False, "El nombre del trabajador es obligatorio.", None

        new_id = self.personal_repo.create(pago)
        self.audit_repo.registrar(
            accion="REGISTRAR_PAGO_PERSONAL",
            entidad="pagos_personal",
            entidad_id=str(new_id),
            local_id=pago.local_id,
            detalles=f"Pago a {pago.trabajador} [{pago.concepto}]: S/ {pago.monto:.2f}",
            usuario=usuario
        )
        return True, "Pago a personal registrado exitosamente.", new_id

    def eliminar_pago_personal(self, pago_id: int, usuario: str = "USUARIO") -> Tuple[bool, str]:
        p = self.personal_repo.get_by_id(pago_id)
        if not p:
            return False, "Registro no encontrado."
        self.personal_repo.delete(pago_id)
        self.audit_repo.registrar(
            accion="ELIMINAR_PAGO_PERSONAL",
            entidad="pagos_personal",
            entidad_id=str(pago_id),
            local_id=p.local_id,
            detalles=f"Eliminado pago personal ID {pago_id}",
            usuario=usuario
        )
        return True, "Pago de personal eliminado."

    # --- Totales Consolidados de Egresos ---
    def get_totales_egresos_mes(self, anio: int, mes: int, local_id: Optional[str] = None) -> Dict[str, float]:
        compras = self.compra_repo.get_total_mes(anio, mes, local_id)
        gastos = self.gasto_repo.get_total_mes(anio, mes, local_id)
        personal = self.personal_repo.get_total_mes(anio, mes, local_id)
        total_egresos = round(compras + gastos + personal, 2)
        return {
            "compras": compras,
            "gastos": gastos,
            "personal": personal,
            "total_egresos": total_egresos
        }

    def get_totales_egresos_fecha(self, fecha: str, local_id: Optional[str] = None) -> Dict[str, float]:
        compras = self.compra_repo.get_total_fecha(fecha, local_id)
        gastos = self.gasto_repo.get_total_fecha(fecha, local_id)
        personal = self.personal_repo.get_total_fecha(fecha, local_id)
        total_egresos = round(compras + gastos + personal, 2)
        return {
            "compras": compras,
            "gastos": gastos,
            "personal": personal,
            "total_egresos": total_egresos
        }
