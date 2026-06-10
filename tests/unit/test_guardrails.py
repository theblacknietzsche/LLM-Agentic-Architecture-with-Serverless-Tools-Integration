"""Tests unitarios para guardrails del agente BrewFinance."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.agent.guardrails import validate_tool_call


class TestSheetsReaderGuardrails:
    def test_valid_read_ventas(self):
        result = validate_tool_call({
            "name": "sheets_reader",
            "args": {"hoja": "Ventas", "filtros": {"mes": "2026-06"}},
        })
        assert result.is_valid is True

    def test_valid_read_costos(self):
        result = validate_tool_call({
            "name": "sheets_reader",
            "args": {"hoja": "Costos"},
        })
        assert result.is_valid is True

    def test_reject_invalid_sheet(self):
        result = validate_tool_call({
            "name": "sheets_reader",
            "args": {"hoja": "Inventario"},
        })
        assert result.is_valid is False
        assert result.error_code == "SHEET_NOT_FOUND"

    def test_reject_missing_sheet(self):
        result = validate_tool_call({
            "name": "sheets_reader",
            "args": {},
        })
        assert result.is_valid is False
        assert result.error_code == "MISSING_PARAMS"

    def test_reject_invalid_canal_filter(self):
        result = validate_tool_call({
            "name": "sheets_reader",
            "args": {"hoja": "Ventas", "filtros": {"canal": "tienda"}},
        })
        assert result.is_valid is False
        assert result.error_code == "INVALID_FILTER"


class TestSheetsWriterGuardrails:
    def test_valid_sale_registration(self):
        result = validate_tool_call({
            "name": "sheets_writer",
            "args": {
                "hoja": "Ventas",
                "registro": {
                    "sabor": "mango", "cantidad": 10, "precio_unitario": 45.00,
                    "presentacion": "345ml", "canal": "gimnasio", "fecha": "2026-06-15",
                },
                "idempotency_key": "v-20260615-mango-10",
            },
        })
        assert result.is_valid is True

    def test_reject_negative_quantity(self):
        result = validate_tool_call({
            "name": "sheets_writer",
            "args": {
                "hoja": "Ventas",
                "registro": {"sabor": "mango", "cantidad": -5, "precio_unitario": 45.00,
                              "presentacion": "345ml", "canal": "gimnasio", "fecha": "2026-06-15"},
                "idempotency_key": "test-neg",
            },
        })
        assert result.is_valid is False
        assert result.error_code == "VALIDATION_FAILED"

    def test_reject_unknown_sabor(self):
        result = validate_tool_call({
            "name": "sheets_writer",
            "args": {
                "hoja": "Ventas",
                "registro": {"sabor": "uva", "cantidad": 5, "precio_unitario": 45.00,
                              "presentacion": "345ml", "canal": "gimnasio", "fecha": "2026-06-15"},
                "idempotency_key": "test-uva",
            },
        })
        assert result.is_valid is False
        assert result.error_code == "UNKNOWN_SABOR"

    def test_reject_write_to_costos(self):
        result = validate_tool_call({
            "name": "sheets_writer",
            "args": {
                "hoja": "Costos",
                "registro": {"sabor": "mango"},
                "idempotency_key": "test-costos",
            },
        })
        assert result.is_valid is False
        assert result.error_code == "INVALID_SHEET"

    def test_reject_unknown_canal(self):
        result = validate_tool_call({
            "name": "sheets_writer",
            "args": {
                "hoja": "Ventas",
                "registro": {"sabor": "mango", "cantidad": 5, "precio_unitario": 45.00,
                              "presentacion": "345ml", "canal": "tienda", "fecha": "2026-06-15"},
                "idempotency_key": "test-canal",
            },
        })
        assert result.is_valid is False
        assert result.error_code == "UNKNOWN_CANAL"

    def test_reject_excessive_price(self):
        result = validate_tool_call({
            "name": "sheets_writer",
            "args": {
                "hoja": "Ventas",
                "registro": {"sabor": "mango", "cantidad": 5, "precio_unitario": 999.00,
                              "presentacion": "345ml", "canal": "gimnasio", "fecha": "2026-06-15"},
                "idempotency_key": "test-price",
            },
        })
        assert result.is_valid is False
        assert result.error_code == "VALIDATION_FAILED"

    def test_reject_future_date(self):
        result = validate_tool_call({
            "name": "sheets_writer",
            "args": {
                "hoja": "Ventas",
                "registro": {"sabor": "mango", "cantidad": 5, "precio_unitario": 45.00,
                              "presentacion": "345ml", "canal": "gimnasio", "fecha": "2030-12-31"},
                "idempotency_key": "test-future",
            },
        })
        assert result.is_valid is False
        assert result.error_code == "VALIDATION_FAILED"

    def test_reject_missing_idempotency_key(self):
        result = validate_tool_call({
            "name": "sheets_writer",
            "args": {
                "hoja": "Ventas",
                "registro": {"sabor": "mango", "cantidad": 5},
            },
        })
        assert result.is_valid is False
        assert result.error_code == "MISSING_PARAMS"


class TestCalculatorGuardrails:
    def test_valid_operation(self):
        result = validate_tool_call({
            "name": "calculator",
            "args": {"operacion": "margen_por_sabor", "params": {"ventas": [], "costos": []}},
        })
        assert result.is_valid is True

    def test_reject_unknown_operation(self):
        result = validate_tool_call({
            "name": "calculator",
            "args": {"operacion": "roi_proyectado", "params": {}},
        })
        assert result.is_valid is False
        assert result.error_code == "UNKNOWN_OPERATION"

    def test_reject_missing_params(self):
        result = validate_tool_call({
            "name": "calculator",
            "args": {"operacion": "margen_por_sabor"},
        })
        assert result.is_valid is False
        assert result.error_code == "MISSING_PARAMS"


class TestReportGeneratorGuardrails:
    def test_valid_report(self):
        result = validate_tool_call({
            "name": "report_generator",
            "args": {"tipo_reporte": "resumen_mensual", "datos": {"periodo": "2026-06"}},
        })
        assert result.is_valid is True

    def test_reject_unknown_type(self):
        result = validate_tool_call({
            "name": "report_generator",
            "args": {"tipo_reporte": "forecast_anual", "datos": {}},
        })
        assert result.is_valid is False
        assert result.error_code == "UNKNOWN_REPORT_TYPE"
