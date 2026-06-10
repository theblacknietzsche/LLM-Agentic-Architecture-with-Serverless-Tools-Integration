"""Tests de integración para el Mock Sheets API."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi.testclient import TestClient
from mock_api.main import app

client = TestClient(app)


class TestHealthCheck:
    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestSheetsReader:
    def test_read_all_ventas(self):
        response = client.post("/api/v1/sheets/read", json={
            "request_id": "test-001",
            "timestamp": "2026-06-15T00:00:00Z",
            "payload": {"hoja": "Ventas"},
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["total_registros"] > 0

    def test_read_ventas_filtered_by_month(self):
        response = client.post("/api/v1/sheets/read", json={
            "request_id": "test-002",
            "timestamp": "2026-06-15T00:00:00Z",
            "payload": {"hoja": "Ventas", "filtros": {"mes": "2026-06"}},
        })
        assert response.status_code == 200
        registros = response.json()["data"]["registros"]
        for r in registros:
            assert r["fecha"].startswith("2026-06")

    def test_read_costos(self):
        response = client.post("/api/v1/sheets/read", json={
            "request_id": "test-003",
            "timestamp": "2026-06-15T00:00:00Z",
            "payload": {"hoja": "Costos"},
        })
        assert response.status_code == 200
        assert response.json()["data"]["total_registros"] == 10

    def test_read_invalid_sheet(self):
        response = client.post("/api/v1/sheets/read", json={
            "request_id": "test-004",
            "timestamp": "2026-06-15T00:00:00Z",
            "payload": {"hoja": "Inventario"},
        })
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "SHEET_NOT_FOUND"


class TestSheetsWriter:
    def test_write_venta(self):
        response = client.post("/api/v1/sheets/write", json={
            "request_id": "test-w01",
            "timestamp": "2026-06-15T00:00:00Z",
            "payload": {
                "hoja": "Ventas",
                "registro": {
                    "fecha": "2026-06-15", "sabor": "mango", "presentacion": "345ml",
                    "cantidad": 3, "precio_unitario": 45.00, "canal": "redes",
                },
                "idempotency_key": "test-write-001",
            },
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["duplicado"] is False

    def test_idempotency_duplicate(self):
        # Primera escritura
        payload = {
            "request_id": "test-w02",
            "timestamp": "2026-06-15T00:00:00Z",
            "payload": {
                "hoja": "Ventas",
                "registro": {
                    "fecha": "2026-06-15", "sabor": "fresa", "presentacion": "345ml",
                    "cantidad": 2, "precio_unitario": 45.00, "canal": "gimnasio",
                },
                "idempotency_key": "test-idem-001",
            },
        }
        client.post("/api/v1/sheets/write", json=payload)
        # Segunda escritura (mismo key)
        response = client.post("/api/v1/sheets/write", json=payload)
        assert response.json()["data"]["duplicado"] is True

    def test_write_to_costos_rejected(self):
        response = client.post("/api/v1/sheets/write", json={
            "request_id": "test-w03",
            "timestamp": "2026-06-15T00:00:00Z",
            "payload": {
                "hoja": "Costos",
                "registro": {"sabor": "mango"},
                "idempotency_key": "test-costos-001",
            },
        })
        assert response.status_code == 400


class TestCalculator:
    def test_margen_calculation(self):
        response = client.post("/api/v1/calc", json={
            "request_id": "test-c01",
            "timestamp": "2026-06-15T00:00:00Z",
            "payload": {
                "operacion": "margen_por_sabor",
                "params": {
                    "ventas": [{"sabor": "mango", "cantidad": 10, "precio_unitario": 45}],
                    "costos": [{"sabor": "mango", "costo_unitario_total": 17.50}],
                },
            },
        })
        assert response.status_code == 200
        assert response.json()["status"] == "success"
