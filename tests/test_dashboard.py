import pytest
from services.dashboard_service import DashboardService
from models.local import LOCAL_RESTAURANTE, LOCAL_FAST_FOOD, LOCAL_CONSOLIDADO

def test_dashboard_service_data():
    svc = DashboardService()
    for local in [LOCAL_RESTAURANTE, LOCAL_FAST_FOOD, LOCAL_CONSOLIDADO]:
        data = svc.get_dashboard_data(2026, 9, local)
        assert "kpis" in data
        assert "series" in data

        k = data["kpis"]
        s = data["series"]

        assert "venta_total" in k
        assert "total_egresos" in k
        assert "saldo_neto" in k
        assert "rentabilidad_pct" in k
        assert "total_tickets_policiales" in k

        assert len(s["dias"]) == 30  # Septiembre has 30 days
        assert len(s["ventas_total"]) == 30
        assert len(s["egresos_total"]) == 30
        assert len(s["saldos_netos"]) == 30
        assert len(s["efectivo"]) == 30
        assert len(s["yape"]) == 30
        assert len(s["compras"]) == 30
        assert len(s["gastos"]) == 30
        assert len(s["personal"]) == 30
        assert len(s["para_unidad"]) == 30
        assert len(s["local"]) == 30
        assert len(s["tickets_pagados"]) == 30
        assert len(s["tickets_debidos"]) == 30
        assert len(s["vales_canjeados"]) == 30

def test_dashboard_calculations():
    svc = DashboardService()
    data = svc.get_dashboard_data(2026, 9, LOCAL_CONSOLIDADO)
    k = data["kpis"]
    # Saldo neto = Venta total - Egresos
    expected_saldo = round(k["venta_total"] - k["total_egresos"], 2)
    assert k["saldo_neto"] == expected_saldo
