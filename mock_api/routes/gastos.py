"""Rutas de lectura/escritura para la hoja Gastos."""

from fastapi import APIRouter
from mock_api.storage import GASTOS, IDEMPOTENCY_KEYS, get_next_fila

router = APIRouter()


def read_gastos(payload: dict) -> list[dict]:
    """Lee y filtra registros de gastos."""
    filtros = payload.get("filtros", {})
    campos = payload.get("campos")
    results = GASTOS.copy()

    if "mes" in filtros:
        results = [r for r in results if r["fecha"].startswith(filtros["mes"])]
    if "categoria" in filtros:
        results = [r for r in results if r["categoria"].lower() == filtros["categoria"].lower()]
    if "fecha_desde" in filtros:
        results = [r for r in results if r["fecha"] >= filtros["fecha_desde"]]
    if "fecha_hasta" in filtros:
        results = [r for r in results if r["fecha"] <= filtros["fecha_hasta"]]

    if campos:
        results = [{k: v for k, v in r.items() if k in campos or k == "fila"} for r in results]

    return results


def write_gasto(payload: dict) -> dict:
    """Inserta un registro de gasto."""
    registro = payload.get("registro", {})
    idem_key = payload.get("idempotency_key", "")

    if idem_key in IDEMPOTENCY_KEYS:
        return {
            "status": "success",
            "data": {
                "hoja": "Gastos",
                "registro": registro,
                "idempotency_key": idem_key,
                "duplicado": True,
            },
        }

    fila = get_next_fila("Gastos")
    new_record = {"fila": fila, **registro}
    GASTOS.append(new_record)
    IDEMPOTENCY_KEYS.add(idem_key)

    return {
        "status": "success",
        "data": {
            "hoja": "Gastos",
            "fila_insertada": fila,
            "registro": new_record,
            "idempotency_key": idem_key,
            "duplicado": False,
        },
    }
