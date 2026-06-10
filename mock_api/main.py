"""Mock Sheets API — Simula Google Sheets para desarrollo local."""

import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mock_api.routes import ventas, costos, gastos

app = FastAPI(title="BrewFinance Mock Sheets API", version="1.0.0")

# ─── Registrar rutas ───
app.include_router(ventas.router, prefix="/api/v1")
app.include_router(costos.router, prefix="/api/v1")
app.include_router(gastos.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "mock-sheets-api"}


@app.post("/api/v1/sheets/read")
async def sheets_read(request: Request):
    """Endpoint unificado de lectura — rutea a la hoja correcta."""
    body = await request.json()
    payload = body.get("payload", {})
    hoja = payload.get("hoja", "")
    start = time.time()

    if hoja == "Ventas":
        data = ventas.read_ventas(payload)
    elif hoja == "Costos":
        data = costos.read_costos(payload)
    elif hoja == "Gastos":
        data = gastos.read_gastos(payload)
    else:
        return JSONResponse(status_code=404, content={
            "request_id": body.get("request_id"),
            "status": "error",
            "error": {
                "code": "SHEET_NOT_FOUND",
                "message": f"Hoja '{hoja}' no existe. Válidas: Ventas, Costos, Gastos.",
            },
        })

    latency = int((time.time() - start) * 1000)
    return {
        "request_id": body.get("request_id"),
        "status": "success",
        "timestamp": body.get("timestamp"),
        "latency_ms": latency,
        "data": {"hoja": hoja, "total_registros": len(data), "registros": data},
    }


@app.post("/api/v1/sheets/write")
async def sheets_write(request: Request):
    """Endpoint unificado de escritura."""
    body = await request.json()
    payload = body.get("payload", {})
    hoja = payload.get("hoja", "")
    start = time.time()

    if hoja == "Ventas":
        result = ventas.write_venta(payload)
    elif hoja == "Gastos":
        result = gastos.write_gasto(payload)
    else:
        return JSONResponse(status_code=400, content={
            "request_id": body.get("request_id"),
            "status": "error",
            "error": {
                "code": "INVALID_SHEET",
                "message": f"No se puede escribir en '{hoja}'. Válidas: Ventas, Gastos.",
            },
        })

    latency = int((time.time() - start) * 1000)
    result["request_id"] = body.get("request_id")
    result["latency_ms"] = latency
    return result


@app.post("/api/v1/calc")
async def calculator(request: Request):
    """Endpoint del calculator — importado de cloud_functions."""
    from cloud_functions.calculator.main import handle_calculation
    body = await request.json()
    start = time.time()
    result = handle_calculation(body.get("payload", {}))
    latency = int((time.time() - start) * 1000)
    result["request_id"] = body.get("request_id")
    result["latency_ms"] = latency
    return result


@app.post("/api/v1/report")
async def report_gen(request: Request):
    """Endpoint del report generator — importado de cloud_functions."""
    from cloud_functions.report_generator.main import handle_report
    body = await request.json()
    start = time.time()
    result = handle_report(body.get("payload", {}))
    latency = int((time.time() - start) * 1000)
    result["request_id"] = body.get("request_id")
    result["latency_ms"] = latency
    return result
