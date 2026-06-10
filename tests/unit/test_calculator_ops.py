"""Tests unitarios para las operaciones del calculator."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from cloud_functions.calculator.main import handle_calculation


class TestMargenPorSabor:
    def test_basic_margin(self):
        result = handle_calculation({
            "operacion": "margen_por_sabor",
            "params": {
                "ventas": [
                    {"sabor": "mango", "cantidad": 10, "precio_unitario": 45.00},
                    {"sabor": "fresa", "cantidad": 5, "precio_unitario": 45.00},
                ],
                "costos": [
                    {"sabor": "mango", "costo_unitario_total": 17.50},
                    {"sabor": "fresa", "costo_unitario_total": 19.00},
                ],
            },
        })
        assert result["status"] == "success"
        sabores = result["data"]["resultado"]
        assert len(sabores) == 2
        mango = next(s for s in sabores if s["sabor"] == "mango")
        assert mango["margen_porcentaje"] == pytest.approx(61.11, abs=0.01)
        assert mango["ingresos"] == 450.00

    def test_empty_ventas(self):
        result = handle_calculation({
            "operacion": "margen_por_sabor",
            "params": {"ventas": [], "costos": []},
        })
        assert result["status"] == "success"
        assert result["data"]["resultado"] == []


class TestPuntoEquilibrio:
    def test_basic_breakeven(self):
        result = handle_calculation({
            "operacion": "punto_equilibrio",
            "params": {
                "costos_fijos_mensuales": 350.00,
                "precio_unitario": 45.00,
                "costo_unitario": 17.50,
            },
        })
        assert result["status"] == "success"
        eq = result["data"]["resultado"]
        assert eq["unidades_equilibrio"] == 13
        assert eq["margen_contribucion_unitario"] == 27.50


class TestProyeccionVentas:
    def test_basic_projection(self):
        result = handle_calculation({
            "operacion": "proyeccion_ventas",
            "params": {
                "ventas_historicas": [
                    {"mes": "2026-04", "unidades": 35},
                    {"mes": "2026-05", "unidades": 40},
                    {"mes": "2026-06", "unidades": 43},
                ],
                "meses_a_proyectar": 3,
            },
        })
        assert result["status"] == "success"
        proy = result["data"]["resultado"]
        assert proy["tendencia"] == "creciente"
        assert len(proy["proyecciones"]) == 3
        assert proy["confianza"] == "baja"


class TestUnknownOperation:
    def test_unknown_op(self):
        result = handle_calculation({
            "operacion": "operacion_falsa",
            "params": {},
        })
        assert result["status"] == "error"
        assert result["error"]["code"] == "UNKNOWN_OPERATION"
