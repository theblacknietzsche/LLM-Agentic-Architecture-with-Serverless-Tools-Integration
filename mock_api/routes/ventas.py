"""Rutas de lectura/escritura para la hoja Ventas."""

from fastapi import APIRouter
from mock_api.storage import VENTAS, IDEMPOTENCY_KEYS, get_next_fila

router = APIRouter()


def read_ventas(payload: dict) -> list[dict]:
    """Lee y filtra registros de ventas."""
    filtros = payload.get("filtros", {})
    campos = payload.get("campos")
    limite = payload.get("limite", 100)
    results = VENTAS.copy()

    if "mes" in filtros:
        results = [r for r in results if r["fecha"].startswith(filtros["mes"])]
    if "sabor" in filtros:
        results = [r for r in results if r["sabor"].lower() == filtros["sabor"].lower()]
    if "canal" in filtros:
        results = [r for r in results if r["canal"].lower() == filtros["canal"].lower()]
    if "presentacion" in filtros:
        results = [r for r in results if r["presentacion"] == filtros["presentacion"]]
    if "fecha_desde" in filtros:
        results = [r for r in results if r["fecha"] >= filtros["fecha_desde"]]
    if "fecha_hasta" in filtros:
        results = [r for r in results if r["fecha"] <= filtros["fecha_hasta"]]

    # Agregar ingreso_total calculado
    for r in results:
        r["ingreso_total"] = round(r["cantidad"] * r["precio_unitario"], 2)

    # Filtrar campos si se especificaron
    if campos:
        results = [{k: v for k, v in r.items() if k in campos or k == "fila"} for r in results]

    return results[:limite]


def write_venta(payload: dict) -> dict:
    """Inserta un registro de venta."""
    registro = payload.get("registro", {})
    idem_key = payload.get("idempotency_key", "")

    # Idempotencia
    if idem_key in IDEMPOTENCY_KEYS:
        return {
            "status": "success",
            "data": {
                "hoja": "Ventas",
                "registro": registro,
                "idempotency_key": idem_key,
                "duplicado": True,
                "message": "Registro ya existente. No se creó duplicado.",
            },
        }

    # Insertar
    fila = get_next_fila("Ventas")
    new_record = {"fila": fila, **registro}
    new_record["ingreso_total"] = round(
        registro.get("cantidad", 0) * registro.get("precio_unitario", 0), 2
    )
    VENTAS.append(new_record)
    IDEMPOTENCY_KEYS.add(idem_key)

    return {
        "status": "success",
        "data": {
            "hoja": "Ventas",
            "fila_insertada": fila,
            "registro": new_record,
            "idempotency_key": idem_key,
            "duplicado": False,
        },
    }
