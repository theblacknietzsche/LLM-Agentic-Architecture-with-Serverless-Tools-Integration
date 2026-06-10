"""Rutas de lectura para la hoja Costos (solo lectura)."""

from fastapi import APIRouter
from mock_api.storage import COSTOS

router = APIRouter()


def read_costos(payload: dict) -> list[dict]:
    """Lee y filtra registros de costos."""
    filtros = payload.get("filtros", {})
    campos = payload.get("campos")
    results = COSTOS.copy()

    if "sabor" in filtros:
        results = [r for r in results if r["sabor"].lower() == filtros["sabor"].lower()]
    if "presentacion" in filtros:
        results = [r for r in results if r["presentacion"] == filtros["presentacion"]]

    if campos:
        results = [{k: v for k, v in r.items() if k in campos} for r in results]

    return results
