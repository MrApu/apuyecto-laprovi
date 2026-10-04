from dataclasses import dataclass
from typing import Optional

@dataclass
class VentaDiaria:
    id: Optional[int] = None
    fecha: str = ""  # YYYY-MM-DD
    local_id: str = "restaurante"
    efectivo: float = 0.0
    yape: float = 0.0
    venta_sin_tickets: float = 0.0
    cantidad_tickets: int = 0
    precio_ticket_aplicado: float = 12.00
    venta_tickets: float = 0.0
    venta_total: float = 0.0
    venta_incluye_tickets: int = 0  # 0: NO (suma tickets a efectivo+yape), 1: SI (efectivo+yape ya los contiene)
    para_unidad: int = 0
    local: int = 0
    vales_consumidos: int = 0
    tickets_pagados: int = 0
    tickets_debidos: int = 0
    observaciones: Optional[str] = None
    fecha_actualizacion: Optional[str] = None
    # Compatibility aliases/fields
    menus_vendidos: Optional[int] = None
    policias: Optional[int] = None
    menus_sin_policias: Optional[int] = None
    precio_policial_aplicado: Optional[float] = None
    venta_policial_calculada: Optional[float] = None
    venta_sin_policias: Optional[float] = None
    vales_canjeados: Optional[int] = None

    def __post_init__(self):
        if self.vales_canjeados is not None:
            self.vales_consumidos = self.vales_canjeados
        else:
            self.vales_canjeados = self.vales_consumidos

        if self.precio_policial_aplicado is not None:
            self.precio_ticket_aplicado = float(self.precio_policial_aplicado)
        else:
            self.precio_policial_aplicado = self.precio_ticket_aplicado

        if self.policias is not None and not self.cantidad_tickets:
            self.cantidad_tickets = self.policias
        else:
            self.policias = self.cantidad_tickets or (self.para_unidad + self.local)

        if self.venta_policial_calculada is not None and not self.venta_tickets:
            self.venta_tickets = float(self.venta_policial_calculada)

        if self.venta_sin_policias is not None and not self.venta_sin_tickets:
            self.venta_sin_tickets = float(self.venta_sin_policias)

        if self.menus_vendidos is not None:
            self.menus_sin_policias = max(0, self.menus_vendidos - self.policias)
        else:
            self.menus_vendidos = self.policias
            self.menus_sin_policias = 0

    def recalcular(self, precio_ticket: Optional[float] = None, venta_incluye_tickets: Optional[int] = None):
        if precio_ticket is not None:
            self.precio_ticket_aplicado = float(precio_ticket)
            self.precio_policial_aplicado = self.precio_ticket_aplicado
        if venta_incluye_tickets is not None:
            self.venta_incluye_tickets = int(venta_incluye_tickets)

        self.cantidad_tickets = (self.para_unidad or 0) + (self.local or 0)
        self.policias = self.cantidad_tickets
        self.venta_tickets = round(self.cantidad_tickets * self.precio_ticket_aplicado, 2)
        self.venta_policial_calculada = self.venta_tickets

        efectivo_yape = round((self.efectivo or 0.0) + (self.yape or 0.0), 2)

        if self.venta_incluye_tickets == 1:
            # Efectivo + Yape YA incluye los tickets policiales
            if self.venta_total == 0.0 and efectivo_yape > 0:
                self.venta_total = efectivo_yape
            self.venta_sin_tickets = round(max(0.0, self.venta_total - self.venta_tickets), 2)
        else:
            # Default: NO incluye tickets -> Venta total = Efectivo + Yape + Venta Tickets
            if self.efectivo > 0 or self.yape > 0 or self.venta_sin_tickets == 0.0:
                self.venta_sin_tickets = efectivo_yape
            if self.venta_total == 0.0 or (self.efectivo > 0 or self.yape > 0):
                self.venta_total = round(self.venta_sin_tickets + self.venta_tickets, 2)

        self.venta_sin_policias = self.venta_sin_tickets
        if self.menus_vendidos is not None and self.menus_vendidos > self.policias:
            self.menus_sin_policias = self.menus_vendidos - self.policias

    @property
    def has_alerta_venta_negativa(self) -> bool:
        return self.venta_total < 0 or self.venta_sin_tickets < 0
